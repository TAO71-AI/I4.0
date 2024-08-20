# Import the models
from typing import Iterator
import Inference.Text.chatbot as cb
import Inference.Text.text_classification as tc
import Inference.Text.translation as tns
import Inference.Images.ai_generate_image as agi
import Inference.Images.ai_img_to_text as itt
import Inference.Audio.ai_generate_audio as aga
import Inference.Mixed.ai_filters as filters
import Inference.Images.ai_depth_estimation as de
import Inference.Images.ai_object_detection as od
import Inference.Audio.speech_recog as sr
import Inference.Audio.rvc_inf as rvc
import Inference.Audio.tts as tts
import Inference.Audio.ai_vocal_separator as uvr
import Inference.Images.image_to_image as img2img
import Inference.Text.ai_question_answering as qa
import internet_connection as internet
import ai_config as cfg
import ai_conversation as conv
import chatbot_basics as cbbasics
import PIL.Image as Image
import os
import base64
import datetime
import calendar
import json

# Please read this
"""
Models:
chatbot - GPT4All or HuggingFace chatbot (Text Generation).
sc - Text classification (Sequence Classification).
tr - Translation.
text2img - Image generation.
img2text - Image to Text.
speech2text - Recognize audio using Whisper.
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

# Get the models' name
def GetAllModels() -> dict[str]:
    models = cfg.current_data["models"].split(" ")
    mls = {}

    for i in models:
        if (i == "chatbot"):
            mls[i] = cb.__get_model_path__(True)
        elif (i == "sc"):
            mls[i] = cfg.current_data["text_classification_model"]
        elif (i == "tr"):
            mls[i] = str([cfg.current_data["translation_classification_model"]] + list(cfg.current_data["translation_models"].values()))
        elif (i == "text2img"):
            mls[i] = cfg.current_data["image_generation"]["model"]
        elif (i == "img2text"):
            mls[i] = cfg.current_data["img_to_text_model"]
        elif (i == "text2audio"):
            mls[i] = cfg.current_data["text_to_audio_model"]
        elif (i == "speech2text"):
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

        mls[i] = str(mls[i])
        mls[i] = mls[i].replace("\\", "/")
        
        if (mls[i].count("/") > 0 and os.path.exists(mls[i])):
            mls[i] = mls[i].split("/")[-1]
    
    return mls

# Load all the models
def LoadAllModels() -> None:
    models = cfg.current_data["models"].split(" ")

    for i in models:
        if (i == "chatbot"):
            cb.LoadModel()
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
        elif (i == "speech2text"):
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
    if (cfg.current_data["models"].count("nsfw_filter-text") > 0):
        return filters.IsTextNSFW(prompt)
    
    # If not, return none
    return None

# Check if an image prompt is NSFW
def IsImageNSFW(image: str | Image.Image) -> bool:
    # If the model is loaded, check NSFW
    if (cfg.current_data["models"].count("nsfw_filter-image") > 0):
        return filters.IsImageNSFW(image)
    
    # If not, return none
    return None

def SearchOverInternet(SearchPrompt: str, QuestionLength: int) -> str:
    # Set the limit
    limit = cfg.current_data["chatbot"]["ctx"] - QuestionLength - 1
    underLength = 12
    maxResults = 5

    # It's a search prompt
    # Get first results
    internetResults = internet.Search(SearchPrompt, maxResults)

    # Read all websites
    internetResponse = ""

    for result in internetResults:
        try:
            internetResponse += internet.ReadTextFromWebsite(result, int(limit / maxResults), underLength) + "\n"
        except:
            print("Error reading a website.")
        
    # Apply limit
    internetResponse = internet.__apply_limit_to_text__(internetResponse, limit, underLength)
    
    # Return the data
    return internetResponse

def GetResponseFromInternet(SearchPrompt: str, Question: str, System: str, SearchOnInternet: bool = True) -> Iterator[str]:
    # Delete empty conversation
    conv.ClearConversation("", "")

    # Search over internet
    internetResponse = SearchOverInternet(SearchPrompt, len(Question)) if (SearchOnInternet) else SearchPrompt
    response = ""
    system2 = ""

    # Check system
    if (System == "qa" or System.startswith("qa-")):
        # The system to use is the Question Answering only
        modelResponse = MakePrompt(json.dumps({
            "context": internetResponse,
            "question": Question
        }), [], "qa", "", [], ["", ""], False)
        system2 = System[2:]
    elif (System == "chatbot" or System.startswith("chatbot-")):
        # The system to use is the Chatbot only
        modelResponse = MakePrompt("\nInternet: " + internetResponse + "\nQuestion: " + Question, [], "chatbot", "", [], ["", ""], False)
        system2 = System[7:]
    else:
        raise Exception("Invalid system.")
    
    if (system2.startswith("-")):
        # Process again using the other system
        system2 = system2[1:]
        response = "".join([token["response"] for token in modelResponse])
        
        # Return the response
        yield GetResponseFromInternet(response, Question, system2)
        return
    
    # Yield every token
    for token in modelResponse:
        yield token["response"]

def MakePrompt(Prompt: str, Files: list[dict[str, str]], Service: str, AIArgs: str | None = None, ExtraSystemPrompts: list[str] | str = [], Conversation: list[str] = ["", ""], UseDefaultSystemPrompts: bool | None = None) -> Iterator[dict[str]]:
    # Define I4.0's personality
    if (AIArgs == None):
        AIArgs = cfg.current_data["ai_args"].split("+")
    else:
        AIArgs = AIArgs.split("+")

    # Set system prompts
    sp = []

    if (UseDefaultSystemPrompts == None):
        UseDefaultSystemPrompts = cfg.current_data["use_default_system_messages"]
    
    if (UseDefaultSystemPrompts):
        # Get default system prompts (for I4.0's personality and server's tools)
        sp += cbbasics.GetDefaultI4SystemMessages(AIArgs)
    
    if (type(ExtraSystemPrompts) == list or type(ExtraSystemPrompts) == list[str]):
        sp += ExtraSystemPrompts
    elif (type(ExtraSystemPrompts) == str):
        sp.append(ExtraSystemPrompts)
    else:
        raise ValueError("Invalid type of ExtraSystemPrompts.")
    
    if (cfg.current_data["use_dynamic_system_args"]):
        # Get dynamic system prompts (for current date, etc.)
        # Get the current date
        cDate = datetime.datetime.now()

        # Add sprompts
        sp += [
            "The current date is " + str(cDate.day) + " of " + calendar.month_name[cDate.month] + " " + str(cDate.year),
            "The current time is " + ("0" + str(cDate.hour) if (cDate.hour < 10) else str(cDate.hour)) + ":" + ("0" + str(cDate.minute) if (cDate.minute < 10) else str(cDate.minute)) + "."
        ]

        if (cDate.day == 16 and cDate.month == 9 and UseDefaultSystemPrompts):
            # I4.0's birthday!!!!
            sp.append("Today it's your birthday.")
    
    # Apply the system prompts to the services
    cb.SystemPrompts = sp
    
    # Check NSFW in prompt
    if ((Service == "chatbot" or Service == "sc" or Service == "tr" or Service == "text2img" or Service == "text2audio" or Service == "tts" or Service == "qa") and not cfg.current_data["allow_processing_if_nsfw"][0] and Service != "nsfw_filter-text"):
        # Check if the prompt is NSFW
        isNSFW = FilterNSFWText(Prompt)

        # Return error if it's NSFW
        if (isNSFW):
            raise Exception("NSFW detected!")
    
    # Check NSFW in files
    for file in Files:
        if (file["type"] == "image" and not cfg.current_data["allow_processing_if_nsfw"][1] and Service != "nsfw_filter-image"):
            # The file is an image
            isNSFW = FilterNSFWImage("ReceivedFiles/" + file["name"] + "_file")

            # Return error if it's NSFW
            if (isNSFW):
                raise Exception("NSFW detected!")
        elif (file["type"] == "audio"):
            # Ignore, the NSFW filter for audio is not created yet
            pass
    
    # Check service
    if (Service == "chatbot" and cfg.current_data["models"].count("chatbot") > 0):
        # Get chatbot response
        textResponse = cb.ProcessPrompt(Prompt, Conversation)

        # Set the final response
        finalResponse = ""

        # For every token
        for token in textResponse:
            # Add to the final response
            finalResponse += token

            # Return the token
            yield {"response": token, "files": []}

        # Strip response and thinking
        finalResponse = finalResponse.strip()

        # Add the final response to the conversation
        conv.AddToConversation(Conversation[0], Conversation[1], Prompt, finalResponse)
        
        # Return an empty response
        yield {"response": "", "files": []}
    elif (Service == "text2img" and cfg.current_data["models"].count("text2img") > 0):
        # Process image
        imageFiles = GenerateImages(Prompt)
        fs = []

        # For every image
        for fi in imageFiles:
            fs.append({"type": "image", "data": fi})

        # Return the images
        yield {"response": "", "files": fs}
    elif (Service == "sc" and cfg.current_data["models"].count("sc") > 0):
        # Get the classification
        classification = ClassifyText(Prompt)

        # Return the response
        yield {"response": classification, "files": []}
    elif (Service == "tr" and cfg.current_data["models"].count("tr") > 0):
        # Translate the prompt
        Prompt = cfg.JSONDeserializer(Prompt)
        translation = Translate(Prompt["translator"], Prompt["text"])

        # Return the response
        yield {"response": translation, "files": []}
    elif (Service == "img2text" and cfg.current_data["models"].count("img2text") > 0):
        # Get the response from the model for each file
        for file in Files:
            # Check if the file is an image
            if (file["type"] != "image"):
                # If it's not, ignore
                continue

            # Get the response
            response = ImageToText("ReceivedFiles/" + file["name"] + "_file")

            # Return the response
            yield {"response": response, "files": []}
        
        # Return the final response
        yield {"response": "", "files": []}
    elif (Service == "speech2text" and cfg.current_data["models"].count("speech2text") > 0):
        # Get the response from the model for each file
        for file in Files:
            # Check if the file is an audio file
            if (file["type"] != "audio"):
                # If it's not, ignore
                continue

            # Get the response
            response = RecognizeAudio("ReceivedFiles/" + file["name"] + "_file")

            # Return the response
            yield {"response": response, "files": []}
        
        # Return the final response
        yield {"response": "", "files": []}
    elif (Service == "text2audio" and cfg.current_data["models"].count("text2audio") > 0):
        # Process audio
        audioFiles = GenerateAudio(Prompt)

        # Return the audios
        yield {"response": "", "files": [{"type": "audio", "data": audioFiles}]}
    elif (Service == "nsfw_filter-text" and cfg.current_data["models"].count("nsfw_filter-text") > 0):
        # Check if it's NSFW
        nsfw = FilterNSFWText(Prompt)

        # Return the response
        yield {"response": nsfw, "files": []}
    elif (Service == "nsfw_filter-image" and cfg.current_data["models"].count("nsfw_filter-image") > 0):
        # Check if it's NSFW for each file
        for file in Files:
            # Check if the file is an image file
            if (file["type"] != "image"):
                # If it's not, ignore
                continue

            # Get the response
            response = FilterNSFWImage("ReceivedFiles/" + file["name"] + "_file")

            # Return the response
            yield {"response": response, "files": []}

        # Return the response
        yield {"response": "", "files": []}
    elif (Service == "de" and cfg.current_data["models"].count("de") > 0):
        # Calculate depth estimation for each file
        for file in Files:
            # Check if the file is an image file
            if (file["type"] != "image"):
                # If it's not, ignore
                continue

            # Get the response
            response = EstimateDepth("ReceivedFiles/" + file["name"] + "_file")

            # Return the response
            yield {"response": "", "files": [{"type": "image", "data": response}]}

        # Return the response
        yield {"response": "", "files": []}
    elif (Service == "od" and cfg.current_data["models"].count("od") > 0):
        # Calculate object detection for each file
        for file in Files:
            # Check if the file is an image file
            if (file["type"] != "image"):
                # If it's not, ignore
                continue

            # Get the response
            response = DetectObjects("ReceivedFiles/" + file["name"] + "_file")

            # Return the response
            yield {"response": response["objects"], "files": [{"type": "image", "data": response["image"]}]}

        # Return the response
        yield {"response": "", "files": []}
    elif (Service == "rvc" and cfg.current_data["models"].count("rvc") > 0):
        # Get RVC of each file
        for file in Files:
            # Check if the file is an audio file
            if (file["type"] != "audio"):
                # If it's not, ignore
                continue

            # Get the response
            promptFile = cfg.JSONDeserializer(Prompt)
            promptFile["input"] = "ReceivedFiles/" + file["name"] + "_file"

            response = DoRVC(promptFile)

            # Return the response
            yield {"response": "", "files": [{"type": "audio", "data": response}]}
        
        # Return the response
        yield {"response": "", "files": []}
    elif (Service == "uvr" and cfg.current_data["models"].count("uvr") > 0):
        # Get UVR of each file
        for file in Files:
            # Check if the file is an audio file
            if (file["type"] != "audio"):
                # If it's not, ignore
                continue

            # Get the response
            promptFile = cfg.JSONDeserializer(Prompt)
            promptFile["input"] = "ReceivedFiles/" + file["name"] + "_file"

            response = DoUVR(promptFile)
            fs = []

            # For every file
            for fi in response:
                # Append it
                fs.append({"type": "audio", "data": fi})

            # Return the response
            yield {"response": "", "files": fs}
        
        # Return the response
        yield {"response": "", "files": []}
    elif (Service == "tts" and cfg.current_data["models"].count("tts") > 0):
        # Generate TTS
        response = DoTTS(Prompt)

        # Return the response
        yield {"response": "", "files": [{"type": "audio", "data": response}]}
    elif (Service == "img2img" and cfg.current_data["models"].count("img2img") > 0):
        # Get image to image for every file
        for file in Files:
            # Check if the file is an image file
            if (file["type"] != "image"):
                # If it's not, ignore
                continue

            # Get the response
            response = DoImg2Img(json.dumps({"prompt": Prompt, "image": "ReceivedFiles/" + file["name"] + "_file"}))
            fs = []

            # For every file
            for fi in response:
                # Append it
                fs.append({"type": "image", "data": fi})

            # Return the response
            yield {"response": "", "files": fs}

        # Return the response
        yield {"response": "", "files": []}
    elif (Service == "qa" and cfg.current_data["models"].count("qa") > 0):
        # Process the prompt
        Prompt = cfg.JSONDeserializer(Prompt)
        response = qa.ProcessPrompt(Prompt["context"], Prompt["question"])

        # Return the response
        yield {"response": response, "files": []}
    else:
        raise Exception("Service not recognized.")

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

def DoRVC(audio_data: str | dict[str, any]) -> str:
    if (type(audio_data) == str):
        # Convert audio data to json
        audio_data = cfg.JSONDeserializer(audio_data)

    # Get RVC audio response
    data = rvc.MakeRVC(audio_data)
    # Encode the audio into base64
    audio = base64.b64encode(data).decode("utf-8")

    # Return the data
    return audio

def Translate(translator: str, prompt: str) -> str:
    if (cfg.current_data["models"].count("tr") > 0):
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
    if (cfg.current_data["models"].count("sc") > 0):
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