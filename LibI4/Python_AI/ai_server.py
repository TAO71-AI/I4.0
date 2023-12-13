import websockets.server
import asyncio
import threading
import os
import json
import datetime
import time
import server_basics as sb
import chatbot_all as cb
import ai_config as cfg
import ai_conversation as conv
import ai_logs as logs
import ip_banning as ip_ban

# Variables
max_buffer_length: int = 4096
max_users: int = 1000
requires_api_key: bool = cfg.current_data.force_api_key
queue: int = 0
args: list[str] = []
extra_system_messages: list[str] = []
plugins: list[str] = cb.basics.Plugins.FromStr(cfg.current_data.enabled_plugins)
version: str = "TAO71 I4.0 for Servers"
times: dict[str, list[float]] = {
    "text2img": [],
    "img2text": [],
    "chatbot": [],
    "translation": [],
    "text2audio": []
}

# Server
def CheckFiles() -> None:
    if (not os.path.exists("openai_api_key.txt")):
        with open("openai_api_key.txt", "w+") as f:
            f.write("")
            f.close()
    
    if (not os.path.exists("API/")):
        os.mkdir("API/")
    
    if (not os.path.exists("Logs/")):
        os.mkdir("Logs/")

def UpdateServer() -> None:
    CheckFiles()

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
            except Exception as ex:
                __print__("Error on API Key '" + str(api_key["key"]) + "': " + str(ex))

            sb.SaveKey(api_key)
    
    conv.SaveConversations()

def __add_queue_time__(model: str, time: float) -> None:
    if (len(times[model]) <= cfg.current_data.max_predicted_queue_time):
        times[model].append(time)

def __get_args__(ai_args: str) -> list[str]:
    args = []

    if (ai_args.__contains__("+self-aware")):
        args += cb.basics.ExtraSystemMessages.SelfAware()
    elif (ai_args.__contains__("+human")):
        args += cb.basics.ExtraSystemMessages.Human()

    if (ai_args.__contains__("+love-humanity")):
        args += cb.basics.ExtraSystemMessages.LoveHumanity()
    elif (ai_args.__contains__("+hate-humanity")):
        args += cb.basics.ExtraSystemMessages.HateHumanity()
    elif (ai_args.__contains__("+evil")):
        args += cb.basics.ExtraSystemMessages.Evil()
    
    return args

def __print__(data: str = "", p: bool = False) -> None:
    if (p):
        logs.AddToLog("PRINT: " + data)

        while queue > 0:
            threading.Event().wait(0.1)
        
        print(data)
        return

    t = threading.Thread(target = __print__, args = (data, True))
    t.start()

def __prompt__(prompt: str, args: str, extra_system_messages: list[str] = [], translator: str = "", force_translator: bool = True, conversation: list[str] = ["", ""], use_default_sys_prompts: bool = True) -> dict:
    global queue
    queue += 1

    while (queue > cfg.current_data.max_prompts):
        threading.Event().wait(0.1)

    response = cb.MakePrompt(prompt, [], args, extra_system_messages, translator, force_translator, conversation, use_default_sys_prompts)
    queue -= 1

    return response

def DoPrompt(prompt: str, args: str = "", extra_system_messages: list[str] = [], translator: str = "", force_translator: bool = True, conversation: list[str] = ["", ""], use_default_sys_prompts: bool = True) -> dict:
    response = __prompt__(prompt, args, extra_system_messages, translator, force_translator, conversation, use_default_sys_prompts)
    
    if (response["text_classification"] == "0"):
        cb.current_emotion = "angry"
    elif (response["text_classification"] == "1"):
        cb.current_emotion = "sad"
    elif (response["text_classification"] == "4"):
        cb.current_emotion = "happy"
    else:
        try:
            cb.current_emotion = str(int(response["text_classification"]))
            cb.current_emotion = "neutral"
        except:
            cb.current_emotion = response["text_classification"]

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
        use_default_sys_prompts = str(extra_data["use_default_sys_prompts"]).lower()
        use_default_sys_prompts = (use_default_sys_prompts == "yes" or use_default_sys_prompts == "true")
    except:
        use_default_sys_prompts = True
    
    try:
        ai_args = str(extra_data["ai_args"]).lower()
    except:
        ai_args = cfg.current_data.ai_args

    try:
        key_data = extra_data["key"]
    except:
        key_data = {}
    
    try:
        conver = list(extra_data["conversation"])

        if (len(conver) < 2):
            raise
    except:
        try:
            conver = [key_data["key"], ""]
        except:
            conver = ["", ""]
    
    ip = str(extra_data["ip"])

    if (len(ai_args.strip()) == 0):
        ai_args = cfg.current_data.ai_args

    cb.system_messages = cb.basics.GetDefault_I4_SystemMessages(plugins, __get_args__(ai_args))

    if (not use_default_sys_prompts):
        esm += __get_args__(ai_args)

    # Execute command
    if (command.startswith("ai_response ")):
        if (cfg.current_data.enable_predicted_queue_time):
            start_timer = time.time()
        
        res = DoPrompt(command[12:len(command)], "", esm, translator, True, conver, use_default_sys_prompts)

        if (res["errors"].count("NSFW") > 0 and cfg.current_data.ban_if_nsfw and ip != "0.0.0.0" and ip != "127.0.0.1"):
            ip_ban.BanIP(ip)
        
        if (cfg.current_data.enable_predicted_queue_time):
            end_timer = time.time()
            __add_queue_time__("chatbot", end_timer - start_timer)

        return res["response"]
    elif (command.startswith("ai_fresponse ")):
        if (cfg.current_data.enable_predicted_queue_time):
            start_timer = time.time()
        
        res = DoPrompt(command[13:len(command)], "", esm, translator, True, conver, use_default_sys_prompts)

        if (res["errors"].count("NSFW") > 0 and cfg.current_data.ban_if_nsfw and ip != "0.0.0.0" and ip != "127.0.0.1"):
            ip_ban.BanIP(ip)

        if (cfg.current_data.enable_predicted_queue_time):
            end_timer = time.time()
            __add_queue_time__("chatbot", end_timer - start_timer)
        
        return str(res)
    elif (command.startswith("ai_image ")):
        if (cfg.current_data.enable_predicted_queue_time):
            start_timer = time.time()
        
        p = command[9:len(command)]
        np = ""

        if (p.__contains__("[NEGATIVE]")):
            np = p[p.index("[NEGATIVE]") + 10:len(p)].strip()
            p = p[0:p.index("[NEGATIVE]")].strip()

        res = DoPrompt(json.dumps({
            "prompt": p,
            "negative_prompt": np
        }), "-ncb-img", esm, translator, True, conver, use_default_sys_prompts)

        if (res["errors"].count("NSFW") > 0 and cfg.current_data.ban_if_nsfw and ip != "0.0.0.0" and ip != "127.0.0.1"):
            ip_ban.BanIP(ip)

        if (len(res["errors"]) > 0):
            __print__("Errors: " + (e + "\n" for e in res["errors"]))

        if (cfg.current_data.enable_predicted_queue_time):
            end_timer = time.time()
            __add_queue_time__("text2img", end_timer - start_timer)

        return res
    elif (command.startswith("ai_audio ")):
        if (cfg.current_data.enable_predicted_queue_time):
            start_timer = time.time()
        
        res = DoPrompt(command[9:len(command)], "-ncb-aud", esm, translator, True, conver, use_default_sys_prompts)

        if (res["errors"].count("NSFW") > 0 and cfg.current_data.ban_if_nsfw and ip != "0.0.0.0" and ip != "127.0.0.1"):
            ip_ban.BanIP(ip)

        if (cfg.current_data.enable_predicted_queue_time):
            end_timer = time.time()
            __add_queue_time__("text2audio", end_timer - start_timer)

        return res
    elif (command.startswith("echo ") and admin):
        return command[5:len(command)]
    elif (command == "createkey" and admin and requires_api_key):
        return sb.GenerateKey(-1, -1, False)["key"]
    elif (command == "createkey_d" and admin and requires_api_key):
        return sb.GenerateKey(-1, -1, True)["key"]
    elif (command == "getallkeys" and admin and requires_api_key):
        return str(sb.GetAllKeys())
    elif (command.startswith("sr ")):
        lang = "en"
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
        q = int(queue / cfg.current_data.max_prompts)
        pt = {}

        for tkey in times:
            t = 0

            if (len(times[tkey]) > 0):
                for tval in times[tkey]:
                    t += tval
                
                t = t / len(times[tkey])
            else:
                t = -1
            
            pt[tkey] = t * (q + 1)

        return str({"queue": q, "time": pt})
    elif (command.startswith("version")):
        return str(version)
    elif (command.startswith("clear_my_history")):
        try:
            conv.ClearConversation(conver[0], conver[1])
        except Exception as ex:
            __print__("ERROR: " + str(ex))
        
        return "Done! Conversation deleted!"
    elif (command.startswith("ai_img_to_text ")):
        img = command[15:len(command)]
        img_bytes = b""
        
        if (not os.path.exists("ReceivedFiles/" + img + ".enc_file")):
            return "The file id '" + img + "' doesn't exists!"
        
        with open("ReceivedFiles/" + img + "_file", "rb") as f:
            img_bytes = f.read()
            f.close()
        
        with open("ReceivedFiles/" + img + ".enc_file", "r") as f:
            img = json.loads(f.read())
            f.close()
        
        tid = 0

        while os.path.exists("temp_img_" + str(tid) + ".png"):
            tid += 1
        
        with open("temp_img_" + str(tid) + ".png", "wb") as f:
            f.write(img_bytes)
            f.close()
        
        if (cfg.current_data.enable_predicted_queue_time):
            start_timer = time.time()

        img = cb.ImageToText("temp_img_" + str(tid) + ".png")
        img = cb.MakePrompt(img, "", "-ncb", esm, translator)

        if (img["errors"].count("NSFW") > 0 and cfg.current_data.ban_if_nsfw and ip != "0.0.0.0" and ip != "127.0.0.1"):
            ip_ban.BanIP(ip)

        if (cfg.current_data.enable_predicted_queue_time):
            end_timer = time.time()
            __add_queue_time__("img2text", end_timer - start_timer)

        os.remove("temp_img_" + str(tid) + ".png")
        return img
    elif (command.startswith("ai_whisper ")):
        audio = command[11:len(command)]
        audio_bytes = b""
        
        if (not os.path.exists("ReceivedFiles/" + audio + ".enc_file")):
            return "The file id '" + audio + "' doesn't exists!"
        
        with open("ReceivedFiles/" + audio + "_file", "rb") as f:
            audio_bytes = f.read()
            f.close()
        
        with open("ReceivedFiles/" + audio + ".enc_file", "r") as f:
            audio = json.loads(f.read())
            f.close()
        
        tid = 0

        while os.path.exists("temp_audio_" + str(tid) + ".wav"):
            tid += 1
        
        with open("temp_audio_" + str(tid) + ".wav", "wb") as f:
            f.write(audio_bytes)
            f.close()

        audio = cb.RecognizeAudio("temp_audio_" + str(tid) + ".wav")
        audio = cb.MakePrompt(audio, "", "-ncb", esm, translator)

        if (audio["errors"].count("NSFW") > 0 and cfg.current_data.ban_if_nsfw and ip != "0.0.0.0" and ip != "127.0.0.1"):
            ip_ban.BanIP(ip)

        os.remove("temp_audio_" + str(tid) + ".wav")
        return audio
    elif (command.startswith("save_tf_model") and admin):
        cb.SaveTF()
        return "Done!"
    elif (command.startswith("ban ") and admin):
        if (ip_ban.BanIP(command[4:len(command)])):
            __print__("IP banned!")
        else:
            __print__("This IP is already banned.")
    elif (command.startswith("unban ") and admin):
        if (ip_ban.UnbanIP(command[4:len(command)])):
            __print__("IP unbanned!")
        else:
            __print__("This IP isn't banned.")
    elif (command.startswith("sbips") and admin):
        ip_ban.ReloadBannedIPs()
        return "The banned IPs are: " + str(ip_ban.banned_ips)
    elif (command.startswith("get_my_conversation")):
        return json.dumps(conv.GetConversation(conver[0], conver[1]))
    elif (command.startswith("get_models")):
        return json.dumps(cb.GetAllModels())
    elif (admin):
        try:
            return str(os.system(command))
        except Exception as ex:
            __print__("Error on command: '" + str(ex) + "'.")
            pass
    
    return "Invalid command."

def RunService(data: str, key_data: dict = None, extra_data: dict[str] = {}) -> dict:
    if (key_data == None):
        key_data = sb.GenerateKey(0, 0, False)
        api_key = not requires_api_key
        temp_key = True
    else:
        api_key = (not requires_api_key or (key_data["tokens"] > 0 and key_data["connections"] > 0))
        temp_key = False

    try:
        if (data.startswith("service_0 ") and api_key):
            # Chatbot full-response

            key_data["tokens"] -= (len(data) - 12) / 6
            server_response = run_server_command("-u ai_fresponse " + data[10:len(data)], extra_data)
        elif (data.startswith("service_1 ") and api_key):
            # Custom server command

            key_data["tokens"] -= (len(data) - 10)
            server_response = run_server_command("-u " + data[10:len(data)], extra_data)
        elif (data.startswith("service_2 ") and api_key):
            # Image generation
            
            key_data["tokens"] -= (len(data) - 12) / 4
            server_response = run_server_command("-u ai_image " + data[10:len(data)], extra_data)
        elif (data.startswith("service_3 ") and api_key):
            # Image to Text

            key_data["tokens"] -= 25
            server_response = run_server_command("-u ai_img_to_text " + data[10:len(data)], extra_data)
        elif (data.startswith("service_4 ") and api_key):
            # Whisper audio recognition

            key_data["tokens"] -= 12
            server_response = run_server_command("-u ai_whisper " + data[10:len(data)], extra_data)
        elif (data.startswith("service_5 ") and api_key):
            # Audio generation
            
            key_data["tokens"] -= (len(data) - 12) / 5
            server_response = run_server_command("-u ai_audio " + data[10:len(data)], extra_data)
        elif (data.lower().startswith("get_queue")):
            # Get queue
            server_response = run_server_command("-u get_queue", extra_data)
            key_data["connections"] += 1
        elif (data.lower().startswith("clear_my_history") and requires_api_key and cfg.current_data.save_conversations):
            # Clear chat history
            try:
                run_server_command("-u clear_my_history", extra_data)
                server_response = ""
            except:
                pass

            key_data["connections"] += 1
        elif (data.lower().startswith("get_tos")):
            # Get Terms Of Service (TOS)
            with open("TOS.txt", "r+") as f:
                server_response = f.read()
                f.close()
            
            key_data["connections"] += 1
        else:
            server_response = ""
            key_data["connections"] += 1

        key_data["connections"] -= 1

        if (temp_key):
            sb.DeleteKey(key_data["key"])
        else:
            sb.SaveKey(key_data)

        # Update server
        UpdateServer()

        return str(server_response)
    except Exception as ex:
        return "Error on the server: " + str(ex)

def on_receive(data: dict[str]) -> dict:
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
            extra_data["ip"] = str(data["ip"])
        except Exception as ex:
            __print__("Error getting IP: " + str(ex))
        
        try:
            extra_data["key"] = key_data

            if (key_data["tokens"] > 0 and key_data["connections"] > 0):
                extra_data["conversation"] = [key_data["key"], data["conversation"]]
                res = RunService(data["cmd"], key_data, extra_data)
            else:
                extra_data["conversation"] = [key_data["key"], data["conversation"]]
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

async def handle_client_ws(websocket) -> None:
    while (True):
        try:
            data = await websocket.recv()
            data = json.loads(data)
        except:
            data = {}

        if (len(data) > 0):
            __print__("Received data from websocket: '" + str(data) + "'.")
            data["ip"] = str(websocket.remote_address[0])
            server_response = on_receive(data)

            __print__("Server response: '" + str(server_response) + "'.")
            await websocket.send(json.dumps(server_response))
        else:
            break

async def accept_client_ws(websocket) -> None:
    __print__("Incomming connection from '" + str(websocket.remote_address[0]) + ":" + str(websocket.remote_address[1]) + "'.")
    ip_ban.ReloadBannedIPs()

    if (ip_ban.IsIPBanned(str(websocket.remote_address[0]))):
        __print__("Banned IP, connection closed.")

        try:
            await websocket.send("{\"response\": \"You are banned.\"}")
        except:
            pass

        await websocket.close()
        return

    await handle_client_ws(websocket)

def ws_server() -> None:
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    
    ip = "127.0.0.1" if (cfg.current_data.use_local_ip) else "0.0.0.0"
    server_ws = websockets.server.serve(accept_client_ws, ip, 8060)

    event_loop.run_until_complete(server_ws)
    event_loop.run_forever()

def start_server(_max_buffer_length = 4096, _max_users = 1000, _args = [], _extra_system_messages = [], _plugins = cb.basics.Plugins.FromStr(cfg.current_data.enabled_plugins), _version = "TAO71 I4.0 for Servers") -> None:
    global max_buffer_length, max_users, args, extra_system_messages, plugins, version

    # Variables
    max_buffer_length = _max_buffer_length
    max_users = _max_users
    args = _args
    extra_system_messages = _extra_system_messages
    plugins = _plugins
    version = _version

    if (not os.path.exists("TOS.txt")):
        with open("TOS.txt", "w+") as f:
            f.close()

    if (requires_api_key and len(os.listdir("API/")) <= 0):
        run_server_command("createkey", {"ip": "0.0.0.0"})

    cfg.SaveConfig()

    cb.system_messages = cb.basics.GetDefault_I4_SystemMessages(plugins, args)
    cb.LoadAllModels()

    # Check everything before start server
    logs.CheckFilesAndDirs()

    # Start websockets server
    try:
        logs.AddToLog("Starting server...")

        ws_server_thread = threading.Thread(target = ws_server)
        ws_server_thread.start()

        __print__("Server started and listening.")
    except Exception as ex:
        __print__("Error starting websocket: " + str(ex))

CheckFiles()
start_server()