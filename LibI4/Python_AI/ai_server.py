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
plugins: list[str] = cb.basics.Plugins.FromStr(cfg.current_data.enabled_plugins)
times: dict[str, list[float]] = {
    "text2img": [],
    "img2text": [],
    "chatbot": [],
    "translation": [],
    "text2audio": [],
    "de": [],
    "whisper": [],
    "od": [],
    "rvc": [],
    "tr": [],
    "sc": [],
    "nsfw_filter-text": [],
    "nsfw_filter-image": [],
    "tts": []
}
__version__: str = "v4.2.0"

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
                        api_key["date"] = sb.GetCurrentDateDict()
            except Exception as ex:
                __print__("Error on API Key '" + str(api_key["key"]) + "': " + str(ex))

            sb.SaveKey(api_key)
    
    conv.SaveConversations()
    ip_ban.ReloadBannedIPs()

def __add_queue_time__(model: str, time: float) -> None:
    if (len(times[model]) <= cfg.current_data.max_predicted_queue_time):
        times[model].append(time)
        logs.AddToLog("Added queue time for model '" + model + "' at the time '" + str(time) + "'.")

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
        logs.AddToLog("PRINT: " + str(data))

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

    response = cb.MakePrompt(prompt, cfg.current_data.prompt_order, args, extra_system_messages, translator, force_translator, conversation, use_default_sys_prompts)
    queue -= 1

    return response

def DoPrompt(prompt: str, args: str = "", extra_system_messages: list[str] = [], translator: str = "", force_translator: bool = True, conversation: list[str] = ["", ""], use_default_sys_prompts: bool = True) -> dict:
    response = __prompt__(prompt, args, extra_system_messages, translator, force_translator, conversation, use_default_sys_prompts)
    
    if (response["text_classification"] == "0 stars"):
        cb.current_emotion = "angry"
    elif (response["text_classification"] == "1 stars"):
        cb.current_emotion = "sad"
    elif (response["text_classification"] == "4 stars"):
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
    esm += __get_args__(ai_args)

    # Execute command
    if (command.startswith("ai_response ")):
        return run_server_command("-u ai_fresponse " + command[12:], extra_data)
    elif (command.startswith("ai_fresponse ")):
        if (cfg.current_data.enable_predicted_queue_time):
            start_timer = time.time()
        
        res = DoPrompt(command[13:], "", esm, translator, True, conver, use_default_sys_prompts)

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
        
        res = DoPrompt(command[9:], "-ncb-aud", esm, translator, True, conver, use_default_sys_prompts)

        if (res["errors"].count("NSFW") > 0 and cfg.current_data.ban_if_nsfw and ip != "0.0.0.0" and ip != "127.0.0.1"):
            ip_ban.BanIP(ip)

        if (cfg.current_data.enable_predicted_queue_time):
            end_timer = time.time()
            __add_queue_time__("text2audio", end_timer - start_timer)

        return res
    elif (command.startswith("ai_depth ")):
        img = command[9:len(command)]
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

        img = cb.MakePrompt("temp_img_" + str(tid) + ".png", cfg.current_data.prompt_order, "-ncb-de", esm, translator)

        if (img["errors"].count("NSFW") > 0 and cfg.current_data.ban_if_nsfw and ip != "0.0.0.0" and ip != "127.0.0.1"):
            ip_ban.BanIP(ip)

        if (cfg.current_data.enable_predicted_queue_time):
            end_timer = time.time()
            __add_queue_time__("de", end_timer - start_timer)

        os.remove("temp_img_" + str(tid) + ".png")
        return img
    elif (command.startswith("ai_object_detection ")):
        img = command[20:]
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

        img = cb.MakePrompt("temp_img_" + str(tid) + ".png", cfg.current_data.prompt_order, "-ncb-od", esm, translator)

        if (img["errors"].count("NSFW") > 0 and cfg.current_data.ban_if_nsfw and ip != "0.0.0.0" and ip != "127.0.0.1"):
            ip_ban.BanIP(ip)

        if (cfg.current_data.enable_predicted_queue_time):
            end_timer = time.time()
            __add_queue_time__("od", end_timer - start_timer)

        os.remove("temp_img_" + str(tid) + ".png")
        return img
    elif (command.startswith("echo ") and admin):
        return command[5:len(command)]
    elif (command == "createkey" and admin and requires_api_key):
        return sb.GenerateKey(-1, False)["key"]
    elif (command == "createkey_d" and admin and requires_api_key):
        return sb.GenerateKey(-1, True)["key"]
    elif (command == "getallkeys" and admin and requires_api_key):
        return str(sb.GetAllKeys())
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
        return str(__version__)
    elif (command.startswith("clear_my_history")):
        try:
            conv.ClearConversation(conver[0], conver[1])
        except Exception as ex:
            __print__("ERROR: " + str(ex))
        
        return "Done! Conversation deleted!"
    elif (command.startswith("ai_img_to_text ")):
        img = command[15:]
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
        img = cb.MakePrompt(img, cfg.current_data.prompt_order, "-ncb-tr", esm, translator)

        if (img["errors"].count("NSFW") > 0 and cfg.current_data.ban_if_nsfw and ip != "0.0.0.0" and ip != "127.0.0.1"):
            ip_ban.BanIP(ip)

        if (cfg.current_data.enable_predicted_queue_time):
            end_timer = time.time()
            __add_queue_time__("img2text", end_timer - start_timer)

        os.remove("temp_img_" + str(tid) + ".png")
        return img
    elif (command.startswith("ai_whisper ")):
        audio = command[11:]
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

        audio = json.loads(cb.RecognizeAudio("temp_audio_" + str(tid) + ".wav"))
        text = audio["text"]
        lang = audio["lang"]

        if (cfg.current_data.enable_predicted_queue_time):
            start_timer = time.time()

        text = cb.MakePrompt(text, cfg.current_data.prompt_order, "-ncb-tr", esm, translator)
        audio = json.dumps({
            "text": text["response"],
            "lang": lang
        })

        if (cfg.current_data.enable_predicted_queue_time):
            end_timer = time.time()
            __add_queue_time__("whisper", end_timer - start_timer)

        if (text["errors"].count("NSFW") > 0 and cfg.current_data.ban_if_nsfw and ip != "0.0.0.0" and ip != "127.0.0.1"):
            ip_ban.BanIP(ip)

        os.remove("temp_audio_" + str(tid) + ".wav")
        return str(audio)
    elif (command.startswith("ai_rvc ")):
        audio = command[7:]
        audio_bytes = b""

        try:
            audio = json.loads(audio)
        except:
            audio = eval(audio)
        
        if (not os.path.exists("ReceivedFiles/" + audio["input"] + ".enc_file")):
            return "The file id '" + audio["input"] + "' doesn't exists!"
        
        with open("ReceivedFiles/" + audio["input"] + "_file", "rb") as f:
            audio_bytes = f.read()
            f.close()
        
        tid = 0

        while (os.path.exists("temp_audio_" + str(tid) + ".wav")):
            tid += 1
        
        with open("temp_audio_" + str(tid) + ".wav", "wb") as f:
            f.write(audio_bytes)
            f.close()

        audio_name = "temp_audio_" + str(tid) + ".wav"
        audio["input"] = audio_name

        if (cfg.current_data.enable_predicted_queue_time):
            start_timer = time.time()

        aud_output = cb.MakePrompt(json.dumps(audio), cfg.current_data.prompt_order, "-ncb-rvc", [], "", False, ["", ""], False)

        if (cfg.current_data.enable_predicted_queue_time):
            end_timer = time.time()
            __add_queue_time__("rvc", end_timer - start_timer)

        os.remove("temp_audio_" + str(tid) + ".wav")
        return str(aud_output)
    elif (command.startswith("translate ")):
        prompt = command[10:]

        if (len(translator.strip()) == 0):
            translator = "mul"
        
        if (cfg.current_data.enable_predicted_queue_time):
            start_timer = time.time()

        response = cb.Translate(translator, prompt)

        if (cfg.current_data.enable_predicted_queue_time):
            end_timer = time.time()
            __add_queue_time__("tr", end_timer - start_timer)

        return response
    elif (command.startswith("classify ")):
        prompt = command[9:]

        if (cfg.current_data.enable_predicted_queue_time):
            start_timer = time.time()

        response = cb.ClassifyText(prompt)

        if (cfg.current_data.enable_predicted_queue_time):
            end_timer = time.time()
            __add_queue_time__("sc", end_timer - start_timer)

        return response
    elif (command.startswith("is_nsfw_text ")):
        prompt = command[13:]

        if (cfg.current_data.enable_predicted_queue_time):
            start_timer = time.time()

        response = str(cb.FilterNSFWText(prompt)).lower()

        if (cfg.current_data.enable_predicted_queue_time):
            end_timer = time.time()
            __add_queue_time__("nsfw_filter-text", end_timer - start_timer)

        return response
    elif (command.startswith("is_nsfw_image ")):
        img = command[15:]
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
        
        img = cb.FilterNSFWImage("temp_img_" + str(tid) + ".png")

        if (cfg.current_data.enable_predicted_queue_time):
            end_timer = time.time()
            __add_queue_time__("nsfw_filter-image", end_timer - start_timer)

        os.remove("temp_img_" + str(tid) + ".png")
        return str(img).lower()
    elif (command.startswith("tts ")):
        if (cfg.current_data.enable_predicted_queue_time):
            start_timer = time.time()
        
        res = DoPrompt(command[4:], "-ncb-tts", [], "", True, conver, use_default_sys_prompts)

        if (res["errors"].count("NSFW") > 0 and cfg.current_data.ban_if_nsfw and ip != "0.0.0.0" and ip != "127.0.0.1"):
            ip_ban.BanIP(ip)

        if (cfg.current_data.enable_predicted_queue_time):
            end_timer = time.time()
            __add_queue_time__("tts", end_timer - start_timer)

        return res
    elif (command.startswith("ban ") and admin):
        if (ip_ban.BanIP(command[4:len(command)])):
            __print__("IP banned!")
        else:
            __print__("This IP is already banned.")
    elif (command.startswith("unban ") and admin):
        if (ip_ban.UnbanIP(command[6:len(command)])):
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
    
    return "Invalid command."

def __execute_service_without_key__(service: str, extra_data: dict[str]) -> str:
    __print__("Executing service without API key: " + service)

    try:
        if (service.lower().startswith("get_queue")):
            # Get queue
            server_response = run_server_command("-u get_queue", extra_data)
        elif (service.lower().startswith("get_tos")):
            # Get Terms Of Service (TOS)
            server_response = "ERROR: Could not get TOS file."

            with open("TOS.txt", "r") as f:
                server_response = f.read()
                f.close()
            
            if (len(server_response.strip()) == 0):
                server_response = "[NO TOS]"
        elif (service.lower().startswith("get_all_models")):
            # Get all models
            server_response = run_server_command("-u get_models", extra_data)
        elif (service.lower().startswith("rvc_models")):
            # Get all RVC models
            server_response = str(list(cfg.current_data.rvc_models.keys()))
        else:
            raise Exception("Service doesn't exist or is not free.")
        
        return str(server_response)
    except Exception as ex:
        logs.AddToLog("[ERROR: NO API SERVICE]: " + str(ex))
        return "Error executing service. Make sure this service exists" + (" and you're using a valid API key." if (cfg.current_data.force_api_key) else ".")

def __execute_service_with_key__(service: str, key_data: dict, extra_data: dict[str]) -> str:
    if (requires_api_key and (key_data == None or key_data["tokens"] <= 0)):
        return __execute_service_without_key__(service, extra_data)
    
    __print__("Executing service with API key: " + service)

    try:
        if (service.startswith("service_0 ")):
            # Chatbot full-response

            key_data["tokens"] -= 30
            server_response = run_server_command("-u ai_fresponse " + service[10:len(service)], extra_data)
        elif (service.startswith("service_1 ")):
            # Custom server command

            key_data["tokens"] -= 50
            server_response = run_server_command("-u " + service[10:len(service)], extra_data)
        elif (service.startswith("service_2 ")):
            # Image generation
            
            key_data["tokens"] -= 25
            server_response = run_server_command("-u ai_image " + service[10:len(service)], extra_data)
        elif (service.startswith("service_3 ")):
            # Image to Text

            key_data["tokens"] -= 25
            server_response = run_server_command("-u ai_img_to_text " + service[10:len(service)], extra_data)
        elif (service.startswith("service_4 ")):
            # Whisper audio recognition

            key_data["tokens"] -= 20
            server_response = run_server_command("-u ai_whisper " + service[10:len(service)], extra_data)
        elif (service.startswith("service_5 ")):
            # Audio generation
            
            key_data["tokens"] -= 25
            server_response = run_server_command("-u ai_audio " + service[10:len(service)], extra_data)
        elif (service.startswith("service_6 ")):
            # Depth estimation
            
            key_data["tokens"] -= 15
            server_response = run_server_command("-u ai_depth " + service[10:len(service)], extra_data)
        elif (service.startswith("service_7 ")):
            # Object detection
            
            key_data["tokens"] -= 15
            server_response = run_server_command("-u ai_object_detection " + service[10:len(service)], extra_data)
        elif (service.startswith("service_8 ")):
            # RVC
            
            key_data["tokens"] -= 20
            server_response = run_server_command("-u ai_rvc " + service[10:], extra_data)
        elif (service.startswith("service_9 ")):
            # Translate
            
            key_data["tokens"] -= 10
            server_response = run_server_command("-u translate " + service[10:], extra_data)
        elif (service.startswith("service_10 ")):
            # Classify text
            
            key_data["tokens"] -= 5
            server_response = run_server_command("-u classify " + service[11:], extra_data)
        elif (service.startswith("service_11 ")):
            # NSFW text filter
            
            key_data["tokens"] -= 2.5
            server_response = run_server_command("-u is_nsfw_text " + service[11:], extra_data)
        elif (service.startswith("service_12 ")):
            # NSFW image filter
            
            key_data["tokens"] -= 2.5
            server_response = run_server_command("-u is_nsfw_image " + service[11:], extra_data)
        elif (service.startswith("service_13 ")):
            # NSFW image filter
            
            key_data["tokens"] -= 5
            server_response = run_server_command("-u tts " + service[11:], extra_data)
        elif (service.lower().startswith("clear_my_history") and cfg.current_data.save_conversations):
            # Clear chat history
            try:
                run_server_command("-u clear_my_history", extra_data)
                server_response = ""
            except Exception as ex:
                __print__("Error deleting chat history: " + str(ex))
        elif (service.lower().startswith("get_my_conversation")):
            server_response = run_server_command("-u get_my_conversation", extra_data)
        else:
            raise Exception("Service doesn't exists.")
        
        logs.AddToLog("Server response for '" + service + "': '" + str(server_response) + "'.")
        logs.AddToLog("Saving key '" + key_data["key"] + "'...")

        sb.SaveKey(key_data)

        logs.AddToLog("Key '" + key_data["key"] + "' saved successfully. New key data: " + str(key_data))

        # Update server
        UpdateServer()

        return str(server_response)
    except Exception as ex:
        logs.AddToLog("[ERROR: API SERVICE]: " + str(ex))
        raise Exception("Error executing service: " + str(ex))

def RunService(data: str, key_data: dict = None, extra_data: dict[str] = {}) -> str:
    try:
        return __execute_service_with_key__(data, key_data, extra_data)
    except Exception as ex:
        logs.AddToLog("Error on the server: " + str(ex))
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
            logs.AddToLog("Could not load received extra_data, using default.")
            extra_data = {
                "system_msgs": [],
                "translator": ""
            }
    
    if (requires_api_key):
        try:
            api_key = data["api_key"]
            key_data = sb.GetKey(api_key)
        except:
            __print__("Could not get API key.")

        try:
            extra_data["ip"] = str(data["ip"])
        except Exception as ex:
            __print__("Error getting IP: " + str(ex))
        
        try:
            extra_data["key"] = key_data
            
            try:
                extra_data["conversation"] = [key_data["key"], data["conversation"]]
            except:
                extra_data["conversation"] = ["null", "null"]

            if (key_data["tokens"] > 0):
                res = RunService(data["cmd"], key_data, extra_data)
            else:
                res = RunService(data["cmd"], None, extra_data)
                error = "ERROR ON API KEY: Not enough tokens."
        except Exception as ex:
            res = RunService(data["cmd"], None, extra_data)

            print("Error! " + str(ex))
            logs.AddToLog("RunService error '" + str(ex) + "'.")
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
        UpdateServer()

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

def start_server(_max_buffer_length = 4096, _max_users = 1000, _args = [], _extra_system_messages = [], _plugins = cb.basics.Plugins.FromStr(cfg.current_data.enabled_plugins)) -> None:
    global max_buffer_length, max_users, args, extra_system_messages, plugins

    # Variables
    max_buffer_length = _max_buffer_length
    max_users = _max_users
    args = _args
    extra_system_messages = _extra_system_messages
    plugins = _plugins

    print("Starting I4.0 server version " + __version__)

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
    
    if (cfg.current_data.auto_start_rec_files_server):
        import rec_files as rf

CheckFiles()
start_server()