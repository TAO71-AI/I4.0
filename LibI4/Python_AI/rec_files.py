import socket
import datetime
import os
import random
import json
import threading
import time
import ip_banning as ip_ban

max_buffer_length: int = 5000000
server: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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

        with open("ReceivedFiles/" + file, "r") as f:
            received_files.append(json.loads(f.read()))
            f.close()

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
                os.remove("ReceivedFiles/" + rf["id"] + ".enc_file")
                os.remove("ReceivedFiles/" + rf["id"] + "_file")

                received_files.remove(rf)
        except Exception as ex:
            print("Error checking files: " + str(ex))
            received_files.remove(rf)

def ProcessClient(client: socket.socket, ip: tuple) -> None:
    if (ip_ban.IsIPBanned(str(ip[0]))):
        print("Banned IP, ignoring...")
        client.close()

        return
    
    data_bytes = b""

    while True:
        recf = client.recv(4096)

        if not recf:
            break

        if (not recf.endswith(b"<end>")):
            data_bytes += recf
        else:
            data_bytes += recf[: -len(b"<end>")]
            break
    
    if (len(recf) > 0):
        print("Received file from client '" + str(ip[0]) + "' (" + str(len(data_bytes)) + " bytes).")
    else:
        print("Bytes limit error.")
        client.close()

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
        print("ERROR: " + str(ex))

    client.send(server_response.encode("utf-8"))
    client.close()

    UpdateServer()

def AcceptClients() -> None:
    while True:
        try:
            client, address = server.accept()
            client_thread = threading.Thread(target = ProcessClient, args = (client, address))

            client_thread.start()
        except Exception as ex:
            print("An error has ocurred! (" + str(ex) + ").")

def UpdateFunction() -> None:
    while True:
        UpdateServer()
        time.sleep(update_every_seconds)

server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, max_buffer_length)
server.bind(("0.0.0.0", 8061))
server.listen()

server_thread = threading.Thread(target = AcceptClients)
server_thread.start()

update_thread = threading.Thread(target = UpdateFunction)
update_thread.start()

UpdateServer()

while True:
    command = input(">$ ")

    if (command == "quit" or command == "close" or command == "stop" or command == "exit"):
        print("Closing server...")

        server.close()
        os._exit(0)