from collections import OrderedDict
import csv

file_path = '200.csv'

def append_to_csv(game_data: OrderedDict):
    with open(file_path, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=game_data.keys())
        writer.writerow(game_data)
    csvfile.close()
    
def create_game_data_dto():
    with open(file_path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)

    data_dict = OrderedDict((col, "") for col in header)
    return data_dict

def append_to_timer(time):
    with open('timer.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([time])