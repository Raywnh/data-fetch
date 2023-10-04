def average(data):
    sum_res = {}
    win_loss_map = {"Yes": 1, "No": 0}
    
    # Convert Wins to float, game length to minutes
    for entry in data:
        outcome = entry["Wins"]
        entry["Wins"] = win_loss_map[outcome]
        
        game_length = entry["Gamelength"]
        entry["Gamelength"] = split_time_into_min(game_length)
        
    # Sum
    for entry in data:
        for key, value in entry.items():
            try:
                if value != None:
                    float_val = float(value) 
                else:
                    float_val = 0
                if key not in sum_res:
                    sum_res[key] = float_val
                else:
                    sum_res[key] += float_val
            except:
                sum_res[key] = value 
    
    # Average
    number_of_games = len(data)
    average_res = {}

    for key in sum_res:
        if isinstance(sum_res[key], float):
            average_res[f"{key}"] = round((sum_res[key] / number_of_games), 2)
        else:
            average_res[f"{key}"] = sum_res[key]
            
    average_res["Total games"] = number_of_games
    average_res["Total Losses"] = number_of_games - sum_res["Wins"]
    average_res["Total Wins"] = sum_res["Wins"]

    
    return average_res

def split_time_into_min(time: str):
    minutes, seconds = map(int, time.split(':'))
    total_minutes = minutes + seconds / 60
    return total_minutes