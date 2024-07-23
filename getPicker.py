from Utils.header import read_headers_from_config
from Utils.params import read_params_from_config
import configparser
from Utils.postgres_tool import PostgresTool
from datetime import datetime
import pytz
import requests
import redis
import time

config = configparser.ConfigParser()
config.read('./config/config.ini')

headers = read_headers_from_config("./config/config.ini")
params = read_params_from_config("./config/config.ini")
url_picker = config['url']['URL_PICKER']
url_ou = config['url']['URL_OU_POST_API']
url_ats = config['url']['URL_ATS_POST_API']
db_config = {
    "host": config['database_sv']['DB_SV_HOSTS'],
    "port": config['database_sv'].getint('DB_SV_PORT'),
    "user": config['database_sv']['DB_SV_USER'],
    "password": config['database_sv']['DB_SV_PASSWORD'],
    "database": config['database_sv']['DB_SV_DATABASE']
}

redis_sv = config['redis_sv']

# Kết nối đến Redis
redis_client = redis.Redis(**redis_sv)
redis_set_key = "unique_get_picker_ids_"

def fetch_data_from_url(url, headers, params):
    response = requests.get(url, headers=headers, params=params)
    return response.json()["picks"]

def process_pick_data(data, gameType):
    for i in data:
        for game, pick in i["picks"].items():
            # print(game, pick)
            datas = {
                "match_id": game,
                "date_add": datetime.now().strftime("%Y-%m-%d"),
                "status_update": "True",
                "stake": pick.get("stake"),
                "seq": pick.get("seq"),
                "result": pick.get("result"),
                "win_pct": i.get("season_win_pct", 0)  # Default to 0 if season_win_pct is missing
            }
            if gameType == "ats":
                if "spread" in pick and "team_id" in pick and i.get("win_pct", 0) >= 55:
                    datas["spread"] = pick["spread"]
                    datas["team_id"] = pick["team_id"]
                    yield datas
                else:
                    continue
            else:
                if "ou_type" in pick and "ou_value" in pick and i.get("win_pct", 0) >= 51:
                    datas["ou_type"] = pick["ou_type"]
                    datas["ou_value"] = pick["ou_value"]
                    yield datas
                else:
                    continue


def get_us_date(timezone_name='US/Eastern'):
    us_timezone = pytz.timezone(timezone_name)
    utc_now = datetime.now(pytz.utc)
    us_now = utc_now.astimezone(us_timezone)
    return us_now.strftime('%Y-%m-%d')

def get_picker(tournament, season, gameType, db_config,season_date):
    conn = PostgresTool(**db_config)
    CURRENT_DATE_US = get_us_date()

    query = f"SELECT idx FROM date_id WHERE date_play = '{CURRENT_DATE_US}' and sport_id = '{tournament}' and season = '{season_date}'"
    idx = conn.query(query, False)[0][0]

    list_url = [url_picker.format(tournament, season, idx, gameType, sequence) for sequence in range(0, 150, 50)]
    for url in list_url:
        data = fetch_data_from_url(url, headers, params)
        for datas in process_pick_data(data, gameType):
            redis_key = f"Picker{datas}"
            exists = redis_client.sismember(redis_set_key, str(datas))
            if not exists:
                redis_client.sadd(redis_set_key,str(datas))
                redis_client.expire(redis_set_key, 60*60*24)
                redis_client.setex(redis_key, 60*60*24, str(datas))
                datas = {k: v for k, v in datas.items() if v is not None}
                if datas.get("win_pct") >= 55 and gameType == "ats" and datas.get("result") == "pregame":
                    conn.push_data(f"expert_{gameType}",datas)
                    requests.post(url= url_ats, json=[datas])
                elif datas.get("win_pct") >= 51 and gameType == "ou" and datas.get("result") == "pregame":
                    print([datas])

                    conn.push_data(f"expert_{gameType}",datas)
                    requests.post(url= url_ou, json=[datas])
                else:
                    continue
            else:
                # print(f"🦄👩🏻‍💻 Duplicate data found, skipping: {datas}")
                continue
    conn.close()

def main():
    get_picker("mlb", "2024", "ats", db_config,"2024")
    get_picker("mlb", "2024", "ou", db_config,"2024")

if __name__ == "__main__":
    while True:
        main()
        time.sleep(2)
