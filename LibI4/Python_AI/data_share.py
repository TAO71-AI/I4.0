import sys
import websockets
import websockets.server
import time
import asyncio
import json
import os
import base64
import ai_config as cfg

UseServer: bool = False
SaveDataDirectory: str = "DataShare/"
Servers: list[str] = []
BannedIPs: list[str] = []

async def __connect_to_server__(Server: int | str) -> websockets.WebSocketClientProtocol:
    if (type(Server) == int):
        Server = Servers[Server]

    uri = "ws://" + Server + ":8062"
    connection = await websockets.connect(uri)
    timeToWait = cfg.current_data["data_share_timeout"]
    t = 0

    while (not connection.open):
        if (t >= timeToWait):
            raise Exception("Connection error!")

        time.sleep(1)
        t += 1

    return connection

async def __send_to_server__(Connection: websockets.WebSocketClientProtocol, SendData: str | bytes) -> str:
    if (type(SendData) == bytes):
        SendData = SendData.decode("utf-8")
    
    await Connection.send(SendData)
    receivedData = await Connection.recv()

    if (type(receivedData) == bytes):
        receivedData = receivedData.decode("utf-8")
    
    return receivedData

async def ConnectAndSend(Server: int | str, SendData: str | bytes) -> tuple[bool, str, websockets.WebSocketClientProtocol]:
    connection = await __connect_to_server__(Server)
    receivedData = await __send_to_server__(connection, SendData)

    return (receivedData.lower().strip() == "ok", receivedData, connection)

async def SendToAllServers(SendData: str | bytes) -> list[tuple[bool, str, websockets.WebSocketClientProtocol]]:
    results = []

    for server in Servers:
        try:
            results.append(await ConnectAndSend(server, SendData))
        except Exception as ex:
            print("[DATA SHARE] Error sending data to server: " + str(ex))
    
    return results

def __add_file__(File: dict[str, str]) -> str:
    fileType = File["Type"].lower().strip()
    fileBytes = File["Data"]

    if (fileType != "image" and fileType != "audio" and fileType != "video" and fileType != "document"):
        fileType = "unknown"

    fileID = 0
    fileName = fileType + "_" + str(fileID)

    while (os.path.exists(SaveDataDirectory + "Files/" + fileName)):
        fileID += 1
        fileName = fileType + "_" + str(fileID)
            
    with open(SaveDataDirectory + "Files/" + fileName, "wb") as f:
        f.write(base64.b64decode(fileBytes))
        f.close()

def __add_data_to_server__(Data: dict[str] | str) -> str:
    try:
        if (type(Data) == str):
            Data = json.loads(Data)
        elif (type(Data) != dict and type(Data) != dict[str]):
            raise Exception("Invalid data type.")

        # Just to verify
        _ = Data["UserText"]
        _ = Data["ResponseText"]

        userFiles = Data["UserFiles"]
        responseFiles = Data["ResponseFiles"]
        fileID = 0
        fileName = "data_" + str(fileID) + ".json"

        while (os.path.exists(SaveDataDirectory + fileName)):
            fileID += 1
            fileName = "data_" + str(fileID) + ".json"

        for file in userFiles:
            userFiles[userFiles.index(file)] = __add_file__(file)
        
        for file in responseFiles:
            responseFiles[responseFiles.index(file)] = __add_file__(file)
        
        Data["UserFiles"] = userFiles
        Data["ResponseFiles"] = responseFiles

        with open(SaveDataDirectory + fileName, "w+") as f:
            f.write(json.dumps(Data))
            f.close()

        return "OK"
    except Exception as ex:
        print("ERROR ON DATA SHARE: " + str(ex))

        return "ERROR [ID: 2]"

async def __handle_connection__(Connection: websockets.WebSocketClientProtocol) -> None:
    while (True):
        try:
            data = await Connection.recv()
            data = cfg.JSONDeserializer(data)

            if (len(data) > 0):
                print("Received data from websocket.")

                server_response = __add_data_to_server__(data)
                await Connection.send(server_response)
            else:
                break
        except:
            try:
                await Connection.send("ERROR [ID: 1]")
            except Exception as ex:
                print("[DATA SHARE] Could not send error response, connection might be closed? ERROR DETAILS: " + str(ex))

            try:
                await Connection.close()
            except Exception as ex:
                print("[DATA SHARE] Error closing the connection, ignoring. ERROR DETAILS: " + str(ex))
            
            break

async def __listen__(Connection: websockets.WebSocketClientProtocol) -> None:
    print("Incomming connection from '" + str(Connection.remote_address[0]) + ":" + str(Connection.remote_address[1]) + "'.")

    # Update banned IPs
    if (os.path.exists("BannedIPs.json")):
        with open("BannedIPs.json", "r") as f:
            BannedIPs = cfg.JSONDeserializer(f.read())["ip"]
            f.close()

    if (str(Connection.remote_address[0]) in BannedIPs):
        print("Banned IP, connection closed.")

        try:
            await Connection.send("Banned.")
        except:
            pass

        await Connection.close()
        return

    await __handle_connection__(Connection)

for arg in sys.argv:
    if (arg == "--server" or arg == "-s"):
        UseServer = True

if (not SaveDataDirectory.endswith("/")):
    SaveDataDirectory += "/"

if (UseServer):
    if (not os.path.exists(SaveDataDirectory)):
        os.mkdir(SaveDataDirectory)
    
    if (not os.path.exists(SaveDataDirectory + "Files/")):
        os.mkdir(SaveDataDirectory + "Files/")

    try:
        # Try to set the banned IPs
        if (os.path.exists("BannedIPs.json")):
            with open("BannedIPs.json", "r") as f:
                BannedIPs = cfg.JSONDeserializer(f.read())
                f.close()

        ip = "127.0.0.1" if (cfg.current_data["use_local_ip"]) else "0.0.0.0"
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        server = websockets.server.serve(__listen__, ip, 8062, max_size = None)
        print("Server started.")

        loop.run_until_complete(server)
        loop.run_forever()
    except KeyboardInterrupt:
        print("Closing server...")
    except Exception as ex:
        print("[DATA SHARE] ERROR: " + str(ex))