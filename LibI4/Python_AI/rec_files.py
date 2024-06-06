import websockets.server
import asyncio
import threading
import datetime
import os
import random
import json
import time
import sys
import ai_config as cfg
import ip_banning as ip_ban

received_files: list[dict[str]] = []
max_sf_minutes: int = 15
update_every_seconds: int = 300

if (not os.path.exists("ReceivedFiles/")):
    os.mkdir("ReceivedFiles/")

if (update_every_seconds < 10):
    print("Error: the minimum update seconds are 10 seconds.")
    os._exit(1)

def UpdateReceivedFiles() -> None:
    for file in os.listdir("ReceivedFiles/"):
        if (not file.endswith(".enc_file")):
            continue

        try:
            with open("ReceivedFiles/" + file, "r") as f:
                received_files.append(json.loads(f.read()))
                f.close()
        except:
            print("Could not append file. Ignoring.")

def UpdateServer() -> None:
    ip_ban.ReloadBannedIPs()
    UpdateReceivedFiles()

    for rf in received_files:
        try:
            day = int(rf["c_day"])
            month = int(rf["c_month"])
            year = int(rf["c_year"])
            hour = int(rf["c_hour"])
            minute = int(rf["c_minute"])

            fd = datetime.datetime(year, month, day, hour, minute)
            cd = datetime.datetime.now()
            date_diff = cd - fd

            if (date_diff.total_seconds() >= max_sf_minutes * 60):
                if (received_files.count(rf)):
                    received_files.remove(rf)

                os.remove("ReceivedFiles/" + rf["id"] + ".enc_file")
                os.remove("ReceivedFiles/" + rf["id"] + "_file")
        except:
            if (received_files.count(rf) > 0):
                received_files.remove(rf)

async def ProcessClient(websocket: websockets.WebSocketClientProtocol) -> None:
    if (ip_ban.IsIPBanned(str(websocket.remote_address[0]))):
        print("Banned IP, ignoring...")
        await websocket.close()

        return
    
    data_bytes = b""
    recf = ""
    print("Receiving file from " + str(websocket.remote_address[0]) + "...")

    while (True):
        recf = await websocket.recv()

        if (len(recf) == 0):
            break

        if (type(recf) == bytes):
            if (not recf.endswith(b"<end>")):
                data_bytes += recf
            else:
                data_bytes += recf[:-5]
                break
        elif (type(recf) == str):
            if (not recf.endswith("<end>")):
                data_bytes += recf.encode("utf-8")
            else:
                data_bytes += recf[:-5].encode("utf-8")
                break
        else:
            raise Exception("Could not receive file from client because it was not a string or bytes.")
    
    if (len(recf) > 0):
        print("Received file from client '" + str(websocket.remote_address[0]) + "' (" + str(len(data_bytes)) + " bytes).")
    else:
        print("Bytes limit error.")
        await websocket.close()

        return
    
    try:
        files = os.listdir("ReceivedFiles/")
        id = random.randint(-99999, 99999)
        file_info = {
            "c_day": datetime.datetime.now().day,
            "c_month": datetime.datetime.now().month,
            "c_year": datetime.datetime.now().year,
            "c_hour": datetime.datetime.now().hour,
            "c_minute": datetime.datetime.now().minute,
            "id": str(id)
        }

        while (files.count(str(id) + ".enc_file") > 0):
            id = random.randint(-99999, 99999)
                
        with open("ReceivedFiles/" + str(id) + ".enc_file", "w+") as f:
            f.write(json.dumps(file_info))
            f.close()
        
        with open("ReceivedFiles/" + str(id) + "_file", "wb") as f:
            f.write(data_bytes)
            f.close()
                
        received_files.append(file_info)
        server_response = str(id)
    except Exception as ex:
        server_response = "Could not save file."
        print("Error saving file: " + str(ex))

    await websocket.send(server_response)
    await websocket.close()

    UpdateServer()

async def AcceptClient(websocket: websockets.WebSocketClientProtocol) -> None:
    print("(Rec Files) Incomming connection from '" + str(websocket.remote_address[0]) + ":" + str(websocket.remote_address[1]) + "'.")
    await ProcessClient(websocket)

def UpdateFunction() -> None:
    while (True):
        UpdateServer()
        time.sleep(update_every_seconds)

def WSServer() -> None:
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    
    ip = "127.0.0.1" if (cfg.current_data.use_local_ip) else "0.0.0.0"
    server_ws = websockets.server.serve(AcceptClient, ip, 8061)

    event_loop.run_until_complete(server_ws)
    event_loop.run_forever()

try:
    ws_server_thread = threading.Thread(target = WSServer)
    ws_server_thread.start()

    print("Rec Files server started and listening.")
except Exception as ex:
    print("Error starting Rec Files websocket: " + str(ex))

update_thread = threading.Thread(target = UpdateFunction)
update_thread.start()

UpdateServer()

if (sys.argv.__contains__("-l") or sys.argv.__contains__("--loop")):
    while True:
        command = input(">$ ")

        if (command == "quit" or command == "close" or command == "stop" or command == "exit"):
            print("Closing server...")
            os._exit(0)