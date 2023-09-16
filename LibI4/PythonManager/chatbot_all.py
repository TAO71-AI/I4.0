import chatbot_gpt4all as cbg4a
import chatbot_hf as cba
import chatbot_basics as basics
import chatbot_tf as cbtf
import chatbot_internet as cbi
import chatbot_pt as cbpt
import text_classification as tc
import translation as tns
import ai_generate_image as agi
import ai_config as cfg
import speech_recognition as sr
import ai_conversation as conv
import openai
import os
import datetime
import calendar
import base64

"""
README

Models:
0 - GPT4All chatbot.
1 - Tensorflow (selected version) chatbot.
2 - ChatGPT (API Key required) chatbot.
3 - Hugging Face selected model (Text-Generation only!).
4 - Text classification.
5 - Translation.
6 - Internet chatbot.
7 - PyTorch chatbot.
8 - Image generation.
"""

openai_model: str = cfg.current_data.openai_model
openai_max_tokens: int = cfg.current_data.max_length
system_messages: list[str] = []
apply_system_messages_to_tensorflow: bool = False
use_chat_history_if_available: bool = cfg.current_data.use_chat_history
order: str = cfg.current_data.prompt_order
model_pt_name: str = "pt_model"
current_emotion: str = "happy"

def SystemMessagesToStr(extra_system_messages: list[str] = None) -> str:
    sm_str = "("

    if (cfg.current_data.use_default_system_messages):
        for i in system_messages:
            sm_str += i

        if (extra_system_messages != None):
            for i in extra_system_messages:
                sm_str += i
    
    sm_str += ") "
    return sm_str

def LoadAllModels() -> None:
    for i in order:
        if (i == "0"):
            cbg4a.LoadModel()
        elif (i == "1"):
            cbtf.train_model()
        elif (i == "2"):
            if (not os.path.exists("openai_api_key.txt")):
                with open("openai_api_key.txt", "w+") as oak:
                    oak.close()
        elif (i == "3"):
            cba.LoadModel()
        elif (i == "4"):
            tc.LoadModel()
        elif (i == "5"):
            tns.LoadModels()
        elif (i == "6"):
            cbi.LoadModel()
        elif (i == "7"):
            cbpt.TrainModel(model_pt_name)
        elif (i == "8"):
            agi.LoadModel()
            
def RecognizeSpeech(lang: str, data: str) -> str:
    msg = ""
    audio = None
    
    if (not os.path.exists("SpeechRecog/")):
        os.mkdir("SpeechRecog/")

    if (not os.path.exists("Conversations/")):
        os.mkdir("Conversations/")
    
    with open("SpeechRecog/" + str(len(os.listdir("SpeechRecog/"))) + ".wav", "w+") as f:
        f.write(data)
        f.close()
    
    with open("SpeechRecog/" + str(len(os.listdir("SpeechRecog/"))) + ".wav", "rb") as f:
        audio = sr.Recognizer().record(f)
        
    try:
        msg = str(sr.Recognizer().recognize_whisper(audio, language = lang, model = cfg.current_data.whisper_model))
    except sr.UnknownValueError:
        msg = "An error has ocurred! Whisper could not understand you."
    except sr.RequestError as e:
        msg = "ERROR: " + str(e)
    
    return msg

def MakePrompt(prompt: str, order_prompt: str = "", args: str = "", extra_system_msgs: list[str] = [],
    translator: str = "", force_translator: bool = True, conversation: str = "") -> dict:
    global order, current_emotion
    LoadAllModels()

    if (cfg.current_data.use_default_system_messages):
        sm = system_messages

        for msg in extra_system_msgs:
            sm.append(msg)

    sm.append(cfg.current_data.custom_system_messages)

    if (cfg.current_data.use_dynamic_system_args):
        current_dt = datetime.datetime.now()

        sm.append("Your current state of humor is '" + current_emotion + "'.")
        sm.append("The current date is "
            + str(current_dt.day) + " of "
            + calendar.month_name[current_dt.month] + " "
            + str(current_dt.year)
            + ", and the current time is "
            + str(current_dt.hour) + ":"
            + str(current_dt.minute) + ".")
    
    if (cfg.current_data.system_messages_in_first_person):
        sm = basics.ToFirstPerson(sm)

    with open("openai_api_key.txt", "r") as oak:
        openai.api_key = oak.read()
        oak.close()
    
    cbg4a.system_messages = sm
    cba.system_messages = sm
    openai_msgs = [{"role": "system", "content": msg} for msg in sm] + [{"role": "user", "content": prompt}]

    if (not prompt.endswith(".") and not prompt.endswith("!") and not prompt.endswith("?")):
        prompt += "."

    if (len(order_prompt) <= 0):
        order_prompt = order

        if (len(order) <= 0):
            order_prompt = cfg.current_data.prompt_order
            order = order_prompt
    
    if (order_prompt.__contains__("5") and force_translator):
        prompt = tns.TranslateFrom1To2(prompt)
    
    if (args.__contains__("-ncb")):
        data = {
            "response": "",
            "model": "-1",
            "image": "",
            "tested_models": [],
            "text_classification": "-1",
            "errors": []
        }

        if (len(translator.strip()) > 0 and order_prompt.__contains__("5")):
            prompt = tns.TranslateFrom2To1(prompt, translator)

            data["response"] = "[translate " + prompt + " to " + translator + "]"
            data["tested_models"].append("5")

        if (args.__contains__("-img") and order_prompt.__contains__("8")):
            data["image"] = GenerateImage(prompt)
            data["response"] = "[agi " + prompt + "]"
            data["tested_models"].append("8")

        return data
    
    tested_models: list[str] = []
    errors: list[str] = []

    for i in order_prompt:
        response = "ERROR"

        try:
            if (i == "0"):
                response = "### RESPONSE: " + cbg4a.MakePrompt(prompt, use_chat_history_if_available, conversation)
            elif (i == "1"):
                response = "### RESPONSE: " + cbtf.get_ai_response((SystemMessagesToStr() if apply_system_messages_to_tensorflow else "") + prompt)
            elif (i == "2"):
                response = "### RESPONSE: " + openai.Completion.create(model = openai_model, messages = openai_msgs,
                    temperature = cfg.current_data.temp, max_tokens = openai_max_tokens)
            elif (i == "3"):
                response = "### RESPONSE: " + cba.MakePrompt(prompt, use_chat_history_if_available, conversation)
            elif (i == "6"):
                response = "### RESPONSE: " + cbi.MakePrompt(prompt)
            elif (i == "7"):
                response = "### RESPONSE: " + cbpt.GenerateResponse((SystemMessagesToStr() if apply_system_messages_to_tensorflow else "") + prompt)
            
            tested_models += i
        except Exception as ex:
            errors.append("Error on model '" + i + "': '" + str(ex) + "'")
            continue

        response = response.strip()
        
        if (response.startswith("### RESPONSE: ")):
            response = response[14:len(response)]

        try:
            if (response.__contains__("### Explanation")):
                response = response.split("### Explanation")[0]
            
            if (response.__contains__("### Prompt")):
                response = response.split("### Prompt")[0]

            if (response.__contains__("### Task")):
                response = response.split("### Task")[0]

            if (response.__contains__("### ASSISTANT")):
                response = response.split("### ASSISTANT")[0]
        except:
            pass
            
        if (len(response.strip()) > 0 and response.lower() != "error" and response.lower() != "error."):
            tcn: str = "-1"
            image: str = ""

            if (cfg.current_data.save_conversations and cfg.current_data.force_api_key and len(conversation.strip()) > 0):
                conv.SaveToConversation(conversation, response + "\n")

            if (order_prompt.__contains__("4")):
                try:
                    tcn = tc.DoPrompt(response)
                except Exception as ex:
                    tcn = "-1"
            
            if (order_prompt.__contains__("8") and response.__contains__("[agi ")):
                try:
                    img_prompt = response[response.index("[agi ") + 5:response[response.index("[agi ") + 5:len(response)].index("]")]
                    response = response.replace("[agi " + img_prompt + "]", "")
                    image = GenerateImage(img_prompt)

                    tested_models.append("8")
                except Exception as ex:
                    errors.append("Could not generate image: " + str(ex))
            
            if (order_prompt.__contains__("5") and len(translator.strip()) > 0):
                response = tns.TranslateFrom2To1(response, translator)
            
            return {
                "response": response,
                "model": i,
                "image": image,
                "tested_models": tested_models,
                "text_classification": tcn,
                "errors": errors
            }

    return {
        "response": "ERROR",
        "image": "",
        "model": "-1",
        "tested_models": tested_models,
        "text_classification": "-1",
        "errors": ["Error on response from all models."] + errors
    }

def SaveTF(model_name_tf: str = "tf_model", model_name_pt: str = "pt_model") -> None:
    if (cfg.current_data.prompt_order.__contains__("1")):
        cbtf.save_model(model_name_tf)
    
    if (cfg.current_data.prompt_order.__contains__("7")):
        cbpt.SaveModel(model_name_pt)

def GenerateImage(prompt: str) -> str:
    img_response = agi.GenerateImage(prompt)
    image = base64.b64encode(img_response).decode("utf-8")

    return image