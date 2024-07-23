from Utils.header import read_headers_from_config
from Utils.params import read_params_from_config
from config.teams import CODE2TEAMNAME
import pandas as pd
import os
import configparser
from Utils.postgres_tool import PostgresTool
from datetime import datetime
import pytz
import requests

config = configparser.ConfigParser()
config.read('./config/config.ini')

headers = read_headers_from_config("./config/config.ini")
params = read_params_from_config("./config/config.ini")
url_factmath = config['url']['URL_FACT_MATH']
db_config = {
    "host": config['database']['DB_SV_HOSTS'],
    "port": config['database'].getint('DB_SV_PORT'),
    "user": config['database']['DB_SV_USER'],
    "password": config['database']['DB_SV_PASSWORD'],
    "database": config['database']['DB_SV_DATABASE']
}

def fetch_data_from_url(url, headers, params):
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()  # Ensure we catch any HTTP errors
    return response.json()
def process_data(data,id_idx):
    for i in data:
        datas = {
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
            "date_id" : id_idx,
            "kickoff_time": i["kickoff"].split('T')[0],
            "sport_id": "mlb",
            
        }

        yield datas

def get_us_date(timezone_name='US/Eastern'):
    us_timezone = pytz.timezone(timezone_name)
    utc_now = datetime.now(pytz.utc)
    us_now = utc_now.astimezone(us_timezone)
    return us_now.strftime('%Y-%m-%d')

def get_math_data(db_config,sport_id,season):
    conn = PostgresTool(**db_config)
    CURRENT_DATE_US = get_us_date()

    query = f"SELECT idx,   id FROM date_id WHERE date_play = '{CURRENT_DATE_US}' AND sport_id = '{sport_id}' AND season = '2024'"
    idx = conn.query(query, False)[0][0]
    id_idx = conn.query(query, False)[0][1]
    querys1 = f"""SELECT COUNT(*) FROM "match" m WHERE m.date_id = '{id_idx-1}' AND m.status != 'Final'"""
    count = conn.query(querys1, False)[0][0]
    if count != 0:
        id_idx = id_idx - 1
        idx = idx - 1
    data = fetch_data_from_url(url_factmath.format(idx), headers, params)
    datas = process_data(data,id_idx)
    for i in datas:
        yield i
    conn.close()
    
def main(db_config):
    conn = PostgresTool(**db_config)

    datas = get_math_data(db_config, "mlb", "2024") # sport_id = "mlb", season = "2024
    for data in datas:
        conn.push_data('match', data)
        # print(data)
        
if __name__ == '__main__':
    main(db_config)