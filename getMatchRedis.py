import redis
import requests
import emoji
import configparser
from datetime import datetime
import pytz
import time
from datetime import timedelta
from Utils.header import read_headers_from_config
from Utils.params import read_params_from_config
from Utils.postgres_tool import PostgresTool

config = configparser.ConfigParser()
config.read('./config/config.ini')

headers = read_headers_from_config("./config/config.ini")
params = read_params_from_config("./config/config.ini")
url_factmath = config['url']['URL_FACT_MATH']
url_post_api = config['url']['URL_MATCH_POST_API']
# config for database server bbsw
db_config = {
    "host": config['database']['DB_SV_HOSTS'],
    "port": config['database'].getint('DB_SV_PORT'),
    "user": config['database']['DB_SV_USER'],
    "password": config['database']['DB_SV_PASSWORD'],
    "database": config['database']['DB_SV_DATABASE']
}

# config for database server aws
db_config_sv = {
    'host': config['database_sv']['DB_SV_HOSTS'],
    'port': config['database_sv'].getint('DB_SV_PORT'),
    'user': config['database_sv']['DB_SV_USER'],
    'password': config['database_sv']['DB_SV_PASSWORD'],
    'database': config['database_sv']['DB_SV_DATABASE']
}

redis_sv = config['redis_sv']
# connect to redis
redis_client = redis.Redis(**redis_sv)

def fetch_data_from_url(url, headers, params):
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()  
    return response.json()

def process_data(data, id_idx):
    for i in data:
        yield {
            "id": i["id"],
            "home_team_id": i["home_team_id"],
            "away_team_id": i["road_team_id"],
            "status": i["game_state"],
            "home_team_score": i["home_team_score"],
            "away_team_score": i["road_team_score"],
            "live_home_team_score": i["live_home_team_score"],
            "live_away_team_score": i["live_road_team_score"],
            "home_team_spread": i["home_team_spread"],
            "away_team_spread": i["road_team_spread"],
            "point_total": i["over_under"],
            "date_id": id_idx,
            "kickoff_time": i['additional_data']["DateTime"],
            "sport_id": "mlb",
        }

def get_us_date(timezone_name='US/Eastern'):
    us_timezone = pytz.timezone(timezone_name)
    utc_now = datetime.now(pytz.utc)
    us_now = utc_now.astimezone(us_timezone) 
    previous_us_date = us_now #- timedelta(days=4)
    return previous_us_date.strftime('%Y-%m-%d')

def delete_catche_redis(redis_set_key):
    set_values = redis_client.smembers(redis_set_key)
    for value in set_values:
        decoded_value = value.decode('utf-8')
        redis_key = f"match:{decoded_value}"
        redis_client.delete(redis_key)

    redis_client.delete(redis_set_key)

def get_math_data(db_config, sport_id, season,redis_set_key):
    conn = PostgresTool(**db_config)
    current_date_us = get_us_date()

    query = f"SELECT idx, id FROM date_id WHERE date_play = '{current_date_us}' AND sport_id = '{sport_id}' AND season = '2024'"
    idx, id_idx = conn.query(query, False)[0]

    query_check_status = f"SELECT COUNT(*) FROM match WHERE date_id = '{id_idx-1}' AND status != 'Final' AND status != 'Postponed' "
    count = conn.query(query_check_status, False)[0][0]
    if count != 0:
        id_idx -= 1
        idx -= 1
    query_check_count = f"SELECT COUNT(*) FROM match WHERE date_id = '{id_idx}' "
    count_check = conn.query(query_check_count, False)[0][0]
    data = fetch_data_from_url(url_factmath.format(idx), headers, params)
    
    if count_check != 0 and count_check > len(data):
        query_delete = f"DELETE FROM match WHERE date_id = '{id_idx}'"
        conn.query(query_delete, False)
        delete_catche_redis(redis_set_key)
        
    conn.close()
    yield from process_data(data, id_idx)
 
def main(db_config, redis_prefix):
    redis_set_key = f"{redis_prefix}_unique_match_ids"
    datas = get_math_data(db_config, "mlb", "2024",redis_set_key)

    for data in datas:
        redis_key = f"{redis_prefix}:match:{data}" 
        exists = redis_client.sismember(redis_set_key, str(data))

        if not exists:
            redis_client.sadd(redis_set_key, str(data))
            redis_client.expire(redis_set_key, 60*60*24)
            redis_client.setex(redis_key, 60*60*24, str(data))

            data = {k: (v if v != "None" else None) for k, v in data.items()}

            conn = PostgresTool(**db_config)
            conn.push_data('match', data)
            conn.close()
            requests.post(url_post_api, json=[data])
        else:
            pass
            
if __name__ == '__main__':
    while True:
        # main(db_config, "dbBBSW")
        main(db_config_sv, "dbAWS")
        time.sleep(2)   
