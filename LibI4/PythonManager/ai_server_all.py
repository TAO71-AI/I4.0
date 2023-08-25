import socket
import websockets.server
import asyncio
import threading
import os
import json
import datetime
import server_basics as sb
import chatbot_all as cb
import ai_config as cfg
import ai_conversation as conv

# Variables
max_buffer_length: int = 4096
max_users: int = 1000
requires_api_key: bool = cfg.current_data.force_api_key
queue: int = 0
args: list[str] = []
extra_system_messages: list[str] = []
version: str = "TAO NeuroN for Servers v1.0.0"

if (cfg.current_data.ai_args.__contains__("+self-aware")):
    args += cb.basics.ExtraSystemMessages.SelfAware()
elif (cfg.current_data.ai_args.__contains__("+human")):
    args += cb.basics.ExtraSystemMessages.Human()

if (cfg.current_data.ai_args.__contains__("+love-humanity")):
    args += cb.basics.ExtraSystemMessages.LoveHumanity()
elif (cfg.current_data.ai_args.__contains__("+hate-humanity")):
    args += cb.basics.ExtraSystemMessages.HateHumanity()
elif (cfg.current_data.ai_args.__contains__("+evil")):
    args += cb.basics.ExtraSystemMessages.Evil()

cb.system_messages = cb.basics.GetDefault_I4_SystemMessages(cb.basics.Plugins.All(), args)
cb.LoadAllModels()

# Server
def __print__(data: str = "", p: bool = False) -> None:
    if (p):
        while queue > 0:
            threading.Event().wait(0.1)

        print(data)
        return

    t = threading.Thread(target = __print__, args = (data, True))
    t.start()

def __prompt__(prompt: str, args: str, extra_system_messages: list[str] = [],
        translator: str = "", force_translator: bool = True, conversation: str = "") -> dict:
    global queue
    queue += 1

    while queue > 1:
        threading.Event().wait(0.1)

    response = cb.MakePrompt(prompt, "", args, extra_system_messages, translator, force_translator, conversation)
    queue -= 1

    return response

def DoPrompt(prompt: str, args: str = "", extra_system_messages: list[str] = [],
        translator: str = "", force_translator: bool = True, conversation: str = "") -> dict:
    response = __prompt__(prompt, args, extra_system_messages, translator, force_translator, conversation)
    
    if (response["text_classification"] == "0"):
        cb.current_emotion = "angry"
    elif (response["text_classification"] == "1"):
        cb.current_emotion = "sad"
    else:
        cb.current_emotion = "happy"

    return response

def run_server_command(command_data: str, extra_data: dict[str] = {}) -> str:
    # Check if its user or admin
    if (command_data.lower().startswith("-u ")):
        command = command_data[3:len(command_data)]
        admin = False

        __print__("A user (-u) used the command: '" + command + "'.")
    else:
        command = command_data
        admin = True
    
    # Try get variables
    try:
        esm = list(extra_data["system_msgs"])
    except:
        esm = []
    
    try:
        translator = extra_data["translator"]
    except:
        translator = ""
    
    try:
        conver = extra_data["conversation"]
    except:
        conver = "server" if admin else ""

    try:
        key_data = extra_data["key"]
    except:
        key_data = {}

    # Execute command
    if (command.startswith("ai_response ")):
        return DoPrompt(command[12:len(command)], "", esm, translator, True, conver)["response"]
    elif (command.startswith("ai_fresponse ")):
        return str(DoPrompt(command[13:len(command)], "", esm, translator, True, conver))
    elif (command.startswith("ai_translation ")):
        return DoPrompt(command[15:len(command)], "-t-ncb", esm, translator, True, "server")["response"]
    elif (command.startswith("echo ") and admin):
        return command[5:len(command)]
    elif (command == "createkey" and admin and requires_api_key):
        return sb.GenerateKey(-1, -1, False)["key"]
    elif (command == "createkey_d" and admin and requires_api_key):
        return sb.GenerateKey(-1, -1, True)["key"]
    elif (command == "getallkeys" and admin and requires_api_key):
        return str(sb.GetAllKeys())
    elif (command.startswith("sr ")):
        lang = ""
        data = ""
        
        try:
            if (command.startswith("sr -l ")):
                lang = command[6:command[6:len(command)].index(" ")]
                data = command[command.index(lang) + 1:len(command)]
            else:
                data = command[3:len(command)]
        except:
            data = command[3:len(command)]
        
        return cb.RecognizeSpeech(lang, data)
    elif (command.startswith("get_queue")):
        return str(queue)
    elif (command.startswith("version")):
        return str(version)
    elif (command.startswith("clear_my_history")):
        key = ""

        try:
            key = key_data["key"]
        except:
            key = "server"
        
        try:
            conv.conversations[key] = ""
        except Exception as ex:
            __print__("ERROR: " + str(ex))
        
        conv.SaveConversation(key)
        return "Done! Conversation deleted!"
    elif (command.startswith("save_tf_model") and admin):
        cb.SaveTF()
        return "Done!"
    elif (admin):
        try:
            return str(os.system(command))
        except Exception as ex:
            __print__("Error on command: '" + str(ex) + "'.")
            pass
    
    return "Invalid command."

def RunService(data: str, key_data: dict = None, extra_data: dict[str] = {}) -> dict:
    if (key_data == None):
        key_data = {"tokens": 0, "connections": 0}
        api_key = False
    else:
        api_key = (not requires_api_key or (key_data["tokens"] > 0 and key_data["connections"] > 0))

    try:
        if (data.startswith("service_0 ") and api_key):
            #Chatbot full-response

            key_data["tokens"] += (len(data) - 12) / 6
            server_response = run_server_command("-u ai_fresponse " + data[10:len(data)], extra_data)
        elif (data.startswith("service_1 ") and api_key):
            #Translation

            key_data["tokens"] += (len(data) - 10) / 8
            server_response = run_server_command("-u ai_translation " + data[10:len(data)], extra_data)
        elif (data.startswith("service_2 ") and api_key):
            #Custom server command

            key_data["tokens"] += (len(data) - 10)
            server_response = run_server_command("-u " + data[10:len(data)], extra_data)
        elif (data.startswith("service_3 ") and api_key):
            #Recognize speech
            
            key_data["tokens"] += (len(data) - 10) / 10
            server_response = run_server_command("-u " + data[10:len(data)], extra_data)
        elif (data.lower().startswith("get_queue")):
            #Get queue
            server_response = run_server_command("-u get_queue")
            key_data["connections"] += 1
        elif (data.lower().startswith("clear_my_history") and requires_api_key and cfg.current_data.save_conversations):
            # Clear chat history
            try:
                run_server_command("-u clear_my_history", extra_data)
                server_response = ""
            except:
                pass

            key_data["connections"] += 1
        else:
            server_response = ""
            key_data["connections"] += 1

        key_data["connections"] -= 1

        # Update server
        if (requires_api_key):
            api_keys = sb.GetAllKeys()

            for api_key in api_keys:
                try:
                    if (str(api_key["daily"]).lower() == "true" or str(api_key["daily"]) == "1"):
                        date = datetime.datetime.now()
                        key_date = datetime.datetime(int(api_key["date"]["year"]), int(api_key["date"]["month"]), int(api_key["date"]["day"]),
                            int(api_key["date"]["hour"]), int(api_key["date"]["minute"]))
                        date_diff = date - key_date

                        if (date_diff.total_seconds() >= 86400):
                            api_key["tokens"] = api_key["default"]["tokens"]
                            api_key["connections"] = api_key["default"]["connections"]
                            api_key["date"] = sb.GetCurrentDateDict()
                except:
                    continue

                sb.SaveKey(api_key)

        return str(server_response)
    except Exception as ex:
        return "Error on the server: " + str(ex)

def on_receive(data: dict[str]):
    server_response = {}
    error = ""
    extra_data = {}
            
    try:
        extra_data = dict(data["extra_data"])
    except:
        try:
            extra_data = json.loads(data["extra_data"])
        except:
            extra_data = {
                "system_msgs": [],
                "translator": ""
            }
    
    if (requires_api_key):
        try:
            api_key = data["api_key"]
            key_data = sb.GetKey(api_key)
        except:
            pass
        
        try:
            extra_data["key"] = key_data

            if (key_data["tokens"] > 0 and key_data["connections"] > 0):
                extra_data["conversation"] = key_data["key"]
                res = RunService(data["cmd"], key_data, extra_data)
            else:
                extra_data["conversation"] = key_data["key"]
                res = RunService(data["cmd"], key_data, extra_data)
                error = "ERROR ON API KEY: Not enough tokens or connections."
        except:
            res = RunService(data["cmd"], None, extra_data)
            error = "ERROR ON API KEY: Invalid key."
    elif (not requires_api_key):
        res = RunService(data["cmd"], None, extra_data)
    else:
        res = RunService(data["cmd"], None, extra_data)
        error = "ERROR ON API KEY: Invalid key."
    
    if (len(res.strip()) <= 0):
        res = error
    
    server_response["cmd"] = data["cmd"]
    server_response["response"] = res

    return server_response

def handle_client(client_socket: socket, address: socket):
    while (True):
        try:
            data = client_socket.recv(max_buffer_length)
            data = data.decode("utf-8")
            data = json.loads(data)
        except:
            server_response = "There was an error processing your petition. Make sure you are encoding the JSON code in UTF-8."
        
        if (len(data) > 0):
            __print__("Received data from '" + str(address) + "': '" + str(data) + "'.")
            server_response = on_receive(data)
        else:
            break

        __print__("Server response: '" + str(server_response) + "'.")
        client_socket.send(json.dumps(server_response).encode())

    client_socket.close()

async def handle_client_ws(websocket):
    while (True):
        try:
            data = await websocket.recv()
            data = json.loads(data)
        except:
            break

        if (len(data) > 0):
            __print__("Received data from websocket: '" + str(data) + "'.")
            server_response = on_receive(data)

            __print__("Server response: '" + str(server_response) + "'.")
            await websocket.send(json.dumps(server_response))
        else:
            break

def accept_client():
    while (True):
        client_socket, address = server_socket.accept()
        __print__("Incomming connection from '" + str(address) + "'.")

        try:
            client_socket.send(cfg.current_data.welcome_message.encode("utf-8"))
        except:
            __print__("Error sending welcome message.")

        client_handle_thread = threading.Thread(target = handle_client, args = (client_socket, address))
        client_handle_thread.start()

async def accept_client_ws(websocket):
    __print__("Incomming connection from websocket.")

    try:
        await websocket.send(cfg.current_data.welcome_message)
    except:
        __print__("Error sending welcome message.")
    
    await handle_client_ws(websocket)

def ws_server():
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    
    server_ws = websockets.server.serve(accept_client_ws, "0.0.0.0", 8061)

    event_loop.run_until_complete(server_ws)
    event_loop.run_forever()

if (requires_api_key and len(os.listdir("API/")) <= 0):
    run_server_command("createkey")

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("0.0.0.0", 8071))
server_socket.listen(max_users)

__print__("Server started and listening.")

ws_server_thread = threading.Thread(target = ws_server)
ws_server_thread.start()

__print__("Websocket server started and listening.\n\n")

try:
    accept_client_thread = threading.Thread(target = accept_client)
    accept_client_thread.start()
except:
    __print__("Error on accept client.")

while (True):
    command = input(">$ ")

    if (command == "quit" or command == "close" or command == "stop" or command == "exit"):
        __print__("Closing server...")

        cfg.SaveConfig()
        sb.StopDB()
        os._exit(0)
    elif (len(command.split()) > 0):
        __print__(run_server_command(command))