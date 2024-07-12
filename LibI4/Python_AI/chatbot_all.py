# Import the models
import Inference.chatbot_gpt4all as cbg4a
import Inference.chatbot_hf as cba
import Inference.text_classification as tc
import Inference.translation as tns
import Inference.ai_generate_image as agi
import Inference.ai_img_to_text as itt
import Inference.ai_generate_audio as aga
import Inference.ai_filters as filters
import Inference.ai_depth_estimation as de
import Inference.ai_object_detection as od
import Inference.speech_recog as sr
import Inference.rvc_inf as rvc
import Inference.tts as tts
import Inference.ai_vocal_separator as uvr
import Inference.image_to_image as img2img
import Inference.ai_question_answering as qa
import internet_connection as internet
import ai_config as cfg
import ai_conversation as conv
import ai_logs as logs
import PIL.Image as Image
import os
import base64
import json
import datetime
import calendar

# Please read this
"""
README

Models:
g4a - GPT4All chatbot (Text Generation).
hf - Hugging Face selected model (Text Generation).
sc - Text classification (Sequence Classification).
tr - Translation.
text2img - Image generation.
img2text - Image to Text.
whisper - Recognize audio using Whisper (Speech To Text).
text2audio - Audio generation.
nsfw_filter-text - Check if a text is NSFW.
nsfw_filter-image - Check if an image is NSFW.
de - Depth Estimation.
od - Object Detection.
rvc - Uses RVC on an audio file.
uvr - Uses UVR on an audio file.
tts - Text to Speech.
img2img - Image to Image.
qa - Question Answering.
"""

# Set some variables
system_messages: list[str] = []
use_chat_history_if_available: bool = cfg.current_data["use_chat_history"]
order: str = cfg.current_data["prompt_order"]

# Get the models' name
def GetAllModels() -> dict[str]:
    models = order.split(" ")
    mls = {}

    for i in models:
        if (i == "g4a"):
            mls[i] = cfg.current_data["gpt4all_model"]
        elif (i == "hf"):
            mls[i] = cfg.current_data["hf_model"]
        elif (i == "sc"):
            mls[i] = cfg.current_data["text_classification_model"]
        elif (i == "tr"):
            mls[i] = str([cfg.current_data["translation_classification_model"]] + list(cfg.current_data["translation_models"].values()))
        elif (i == "text2img"):
            mls[i] = cfg.current_data["image_generation_model"]
        elif (i == "img2text"):
            mls[i] = cfg.current_data["img_to_text_model"]
        elif (i == "text2audio"):
            mls[i] = cfg.current_data["text_to_audio_model"]
        elif (i == "whisper"):
            mls[i] = cfg.current_data["whisper_model"]
        elif (i == "nsfw_filter-text"):
            mls[i] = cfg.current_data["nsfw_filter_text_model"]
        elif (i == "nsfw_filter-image"):
            mls[i] = cfg.current_data["nsfw_filter_image_model"]
        elif (i == "de"):
            mls[i] = cfg.current_data["depth_estimation_model"]
        elif (i == "od"):
            mls[i] = cfg.current_data["object_detection_model"]
        elif (i == "rvc"):
            mls[i] = str(list(cfg.current_data["rvc_models"].keys()))
        elif (i == "tts"):
            mls[i] = str(tts.GetVoices())
        elif (i == "uvr"):
            mls[i] = cfg.current_data["uvr_model"]
        elif (i == "img2img"):
            mls[i] = cfg.current_data["image_to_image_model"]
        elif (i == "qa"):
            mls[i] = cfg.current_data["qa_model"]

        mls[i] = mls[i].replace("\\", "/")
        
        if (mls[i].count("/") > 0 and os.path.exists(mls[i])):
            mls[i] = mls[i].split("/")[-1]
    
    return mls

# Load all the models
def LoadAllModels() -> None:
    models = order.split(" ")

    for i in models:
        if (i == "g4a"):
            cbg4a.LoadModel()
        elif (i == "hf"):
            cba.LoadModel()
        elif (i == "sc"):
            tc.LoadModel()
        elif (i == "tr"):
            tns.LoadModels()
        elif (i == "text2img"):
            agi.LoadModel()
        elif (i == "img2text"):
            itt.LoadModel()
        elif (i == "text2audio"):
            aga.LoadModel()
        elif (i == "nsfw_filter-text"):
            filters.LoadTextModel()
        elif (i == "nsfw_filter-image"):
            filters.LoadImageModel()
        elif (i == "de"):
            de.LoadModel()
        elif (i == "od"):
            od.LoadModel()
        elif (i == "whisper"):
            sr.LoadModel()
        elif (i == "tts"):
            tts.LoadTTS()
        elif (i == "img2img"):
            img2img.LoadModel()
        elif (i == "qa"):
            qa.LoadModel()

# Check if a text prompt is NSFW
def IsTextNSFW(prompt: str) -> bool:
    # If the model is loaded, check NSFW
    if (cfg.current_data["prompt_order"].__contains__("nsfw_filter-text")):
        return filters.IsTextNSFW(prompt)
    
    # If not, return none
    return None

# Check if an image prompt is NSFW
def IsImageNSFW(image: str | Image.Image) -> bool:
    # If the model is loaded, check NSFW
    if (cfg.current_data["prompt_order"].__contains__("nsfw_filter-image")):
        return filters.IsImageNSFW(image)
    
    # If not, return none
    return None

# Process the user prompt
def MakePrompt(prompt: str, order_prompt: str = "", args: str = "", extra_system_msgs: list[str] = [], translator: str = "", force_translator: bool = True, conversation: list[str] = ["", ""], use_default_sys_prompts: bool = True, internet_type: str = "qa") -> dict:
    # Import some global variables and load the models if not loaded
    global order
    LoadAllModels()

    # Set args
    args = args.split("-")

    # Set System Prompts
    sm = []

    # Set System Prompts to default if allowed
    if (cfg.current_data["use_default_system_messages"]):
        sm = system_messages if (use_default_sys_prompts) else []

    # Set extra or custom System Prompts
    for msg in extra_system_msgs:
        if (sm.count(msg.strip()) == 0):
            sm.append(msg.strip())

    # Set dynamic System Prompts if allowed
    if (cfg.current_data["use_dynamic_system_args"]):
        # Get the current date and create variables
        current_dt = datetime.datetime.now()
        dsm = []

        # Apply to System Prompts
        dsm.append("The current date is " + str(current_dt.day) + " of " + calendar.month_name[current_dt.month] + " " + str(current_dt.year) + ", and the current time is " + ("0" + str(current_dt.hour) if (current_dt.hour < 10) else str(current_dt.hour)) + ":" + ("0" + str(current_dt.minute) if (current_dt.minute < 10) else str(current_dt.minute)) + ".")

        if (current_dt.day == 16 and current_dt.month == 9):
            dsm.append("Today it's your birthday.")

        for m in dsm:
            if (sm.count(m) == 0):
                sm.append(m)
    
    # Strip the System Prompts
    for sp in sm:
        if (len(sp.split()) == 0):
            sm.remove(sp)
        elif (sp.endswith("\n")):
            sm[sm.index(sp)] = sp[:-1]
    
    # Apply the System Prompts to models
    cbg4a.system_messages = sm
    cba.system_messages = sm

    # Set the prompt order
    if (len(order_prompt) <= 0):
        order_prompt = order

        if (len(order) <= 0):
            order_prompt = cfg.current_data["prompt_order"]
            order = order_prompt
    
    # Translate if the use of translators are forced
    if (force_translator and cfg.current_data["use_other_services_on_chatbot"]):
        prompt = Translate("auto", prompt)
    
    # Check if the prompt is NSFW
    if (not cfg.current_data["allow_processing_if_nsfw"]):
        # Check the prompt
        is_nsfw = FilterNSFWText(prompt)

        if (is_nsfw == None):
            is_nsfw = False

        # If it's NSFW and the use of NSFW is not allowed, return an error
        if (is_nsfw):
            return {
                "response": "ERROR",
                "model": "-1",
                "files": {},
                "tested_models": [],
                "text_classification": "-1",
                "title": "NO TITLE",
                "errors": ["NSFW detected! NSFW is not allowed.", "NSFW"]
            }
    
    # If the user doesn't want to use the chatbot
    if (args.count("ncb") >= 1):
        # Create data dictionary
        data = {
            "response": "",
            "model": "-1",
            "files": {},
            "tested_models": [],
            "text_classification": "-1",
            "title": "NO TITLE",
            "errors": []
        }

        # Translate if use the use of translators are allowed
        if (len(translator.strip()) > 0 and cfg.current_data["use_other_services_on_chatbot"]):
            data["response"] = Translate(translator, prompt)
            data["tested_models"].append("tr")
        else:
            data["response"] = prompt

        # Check the Image to Text if the user requests it
        if (args.count("img2text") >= 1 and order_prompt.__contains__("img2text")):
            # Check if the user's image is NSFW (if allowed)
            if (not cfg.current_data["allow_processing_if_nsfw"]):
                # Check if the user's image is NSFW
                is_nsfw = FilterNSFWImage(prompt)

                if (is_nsfw == None):
                    is_nsfw = False

                # If the user's image is NSFW and the use of NSFW is not allowed, return an error
                if (is_nsfw and not cfg.current_data["allow_processing_if_nsfw"]):
                    return {
                        "response": "ERROR",
                        "model": "-1",
                        "files": {},
                        "tested_models": [],
                        "text_classification": "-1",
                        "title": "NO TITLE",
                        "errors": ["NSFW detected! NSFW is not allowed.", "NSFW"]
                    }
            
            # Get response from the Image To Text model
            data["response"] = ImageToText(prompt)
            data["tested_models"].append("img2text")

        # Generate an image if the user requests it
        if (args.count("img") >= 1 and order_prompt.__contains__("text2img")):
            imgs = GenerateImages(prompt)
            
            try:
                # Try to append all the images. If the list is not set, will return an error
                data["files"]["images"] += imgs
            except:
                # Create the list if there is an error
                data["files"]["images"] = imgs
            
            data["response"] = "[agi " + prompt + "]"
            data["tested_models"].append("text2img")
        
        # Generate an audio if the user requests it
        if (args.count("aud") >= 1 and order_prompt.__contains__("text2audio")):
            aud = GenerateAudio(prompt)

            try:
                # Try to append all the audios. If the list is not set, will return an error
                data["files"]["audios"].append(aud)
            except:
                # Create the list if there is an error
                data["files"]["audios"] = [aud]
            
            data["response"] = "[aga " + prompt + "]"
            data["tested_models"].append("text2audio")
        
        # Estimate depth if the user requests it
        if (args.count("de") >= 1 and order_prompt.__contains__("de")):
            # Check if the user's image is NSFW
            if (not cfg.current_data["allow_processing_if_nsfw"]):
                is_nsfw = FilterNSFWImage(prompt)

                if (is_nsfw == None):
                    is_nsfw = False

                # If the user's image is NSFW and the use of NSFW is not allowed, return an error
                if (is_nsfw):
                    return {
                        "response": "ERROR",
                        "model": "-1",
                        "files": {},
                        "tested_models": [],
                        "text_classification": "-1",
                        "title": "NO TITLE",
                        "errors": ["NSFW detected! NSFW is not allowed.", "NSFW"]
                    }

            # If the image is SFW or the use of NSFW is allowed, estimate depth
            de_result = EstimateDepth(prompt)

            try:
                # Try to append the image to the list. If the list is not set, will return an error
                data["files"]["images"].append(de_result)
            except:
                # Set the list and append the image if there is an error
                data["files"]["images"] = [de_result]
            
            data["response"] = "[de " + prompt + "]"
            data["tested_models"].append("de")
        
        # Detect objects
        if (args.count("od") >= 1 and order_prompt.__contains__("od")):
            # Check if the user's image is NSFW
            if (not cfg.current_data["allow_processing_if_nsfw"]):
                is_nsfw = FilterNSFWImage(prompt)

                if (is_nsfw == None):
                    is_nsfw = False

                # If the user's image is NSFW and the use of NSFW is not allowed, return an error
                if (is_nsfw):
                    return {
                        "response": "ERROR",
                        "model": "-1",
                        "files": {},
                        "tested_models": [],
                        "text_classification": "-1",
                        "title": "NO TITLE",
                        "errors": ["NSFW detected! NSFW is not allowed.", "NSFW"]
                    }
            
            # If the image is SFW or the use of NSFW is allowed, detect objects
            od = DetectObjects(prompt)
            od_img_result = od["image"]
            
            try:
                # Append the image to the list of images. If the list is not set this will return an error
                data["files"]["images"].append(od_img_result)
            except:
                # If there is an error, create the list and append the image
                data["files"]["images"] = [od_img_result]

            data["response"] = str(od["objects"])
            data["tested_models"].append("od")
        
        # Generate RVC response if the user requests it
        if (args.count("rvc") >= 1 and order_prompt.__contains__("rvc")):
            aud = DoRVC(prompt)

            try:
                # Try to append all the audios. If the list is not set, will return an error
                data["files"]["audios"].append(aud)
            except:
                # Create the list if there is an error
                data["files"]["audios"] = [aud]
            
            data["response"] = "[rvc " + str(prompt) + "]"
            data["tested_models"].append("rvc")

        # Generate UVR response if the user requests it
        if (args.count("uvr") >= 1 and order_prompt.__contains__("uvr")):
            aud = DoUVR(prompt)

            if (type(aud) == list):
                data["files"]["audios"] = aud
            else:
                try:
                    # Try to append all the audios. If the list is not set, will return an error
                    data["files"]["audios"].append(aud)
                except:
                    # Create the list if there is an error
                    data["files"]["audios"] = [aud]
            
            data["response"] = "[uvr " + str(prompt) + "]"
            data["tested_models"].append("uvr")
        
        # Generate Image2Image response if the user requests it
        if (args.count("img2img") >= 1 and order_prompt.__contains__("img2img")):
            # Check if the user's image is NSFW
            if (not cfg.current_data["allow_processing_if_nsfw"]):
                is_nsfw = FilterNSFWImage(prompt)

                if (is_nsfw == None):
                    is_nsfw = False

                # If the user's image is NSFW and the use of NSFW is not allowed, return an error
                if (is_nsfw):
                    return {
                        "response": "ERROR",
                        "model": "-1",
                        "files": {},
                        "tested_models": [],
                        "text_classification": "-1",
                        "title": "NO TITLE",
                        "errors": ["NSFW detected! NSFW is not allowed.", "NSFW"]
                    }
            
            imgs = DoImg2Img(prompt)

            try:
                # Try to append all the images. If the list is not set, will return an error
                data["files"]["images"] += imgs
            except:
                # Create the list if there is an error
                data["files"]["images"] = imgs
            
            data["response"] = "[i2i " + str(prompt) + "]"
            data["tested_models"].append("img2img")
        
        # Generate TTS response if the user requests it
        if (args.count("tts") >= 1 and order_prompt.__contains__("tts")):
            aud = DoTTS(prompt)

            try:
                # Try to append all the audios. If the list is not set, will return an error
                data["files"]["audios"].append(aud)
            except:
                # Create the list if there is an error
                data["files"]["audios"] = [aud]
            
            data["response"] = "[tts " + str(prompt) + "]"
            data["tested_models"].append("tts")
        
        # Translate the prompt if the user requests it
        if (args.count("tr") >= 1 and order_prompt.__contains__("tr")):
            res = json.loads(prompt)
            res = Translate(res["tr"], res["prompt"])

            print(str(res))

            data["response"] = res
            data["tested_models"].append("tr")
        
        # Classify the prompt if the user requests it
        if (args.count("sc") >= 1 and order_prompt.__contains__("sc")):
            res = ClassifyText(prompt)

            data["response"] = res
            data["tested_models"].append("sc")
        
        # Set the files to string and return the data
        return data
    
    # Set some variables
    tested_models: list[str] = []
    errors: list[str] = []
    responses = []
    response: str = "ERROR"
    tcn: str = "-1"
    files: dict[str] = {}
    model: str = ""
    title: str = ""

    # For every model
    for i in order_prompt.split(" "):
        # Try to get a response from the model
        try:
            if (i == "g4a"):
                # Get response from GPT4All (if allowed)
                response = cbg4a.MakePrompt(prompt, use_chat_history_if_available, conversation)
            elif (i == "hf"):
                # Get response from HuggingFace's Text Generation model (if allowed)
                response = cba.MakePrompt(prompt, use_chat_history_if_available, conversation)
            else:
                # If the model is not here, try next model
                continue
            
            # Set the model and append the tested model to the tested models list
            model = i
            tested_models.append(i)
        except Exception as ex:
            # It there is an error, append to error to the errors list and add it to log
            errors.append("Error on model '" + i + "': '" + str(ex) + "'")
            logs.AddToLog("Model '" + i + "' found an error processing '" + prompt + "': '" + str(ex) + "'")

            # Try to use next model
            continue

        # Remove the white spaces from the beginning and the end of the response
        response = response.strip()

        # If the response contains with this, trim the response
        if (response.__contains__("### USER")):
            logs.AddToLog("The response contains '### USER', trimming the response.")
            response = response[:response.index("### USER")]
        
        # If the response contains with this, trim the response
        if (response.__contains__("### ASSISTANT")):
            logs.AddToLog("The response contains '### ASSISTANT', trimming the response.")
            response = response[:response.index("### ASSISTANT")]
        
        # If the response length is greater than 0 and isn't an error...
        if (len(response.strip()) > 0 and response.lower() != "error" and response.lower() != "error."):
            # ...Add it to the logs
            logs.AddToLog("Model '" + i + "' response to '" + prompt + "': '" + response + "'")

            # If the titles are allowed and there is a title
            if (cfg.current_data["allow_titles"] and response.startswith("[") and response.__contains__("]")):
                # Isolate the title from the response
                title = response[1:response.index("]")]
                response = response[response.index("]") + 1:].strip()

                # If the response, without the title, is empty, add the title again
                if (len(response.strip()) == 0):
                    response = "[" + title + "]"
            else:
                # Set the title to "NO TITLE" if the use of titles are not allowed or if there isn't a title
                title = "NO TITLE"
            
            # Append the response to the responses list if the use of multiple models is allowed, then use the next model
            if (cfg.current_data["use_multi_model"]):
                responses.append(response)
                continue
    
    # If the use of multiple models is allowed...
    if (cfg.current_data["use_multi_model"]):
        # ...Set an empty response
        response = ""

        # Get only 1 response from all the responses list
        if (cfg.current_data["multi_model_mode"] == "shortest"):
            # Get only the shortest response
            for r in responses:
                if (len(response.strip()) == 0):
                    response = r
                    continue

                if (len(r) < len(response)):
                    response = r
        elif (cfg.current_data["multi_model_mode"] == "longest"):
            # Get only the longest response
            for r in responses:
                if (len(response.strip()) == 0):
                    response = r
                    continue

                if (len(r) > len(response)):
                    response = r
    
    # If save conversation is allowed...
    if (cfg.current_data["save_conversations"]):
        # If the use of titles is allowed and there is a title
        if (cfg.current_data["allow_titles"] and response.startswith("[") and response.__contains__("]")):
            # Get only the response
            response_conv = response[response.index("]") + 1:].strip()
        else:
            # If there isn't a title, then doesn't modify the response
            response_conv = response

        # If the response if the conversation is empty, then set it to the response
        if (len(response_conv.strip()) == 0):
            response_conv = response
        
        # Remove starting and ending white spaces from the response
        response_conv = response_conv.strip()
        response_thinking = ""
        
        # Set thinking
        if (response_conv.count("[T: ") > 0 and response_conv.count("]") > 0):
            response_thinking = response_conv[response_conv.index("[T: ") + 4:response_conv.index("]")]
            response_conv = response_conv.replace("[T: " + response_thinking + "]", "").strip()
            
            if (response_thinking.strip() == "THINKING"):
                response_thinking = ""
            else:
                response_thinking = response_thinking.strip()
            
            if (response_thinking.startswith("\'") or response_thinking.startswith("\"")):
                response_thinking = response_thinking[1:].strip()
            
            if (response_thinking.endswith("\'") or response_thinking.endswith("\"")):
                response_thinking = response_thinking[:-1].strip()
            
            if (len(response_conv) == 0):
                response_conv = response_thinking
            
            response = response_conv
        
        # ...Remove the white spaces from the beginning and the end of the response, then add the response to the conversation
        conv.AddToConversation(conversation[0], conversation[1], prompt, response_conv, response_thinking)

    # If the use of Sequence Classification (Text Classification) is allowed, then classify the response
    if (cfg.current_data["use_other_services_on_chatbot"]):
        try:
            # Try to classify the response
            tcn = ClassifyText(response)
        except Exception as ex:
            # If there is an error, set the classification to -1
            tcn = "-1"
            
            # Append the error message to the errors list and logs
            errors.append("There was an error classifying the response: " + str(ex))
            logs.AddToLog("(ERROR) Response classification: " + str(ex))
    
    # If the model returned the Internet Search command...
    if (response.__contains__("[int ")):
        try:
            # ...Try to separate the response from the prompt to search, then search the image
            int_prompt = response[response.index("[int ") + 5:]
            int_prompt = int_prompt[:int_prompt.index("]")]

            # Remove the double quotes from the prompt, it it starts with it
            if (int_prompt.startswith("\"") or int_prompt.startswith("\'")):
                int_prompt_filtered = int_prompt[1:]
            else:
                int_prompt_filtered = int_prompt
            
            # Remove the double quotes from the prompt, it it ends with it
            if (int_prompt.endswith("\"") or int_prompt.endswith("\'")):
                int_prompt_filtered = int_prompt_filtered[:-1]
            else:
                int_prompt_filtered = int_prompt_filtered
            
            int_search_prompt = int_prompt_filtered[:int_prompt_filtered.index(" (REQUEST) ")]
            int_question_prompt = int_prompt_filtered[int_prompt_filtered.index(" (REQUEST) ") + 11:]
            
            if (int_search_prompt.startswith("http://") or int_search_prompt.startswith("https://")):
                # Read a website if the prompt starts with an URL
                internet_results = internet.ReadTextFromWebsite(int_search_prompt)
            else:
                # Search on internet and read ALL the results if the prompt does not start from a URL
                internet_results = internet.Search(int_search_prompt)
                internet_results = "".join(internet.ReadTextFromWebsite(result) + "\n" for result in internet_results).strip()

            # Cut the results
            if (len(internet_results) > 500):
                internet_results = internet_results[:500]

            internet_response = ""

            # Select the internet model to use
            if (internet_type == "qa" and cfg.current_data["prompt_order"].count("qa") > 0):
                # Use only a Question Answering model (if allowed)
                internet_response = qa.ProcessPrompt(internet_results, int_question_prompt)
                tested_models.append("qa")
            elif (internet_type == "chatbot"):
                # Use only a Chatbot model (if allowed)

                if (cfg.current_data["prompt_order"].count("g4a") > 0):
                    # Use GPT4All (the recommended option) if it's available
                    sprompt = cbg4a.system_messages
                    cbg4a.system_messages = internet_results.split("\n")

                    internet_response = cbg4a.MakePrompt(int_question_prompt, False, ["", ""])
                    cbg4a.system_messages = sprompt

                    if (tested_models.count("g4a") == 0):
                        tested_models.append("g4a")
                elif (cfg.current_data["prompt_order"].count("hf") > 0):
                    # Use a HuggingFace's Text Generation model if it's available
                    sprompt = cba.system_messages
                    cba.system_messages = internet_results.split("\n")

                    internet_response = cba.MakePrompt(int_question_prompt, False, ["", ""])
                    cba.system_messages = sprompt

                    if (tested_models.count("hf") == 0):
                        tested_models.append("hf")
            elif (internet_type == "qa-chatbot" and cfg.current_data["prompt_order"].count("qa") > 0):
                # Use a Question Answering model, then use a Chatbot model (if allowed)
                # Get the response from the Question Answering model
                internet_results = qa.ProcessPrompt(internet_results, int_question_prompt)
                tested_models.append("qa")

                # Get the response from the chatbot
                if (cfg.current_data["prompt_order"].count("g4a") > 0):
                    # Use GPT4All (the recommended option) if it's available
                    sprompt = cbg4a.system_messages
                    cbg4a.system_messages = internet_results.split("\n")

                    internet_response = cbg4a.MakePrompt(int_question_prompt, False, ["", ""])
                    cbg4a.system_messages = sprompt

                    if (tested_models.count("g4a") == 0):
                        tested_models.append("g4a")
                elif (cfg.current_data["prompt_order"].count("hf") > 0):
                    # Use a HuggingFace's Text Generation model if it's available
                    sprompt = cba.system_messages
                    cba.system_messages = internet_results.split("\n")

                    internet_response = cba.MakePrompt(int_question_prompt, False, ["", ""])
                    cba.system_messages = sprompt

                    if (tested_models.count("hf") == 0):
                        tested_models.append("hf")
            elif (internet_type == "chatbot-qa" and cfg.current_data["prompt_order"].count("qa") > 0):
                # Use a Chatbot model, then use a Question Answering model (if allowed)
                # Get the response from the chatbot
                if (cfg.current_data["prompt_order"].count("g4a") > 0):
                    # Use GPT4All (the recommended option) if it's available
                    sprompt = cbg4a.system_messages
                    cbg4a.system_messages = internet_results.split("\n")

                    internet_results = cbg4a.MakePrompt(int_question_prompt, False, ["", ""])
                    cbg4a.system_messages = sprompt

                    if (tested_models.count("g4a") == 0):
                        tested_models.append("g4a")
                elif (cfg.current_data["prompt_order"].count("hf") > 0):
                    # Use a HuggingFace's Text Generation model if it's available
                    sprompt = cba.system_messages
                    cba.system_messages = internet_results.split("\n")

                    internet_results = cba.MakePrompt(int_question_prompt, False, ["", ""])
                    cba.system_messages = sprompt

                    if (tested_models.count("hf") == 0):
                        tested_models.append("hf")
                
                # Get the response from the Question Answering model
                internet_response = qa.ProcessPrompt(internet_results, int_question_prompt)
                tested_models.append("qa")
            else:
                # If the internet_type specified by the user is not recognized or if the model is not available, append it to the errors list
                errors.append("Unrecognized internet_type or model not available.")
            
            # Replace the command with the internet response
            response = response.replace("[int " + int_prompt + "]", internet_response)
        except Exception as ex:
            # If there is an error, append it to the errors list and logs
            errors.append("Could not search on internet: " + str(ex))
            logs.AddToLog("(ERROR) Internet Search from response failed: " + str(ex))
            
    # If the model returned the Image Generation command and the use of Image Generation is allowed...
    if (order_prompt.__contains__("text2img") and response.__contains__("[agi ")):
        try:
            # ...Try to separate the response from the image to generate, then generate the image
            img_prompt = response[response.index("[agi ") + 5:]
            img_prompt = img_prompt[:img_prompt.index("]")]

            # Remove the double quotes from the image prompt, if it starts with it
            if (img_prompt.startswith("\"") or img_prompt.startswith("\'")):
                img_prompt_filtered = img_prompt[1:]
            else:
                img_prompt_filtered = img_prompt
            
            # Remove the double quotes from the image prompt, if it ends with it
            if (img_prompt.endswith("\"")) or img_prompt.endswith("\'"):
                img_prompt_filtered = img_prompt_filtered[:-1]
            else:
                img_prompt_filtered = img_prompt_filtered

            # Cut the response
            response = response.replace("[agi " + img_prompt + "]", "")

            # Separate the prompt and the negative prompt
            if (img_prompt_filtered.count("(NEGATIVE)") > 0):
                g_np = img_prompt_filtered[img_prompt_filtered.index("(NEGATIVE)") + 10:].strip()
                g_p = img_prompt_filtered[:img_prompt_filtered.index("(NEGATIVE)")].strip()
            else:
                g_np = ""
                g_p = img_prompt_filtered

            # Set the img_prompt to a dict, then run the image generation command
            img_prompt = json.dumps({"prompt": g_p, "negative_prompt": g_np})
            imgs = MakePrompt(img_prompt, "".join(i for i in order_prompt), "-ncb-img", extra_system_msgs, translator, force_translator, conversation, use_default_sys_prompts)["files"]["images"]

            try:
                # Try to add the generated images to the list
                files["images"] += imgs
            except:
                # If the try fails, create the list and add the images to the list
                files["images"] = imgs

            # Append the Image Generation model to the tested models list
            tested_models.append("text2img")
        except Exception as ex:
            # If there is an error, append it to the errors list and logs
            errors.append("Could not generate image: " + str(ex))
            logs.AddToLog("(ERROR) Image Generation from response failed: " + str(ex))
            
    # If the model returned the Audio Generation command and the use of Audio Generation is allowed...
    if (order_prompt.__contains__("text2audio") and response.__contains__("[aga ")):
        try:
            # ...Try to separate the response from the audio to generate, then generate the audio
            aud_prompt = response[response.index("[aga ") + 5:]
            aud_prompt = aud_prompt[:aud_prompt.index("]")]

            # Remove the double quotes from the image prompt, if it starts with it
            if (aud_prompt.startswith("\"")):
                aud_prompt_filtered = aud_prompt[1:]
            else:
                aud_prompt_filtered = aud_prompt
            
            # Remove the double quotes from the image prompt, if it ends with it
            if (aud_prompt.endswith("\"")):
                aud_prompt_filtered = aud_prompt_filtered[:-1]
            else:
                aud_prompt_filtered = aud_prompt_filtered

            response = response.replace("[aga " + aud_prompt + "]", "")
            auds = MakePrompt(img_prompt_filtered, order_prompt, "-ncb-aud", extra_system_msgs, translator, force_translator, conversation, use_default_sys_prompts)["files"]["audios"]

            try:
                files["audios"] += auds
            except:
                files["audios"] = auds

            # Append the Audio Generation model to the tested models list
            tested_models.append("text2audio")
        except Exception as ex:
            # If there is an error, append it to the errors list and logs
            errors.append("Could not generate audio: " + str(ex))
            logs.AddToLog("(ERROR) Audio Generation from response failed: " + str(ex))
            
    # If the use of translators is allowed and the translator language is not empty...
    if (len(translator.strip()) > 0 and cfg.current_data["use_other_services_on_chatbot"]):
        # ...Translate the response to the translator language
        response = Translate(translator, response)
            
    # If the use of Dynamic System Prompts is allowed...
    if (cfg.current_data["use_dynamic_system_args"]):
        # Remove from the System Prompts list
        for m in dsm:
            if (sm.count(m) > 0):
                sm.remove(m)

    # Return the response
    return {
        "response": response,
        "model": model,
        "files": files,
        "tested_models": tested_models,
        "text_classification": tcn,
        "title": title,
        "errors": errors
    }

def GenerateImages(prompt: str) -> list[str]:
    # Get generated images
    imgs_response = agi.GenerateImages(prompt)
    images = []

    # Generate images
    for img in imgs_response:
        images.append(base64.b64encode(img).decode("utf-8"))
    
    # Return the generated images
    return images

def EstimateDepth(img: str) -> str:
    # Estimate depth
    img_response = de.EstimateDepth(img)
    # Encode the image in base64
    image = base64.b64encode(img_response).decode("utf-8")

    # Return the image
    return image

def GenerateAudio(prompt: str) -> str:
    # Get generated audio
    aud_response = aga.GenerateAudio(prompt)

    # Return generated audio
    return base64.b64encode(aud_response).decode("utf-8")

def ImageToText(img: str) -> str:
    # Get and return the text from an image
    return itt.MakePrompt(img)

def RecognizeAudio(audio: str) -> dict[str, str]:
    # Recognize and return an audio
    return sr.Recognize(sr.FileToAudioData(audio))

def DetectObjects(img: str) -> dict[str]:
    # Get objects data
    data = od.MakePrompt(img)
    # Encode the image into base64
    image = base64.b64encode(data["image"]).decode("utf-8")

    # Return the data
    return {
        "objects": data["objects"],
        "image": image
    }

def DoRVC(audio_data: str) -> str:
    # Convert audio data to json
    audio_data = cfg.JSONDeserializer(audio_data)

    # Get RVC audio response
    data = rvc.MakeRVC(audio_data)
    # Encode the audio into base64
    audio = base64.b64encode(data).decode("utf-8")

    # Return the data
    return audio

def Translate(translator: str, prompt: str) -> str:
    if (cfg.current_data["prompt_order"].count("tr") > 0):
        # Get the prompt language
        lang = tns.GetLanguage(prompt)

        if (translator.lower().strip() == "auto"):
            # Translate using the auto translator to the server's language
            return tns.TranslateToServerLanguage(prompt, lang)
        
        # Try to translate using the specified language
        return tns.TranslateFromServerLanguage(prompt, translator)
    
    return prompt

def ClassifyText(prompt: str) -> str:
    # Classify text
    if (cfg.current_data["prompt_order"].count("sc") > 0):
        return tc.DoPrompt(prompt)
    
    return "-1"

def FilterNSFWText(prompt: str) -> bool:
    # Filter NSFW text
    return IsTextNSFW(prompt)

def FilterNSFWImage(image: str) -> bool:
    # Filter NSFW image
    return IsImageNSFW(image)

def DoTTS(prompt: str):
    # Convert audio data to json
    prompt = cfg.JSONDeserializer(prompt)

    # Get TTS audio response
    data = tts.MakeTTS(prompt)
    # Encode the audio into base64
    audio = base64.b64encode(data).decode("utf-8")

    # Return the data
    return audio

def DoUVR(audio_data: str) -> list[str]:
    # Convert audio data to json
    audio_data = cfg.JSONDeserializer(audio_data)

    # Get UVR audio response
    data = uvr.MakeUVR(audio_data)
    
    for aud in data:
        # Encode the audio into base64
        data[data.index(aud)] = base64.b64encode(aud).decode("utf-8")

    # Return the data
    return data

def DoImg2Img(prompt: str) -> list[str]:
    # Convert image data to json
    img_data = cfg.JSONDeserializer(prompt)

    # Get images
    imgs_response = img2img.Prompt(img_data)
    images = []

    # Generate images
    for img in imgs_response:
        images.append(base64.b64encode(img).decode("utf-8"))
    
    # Return the generated images
    return images