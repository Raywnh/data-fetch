import json
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from mwrogue.esports_client import EsportsClient
from parser.lol import aggregate_data

site = EsportsClient("lol")

def get_champion_matchup_data(champion1_unfiltered: str,champion2_unfiltered: str, role: str, region: str, patch: str, limit: int , year: str, before: str, aggregate: bool):
    champion1 = champion1_unfiltered.replace("'", "\\'")
    champion2 = champion2_unfiltered.replace("'", "\\'")

    query_fields = "SP.Link, SPVs.Link=LinkVs, SP.Champion, SPVs.Champion=ChampionVs, SP.PlayerWin=Wins, SP.GameId, SG.Patch, SP.DateTime_UTC, SG.Gamelength, SP.Kills, SPVs.Kills=KillsVs, SP.Deaths, SPVs.Deaths=DeathsVs, SP.Assists, SPVs.Assists=AssistsVs, SP.CS, SPVs.CS=CSVs, SP.Gold, SPVs.Gold=GoldVs"
    where_clause = []
    where_clause.append(f"SP.Champion='{champion1}'")
    where_clause.append(f"SPVs.Champion='{champion2}'")

    if patch:
        where_string = ""  
        integer_part = int(patch.split('.')[0])

        for i in range(1, 25):
            where_string += f" SG.Patch='{integer_part}.{i}' OR "
        where_string = where_string[:-4]
        where_clause.append("(" + where_string + ")")
    if role:
        where_clause.append(f"SP.Role='{role}'")
        where_clause.append(f"SPVs.Role='{role}'")
    if year:
        where_clause.append(f"SP.DateTime_UTC < '{str(int(year) + 1)}-01-00 01:00:00'")
        where_clause.append(f"SP.DateTime_UTC >= '{year}-01-00 01:00:00'")
    if region:
        where_clause.append(f"T.Region='{region}'")
    if before:
        where_clause.append(f"SP.DateTime_UTC < '{before}'")
    if aggregate:
        query_fields = query_fields.replace("SP.Link,", "")
        query_fields = query_fields.replace("SP.GameId,", "")
        query_fields = query_fields.replace("SG.Patch,", "")
        query_fields = query_fields.replace("SPVs.Link=LinkVs,", "")
        query_fields = query_fields.replace("SP.DateTime_UTC,", "")
        query_fields = query_fields.strip(" ")

    where_clause.append(f"T.TournamentLevel='Primary'")
    data = site.cargo_client.query(
        tables="ScoreboardPlayers=SP, ScoreboardPlayers=SPVs, ScoreboardGames=SG, Tournaments=T",
        join_on="SP.OverviewPage=T.OverviewPage,SP.UniqueRoleVs=SPVs.UniqueRole, SG.GameId=SP.GameId",
        fields= query_fields,
        where=' AND '.join(where_clause),
        limit={limit},
        order_by="SP.DateTime_UTC DESC"
    )
    response = data
    
    if aggregate:
        response = aggregate_data.average(data)

    api_response = {
        "length" : len(data),
        "data": jsonable_encoder(response)
    }
    return JSONResponse(content=api_response, media_type="application/json")

def get_champion_data(champion: str, region: str, limit: int, aggregate: bool, year: str, before: str):
    query_fields = "SP.Name, SP.Team, SP.Champion, SP.Kills, SP.Deaths, SP.Assists, SP.Gold, SP.CS, SP.PlayerWin=Wins, SP.Role, T.Region, SP.GameId, SG.Gamelength, SP.DateTime_UTC"
    where_clause = []
    if champion:
        champion = champion.replace("'", "\\'")        
        where_clause.append(f"SP.Champion='{champion}'")
    if region:
        where_clause.append(f"T.Region='{region}'")
    if year:
        where_clause.append(f"SP.DateTime_UTC < '{str(int(year) + 1)}-01-00 01:00:00'")
        where_clause.append(f"SP.DateTime_UTC >= '{year}-01-00 01:00:00'")
    if before:
        where_clause.append(f"SP.DateTime_UTC < '{before}'")
    if aggregate:
        query_fields = query_fields.replace("SP.Name,", "")
        query_fields = query_fields.replace("SP.Team,", "")
        query_fields = query_fields.replace("SP.Side,", "")
        query_fields = query_fields.replace("SP.Role,", "")
        query_fields = query_fields.replace("SP.GameId,", "")
        if not region:
            query_fields = query_fields.replace("T.Region", "")
        query_fields = query_fields.replace("SP.DateTime_UTC", "")
        query_fields = query_fields.strip(" ")

    where_clause.append(f"T.TournamentLevel='Primary'")
    
    data = site.cargo_client.query(
        tables="ScoreboardPlayers=SP, Tournaments=T, ScoreboardGames=SG",
        join_on="SP.OverviewPage=T.OverviewPage, SG.GameId=SP.GameId",
        fields=query_fields,
        where=' AND '.join(where_clause),
        limit={limit},
        order_by="SP.DateTime_UTC DESC"
    )
     
    response = data

    if len(response) != 0 and aggregate:
        response = aggregate_data.average(data)
    
    api_response = {
        "length" : len(data),
        "data": jsonable_encoder(response)
    }
    return JSONResponse(content=api_response, media_type="application/json")

def get_player_data(playername: str, champion: str, limit: int, patch: str, aggregate: bool, year: str, before: str):
    query_fields = "SP.Name, SP.Champion, SP.Kills, SP.Deaths, SP.Assists, SP.Gold, SP.CS, SP.PlayerWin=Wins, SP.Role, SP.Side, SP.MatchId, SG.Gamelength, SG.Patch, SG.DateTime_UTC"
    where_clause=[]
    if playername:
        where_clause.append(f"SP.Name='{playername}'")
    if champion:
        champion = champion.replace("'", "\\'")        
        where_clause.append(f"SP.Champion='{champion}'")
    if patch:
        where_clause.append(f"SG.Patch='{patch}'")
    if year:
        where_clause.append(f"SG.DateTime_UTC < '{str(int(year) + 1)}-01-00 01:00:00'")
        where_clause.append(f"SG.DateTime_UTC >= '{year}-01-00 01:00:00'")
    if before:
        where_clause.append(f"SG.DateTime_UTC < '{before}'")
    if aggregate:
        query_fields = query_fields.replace("SP.Side,", "")
        query_fields = query_fields.replace("SP.MatchId,", "")
        query_fields = query_fields.replace("SG.DateTime_UTC", "")
        if not champion:
            query_fields = query_fields.replace("SP.Champion", "")
        query_fields = query_fields.strip(" ")
        
    where_clause.append(f"T.TournamentLevel='Primary'")
    
    data = site.cargo_client.query(
        tables="ScoreboardPlayers=SP, ScoreboardGames=SG, Tournaments=T",
        join_on="SP.OverviewPage=SG.OverviewPage, SG.OverviewPage=T.OverviewPage, SG.GameId=SP.GameId",
        fields=query_fields,
        where=' AND '.join(where_clause),
        limit={limit},
        order_by='SG.DateTime_UTC DESC'
    )
    
    response = data
    
    if len(response) != 0 and aggregate:
        response = aggregate_data.average(data)
    
    api_response = {
        "length" : len(data),
        "data": jsonable_encoder(response)
    }
    return JSONResponse(content=api_response, media_type="application/json")

def get_team_games(team_name: str, region: str, limit: int, aggregate: bool, year: str, before: str):
    query_fields = "SG.WinTeam, SG.LossTeam, TO.Region, SG.Team1, SG.Team1Players, SG.Team1Bans, SG.Team1Picks, SG.Team1Gold, SG.Team1Kills, SG.Team2, SG.Team2Players, SG.Team2Bans, SG.Team2Picks, SG.Team2Gold, SG.Team2Kills, SG.Gamelength, SG.MatchId, SG.Patch, SG.DateTime_UTC"
    where_clause = []
    
    if team_name:
        where_clause.append(f"SG.WinTeam='{team_name}' OR SG.LossTeam='{team_name}'")
    if region:
        where_clause.append(f"TO.Region='{region}'")
    if year:
        where_clause.append(f"SG.DateTime_UTC < '{str(int(year) + 1)}-01-00 01:00:00'")
        where_clause.append(f"SG.DateTime_UTC >= '{year}-01-00 01:00:00'")
    if before:
        where_clause.append(f"SG.DateTime_UTC < '{before}'")
   
    where_clause.append(f"TO.TournamentLevel='Primary'")
    data = site.cargo_client.query(
        tables="ScoreboardGames=SG, Tournaments=TO",
        join_on="TO.OverviewPage=SG.OverviewPage",
        fields=query_fields,
        where=' AND '.join(where_clause),
        limit={limit},
        order_by='SG.DateTime_UTC DESC'
    )

    # Swap team data if team1 is not team
    modified_data = []
    team_sub_stats = ["Players", "Bans", "Picks", "Gold", "Kills"]
    for match in data:
        if match["Team2"] == team_name:
            for substat in team_sub_stats:    
                team1_stat = match["Team1" + substat]
                match["Team1" + substat] = match["Team2" + substat]
                match["Team2" + substat] = team1_stat
            team1 = match["Team1"]
            match["Team1"] = match["Team2"]
            match["Team2"] = team1
                
        match["Team1"] = {"Name": match["Team1"]}
        match["Team2"] = {"Name": match["Team2"]}
        
        for subfield in team_sub_stats:    
            match["Team1"][subfield] = match["Team1" + subfield]
            match["Team2"][subfield] = match["Team2" + subfield]
            match.pop("Team1" + subfield)
            match.pop("Team2" + subfield)

        modified_data.append(match)

    response = modified_data

    if team_name and aggregate and len(response) != 0:
        total_winners = 0
        total_matches = len(modified_data)
        total_gold = 0
        total_kills = 0
        game_length = 0
        
        for match in modified_data:
            if team_name == match["WinTeam"]:
                total_winners += 1
            total_gold += float(match["Team1"]["Gold"])
            total_kills += float(match["Team1"]["Kills"])
            game_length += aggregate_data.split_time_into_min(match["Gamelength"])
            
        if total_matches > 0:
            average_winner = total_winners / total_matches
            average_game_length = game_length / total_matches
        else:
            average_winner = 0
            
        response = {
            "Team": team_name,
            "Players": modified_data[0]["Team1"]["Players"],
            "Average Gold": total_gold / total_matches,
            "Average Kills": total_kills / total_matches,
            "Average Team Winrate": average_winner,
            "Average Game Length": average_game_length
            }
  
    api_response = {
        "length" : len(data),
        "data": jsonable_encoder(response)
    }

    return JSONResponse(content=api_response, media_type="application/json")

def get_team_regions(region: str, limit: int, year: str):
    query_fields = "TR.Team, T.Region, TR.RosterLinks, T.Year"
    where_clause = []
    if region:
        where_clause.append(f"T.Region='{region}'")
    if year:
        where_clause.append(f"T.Year='{year}'")
  
    where_clause.append(f"Teams.Name=TR.Team")
    
    data = site.cargo_client.query(
        tables="TournamentRosters=TR, Tournaments=T, Teams=Teams",
        join_on="TR.Tournament=T.Name, Teams.Name=TR.Team",
        fields=query_fields,
        where=' AND '.join(where_clause),
        group_by="TR.Team", 
        limit={limit},
        order_by="T.Year DESC"
    )
    response = data
    
    for teams in data:
        teams["RosterLinks"] = str(teams["RosterLinks"]).split(";;")
    api_response = {
        "length" : len(data),        
        "data": jsonable_encoder(response)
    }
    return JSONResponse(content=api_response, media_type="application/json")
