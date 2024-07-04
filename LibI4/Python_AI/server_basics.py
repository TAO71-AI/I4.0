import os
import random
import json
import datetime
import pymysql as mysql
import pymysql.cursors as mysql_c
import ai_config as cfg

default_tokens: int = 5000
use_mysql: bool = cfg.current_data["keys_db"]["use"] if (type(cfg.current_data["keys_db"]["user"]) == bool) else (str(cfg.current_data["keys_db"]["user"]).lower() == "true")
mysql_connection = None
mysql_cursor = None

if (not os.path.exists("API/")):
    os.mkdir("API/")

def ReloadDB() -> None:
    global mysql_connection, mysql_cursor

    if (use_mysql):
        mysql_connection = mysql.connect(host = cfg.current_data["keys_db"]["server"], user = cfg.current_data["keys_db"]["user"], password = cfg.current_data["keys_db"]["password"], database = cfg.current_data["keys_db"]["database"], cursorclass = mysql_c.DictCursor)
        mysql_cursor = mysql_connection.cursor()

def Init() -> None:
    global default_tokens

    if (not os.path.exists("API/")):
        os.mkdir("API/")
    
    if (default_tokens < 0):
        default_tokens = 1
    
    ReloadDB()

def GetCurrentDateDict() -> dict[str, str]:
    return {
        "day": str(datetime.datetime.now().day),
        "month": str(datetime.datetime.now().month),
        "year": str(datetime.datetime.now().year),
        "hour": str(datetime.datetime.now().hour),
        "minute": str(datetime.datetime.now().minute)
    }

def GenerateKey(tokens: int = -1, daily_key: bool = False) -> dict:
    Init()

    if (tokens < 0):
        tokens = default_tokens
    
    char_list = "abcdefghijklmnopqrstuvwxyz0123456789"
    key = ""
    key_data = {}
    i = 0

    while (i < 15):
        try:
            key += char_list[random.randint(0, len(char_list))]
        except:
            key += "0"
        
        i += 1
    
    if (os.path.exists("API/" + key + ".key")):
        return GenerateKey(tokens, daily_key)
    
    default_key = {
        "tokens": tokens
    }
    
    key_data["user_id"] = -1
    key_data["tokens"] = tokens
    key_data["key"] = key
    key_data["daily"] = "true" if daily_key else "false"
    key_data["date"] = GetCurrentDateDict()
    key_data["default"] = default_key
    SaveKey(key_data)
    
    return key_data

def SaveKey(key_data: dict) -> str:
    try:
        if (key_data["user_id"] > 0 and use_mysql):
            raise Exception()

        with open("API/" + key_data["key"] + ".key", "w+") as f:
            f.write(json.dumps(key_data))
            f.close()
            
        return "Done!"
    except:
        pass

    if (use_mysql):
        try:
            mysql_cursor.execute("UPDATE " + cfg.current_data["keys_db"]["table"] + " SET tokens = '" + str(key_data["tokens"]) + "', date = '" + json.dumps(key_data["date"]).replace("\'", "\"") + "' WHERE akey = '" + str(key_data["key"]) + "'")
            mysql_connection.commit()

            return "Database updated, " + str(mysql_cursor.rowcount) + " record(s) updated!"
        except:
            ReloadDB()

            try:
                mysql_cursor.execute("UPDATE " + cfg.current_data["keys_db"]["table"] + " SET tokens = '" + str(key_data["tokens"]) + "', date = '" + json.dumps(key_data["date"]).replace("\'", "\"") + "' WHERE akey = '" + str(key_data["key"]) + "'")
                mysql_connection.commit()

                return "Database updated, " + str(mysql_cursor.rowcount) + " record(s) updated!"
            except Exception as ex:
                return "ERROR SAVING KEY ON DB: " + str(ex)
    
    return "Done!"

def GetAllKeys() -> list[dict]:
    Init()
    keys = []

    for key in os.listdir("API/"):
        with open("API/" + key) as f:
            content = json.load(f)
            f.close()

            keys.append(content)
    
    if (use_mysql):
        try:
            mysql_cursor.execute("SELECT * FROM " + cfg.current_data["keys_db"]["table"])
            results = mysql_cursor.fetchall()

            for db_key in results:
                try:
                    key_data = {
                        "user_id": int(db_key[1]),
                        "tokens": float(db_key[2]),
                        "key": db_key[3],
                        "daily": (int(db_key[4]) == 1 or str(db_key[4]).lower() == "true"),
                        "date": json.loads(db_key[5]),
                        "default": {
                            "tokens": float(db_key[6])
                        }
                    }
                    keys.append(key_data)
                except:
                    continue
        except:
            ReloadDB()

            try:
                mysql_cursor.execute("SELECT * FROM " + cfg.current_data["keys_db"]["table"])
                results = mysql_cursor.fetchall()

                for db_key in results:
                    try:
                        key_data = {
                            "user_id": int(db_key[1]),
                            "tokens": float(db_key[2]),
                            "key": db_key[3],
                            "daily": (int(db_key[4]) == 1 or str(db_key[4]).lower() == "true"),
                            "date": json.loads(db_key[5]),
                            "default": {
                                "tokens": float(db_key[6])
                            }
                        }
                        keys.append(key_data)
                    except:
                        continue
            except:
                pass
    
    return keys

def GetKey(key: str) -> dict:
    Init()
    keys = GetAllKeys()

    for akey in keys:
        if (akey["key"] == key):
            return akey
    
    return {"ERROR": "Invalid API key."}

def DeleteKey(key: str) -> None:
    Init()

    if (not os.path.exists("API/" + key + ".key")):
        return
    
    os.remove("API/" + key + ".key")

def StopDB() -> None:
    if (use_mysql):
        try:
            mysql_cursor.close()
            mysql_connection.close()
        except:
            pass