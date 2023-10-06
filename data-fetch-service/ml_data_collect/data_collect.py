import csv_helper
import data_constants
import requests
import json
import re
import time

player_url = "http://localhost:8000/api/lol/players"
games_url = "http://localhost:8000/api/lol/teams/games"
champions_matchup_url = "http://localhost:8000/api/lol/champions/matchup"
champions_url = "http://localhost:8000/api/lol/champions"

def fetch_games(region=None, team_name = None, year = None, before = None, limit = None, aggregate = False):
    params = {}
    
    if region:
        params["region"] = region
    if team_name:
        params["team_name"] = team_name
    if year:
        params["year"] = year
    if before:
        params["before"] = before
    if limit:
        params["limit"] = limit
    if aggregate:
        params["aggregate"] = aggregate
    
    return make_get_request(games_url, params)
    
def start_data_collect():
    # Commented out because we start with one game first
    # for year in data_constants.years:
    #     for region in data_constants.regions:
    #         games = fetch_games(region, year=year, limit=data_constants.total_games)
    #         for game in games:

    game = fetch_games(region="China", year="2023", limit=data_constants.total_games_per_year)
    
    # gathered 250 games from:
    #   KOREA
    # To Do:
    #   NA <- NOW
    #   EUW
    #   CHINA
    for i in range(0, 250):
        start_time = time.time()

        csv_helper.append_to_csv(start_core_loop(game[i], "2023"))

        total_time = time.time() - start_time
        print(f"Process finished {i} --- {total_time} seconds ---")
        csv_helper.append_to_timer(total_time)

    
def start_core_loop(game, year):
    if not game:
        print("No game found")
        return
    game_dto = csv_helper.create_game_data_dto()
    
    team_one = game["Team1"]
    team_two = game["Team2"]
    
    if game["WinTeam"] != team_one["Name"]:
        game_dto["teamA_win"] = "0"
    else:
        game_dto["teamA_win"] = "1"
    
    before = game["DateTime UTC"]
    kpa_team_a = []
    kpa_team_b = []
    
    # PLAYER SPECIFIC DATA - 22 requests total
    hydrate_player_specific_data(before, year, team_one, "teamA", game_dto, kpa_team_a)
    hydrate_player_specific_data(before, year, team_two, "teamB", game_dto, kpa_team_b)
    
    # TEAM SPECIFIC DATA
    hydrate_team_specific_data(before, year, team_one, "teamA", game_dto, kpa_team_a)
    hydrate_team_specific_data(before, year, team_two, "teamB", game_dto, kpa_team_b)
    
    # CHAMP SPECIFIC DATA
    hydrate_champ_specific_data(before, year, team_one, team_two, "teamA", "teamB", game_dto)
    print(game_dto)
    return game_dto
    
def hydrate_player_specific_data(before, year, team_data, team_name, game_dto, kpa):
    ingame_playernames = re.sub(r'\([^)]*\)', '', team_data["Players"])
    players = ingame_playernames.split(",")
    champions = team_data["Picks"].split(",")
    
    past_years_games = fetch_games(team_name=team_data.get("Name", None), before=before, year=year, limit=500) 
    
    for i in range(len(data_constants.index_to_lane)):
        
        params = {
            "before" : before,
            "aggregate" : "false",
            "year": year,
            "playername" : players[i],
            "limit" : "10",
        }
        
        player_prefix = f"{team_name}_{data_constants.index_to_lane[i]}"
        
        # General winrate 10 games
        # General winrate 50 games
        # Num games played on champ past 50 games
        params["limit"] = "50"
        
        res = make_get_request(player_url, params)
        num_played_on_champ = 0
        wins_50 = 0
        wins_10 = 0
        total_kills = 0
        total_assists = 0
        for j in range(len(res)):
            if res[j].get("Champion", "None") == champions[i]:
                num_played_on_champ += 1
            if res[j].get("Wins", None) == "Yes":
                if j < 10:
                    wins_10 += 1
                    k = res[j].get("Kills", None)
                    a = res[j].get("Assists", None)
                    
                    if k == None:
                        k = 0
                    if a == None:
                        a = 0
                        
                    total_kills += float(k)
                    total_assists += float(a)
                wins_50 += 1
        
        kpa.append((total_kills / 10 if len(res) >= 10 else len(res)) + (total_assists / 10 if len(res) >= 10 else len(res)))
        

        if len(res) > 0:
            game_dto[f"{player_prefix}_winrate_past_10_games"] = str(round(wins_10 / min(10, len(res)), 2))
        else:
            game_dto[f"{player_prefix}_winrate_past_10_games"] = '50.00'

        if len(res) > 0:
            game_dto[f"{player_prefix}_winrate_past_50_games"] = str(round(wins_50 / len(res), 2))
        else:
            game_dto[f"{player_prefix}_winrate_past_50_games"] = '50.00'

        game_dto[f"{player_prefix}_num_games_played_on_champ_past_50_games"] = str(num_played_on_champ)

        
        
        # Champ winrate past 50
        # Champ winrate past 10
        # Past 10 games stats
        params["champion"] = champions[i]
        res = make_get_request(player_url, params)
        wins_50 = 0
        wins_10 = 0
        kills = 0
        assists = 0
        deaths = 0
        gold = 0
        game_length = 0
        for j in range(len(res)):
            if res[j].get("Wins", None) == "Yes":
                if j < 10:
                    wins_10 += 1
                wins_50 += 1
                if j < 10:
                    k = res[j].get("Kills", "0")
                    a = res[j].get("Assists", "0")
                    d = res[j].get("Deaths", "0")
                    g = res[j].get("Gold", "0")
                    if k == None:
                        k = 0
                    if a == None:
                        a = 0
                    if d == None:
                        d = 0
                    if g == None:
                        g = 0
                        
                    kills += float(k)
                    assists += float(a)
                    deaths += float(d)
                    gold += float(g)
                    
                    time = res[j].get("Gamelength", "0:00")
                    if time == None:
                        time = "0:00"
                    minutes, seconds = map(int, time.split(':'))
                    total_minutes = minutes + seconds / 60
                    game_length += total_minutes

        if len(res) > 0:
            game_dto[f"{player_prefix}_winrate_on_champ_past_50_games"] = str(round(wins_50 / len(res), 2))
        else:
            game_dto[f"{player_prefix}_winrate_on_champ_past_50_games"] = "50.0"

        if len(res) >= 10:
            game_dto[f"{player_prefix}_winrate_on_champ_past_10_games"] = str(round(wins_10 / len(res), 2))
        else:
            game_dto[f"{player_prefix}_winrate_on_champ_past_10_games"] = "50.0"
        
        if len(res) > 0:
            divisor = 10 if len(res) >= 10 else len(res)
            kills /= divisor
            assists /= divisor
            deaths /= divisor
            gold /= divisor
            game_length /= divisor
        else:
            kills = 0
            assists = 0
            deaths = 0
            gold = 0
            game_length = 0
        
        # KDA
        kda = (kills + assists) / deaths if deaths > 0 else 0
        game_dto[f"{player_prefix}_kda_on_champ_past_10_games"] = str(round(kda, 2))
        
        # GOLD/MIN
        gold_per_min = gold / game_length if game_length > 0 else 0
        game_dto[f"{player_prefix}_gold_per_min_on_champ_past_10_games"] = str(round(gold_per_min, 2))
        
        # Calculate KPA
        game_count = 0
        team_kills = 0
        for game in past_years_games:
            if game_count >= 10:
                break
            
            curr_game = game.get("Team1", None)
   
            if champions[i] in curr_game.get("Picks", None) and  players[i] in curr_game.get("Players", None) :
                game_count += 1
                curr_game_kills = curr_game.get("Kills", 0)
                if curr_game_kills == None:
                    curr_game_kills = 0
                team_kills += int(curr_game_kills)

        # KPA
        kill_participation = ((kills + assists) / float(team_kills / game_count)) if (game_count > 0 and team_kills > 0) else 0
        game_dto[f"{player_prefix}_kill_participation_on_champ_past_10_games"] = str(round(kill_participation, 2))
        
def hydrate_team_specific_data(before, year, team_data, team_name, game_dto, kpa):
    # Win 50 game
    res = fetch_games(before=before, year=year, limit=50, team_name=team_data.get("Name", None), aggregate=False)
    
    win_10 = 0
    win_50 = 0
    gold = 0
    team_kills = 0
    gamelength = 0
    for i in range(len(res)):
        if i < 10:
            tk = res[i].get("Team1", None).get("Kills", 0)
            g = res[i].get("Team1", None).get("Gold", 0)
            
            if tk == None:
                tk = 0
            team_kills += float(tk)
            
            if g == None:
                g = 0
            gold += float(g)
            
            time = res[i].get("Gamelength", "0:00")
            if time == None:
                time = "0:00"
            minutes, seconds = map(int, time.split(':'))
            total_minutes = minutes + seconds / 60
            gamelength += total_minutes
            
        if res[i].get("WinTeam", None) == team_data.get("Name", None):
            win_50 += 1
            if i < 10:
                win_10 += 1
                
    team_kills /= 10 if len(res) >= 10 else len(res)
    gold /= 10 if len(res) >= 10 else len(res)
    gamelength /= 10 if len(res) >= 10 else len(res)
                
    game_dto[f"{team_name}_winrate_past_50_games"] = str(round(win_50 / len(res), 2))
    game_dto[f"{team_name}_winrate_past_10_games"] = str(round(win_10 / (10 if len(res) >= 10 else len(res)), 2))
    game_dto[f"{team_name}_average_gold_per_min_past_10_games"] = str(round(gold / gamelength, 2))

    total_kpa = 0
    for individual_kpa in kpa:
        total_kpa += individual_kpa / team_kills
        
    game_dto[f"{team_name}_average_kill_participation_past_10_games"] = str(round(total_kpa / len(data_constants.index_to_lane), 2))
    
def hydrate_champ_specific_data(before, year, teamA_data, teamB_data, teamA_name, teamB_name, game_dto):
    roles = ["Top", "Jungle", "Mid", "Bot", "Support"]
    teamAChampions = dict(zip(roles, teamA_data["Picks"].split(",")))
    teamBChampions = dict(zip(roles, teamB_data["Picks"].split(",")))

    idx = 0
    for key in teamAChampions:
        # champion vs champion matchup specific winrates
        params = {
                "before" : before,
                "year": year,
                "champion_ally": teamAChampions.get(key),
                "champion_enemy": teamBChampions.get(key),
                "role": key
            }      
        res = average(make_get_request(champions_matchup_url, params))
        game_dto[f"{data_constants.index_to_lane[idx]}_matchup_winrate_pro_current_season"] = str(res.get("Wins", 0))

        # champion winrates 50 games
        params =  {
            "before" : before,
            "year": year,
            "champion": teamAChampions.get(key),
            "limit": 50
        }
        teamA50GamesRaw = make_get_request(champions_url, params)
        teamA10GamesRaw = teamA50GamesRaw[:10] if len(teamA50GamesRaw) >= 10 else teamA50GamesRaw

        res = average(teamA50GamesRaw)
        game_dto[f"{teamA_name}_{data_constants.index_to_lane[idx]}_winrate_pro_past_50_games"] = str(res.get("Wins", 0))

        res = average(teamA10GamesRaw)
        game_dto[f"{teamA_name}_{data_constants.index_to_lane[idx]}_winrate_pro_past_10_games"] = str(res.get("Wins", 0))

        params =  {
            "before" : before,
            "year": year,
            "champion": teamBChampions.get(key),
            "limit": 50
        }
        teamB50GamesRaw = make_get_request(champions_url, params)
        teamB10GamesRaw = teamB50GamesRaw[:10] if len(teamB50GamesRaw) >= 10 else teamB50GamesRaw

        res = average(teamB50GamesRaw)
        game_dto[f"{teamB_name}_{data_constants.index_to_lane[idx]}_winrate_pro_past_50_games"] = str(res.get("Wins", 0))

        res = average(teamB10GamesRaw)
        game_dto[f"{teamB_name}_{data_constants.index_to_lane[idx]}_winrate_pro_past_10_games"] = str(res.get("Wins", 0))

        idx += 1

def make_get_request(url, params):
    response = requests.get(url, params=params)

    if response.status_code == 200:
        response_json_dict = json.loads(response.content)
        # Handling cases where no data is on that player
        if response_json_dict["length"] == 0:
            response_json_dict["data"] = {}    
        
        return response_json_dict["data"]
    else:
        print(f"Request failed with status code: {response.status_code}")
        return 

def average(data):
    total_wins = sum(1 if entry['Wins'].lower() == 'yes' else 0 for entry in data)
    average_wins = total_wins / len(data) if len(data) > 0 else 0

    average_wins_dict = {"Wins": average_wins}
    return average_wins_dict


if __name__ == "__main__":
    start_data_collect()
