import os
import json
import discord
import websockets
import time
import asyncio
import requests
import imghdr
import wave
import base64
import math
from discord.ext import commands

if (not os.path.exists("temp/")):
    os.mkdir("temp/")

if (not os.path.exists("temp/discord_apikey.txt")):
    with open("temp/discord_apikey.txt", "w+") as f:
        f.close()
    
if (not os.path.exists("temp/discord_server_apikey.txt")):
    with open("temp/discord_server_apikey.txt", "w+") as f:
        f.close()

with open("temp/discord_apikey.txt", "r") as f:
    api_key = f.read().strip()
    f.close()

with open("temp/discord_server_apikey.txt", "r") as f:
    server_api_key = f.read().strip()
    f.close()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix = "!i4", intents = intents)
websocket = None
fwebsocket = None
ips: list[str] = [
    "127.0.0.1"
]
conversation = "discord_"
translators = {}

if (os.path.exists("temp/discord_trs.json")):
    with open("temp/discord_trs.json", "r") as f:
        translators = json.loads(f.read())
        f.close()

async def connect_to_server_and_send(send_data: str = "", is_file: bool = False) -> str:
    global websocket, fwebsocket

    for ip in ips:
        try:
            uri = "ws://" + ip + ":8060"
            
            if (websocket == None or websocket.state != 1):
                websocket = await websockets.connect(uri)

            s = 0
            c = False

            while (websocket.state != 1):
                if (s >= 10):
                    c = True
                    break

                time.sleep(1)
                s += 1
                
            if (c):
                continue
            
            try:
                await websocket.send(send_data)
                response = await websocket.recv()

                return response
            except Exception as ex:
                print("Error sending: " + str(ex))

            raise Exception("Could not send or receive from server.")
        except Exception as ex:
            print("ERROR CONNECTING TO I4.0 SERVER: " + str(ex))
    
        try:
            uri = "ws://" + ip + ":8061"

            if (fwebsocket == None or fwebsocket.state != 1):
                fwebsocket = await websockets.connect(uri)
            
            s = 0
            c = False

            while (fwebsocket.state != 1):
                if (s > 10):
                    c = True
                    break
            
            if (c):
                continue

            try:
                chunk_size = 4096
                chunks = math.ceil(len(send_data) / chunk_size)

                for i in range(chunks):
                    offset = i * chunk_size
                    chunk = send_data[offset:offset + chunk_size]

                    await fwebsocket.send(chunk)

                await fwebsocket.send(b"<end>")
                response = await fwebsocket.recv()

                return response
            except Exception as ex:
                print("Error sending file: " + str(ex))
            
            raise Exception("Could not send or receive file from server.")
        except Exception as ex:
            print("ERROR CONNECTING TO I4.0 FILES SERVER: " + str(ex))

    return "ERROR CONNECTING TO ALL SERVERS."

def __file_is_img__(path: str) -> bool:
    return imghdr.what(path) != None

def __file_is_aud__(path: str) -> bool:
    try:
        with wave.open(path, "r") as f:
            f.close()
            return True
    except wave.Error:
        return False
    
def delete_if_exists(path: str) -> None:
    if (os.path.exists(path)):
        os.remove(path)

def __download_file__(url: str, ext: str) -> str:
    response = requests.get(url)

    if (response.status_code == 200):
        file_name = "discord_file_"
        file_id = 0

        while (os.path.exists(file_name + str(file_id) + ext)):
            file_id += 1
                    
        with open(file_name + str(file_id) + ext, "wb") as f:
            f.write(response.content)
            f.close()
                    
        return file_name + str(file_id) + ext
    
    print(str(response.content))
    
    raise Exception("ERROR DOWNLOADING FILE!")

def __get_images_from_message__(message, download: bool) -> list[str]:
    images = []

    for img in message.attachments:
        url = img.url
        df = __download_file__(url, ".png")

        if (not __file_is_img__(df)):
            os.remove(df)
            continue
        
        if (download):
            images.append(df)
        else:
            os.remove(df)
            images.append(url)
    
    return images

def __get_audios_from_message__(message, download: bool) -> list[str]:
    audios = []

    for audio in message.attachments:
        url = audio.url
        df = __download_file__(url, ".wav")

        if (not __file_is_aud__(df)):
            os.remove(df)
            continue
        
        if (download):
            audios.append(df)
        else:
            os.remove(df)
            audios.append(url)
    
    return audios

async def __prepare_audios_for_inference__(message, user, translator) -> str:
    audios_str = ""
    audios = __get_audios_from_message__(message, True)

    for audio in range(len(audios)):
        audios_str += "AUDIO #" + str(audio + 1) + ": "

        with open(audios[audio], "rb") as f:
            audio_bytes = f.read()
            audio_id = await connect_to_server_and_send(audio_bytes, True)

            f.close()

        delete_if_exists(audios[audio])
                    
        p = {
            "cmd": "service_4 " + str(audio_id),
            "api_key": server_api_key,
            "conversation": conversation + user,
            "extra_data": {
                "translator": translator
            }
        }
        p = json.dumps(p)
        res = await connect_to_server_and_send(p, False)
        res = json.loads(res)["response"]
        res = json.loads(res)["text"]

        audios_str += res + "\n"
                
    audios_str = audios_str.strip()
    return audios_str

async def __prepare_images_for_inference__(message, user, translator) -> str:
    images_str = ""
    images = __get_images_from_message__(message, True)

    for image in range(len(images)):
        images_str += "IMAGE #" + str(image + 1) + ": "

        with open(images[image], "rb") as f:
            image_bytes = f.read()
            image_id = await connect_to_server_and_send(image_bytes, True)

            f.close()

        delete_if_exists(images[image])
                    
        p = {
            "cmd": "service_3 " + str(image_id),
            "api_key": server_api_key,
            "conversation": conversation + user,
            "extra_data": {
                "translator": translator
            }
        }
        p = json.dumps(p)
        res = await connect_to_server_and_send(p, False)
        res = json.loads(res)
        res = eval(str(res["response"]))
        res = str(res["response"])

        images_str += res + "\n"
                
    images_str = images_str.strip()
    return images_str

@bot.event
async def on_ready() -> None:
    print("Logged in as " + bot.user.name)

@bot.command()
async def send_message(channel, message) -> None:
    await channel.send(message)

@bot.event
async def on_message(message) -> None:
    if (message.content.startswith("!i4")):
        data = message.content.split(" ")
        user = message.author.name
        mention = message.author.mention
        translator = translators.get(user, "")

        try:
            if (len(data) == 2):
                t = data[1]
                p = ""
            elif (len(data) >= 3):
                t = data[1]
                p = "".join([data[i] + " " for i in range(2, len(data))]).strip()
            else:
                raise Exception("Please see the I4.0 help, you got the syntax wrong.")
            
            if (t == "help"):
                res = "I4.0 Help:\nSyntax must be !i4 [OPTION] [MESSAGE]."
                res += "\nReplace [OPTION] with a valid option and [MESSAGE] with your message."
                res += "\nThe available options are:\nresponse - send a message to I4.0."
                res += "\ncc - clear the conversation. If you're having errors and you don't know why, use this option."
                res += "\ntr - set the I4.0 translator to your favourite language."
                res += "\ntrans - transcribe an audio."
                res += "\nitt - test the I4.0's Image To Text."
                res += "\nhelp - see this help message."
            elif (t == "response"):
                queue = json.loads(await connect_to_server_and_send(json.dumps({
                    "cmd": "get_queue"
                })))["response"]
                queue = json.loads(queue.replace("\'", "\""))
                queue_users = queue["queue"]
                queue_time = queue["time"]["chatbot"]

                if (queue_time < 0):
                    queue_time = "Unknown"

                await send_message(message.channel, "The current server queue is of '" + str(queue_users) + "' users.\nPredicted time: " + str(queue_time) + " seconds.")

                #images = await __prepare_images_for_inference__(message, user, translator)
                #audios = await __prepare_audios_for_inference__(message, user, translator)
                images = ""
                audios = ""

                p = images + "\n" + audios + "'" + user + "' says to you:\n" + p
                p = p.strip()

                p = json.dumps({
                    "cmd": "service_0 " + p,
                    "api_key": server_api_key,
                    "conversation": conversation + user,
                    "extra_data": {
                        "translator": translator
                    }
                })
                res = await connect_to_server_and_send(p)
                
                try:
                    res = dict(json.loads(res))
                    res = dict(json.loads(res["response"].replace("'", "\"")))

                    res = str(mention + " " + res["response"])
                except Exception as ex:
                    res = res["response"]
                    print("ERROR: " + str(ex))
            elif (t == "cc"):
                p = json.dumps({
                    "cmd": "clear_my_history",
                    "api_key": server_api_key,
                    "conversation": conversation + user
                })
                res = await connect_to_server_and_send(p)
                res = json.loads(res)
                res = res["response"]
                res = "Conversation deleted!"
            elif (t == "tr"):
                translators[user] = p
                res = "Translator set to '" + p + "'!"
            elif (t == "trans"):
                res = await __prepare_audios_for_inference__(message, user, translator)
            elif (t == "itt"):
                res = await __prepare_images_for_inference__(message, user, translator)
            else:
                raise Exception("Please see the I4.0 help using the command `!i4 help`, you got the syntax wrong.")
                
            await send_message(message.channel, str(res))
        except Exception as ex:
            await send_message(message.channel, "An error has occured! Please contact Alcoft or type `!i4 help`. ERROR: " + str(ex))

async def start():
    await bot.start(api_key)

async def close():
    await bot.close()

try:
    asyncio.get_event_loop().run_until_complete(start())
except KeyboardInterrupt:
    print("\nClosing server...")
    asyncio.get_event_loop().run_until_complete(close())

with open("temp/discord_trs.json", "w+") as f:
    f.write(json.dumps(translators))
    f.close()