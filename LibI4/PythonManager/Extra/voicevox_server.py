from voicevox import Client
import asyncio
import socket
import threading
import json
import os
import random
import pygame

client: Client = Client()
server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
max_users: int = 50000
ignore: list[str] = ["-", "_", " ", "·", "'", '"', ","]
replace: dict[str, str] = {}

server_socket.bind(("0.0.0.0", 8072))
server_socket.listen(max_users)

async def GetAudioFromJson(jsondata: str):
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

    try:
        vel = float(jsonloaded["velocity"])
    except:
        try:
            vel = float(jsonloaded["speed"])
        except:
            vel = 1
    
    for i in ignore:
        msg = msg.replace(i, "")

    for i in replace.keys():
        msg = msg.replace(i, replace[i])
    
    if (len(msg.strip()) <= 0):
        return bytes()

    audio_query = await client.create_audio_query(msg, speaker = voice)
    audio_syn = await audio_query.synthesis(speaker = voice)

    return bytes(audio_syn)

def CreateAndWriteRandomFile(data: bytes) -> str:
    if (not os.path.exists("tmp/")):
        os.mkdir("tmp/")
    
    rid = 0

    while (os.path.exists("tmp/" + str(rid) + ".tmp")):
        rid = random.randint(-5000, 5000)
    
    with open("tmp/" + str(rid) + ".tmp", "w+") as f:
        f.close()
    
    with open("tmp/" + str(rid) + ".tmp", "wb") as f:
        f.write(data)
        f.close()
    
    return "tmp/" + str(rid) + ".tmp"

def GetAudioDataFromAsyncio(jsondata: str):
    loop = asyncio.new_event_loop()
    cr = loop.run_until_complete(GetAudioFromJson(jsondata))

    return bytes(cr)

def HandleClient(client_socket, ip):
    print("Incomming connection from '" + str(ip) + "'.")

    try:
        rec_data = client_socket.recv(32768).decode("utf-8")
        print("Received data: '" + rec_data + "'.")

        if (not rec_data.startswith("{") or not rec_data.endswith("}")):
            client_socket.send(bytes())

        try:
            cr = GetAudioDataFromAsyncio(rec_data)
            cr = CreateAndWriteRandomFile(bytes(cr))

            with open(cr, "rb") as f:
                bs = f.read()

                client_socket.sendall(bs)
                print("'" + str(len(str(bs))) + "' bytes sent to '" + str(ip) + "'.")

                f.close()
                
            os.remove(cr)
        except Exception as ex:
            print("Error on sending audio: " + str(ex))
            client_socket.send(bytes())
    except Exception as ex:
        print("An error has ocurred on client '" + str(ip) + "': " + str(ex) + ".")
    finally:
        client_socket.close()

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

try:
    pygame.init()
    pygame.mixer.init()
except:
    pass

while True:
    user = input(">$ ")

    if (user.lower() == "exit"):
        break
    elif (user.lower().startswith("test_voice ")):
        user2 = user[11:len(user)]
        
        voice = int(user2.split(" ")[0])
        msg = user2[len(str(voice)) + 1:len(user2)]
        jsondata = '{"voice":' + str(voice) + ', "msg":"' + msg + '"}'

        try:
            response = GetAudioDataFromAsyncio(jsondata)
            file = CreateAndWriteRandomFile(response)
            print("returned " + str(len(str(response))) + " bytes.")

            try:
                pygame.mixer.music.load(file)
                pygame.mixer.music.play()

                while (pygame.mixer.music.get_busy()):
                    continue

                pygame.mixer.music.stop()
                os.remove(file)
            except:
                pass
        except Exception as ex:
            print("Error on returning audio. ERROR: " + str(ex))
    elif (user.lower().startswith("test_voice_nr ")):
        user2 = user[14:len(user)]
        
        voice = int(user2.split(" ")[0])
        msg = user2[len(str(voice)) + 1:len(user2)]
        jsondata = '{"voice":' + str(voice) + ', "msg":"' + msg + '"}'

        try:
            response = GetAudioDataFromAsyncio(jsondata)
            file = CreateAndWriteRandomFile(response)
            print("returned " + str(len(str(response))) + " bytes.")

            try:
                pygame.mixer.music.load(file)
                pygame.mixer.music.play()

                while (pygame.mixer.music.get_busy()):
                    continue

                pygame.mixer.music.stop()
            except:
                pass
        except Exception as ex:
            print("Error on returning audio. ERROR: " + str(ex))

print("Closing server.")
os._exit(0)