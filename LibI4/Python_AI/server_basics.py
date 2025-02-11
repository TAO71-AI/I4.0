# Import I4.0 utilities
import encryption as enc
import ai_config as cfg

# Import libraries
import random
import datetime
import json
import websockets
import asyncio
import os
import concurrent.futures

# Create variables
DefaultTokens: int = 0
KeyLength: int = 150
ServerPrivateKey: bytes | None = None
ServerPublicKey: bytes | None = None

def __get_current_datetime__() -> dict[str, str]:
    return {
        "day": str(datetime.datetime.now().day),
        "month": str(datetime.datetime.now().month),
        "year": str(datetime.datetime.now().year),
        "hour": str(datetime.datetime.now().hour),
        "minute": str(datetime.datetime.now().minute)
    }

def __create_keys__() -> None:
    global ServerPublicKey, ServerPrivateKey

    if (ServerPublicKey is not None and ServerPrivateKey is not None):
        return

    if (os.path.exists("db_pub.pem") and os.path.exists("db_pri.pem")):
        with open("db_pub.pem", "rb") as f:
            ServerPublicKey = f.read()
        
        with open("db_pri.pem", "rb") as f:
            ServerPrivateKey = f.read()
    else:
        print("Public or private keys not found. Creating new keys.")
        ServerPrivateKey, ServerPublicKey = enc.CreateKeys()

        with open("db_pub.pem", "wb") as f:
            f.write(ServerPublicKey)
        
        with open("db_pri.pem", "wb") as f:
            f.write(ServerPrivateKey)

async def AsyncExecuteCommandOnDatabase(Command: str, Objects: list[any] | None = None) -> list[any]:
    """
    Executes a command on the database.
    """
    # Get the keys
    __create_keys__()

    # Get the port
    try:
        port = cfg.current_data["server_port"] + 1
    except:
        port = 8061

    # Connect to the database server
    client: websockets.WebSocketClientProtocol = await websockets.connect(f"ws://{cfg.current_data['db']['host']}:{port}", max_size = None)

    # Create the JSON string
    data = {
        "Command": Command,
        "Objects": Objects
    }
    data = json.dumps(data)

    # Encrypt the data using the public server key file
    hash = enc.__parse_hash__(cfg.current_data["db"]["hash"])
    data = enc.EncryptMessage(data, ServerPublicKey, hash)

    # Convert to bytes
    data = data.encode("utf-8")

    # Send the data
    await client.send(data)

    # Receive the response
    response = await client.recv()

    # Decrypt the response
    response = enc.DecryptMessage(response, ServerPrivateKey, hash)

    # Close the connection
    await client.close()

    # Check the response
    if (response == "ERROR"):
        # Return an error
        raise Exception("Error on the database server.")

    # Return the response
    return cfg.JSONDeserializer(response)

def ExecuteCommandOnDatabase(Command: str, Objects: list[any] | None = None) -> list[any]:
    """
    Executes a command on the database using asyncio.
    """
    def __execute_command_on_db__() -> list[any]:
        # Create new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Execute the command on the database
            result = loop.run_until_complete(AsyncExecuteCommandOnDatabase(Command, Objects))
        finally:
            loop.close()
        
        # Return the result
        return result

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(__execute_command_on_db__)
        result = future.result()
    
    if (isinstance(result, str) and result == "ERROR"):
        raise Exception("Error on the server.")
    
    return result

def CreateKey(Tokens: int | None = None, IsDaily: bool = False) -> dict[str, any]:
    """
    Creates a new key.
    """
    # Check if the tokens are none
    if (Tokens is None):
        # Use the default tokens
        Tokens = DefaultTokens
    
    # Check key length
    if (KeyLength <= 0):
        # Set the key length to 150
        KeyLength = 150
    
    # Create variables
    charList = "abcdefghijklmnopqrstuvwxyz"
    charList += charList.upper() + "0123456789!·$%&()=?@#¬[]-_.:,;"
    keyData = {
        "tokens": Tokens,
        "key": "",
        "daily": IsDaily,
        "date": __get_current_datetime__(),
        "default": {
            "tokens": Tokens
        },
        "admin": False
    }

    # Generate a unique key
    for _ in range(KeyLength):
        # Add a random char to the key
        keyData["key"] += charList[random.randint(0, len(charList) - 1)]

    # Save the key
    SaveKey(keyData)

    # Return the key data
    return keyData

def SaveKey(KeyData: dict[str, any] | None) -> None:
    """
    Saves a key to the DB.
    """
    # Check if the key is none
    if (KeyData is None):
        return

    # Get values
    key = str(KeyData["key"])
    tokens = float(KeyData["tokens"])
    daily = bool(KeyData["daily"])
    date = json.dumps(KeyData["date"])
    default = json.dumps(KeyData["default"])
    admin = bool(KeyData["admin"])

    # Check if the key already exists
    results = ExecuteCommandOnDatabase(f"SELECT * FROM {cfg.current_data['db']['keys']['table']} WHERE {cfg.current_data['db']['keys']['key']} = %s LIMIT 1", [key])

    # Check if the key was found
    if (len(results) > 0):
        # Found!
        # Update the key
        ExecuteCommandOnDatabase(f"UPDATE {cfg.current_data['db']['keys']['table']} SET {cfg.current_data['db']['keys']['tokens']} = %s, {cfg.current_data['db']['keys']['daily']} = %s, {cfg.current_data['db']['keys']['date']} = %s, {cfg.current_data['db']['keys']['default']} = %s, {cfg.current_data['db']['keys']['admin']} = %s WHERE {cfg.current_data['db']['keys']['key']} = %s", [tokens, daily, date, default, admin, key])
    else:
        # Not found, create
        ExecuteCommandOnDatabase(f"INSERT INTO {cfg.current_data['db']['keys']['table']} ({cfg.current_data['db']['keys']['key']}, {cfg.current_data['db']['keys']['tokens']}, {cfg.current_data['db']['keys']['daily']}, {cfg.current_data['db']['keys']['date']}, {cfg.current_data['db']['keys']['default']}, {cfg.current_data['db']['keys']['admin']}) VALUES (%s, %s, %s, %s, %s, %s)", [key, tokens, daily, date, default, admin])

def GetKey(Key: str) -> dict[str, any]:
    """
    Gets a key from the DB.
    """
    # Get the key
    results = ExecuteCommandOnDatabase(f"SELECT * FROM {cfg.current_data['db']['keys']['table']} WHERE {cfg.current_data['db']['keys']['key']} = %s LIMIT 1", [Key])
    result = results[0]

    key = str(result[cfg.current_data["db"]["keys"]["key"]])
    tokens = float(result[cfg.current_data["db"]["keys"]["tokens"]])
    daily = bool(result[cfg.current_data["db"]["keys"]["daily"]])
    date = cfg.JSONDeserializer(str(result[cfg.current_data["db"]["keys"]["date"]]))
    default = cfg.JSONDeserializer(str(result[cfg.current_data["db"]["keys"]["default"]]))
    admin = bool(result[cfg.current_data["db"]["keys"]["admin"]])

    # Parse the key
    keyData = {
        "tokens": tokens,
        "key": key,
        "daily": daily,
        "date": date,
        "default": default,
        "admin": admin
    }

    # Return the key data
    return keyData

def GetKeys() -> list[dict[str, any]]:
    """
    Gets all the keys from the DB.
    """
    # Get all key names
    results = ExecuteCommandOnDatabase(f"SELECT {cfg.current_data['db']['keys']['key']} FROM {cfg.current_data['db']['keys']['table']}")
    keys = []

    # For each result
    for result in results:
        # Get the key
        keys.append(GetKey(result[cfg.current_data["db"]["keys"]["key"]]))
    
    # Return the keys
    return keys

def DeleteKey(Key: str) -> None:
    """
    Deletes a key from the DB.
    """
    # Delete the key from the DB
    ExecuteCommandOnDatabase(f"DELETE FROM {cfg.current_data['db']['keys']['table']} WHERE {cfg.current_data['db']['keys']['key']} = %s", [Key])