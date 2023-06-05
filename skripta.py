import requests
from pymongo import MongoClient
from config import config
import sys
import time

sys.setrecursionlimit(100000)

api_key = config['api_key']
mongodb_host = config['mongodb']['host']
mongodb_port = config['mongodb']['port']
mongodb_db = config['mongodb']['db']

region = 'europe'

# spajanje s mongodb
client = MongoClient(mongodb_host, mongodb_port)
db = client[mongodb_db]
matches_collection = db["lol"]

# dohvacanje podataka pomocu matchId
def get_match_data(match_id):
    url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={api_key}"
    response = requests.get(url)
    match_data = response.json()
    return match_data

# rekurzivna funkcija za pozivanje get_match_data
def gather_match_data(match_id):
        match_data = get_match_data(match_id)
        if match_data:
            matches_collection.insert_one(match_data)
            print(f"Match with ID {match_id} fetched and saved.")
            # Wait for 1.5 seconds
            time.sleep(1.5)
            # Run gather_match_data for the new match ID
            gather_match_data(increment_match_id(match_id))
        else:
            print(f"Failed to fetch match with ID {match_id}. Skipping...")

#bruteforce mijenjanje matchid-a
def increment_match_id(match_id):
    prefix, number = match_id.split("_")
    number = int(number)
    number += 1
    return f"{prefix}_{number}"

start_match_id = "EUN1_3377732531"


gather_match_data(start_match_id)
