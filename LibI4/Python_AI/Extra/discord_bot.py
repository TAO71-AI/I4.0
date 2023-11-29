import os
import json
import discord
import websockets
import asyncio
import time
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
    api_key = f.read()
    f.close()

with open("temp/discord_server_apikey.txt", "r") as f:
    server_api_key = f.read()
    f.close()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix = "!i4", intents = intents)
websocket = None
ips: list[str] = [
    "127.0.0.1:8060",
    "147.78.87.113:8060"
]

async def connect_to_server_and_send(send_data: str = "") -> str:
    global websocket

    for ip in ips:
        try:
            uri = "ws://" + ip
            
            if (websocket == None or websocket.state != 1):
                websocket = await websockets.connect(uri, ping_timeout = 300)

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

            await websocket.send(send_data)
            response = await websocket.recv()
            
            return response
        except Exception as ex:
            print("ERROR: " + str(ex))

    return "ERROR CONNECTING TO ALL SERVERS."

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

        try:
            if (len(data) == 2):
                t = data[1]
                p = ""
            elif (len(data) >= 3):
                t = data[1]
                p = "".join([data[i] + " " for i in range(2, len(data))])
            else:
                raise Exception("Please see the I4.0 help, you got the syntax wrong.")
            
            if (t == "help"):
                res = "I4.0 Help:\nSyntax must be !i4 [OPTION] [MESSAGE]."
                res += "\nReplace [OPTION] with a valid option and [MESSAGE] with your message."
                res += "\nThe available options are:\nresponse - send a message to I4.0."
                res += "\ncc - clear the conversation. If you're having errors and you don't know why, use this option."
                res += "\nhelp - see this help message."
            elif (t == "response"):
                await send_message(message.channel, "The current server queue is of '" + json.loads(await connect_to_server_and_send(json.dumps({
                    "cmd": "get_queue"
                })))["response"] + "' users.")

                p = json.dumps({
                    "cmd": "service_0 " + p,
                    "api_key": server_api_key
                })
                res = await connect_to_server_and_send(p)
                
                try:
                    res = dict(json.loads(res))
                    res = dict(json.loads(res["response"].replace("'", "\"")))

                    res = str(res["response"])
                except Exception as ex:
                    res = res["response"]
                    print("ERROR: " + str(ex))
            elif (t == "cc"):
                p = json.dumps({
                    "cmd": "clear_my_history",
                    "api_key": server_api_key
                })
                res = await connect_to_server_and_send(p)
                res = json.loads(res)
                res = res["response"]
                res = "Conversation deleted!"
            else:
                raise Exception("Please see the I4.0 help, you got the syntax wrong.")
                
            await send_message(message.channel, str(res))
        except Exception as ex:
            await send_message(message.channel, "An error has occured! Please contact Alcoft or type '!i4 help'. ERROR: " + str(ex))

bot.run(api_key)