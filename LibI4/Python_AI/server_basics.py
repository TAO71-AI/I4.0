from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
import os
import random
import time
import json
import datetime
import base64
import pymysql as mysql
import pymysql.cursors as mysql_c
import ai_config as cfg

default_tokens: int = 2000
use_mysql: bool = cfg.current_data["keys_db"]["use"] if (type(cfg.current_data["keys_db"]["use"]) == bool) else (str(cfg.current_data["keys_db"]["use"]).lower() == "true")
mysql_connection = None
mysql_cursor = None
saving: bool = False
reading: bool = False
privateKey: bytes = b""
publicKey: bytes = b""

if (not os.path.exists("API/")):
    os.mkdir("API/")

def __split_message__(Message: bytes, MaxSize: int) -> list[bytes]:
    # Split the message into chunks
    return [Message[i:i+MaxSize] for i in range(0, len(Message), MaxSize)]

def __create_keys__() -> None:
    global privateKey, publicKey

    # Generate the keys
    prKey = rsa.generate_private_key(public_exponent = 65537, key_size = 2048)
    puKey = prKey.public_key()

    # Get private and public bytes
    privateKey = prKey.private_bytes(
        encoding = serialization.Encoding.PEM,
        format = serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm = serialization.NoEncryption()
    )
    publicKey = puKey.public_bytes(
        encoding = serialization.Encoding.PEM,
        format = serialization.PublicFormat.SubjectPublicKeyInfo
    )

def DecryptMessage(Message: str | bytes) -> str:
    global privateKey

    # Get the private key from the data
    prKey = serialization.load_pem_private_key(privateKey, password = None)

    # Encode the message
    if (type(Message) is bytes):
        Message = Message.decode("utf-8")
    
    Message = [base64.b64decode(chunk) for chunk in Message.split("|")]

    # Create the chunks list
    decChunks = []

    for chunk in Message:
        # Decrypt using the private key
        message = prKey.decrypt(
            chunk,
            padding.OAEP(
                mgf = padding.MGF1(algorithm = hashes.SHA512()),
                algorithm = hashes.SHA512(),
                label = None
            )
        )

        # Append into the chunks list
        decChunks.append(message)

    # Return the message
    return b"".join(decChunks).decode("utf-8")

def EncryptMessage(Message: str | bytes, Key: str | bytes | None) -> str:
    global publicKey

    # Get the public key from the data
    if (type(Key) is str):
        Key = Key.encode("utf-8")
    elif (type(Key) is None):
        Key = publicKey

    puKey = serialization.load_pem_public_key(Key)

    # Encode the message
    if (type(Message) is str):
        Message = Message.encode("utf-8")

    # Create the chunks list
    encChunks = []

    for chunk in __split_message__(Message, 126):
        # Encrypt using the public key
        message = puKey.encrypt(
            chunk,
            padding.OAEP(
                mgf = padding.MGF1(algorithm = hashes.SHA512()),
                algorithm = hashes.SHA512(),
                label = None
            )
        )

        # Append into the chunks list
        encChunks.append(base64.b64encode(message).decode("utf-8"))

    # Return the message
    return "|".join(encChunks)

def ReloadDB() -> None:
    global mysql_connection, mysql_cursor

    if (use_mysql):
        mysql_connection = mysql.connect(
            host = cfg.current_data["keys_db"]["server"],
            user = cfg.current_data["keys_db"]["user"],
            password = cfg.current_data["keys_db"]["password"],
            database = cfg.current_data["keys_db"]["database"],
            cursorclass = mysql_c.DictCursor
        )
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
    
    char_list = "abcdefghijklmnopqrstuvwxyz"
    char_list += char_list.upper() + "0123456789!·$%&()=?@#¬[]-_.:,;"
    key = ""
    key_data = {}

    for _ in range(15):
        try:
            key += char_list[random.randint(0, len(char_list) - 1)]
        except:
            key += "0"
    
    if (os.path.exists("API/" + key + ".key")):
        return GenerateKey(tokens, daily_key)
    
    default_key = {
        "tokens": tokens
    }
    
    key_data["tokens"] = tokens
    key_data["key"] = key
    key_data["daily"] = "true" if (daily_key) else "false"
    key_data["date"] = GetCurrentDateDict()
    key_data["default"] = default_key
    key_data["admin"] = False
    SaveKey(key_data)
    
    return key_data

def SaveKey(key_data: dict, UseMySQL: bool | None = None, Err: int = 0) -> None:
    global saving

    if (UseMySQL and use_mysql):
        try:
            mysql_cursor.execute("UPDATE " + cfg.current_data["keys_db"]["table"] + " SET tokens = '" + str(key_data["tokens"]) + "', date = '" + json.dumps(key_data["date"]).replace("\'", "\"") + "' WHERE akey = '" + str(key_data["key"]) + "'")
            mysql_connection.commit()
        except:
            if (Err == 0):
                ReloadDB()
                return SaveKey(key_data, True, 1)

    try:
        if (key_data["user_id"] > 0 and use_mysql):
            raise Exception()

        while (saving):
            time.sleep(0.05)

        saving = True

        with open("API/" + key_data["key"] + ".key", "w+") as f:
            f.write(json.dumps(key_data))
            f.close()

        saving = False
        
        if (UseMySQL == None):
            SaveKey(key_data, True)
    except:
        saving = False

def GetAllKeys(UseMySQL: bool | None = None, Err: int = 0) -> list[dict]:
    global reading

    Init()
    keys = []

    if (UseMySQL and use_mysql):
        try:
            mysql_cursor.execute("SELECT * FROM " + cfg.current_data["keys_db"]["table"])
            results = mysql_cursor.fetchall()

            for db_key in results:
                try:
                    key_data = {
                        "tokens": float(db_key[1]),
                        "key": db_key[2],
                        "daily": int(db_key[3]) == 1 or str(db_key[3]).lower() == "true",
                        "date": json.loads(db_key[4]),
                        "default": {
                            "tokens": float(db_key[5])
                        },
                        "admin": int(db_key[6]) == 1 or str(db_key[6]).lower() == "true"
                    }
                    keys.append(key_data)
                except:
                    continue
            
            return keys
        except:
            if (Err == 0):
                ReloadDB()
                return GetAllKeys(True, 1)

    while (reading):
        time.sleep(0.05)

    reading = True

    try:
        for key in os.listdir("API/"):
            with open(f"API/{key}", "r") as f:
                content: dict = json.loads(f.read())
                f.close()

                if (list(content.keys()).count("admin") == 0):
                    content["admin"] = False

                keys.append(content)
        
        reading = False
    except:
        reading = False

    if (UseMySQL == None):
        keys += GetAllKeys(True)
    
    return keys

def GetKey(key: str) -> dict:
    Init()
    keys = GetAllKeys()

    for akey in keys:
        if (akey["key"] == key):
            return akey
    
    raise Exception("Invalid key.")

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