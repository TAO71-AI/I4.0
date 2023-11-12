import os
import random
import json
import datetime
import mysql.connector
import ai_config as cfg

default_tokens: int = 5000
default_max_connections: int = 100
use_database: bool = (cfg.current_data.keys_db["use"].lower() == "true")
db = None
db_con = None

if (not os.path.exists("API/")):
    os.mkdir("API/")

def ReloadDB() -> None:
    if (use_database):
        db_con = mysql.connector.connect(
            host = cfg.current_data.keys_db["server"],
            user = cfg.current_data.keys_db["user"],
            password = cfg.current_data.keys_db["password"],
            database = cfg.current_data.keys_db["database"],
            raise_on_warnings = False
        )
        db = db_con.cursor()

ReloadDB()

def Init() -> None:
    global default_tokens

    if (not os.path.exists("API/")):
        os.mkdir("API/")
    
    if (default_tokens < 0):
        default_tokens = 1

def GetCurrentDateDict() -> dict[str, str]:
    return {
        "day": str(datetime.datetime.now().day),
        "month": str(datetime.datetime.now().month),
        "year": str(datetime.datetime.now().year),
        "hour": str(datetime.datetime.now().hour),
        "minute": str(datetime.datetime.now().minute)
    }

def GenerateKey(tokens: int = -1, max_connections: int = -1, daily_key: bool = False) -> dict:
    Init()

    if (tokens < 0):
        tokens = default_tokens
    
    if (max_connections < 0):
        max_connections = default_max_connections
    
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
        return GenerateKey(tokens)
    
    default_key = {
        "tokens": tokens,
        "connections": max_connections
    }
    
    key_data["user_id"] = -1
    key_data["tokens"] = tokens
    key_data["connections"] = max_connections
    key_data["key"] = key
    key_data["daily"] = "true" if daily_key else "false"
    key_data["date"] = GetCurrentDateDict()
    key_data["default"] = default_key
    SaveKey(key_data)
    
    return key_data

def SaveKey(key_data: dict) -> str:
    try:
        if (key_data["user_id"] > 0 and use_database):
            raise Exception()
        
        with open("API/" + key_data["key"] + ".key", "w+") as f:
            f.write(json.dumps(key_data))
            f.close()
            
        return "Done!"
    except:
        pass

    if (use_database):
        try:
            db.execute("UPDATE " + cfg.current_data.keys_db["table"] + " SET " +
                "tokens = '" + str(key_data["tokens"]) + "', connections = '" + str(key_data["connections"]) + "', date = '" +
                json.dumps(key_data["date"]).replace("'", "\"") + "' WHERE akey = '" + str(key_data["key"]) + "'")
            db_con.commit()

            return "Database updated, " + str(db.rowcount) + " record(s) updated!"
        except:
            ReloadDB()

            try:
                db.execute("UPDATE " + cfg.current_data.keys_db["table"] + " SET " +
                    "tokens = '" + str(key_data["tokens"]) + "', connections = '" + str(key_data["connections"]) + "', date = '" +
                    json.dumps(key_data["date"]).replace("'", "\"") + "' WHERE akey = '" + str(key_data["key"]) + "'")
                db_con.commit()

                return "Database updated, " + str(db.rowcount) + " record(s) updated!"
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
    
    if (use_database):
        try:
            db.execute("SELECT * FROM " + cfg.current_data.keys_db["table"])
            results = db.fetchall()

            for db_key in results:
                try:
                    key_data = {}

                    key_data["user_id"] = int(db_key[1])
                    key_data["tokens"] = float(db_key[2])
                    key_data["connections"] = int(db_key[3])
                    key_data["key"] = db_key[4]
                    key_data["daily"] = (int(db_key[5]) == 1)
                    key_data["date"] = json.loads(db_key[6])
                    key_data["default"] = {
                        "tokens": float(db_key[7]),
                        "connections": int(db_key[8])
                    }

                    keys.append(key_data)
                except:
                    continue
        except:
            ReloadDB()

            try:
                db.execute("SELECT * FROM " + cfg.current_data.keys_db["table"])
                results = db.fetchall()

                for db_key in results:
                    try:
                        key_data = {}

                        key_data["user_id"] = int(db_key[1])
                        key_data["tokens"] = float(db_key[2])
                        key_data["connections"] = int(db_key[3])
                        key_data["key"] = db_key[4]
                        key_data["daily"] = (int(db_key[5]) == 1)
                        key_data["date"] = json.loads(db_key[6])
                        key_data["default"] = {
                            "tokens": float(db_key[7]),
                            "connections": int(db_key[8])
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
    if (use_database):
        try:
            db.close()
            db_con.close()
        except:
            pass