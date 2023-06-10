import os
import random
import json

default_tokens: int = 5000
default_max_connections: int = 100

def Init() -> None:
    global default_tokens

    if (not os.path.exists("API/")):
        os.mkdir("API/")
    
    if (default_tokens < 0):
        default_tokens = 1

def GenerateKey(tokens: int = -1, max_connections: int = -1) -> dict:
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
    
    key_data["tokens"] = tokens
    key_data["connections"] = max_connections
    key_data["key"] = key
    SaveKey(key_data)
    
    return key_data

def SaveKey(key_data: dict) -> None:
    key_data2 = {}
    key_data2["tokens"] = key_data["tokens"]
    key_data2["connections"] = key_data["connections"]
    key_data2["key"] = key_data["key"]

    if (key_data["tokens"] <= 0 or key_data["connections"] <= 0):
        DeleteKey(key_data["key"])
    
    with open("API/" + key_data["key"] + ".key", "w+") as f:
        json.dump(key_data, f)
        f.close()

def GetKey(key: str) -> dict:
    Init()

    if (not os.path.exists("API/" + key + ".key")):
        return {"ERROR": "Invalid API key."}
    
    with open("API/" + key + ".key", "r") as f:
        content = json.load(f)
        f.close()

        return content

def DeleteKey(key: str) -> None:
    Init()

    if (not os.path.exists("API/" + key + ".key")):
        return
    
    os.remove("API/" + key + ".key")