from pymongo import MongoClient
from config import config

mongodb_host = config['mongodb']['host']
mongodb_port = config['mongodb']['port']
mongodb_db = config['mongodb']['db']
client = MongoClient(mongodb_host, mongodb_port)

source_collection = client['lol']['lol']

target_collection = client['lol']['sum']

pipeline = [
    {
        "$match": {
            "info.mapId": 11, #mapa 5v5
            "info.gameMode":"CLASSIC",
            "info.gameType": "MATCHED_GAME"            
        }
    },
    {
        '$unwind': '$info.participants'
    },
    {
        '$group': {
            '_id': {
                'matchId': '$metadata.matchId',
                'win': '$info.participants.win'
            },
            'allInPings': {'$sum': '$info.participants.allInPings'},
            'assists': {'$sum': '$info.participants.assists'},
            'champExperience': {'$sum': '$info.participants.champExperience'},
            'deaths': {'$sum': '$info.participants.deaths'},
            'goldEarned': {'$sum': '$info.participants.goldEarned'},
            'kills': {'$sum': '$info.participants.kills'},
            'visionScore': {'$sum': '$info.participants.visionScore'},
            'visionWardsBoughtInGame': {'$sum': '$info.participants.visionWardsBoughtInGame'}

        }
    },
    {
        '$project': {
            '_id': 0,
            'matchId': '$_id.matchId',
            'win': '$_id.win',
            'allInPings': 1,
            'assists': 1,
            'champExperience': 1,
            'deaths': 1,
            'goldEarned': 1,
            'kills': 1,
            'visionScore': 1,
            'visionWardsBoughtInGame': 1

        }
    }
]

transformed_data = list(source_collection.aggregate(pipeline))

target_collection.insert_many(transformed_data)

client.close()







