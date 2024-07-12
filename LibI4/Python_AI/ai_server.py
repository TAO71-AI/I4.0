import websockets.server
import asyncio
import threading
import os
import json
import datetime
import time
import server_basics as sb
import chatbot_basics as cbb
import chatbot_all as cb
import ai_config as cfg
import ai_conversation as conv
import ai_logs as logs
import ip_banning as ip_ban
import data_share as ds

# Variables
max_buffer_length: int = 4096
max_users: int = 1000
requires_api_key: bool = cfg.current_data["force_api_key"]
queue: dict[str, int] = {}
args: list[str] = []
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
    "tts": [],
    "uvr": [],
    "img2img": [],
    "qa": []
}
persionality: list[str] = cfg.current_data["ai_args"].lower().split("+")
__version__: str = "v6.5.0"

# Server
def CheckFiles() -> None:
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
    if (len(times[model]) <= cfg.current_data["max_predicted_queue_time"]):
        times[model].append(time)
        logs.AddToLog("Added queue time for model '" + model + "' at the time '" + str(time) + "'.")

def __print__(data: str = "") -> None:
    logs.AddToLog("PRINT: " + str(data))
    print(str(data))

def __prompt__(service: str, prompt: str, args: str, extra_system_messages: list[str] = [], translator: str = "", force_translator: bool = True, conversation: list[str] = ["", ""], use_default_sys_prompts: bool = True, internet_type: str = "qa") -> dict:
    global queue

    if (list(queue.keys()).count(service) == 0):
        queue[service] = 0

    queue[service] += 1

    while (__get_queue_users__(service) > cfg.current_data["max_prompts"]):
        threading.Event().wait(1)
    
    try:
        if (service == "nsfw_filter-image"):
            response = cb.FilterNSFWImage(prompt)
        elif (service == "nsfw_filter-text"):
            response = cb.FilterNSFWText(prompt)
        elif (service == "whisper"):
            response = cb.RecognizeAudio(prompt)
        elif (service == "od" or service == "de" or service == "rvc" or service == "uvr" or service == "img2img" or service == "tr" or service == "sc" or service == "img2text"):
            response = cb.MakePrompt(prompt, cfg.current_data["prompt_order"], "-ncb-" + service, [], "", False, ["", ""], False, internet_type)
        else:
            response = cb.MakePrompt(prompt, cfg.current_data["prompt_order"], args, extra_system_messages, translator, force_translator, conversation, use_default_sys_prompts, internet_type)
    except Exception as ex:
        queue[service] -= 1
        raise ex
    
    queue[service] -= 1

    if (queue[service] < 0):
        queue[service] = 0

    if (type(response) != dict):
        response = {
            "response": str(response),
            "model": "",
            "files": [],
            "tested_models": [service],
            "text_classification": "",
            "title": "",
            "errors": []
        }

    return response

def __get_queue_users__(service: str) -> int:
    if (list(queue.keys()).count(service) == 0):
        return 0
    
    return queue[service]

def __predict_queue_time__(service: str) -> float:
    if (list(times.keys()).count(service) == 0):
        return -1
    
    predictedTime = 0
    
    for t in times[service]:
        predictedTime += t

    return predictedTime / (len(times[service]) if (len(times[service]) > 0) else 1)

def __send_share_data__(Data: str | bytes) -> list[tuple[bool, str, websockets.WebSocketClientProtocol]]:
    ds.Servers = cfg.current_data["data_share_servers"]
    
    loop = asyncio.new_event_loop()
    results = loop.run_until_complete(ds.SendToAllServers(Data))

    return results

def __share_data__(UserPrompt: str, UserFiles: dict[str, str | bytes], Response: str, ResponseFiles: dict[str, str | bytes]) -> None:
    if (not cfg.current_data["allow_data_share"]):
        return
    
    userFiles = []
    responseFiles = []
    
    for ft in UserFiles:
        for f in UserFiles[ft]:
            t = "unknown"

            if (ft == "images" or ft == "image"):
                t = "image"
            elif (ft == "audios" or ft == "audio"):
                t = "audio"
            elif (ft == "videos" or ft == "video"):
                t = "video"
            elif (ft == "documents" or ft == "document"):
                t = "document"
            
            userFiles.append({"Type": t, "Data": f})
    
    for ft in ResponseFiles:
        for f in ResponseFiles[ft]:
            t = "unknown"

            if (ft == "images" or ft == "image"):
                t = "image"
            elif (ft == "audios" or ft == "audio"):
                t = "audio"
            elif (ft == "videos" or ft == "video"):
                t = "video"
            elif (ft == "documents" or ft == "document"):
                t = "document"
            
            responseFiles.append({"Type": t, "Data": f})

    data = {
        "UserText": UserPrompt,
        "ResponseText": Response,
        "UserFiles": userFiles,
        "ResponseFiles": responseFiles
    }
    
    try:
        results = []
        dataThread = threading.Thread(target = lambda: results.extend(__send_share_data__(json.dumps(data))))
        dataThread.start()
        dataThread.join()

        for result in results:
            logs.AddToLog("[DATA SHARE] Result for '" + ds.Servers[results.index(result)] + "': '" + result[1] + "'.")

            if (result[0]):
                __print__("[DATA SHARE] Sent without errors to the server '" + ds.Servers[results.index(result)] + "'.")
            else:
                __print__("[DATA SHARE] Error sending to the server '" + ds.Servers[results.index(result)] + "'.")
    except Exception as ex:
        logs.AddToLog("[DATA SHARE] Error sending to ALL servers. Error: " + str(ex))
        __print__("[DATA SHARE] Error sending to ALL servers. Please check logs for more info.")

def DoPrompt(service: str, prompt: str, args: str = "", extra_system_messages: list[str] = [], translator: str = "", force_translator: bool = True, conversation: list[str] = ["", ""], use_default_sys_prompts: bool = True, internet_type: str = "qa") -> dict:
    return __prompt__(service, prompt, args, extra_system_messages, translator, force_translator, conversation, use_default_sys_prompts, internet_type)

def run_server_command(command_data: str, extra_data: dict[str] = {}) -> str:
    # Check if its user or admin
    if (command_data.lower().startswith("-u ")):
        command = command_data[3:]
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
        ai_args = cfg.current_data["ai_args"].lower()

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
    
    try:
        internet_type = extra_data["internet_type"]

        if (internet_type != "qa" and internet_type != "chatbot" and internet_type != "qa-chatbot"):
            raise ValueError("Internet type must be 'qa' or 'chatbot'.")
    except:
        internet_type = "qa"
    
    ip = str(extra_data["ip"])

    if (len(ai_args.strip()) == 0):
        ai_args = cfg.current_data["ai_args"]

    cb.system_messages = cbb.GetDefaultI4SystemMessages(ai_args.split("+"))

    # Execute command
    if (command.startswith("ai_fresponse ")):
        if (cfg.current_data["enable_predicted_queue_time"]):
            start_timer = time.time()
        
        res = DoPrompt("chatbot", command[13:], "", esm, translator, True, conver, use_default_sys_prompts, internet_type)

        if (res["errors"].count("NSFW") > 0 and cfg.current_data["ban_if_nsfw"] and ip != "0.0.0.0" and ip != "127.0.0.1"):
            ip_ban.BanIP(ip)
        
        try:
            __share_data__(command[13:], {}, res["response"], res["files"])
        except Exception as ex:
            logs.AddToLog("Could not send data to data server: " + str(ex))
            __print__("Could not send data to data server: " + str(ex))

        if (cfg.current_data["enable_predicted_queue_time"]):
            end_timer = time.time()
            __add_queue_time__("chatbot", end_timer - start_timer)
        
        return str(res)
    elif (command.startswith("ai_image ")):
        if (cfg.current_data["enable_predicted_queue_time"]):
            start_timer = time.time()
        
        p = command[9:]
        np = ""

        if (p.__contains__("[NEGATIVE]")):
            np = p[p.index("[NEGATIVE]") + 10:].strip()
            p = p[:p.index("[NEGATIVE]")].strip()
        elif (p.__contains__("(NEGATIVE)")):
            np = p[p.index("(NEGATIVE)") + 10:].strip()
            p = p[:p.index("(NEGATIVE)")].strip()

        res = DoPrompt("text2img", json.dumps({
            "prompt": p,
            "negative_prompt": np
        }), "-ncb-img", esm, translator, True, conver, use_default_sys_prompts, internet_type)

        if (res["errors"].count("NSFW") > 0 and cfg.current_data["ban_if_nsfw"] and ip != "0.0.0.0" and ip != "127.0.0.1"):
            ip_ban.BanIP(ip)

        try:
            __share_data__(command[9:], {}, res["response"], res["files"])
        except Exception as ex:
            logs.AddToLog("Could not send data to data server: " + str(ex))
            __print__("Could not send data to data server: " + str(ex))

        if (cfg.current_data["enable_predicted_queue_time"]):
            end_timer = time.time()
            __add_queue_time__("text2img", end_timer - start_timer)

        return res
    elif (command.startswith("ai_audio ")):
        if (cfg.current_data["enable_predicted_queue_time"]):
            start_timer = time.time()
        
        res = DoPrompt("text2audio", command[9:], "-ncb-aud", esm, translator, True, conver, use_default_sys_prompts, internet_type)

        if (res["errors"].count("NSFW") > 0 and cfg.current_data["ban_if_nsfw"] and ip != "0.0.0.0" and ip != "127.0.0.1"):
            ip_ban.BanIP(ip)

        try:
            __share_data__(command[9:], {}, res["response"], res["files"])
        except Exception as ex:
            logs.AddToLog("Could not send data to data server: " + str(ex))
            __print__("Could not send data to data server: " + str(ex))

        if (cfg.current_data["enable_predicted_queue_time"]):
            end_timer = time.time()
            __add_queue_time__("text2audio", end_timer - start_timer)

        return res
    elif (command.startswith("ai_depth ")):
        img = command[9:]
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
        
        if (cfg.current_data["enable_predicted_queue_time"]):
            start_timer = time.time()

        img = DoPrompt("de", "temp_img_" + str(tid) + ".png", "", [], "", False, ["", ""], False, internet_type)

        if (img["errors"].count("NSFW") > 0 and cfg.current_data["ban_if_nsfw"] and ip != "0.0.0.0" and ip != "127.0.0.1"):
            ip_ban.BanIP(ip)
        
        try:
            __share_data__("", {"images": ["temp_img_" + str(tid) + ".png"]}, "", img["files"])
        except Exception as ex:
            logs.AddToLog("Could not send data to data server: " + str(ex))
            __print__("Could not send data to data server: " + str(ex))

        if (cfg.current_data["enable_predicted_queue_time"]):
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
        
        if (cfg.current_data["enable_predicted_queue_time"]):
            start_timer = time.time()

        img = DoPrompt("od", "temp_img_" + str(tid) + ".png", "", [], "", False, ["", ""], False, internet_type)

        if (img["errors"].count("NSFW") > 0 and cfg.current_data["ban_if_nsfw"] and ip != "0.0.0.0" and ip != "127.0.0.1"):
            ip_ban.BanIP(ip)
        
        try:
            __share_data__("", {"images": ["temp_img_" + str(tid) + ".png"]}, "", img["files"])
        except Exception as ex:
            logs.AddToLog("Could not send data to data server: " + str(ex))
            __print__("Could not send data to data server: " + str(ex))

        if (cfg.current_data["enable_predicted_queue_time"]):
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
    elif (command.startswith("get_queue ")):
        queueType = command[10:]
        
        try:
            queueUsers = __get_queue_users__(queueType)
            queueTime = __predict_queue_time__(queueType)
        except Exception as ex:
            __print__("ERROR ON QUEUE: " + str(ex))
            logs.AddToLog("ERROR ON QUEUE: " + str(ex))

            raise Exception("Error obtaining the queue.")

        return str({"queue": queueUsers, "time": queueTime})
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
        
        if (cfg.current_data["enable_predicted_queue_time"]):
            start_timer = time.time()

        img = DoPrompt("img2text", "temp_img_" + str(tid) + ".png", "", [], "", False, ["", ""], False, internet_type)

        if (img["errors"].count("NSFW") > 0 and cfg.current_data["ban_if_nsfw"] and ip != "0.0.0.0" and ip != "127.0.0.1"):
            ip_ban.BanIP(ip)
        
        try:
            __share_data__("", {"images": ["temp_img_" + str(tid) + ".png"]}, img["response"], img["files"])
        except Exception as ex:
            logs.AddToLog("Could not send data to data server: " + str(ex))
            __print__("Could not send data to data server: " + str(ex))

        if (cfg.current_data["enable_predicted_queue_time"]):
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

        if (cfg.current_data["enable_predicted_queue_time"]):
            start_timer = time.time()

        audio = DoPrompt("whisper", "temp_audio_" + str(tid) + ".wav", "", [], "", False, ["", ""], False, internet_type)

        if (cfg.current_data["enable_predicted_queue_time"]):
            end_timer = time.time()
            __add_queue_time__("whisper", end_timer - start_timer)

        if (audio["error"].count("NSFW") > 0 and cfg.current_data["ban_if_nsfw"] and ip != "0.0.0.0" and ip != "127.0.0.1"):
            ip_ban.BanIP(ip)
        
        audio = json.dumps(audio)

        try:
            __share_data__("", {"audios": ["temp_audio_" + str(tid) + ".wav"]}, audio, {})
        except Exception as ex:
            logs.AddToLog("Could not send data to data server: " + str(ex))
            __print__("Could not send data to data server: " + str(ex))

        os.remove("temp_audio_" + str(tid) + ".wav")
        return str(audio)
    elif (command.startswith("ai_rvc ")):
        audio = command[7:]
        audio_bytes = b""

        audio = cfg.JSONDeserializer(audio)
        
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

        if (cfg.current_data["enable_predicted_queue_time"]):
            start_timer = time.time()

        aud_output = DoPrompt("rvc", json.dumps(audio), "", [], "", False, ["", ""], False, internet_type)

        try:
            __share_data__("", {"audios": ["temp_audio_" + str(tid) + ".wav"]}, "", aud_output["files"])
        except Exception as ex:
            logs.AddToLog("Could not send data to data server: " + str(ex))
            __print__("Could not send data to data server: " + str(ex))

        if (cfg.current_data["enable_predicted_queue_time"]):
            end_timer = time.time()
            __add_queue_time__("rvc", end_timer - start_timer)

        os.remove("temp_audio_" + str(tid) + ".wav")
        return str(aud_output)
    elif (command.startswith("translate ")):
        prompt = command[10:]

        if (len(translator.strip()) == 0):
            translator = "mul"
        
        if (cfg.current_data["enable_predicted_queue_time"]):
            start_timer = time.time()

        response = DoPrompt("tr", json.dumps({"tr": translator, "prompt": prompt}), "", [], "", False, ["", ""], False, internet_type)

        if (response["errors"].count("NSFW") > 0 and cfg.current_data["ban_if_nsfw"] and ip != "0.0.0.0" and ip != "127.0.0.1"):
            ip_ban.BanIP(ip)

        try:
            __share_data__(prompt, {}, response["response"], response["files"])
        except Exception as ex:
            logs.AddToLog("Could not send data to data server: " + str(ex))
            __print__("Could not send data to data server: " + str(ex))

        if (cfg.current_data["enable_predicted_queue_time"]):
            end_timer = time.time()
            __add_queue_time__("tr", end_timer - start_timer)

        return response
    elif (command.startswith("classify ")):
        prompt = command[9:]

        if (cfg.current_data["enable_predicted_queue_time"]):
            start_timer = time.time()

        response = DoPrompt("sc", prompt, "", [], "", False, ["", ""], False, internet_type)

        if (response["errors"].count("NSFW") > 0 and cfg.current_data["ban_if_nsfw"] and ip != "0.0.0.0" and ip != "127.0.0.1"):
            ip_ban.BanIP(ip)

        try:
            __share_data__(prompt, {}, response["response"], response["files"])
        except Exception as ex:
            logs.AddToLog("Could not send data to data server: " + str(ex))
            __print__("Could not send data to data server: " + str(ex))

        if (cfg.current_data["enable_predicted_queue_time"]):
            end_timer = time.time()
            __add_queue_time__("sc", end_timer - start_timer)

        return response
    elif (command.startswith("is_nsfw_text ")):
        prompt = command[13:]

        if (cfg.current_data["enable_predicted_queue_time"]):
            start_timer = time.time()

        response = DoPrompt("nsfw_filter-text", prompt, "", [], "", False, ["", ""], False, internet_type)

        try:
            __share_data__(prompt, {}, response["response"], response["files"])
        except Exception as ex:
            logs.AddToLog("Could not send data to data server: " + str(ex))
            __print__("Could not send data to data server: " + str(ex))

        if (cfg.current_data["enable_predicted_queue_time"]):
            end_timer = time.time()
            __add_queue_time__("nsfw_filter-text", end_timer - start_timer)

        return response
    elif (command.startswith("is_nsfw_image ")):
        img = command[14:]
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
        
        if (cfg.current_data["enable_predicted_queue_time"]):
            start_timer = time.time()
        
        img = DoPrompt("nsfw_filter-image", "temp_img_" + str(tid) + ".png", "", [], "", False, ["", ""], False, internet_type)

        try:
            __share_data__("", {"images": ["temp_img_" + str(tid) + ".png"]}, img["response"], img["files"])
        except Exception as ex:
            logs.AddToLog("Could not send data to data server: " + str(ex))
            __print__("Could not send data to data server: " + str(ex))

        if (cfg.current_data["enable_predicted_queue_time"]):
            end_timer = time.time()
            __add_queue_time__("nsfw_filter-image", end_timer - start_timer)

        os.remove("temp_img_" + str(tid) + ".png")
        return img
    elif (command.startswith("tts ")):
        if (cfg.current_data["enable_predicted_queue_time"]):
            start_timer = time.time()
        
        res = DoPrompt("tts", command[4:], "-ncb-tts", [], "", True, conver, use_default_sys_prompts, internet_type)

        if (res["errors"].count("NSFW") > 0 and cfg.current_data["ban_if_nsfw"] and ip != "0.0.0.0" and ip != "127.0.0.1"):
            ip_ban.BanIP(ip)
        
        try:
            __share_data__(command[4:], {}, res["response"], res["files"])
        except Exception as ex:
            logs.AddToLog("Could not send data to data server: " + str(ex))
            __print__("Could not send data to data server: " + str(ex))

        if (cfg.current_data["enable_predicted_queue_time"]):
            end_timer = time.time()
            __add_queue_time__("tts", end_timer - start_timer)

        return res
    elif (command.startswith("ai_uvr ")):
        audio = command[7:]
        audio_bytes = b""

        audio = cfg.JSONDeserializer(audio)
        
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

        if (cfg.current_data["enable_predicted_queue_time"]):
            start_timer = time.time()

        aud_output = DoPrompt("uvr", json.dumps(audio), "", [], "", False, ["", ""], False, internet_type)

        try:
            __share_data__("", {"audios": ["temp_audio_" + str(tid) + ".wav"]}, "", aud_output["files"])
        except Exception as ex:
            logs.AddToLog("Could not send data to data server: " + str(ex))
            __print__("Could not send data to data server: " + str(ex))

        if (cfg.current_data["enable_predicted_queue_time"]):
            end_timer = time.time()
            __add_queue_time__("uvr", end_timer - start_timer)

        os.remove("temp_audio_" + str(tid) + ".wav")
        return str(aud_output)
    elif (command.startswith("ai_img_to_img ")):
        image = command[14:]
        img_bytes = b""

        image = cfg.JSONDeserializer(image)
        
        if (not os.path.exists("ReceivedFiles/" + image["image"] + ".enc_file")):
            return "The file id '" + image["image"] + "' doesn't exists!"
        
        with open("ReceivedFiles/" + image["image"] + "_file", "rb") as f:
            img_bytes = f.read()
            f.close()
        
        tid = 0

        while (os.path.exists("temp_img_" + str(tid) + ".png")):
            tid += 1
        
        with open("temp_img_" + str(tid) + ".png", "wb") as f:
            f.write(img_bytes)
            f.close()

        img_name = "temp_img_" + str(tid) + ".png"
        image["image"] = img_name

        if (cfg.current_data["enable_predicted_queue_time"]):
            start_timer = time.time()

        img_output = DoPrompt("img2img", json.dumps(image), "", [], "", False, ["", ""], False, internet_type)

        if (img_output["errors"].count("NSFW") > 0 and cfg.current_data["ban_if_nsfw"] and ip != "0.0.0.0" and ip != "127.0.0.1"):
            ip_ban.BanIP(ip)

        try:
            __share_data__("", {"images": ["temp_image_" + str(tid) + ".png"]}, "", img_output["files"])
        except Exception as ex:
            logs.AddToLog("Could not send data to data server: " + str(ex))
            __print__("Could not send data to data server: " + str(ex))
        
        if (cfg.current_data["enable_predicted_queue_time"]):
            end_timer = time.time()
            __add_queue_time__("img2img", end_timer - start_timer)

        os.remove("temp_img_" + str(tid) + ".png")
        return str(img_output)
    elif (command.startswith("ban ") and admin):
        if (ip_ban.BanIP(command[4:])):
            __print__("IP banned!")
        else:
            __print__("This IP is already banned.")
    elif (command.startswith("unban ") and admin):
        if (ip_ban.UnbanIP(command[6:])):
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
        if (service.lower().startswith("get_queue ")):
            # Get queue
            prompt = service[10:].strip()
            server_response = run_server_command("-u get_queue " + prompt, extra_data)
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
            server_response = str(list(cfg.current_data["rvc_models"].keys()))
        else:
            raise Exception("Service doesn't exist or is not free.")
        
        return str(server_response)
    except Exception as ex:
        logs.AddToLog("[ERROR: NO API SERVICE]: " + str(ex))
        return "Error executing service. Make sure this service exists" + (" and you're using a valid API key." if (cfg.current_data["force_api_key"]) else ".")

def __execute_service_with_key__(service: str, key_data: dict, extra_data: dict[str]) -> str:
    cmd = ""
    price = 0
    has_exception = False

    if (service.startswith("service_0 ")):
        # Chatbot full-response

        price = 30
        cmd = "-u ai_fresponse " + service[10:]
    elif (service.startswith("service_1 ")):
        # Custom server command

        price = 50
        cmd = "-u " + service[10:]
    elif (service.startswith("service_2 ")):
        # Image generation

        price = 30
        cmd = "-u ai_image " + service[10:]
    elif (service.startswith("service_3 ")):
        # Image to Text

        price = 20
        cmd = "-u ai_img_to_text " + service[10:]
    elif (service.startswith("service_4 ")):
        # Whisper audio recognition

        price = 25
        cmd = "-u ai_whisper " + service[10:]
    elif (service.startswith("service_5 ")):
        # Audio generation
            
        price = 25
        cmd = "-u ai_audio " + service[10:]
    elif (service.startswith("service_6 ")):
        # Depth estimation
            
        price = 15
        cmd = "-u ai_depth " + service[10:]
    elif (service.startswith("service_7 ")):
        # Object detection
            
        price = 15
        cmd = "-u ai_object_detection " + service[10:]
    elif (service.startswith("service_8 ")):
        # RVC
            
        price = 20
        cmd = "-u ai_rvc " + service[10:]
    elif (service.startswith("service_9 ")):
        # Translate
            
        price = 10
        cmd = "-u translate " + service[10:]
    elif (service.startswith("service_10 ")):
        # Classify text
            
        price = 5
        cmd = "-u classify " + service[11:]
    elif (service.startswith("service_11 ")):
        # NSFW text filter
            
        price = 2.5
        cmd = "-u is_nsfw_text " + service[11:]
    elif (service.startswith("service_12 ")):
        # NSFW image filter
            
        price = 52.5
        cmd = "-u is_nsfw_image " + service[11:]
    elif (service.startswith("service_13 ")):
        # TTS
            
        price = 5
        cmd = "-u tts " + service[11:]
    elif (service.startswith("service_14 ")):
        # UVR
            
        price = 20
        cmd = "-u ai_uvr " + service[11:]
    elif (service.startswith("service_15 ")):
        # Image To Image
            
        price = 30
        cmd = "-u ai_img_to_img " + service[11:]
    elif (service.lower().startswith("clear_my_history") and cfg.current_data["save_conversations"]):
        # Clear chat history

        try:
            price = 0
            cmd = "-u clear_my_history"
            server_response = ""
        except Exception as ex:
            __print__("Error deleting chat history: " + str(ex))
    elif (service.lower().startswith("get_my_conversation")):
        price = 0
        cmd = "-u get_my_conversation"
        
    # Check if the key has enough tokens
    if (requires_api_key and (key_data == None or key_data["tokens"] < price)):
        return __execute_service_without_key__(service, extra_data)
    
    # Check if the service exists
    if (cmd == ""):
        raise Exception("Service doesn't exists.")
    
    __print__("Executing service with API key: " + service)

    try:
        # Get response
        key_data["tokens"] -= price
        server_response = run_server_command(cmd, extra_data)
        
        logs.AddToLog("Server response for '" + service + "': '" + str(server_response) + "'.")

        # Return the response
        server_response = str(server_response)
    except Exception as ex:
        if (str(ex).strip().lower() != "not enough tokens."):
            key_data["tokens"] += price / 2

        logs.AddToLog("[ERROR: API SERVICE]: " + str(ex))

        server_response = "Error executing service: " + str(ex)
        has_exception = True
    
    # Update key
    logs.AddToLog("Saving key '" + key_data["key"] + "'...")
    sb.SaveKey(key_data)
    logs.AddToLog("Key '" + key_data["key"] + "' saved successfully. New key data: " + str(key_data))

    # Update server
    UpdateServer()

    # Return an exception
    if (has_exception):
        raise Exception(server_response)
    
    # Return the response
    return server_response

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
            extra_data = cfg.JSONDeserializer(data["extra_data"])
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
    
    if (len(res.strip()) == 0):
        res = error
    
    server_response["cmd"] = data["cmd"]
    server_response["response"] = res

    return server_response

async def handle_client_ws(websocket: websockets.WebSocketClientProtocol) -> None:
    while (True):
        UpdateServer()

        try:
            data = await websocket.recv()
            data = cfg.JSONDeserializer(data)
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

async def accept_client_ws(websocket: websockets.WebSocketClientProtocol) -> None:
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
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    ip = "127.0.0.1" if (cfg.current_data["use_local_ip"]) else "0.0.0.0"
    server_ws = websockets.serve(accept_client_ws, ip, 8060)
    
    loop.run_until_complete(server_ws)
    loop.run_forever()

def start_server(_max_buffer_length = 4096, _max_users = 1000, _args = [], _extra_system_messages = [], _personality = cfg.current_data["ai_args"].lower().split("+")) -> None:
    global max_buffer_length, max_users, args, extra_system_messages, persionality

    # Variables
    max_buffer_length = _max_buffer_length
    max_users = _max_users
    args = _args
    extra_system_messages = _extra_system_messages
    persionality = _personality

    print("Starting I4.0 server version " + __version__)

    if (not os.path.exists("TOS.txt")):
        with open("TOS.txt", "w+") as f:
            f.close()

    if (requires_api_key and len(os.listdir("API/")) == 0):
        run_server_command("createkey", {"ip": "0.0.0.0"})

    cfg.SaveConfig()

    cb.system_messages = cbb.GetDefaultI4SystemMessages(persionality)
    cb.LoadAllModels()

    # Check everything before start server
    logs.CheckFilesAndDirs()

    # Start websockets server
    try:
        logs.AddToLog("Starting server...")
        threading.Thread(target = ws_server).start()
        __print__("Server started and listening.")
    except KeyboardInterrupt:
        logs.AddToLog("Server stopped.")
        print("Server stopped.")

        cfg.SaveConfig(cfg.current_data)
        os._exit(0)
    except Exception as ex:
        __print__("Error starting websocket: " + str(ex))
    
    if (cfg.current_data["auto_start_rec_files_server"]):
        import rec_files

CheckFiles()
start_server()