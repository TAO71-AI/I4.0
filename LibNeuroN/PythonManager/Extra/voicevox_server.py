from voicevox import Client
import asyncio
import socket
import threading
import json
import os

client: Client = Client()
server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
max_users: int = 50000

server_socket.bind(("0.0.0.0", 8072))
server_socket.listen(max_users)

def GetAudioFromJson(jsondata: str):
    jsonloaded = json.loads(jsondata)
    
    try:
        voice = int(jsonloaded["voice"])
    except:
        try:
            voice = int(jsonloaded["speaker"])
        except:
            voice = 1

    try:
        msg = jsonloaded["msg"]
    except:
        try:
            msg = jsonloaded["text"]
        except:
            msg = ""
    
    if (len(msg.strip()) <= 0):
        return bytes()

    audio_query = asyncio.run(client.create_audio_query(msg, speaker = voice))
    audio_syn = asyncio.run(audio_query.synthesis(speaker = voice))

    return audio_syn

def HandleClient(client_socket, ip):
    print("Incomming connection from '" + str(ip) + "'.")

    try:
        while True:
            rec_data = client_socket.recv(32768).decode("utf-8")
            print("Received data: '" + rec_data + "'.")

            if (len(rec_data) <= 0):
                break

            try:
                response = GetAudioFromJson(rec_data)
                client_socket.send(bytes(response))
            except Exception as ex:
                print("Error on sending audio: " + str(ex))
                client_socket.send(bytes())
    except:
        print("An error has ocurred on client '" + str(ip) + "'.")

def HandleClients():
    while True:
        client_socket, ip = server_socket.accept()

        client_handle_thread = threading.Thread(target = HandleClient, args = (client_socket, ip))
        client_handle_thread.start()

print("Server started and listening!")

try:
    t = threading.Thread(target = HandleClients)
    t.start()
except:
    print("Error on accept client.")

while True:
    user = input(">$ ")

    if (user.lower() == "exit"):
        break
    elif (user.lower().startswith("test_voice ")):
        user2 = user[11:len(user)]
        
        voice = int(user2.split(" ")[0])
        msg = user2[len(str(voice)) + 1]
        jsondata = '{"voice":' + str(voice) + ', "msg":"' + msg + '"}'

        try:
            response = GetAudioFromJson(jsondata)
            print("returned " + str(len(str(response))) + " bytes.")
        except Exception as ex:
            print("Error on returning audio. ERROR: " + str(ex))

print("Closing server.")
os._exit(0)