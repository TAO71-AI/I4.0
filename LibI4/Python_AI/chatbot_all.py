# Import the models
from collections.abc import Iterator
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
ld - Language Detection.
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

def GetServicesAndIndexes() -> dict[str, int]:
    # Create the dict
    services = {}

    # For each model
    for model in cfg.current_data["models"]:
        # Get the service
        service = model["service"]

        try:
            # Try to add 1 to the count of the service
            services[service] += 1
        except:
            # First count of the service, create to the dictionary
            services[service] = 1
    
    # Return the services
    return services

def LoadAllModels() -> None:
    # Load all the models
    cb.LoadModels()
    tc.LoadModels()
    tns.LoadModels()
    tns.LoadClassifiers()
    agi.LoadModels()
    itt.LoadModels()
    sr.LoadModels()
    aga.LoadModels()
    filters.LoadModels()
    de.LoadModels()
    od.LoadModels()
    rvc.LoadModels()
    #uvr.LoadModels()                # TODO
    tts.LoadTTS()
    img2img.LoadModels()
    qa.LoadModels()

def SearchOverInternet(Index: int, SearchPrompt: str, QuestionLength: int) -> str:
    # Set the limit
    limit = cfg.GetInfoOfTask("chatbot", Index)["ctx"] - QuestionLength - 1
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

def GetResponseFromInternet(Index: int, SearchPrompt: str, Question: str, System: str, SearchOnInternet: bool = True) -> Iterator[str]:
    # Delete empty conversation
    conv.ClearConversation("", "")

    # Search over internet
    internetResponse = SearchOverInternet(Index, SearchPrompt, len(Question)) if (SearchOnInternet) else SearchPrompt
    response = ""
    system2 = ""

    # Check system
    if (System == "qa" or System.startswith("qa-")):
        # The system to use is the Question Answering only
        modelResponse = MakePrompt(Index, json.dumps({
            "context": internetResponse,
            "question": Question
        }), [], "qa", "", [], ["", ""], False)
        system2 = System[2:]
    elif (System == "chatbot" or System.startswith("chatbot-")):
        # The system to use is the Chatbot only
        modelResponse = MakePrompt(Index, "\nInternet: " + internetResponse + "\nQuestion: " + Question, [], "chatbot", "", [], ["", ""], False)
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

def MakePrompt(Index: int, Prompt: str, Files: list[dict[str, str]], Service: str, AIArgs: str | None = None, ExtraSystemPrompts: list[str] | str = [], Conversation: list[str] = ["", ""], UseDefaultSystemPrompts: bool | None = None) -> Iterator[dict[str]]:
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
        isNSFW = IsTextNSFW(Prompt)

        # Return error if it's NSFW
        if (isNSFW):
            raise Exception("NSFW detected!")
    
    # Check NSFW in files
    for file in Files:
        if (file["type"] == "image" and not cfg.current_data["allow_processing_if_nsfw"][1] and Service != "nsfw_filter-image"):
            # The file is an image
            isNSFW = IsImageNSFW("ReceivedFiles/" + file["name"] + "_file")

            # Return error if it's NSFW
            if (isNSFW):
                raise Exception("NSFW detected!")
        elif (file["type"] == "audio"):
            # Ignore, the NSFW filter for audio is not created yet
            pass
    
    # Check service
    if (Service == "chatbot" and len(cfg.GetAllInfosOfATask(Service)) > 0):
        # Get chatbot response
        textResponse = cb.Inference(Index, Prompt, Conversation)

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
    elif (Service == "text2img" and len(cfg.GetAllInfosOfATask(Service)) > 0):
        # Process image
        imageFiles = GenerateImages(Index, Prompt)
        fs = []

        # For every image
        for fi in imageFiles:
            fs.append({"type": "image", "data": fi})

        # Return the images
        yield {"response": "", "files": fs}
    elif (Service == "sc" and len(cfg.GetAllInfosOfATask(Service)) > 0):
        # Get the classification
        classification = ClassifyText(Index, Prompt)

        # Return the response
        yield {"response": classification, "files": []}
    elif (Service == "tr" and len(cfg.GetAllInfosOfATask(Service)) > 0):
        # Translate the prompt
        Prompt = cfg.JSONDeserializer(Prompt)
        translation = Translate(Prompt["translator"], Prompt["text"], Index)

        # Return the response
        yield {"response": translation, "files": []}
    elif (Service == "img2text" and len(cfg.GetAllInfosOfATask(Service)) > 0):
        # Get the response from the model for each file
        for file in Files:
            # Check if the file is an image
            if (file["type"] != "image"):
                # If it's not, ignore
                continue

            # Get the response
            response = ImageToText(Index, "ReceivedFiles/" + file["name"] + "_file")

            # Return the response
            yield {"response": response, "files": []}
        
        # Return the final response
        yield {"response": "", "files": []}
    elif (Service == "speech2text" and len(cfg.GetAllInfosOfATask(Service)) > 0):
        # Get the response from the model for each file
        for file in Files:
            # Check if the file is an audio file
            if (file["type"] != "audio"):
                # If it's not, ignore
                continue

            # Get the response
            response = RecognizeAudio(Index, "ReceivedFiles/" + file["name"] + "_file")

            # Return the response
            yield {"response": response, "files": []}
        
        # Return the final response
        yield {"response": "", "files": []}
    elif (Service == "text2audio" and len(cfg.GetAllInfosOfATask(Service)) > 0):
        # Process audio
        audioFiles = GenerateAudio(Index, Prompt)

        # Return the audios
        yield {"response": "", "files": [{"type": "audio", "data": audioFiles}]}
    elif (Service == "nsfw_filter-text" and len(cfg.GetAllInfosOfATask(Service)) > 0):
        # Check if it's NSFW
        nsfw = IsTextNSFW(Prompt, Index)

        # Return the response
        yield {"response": nsfw, "files": []}
    elif (Service == "nsfw_filter-image" and len(cfg.GetAllInfosOfATask(Service)) > 0):
        # Check if it's NSFW for each file
        for file in Files:
            # Check if the file is an image file
            if (file["type"] != "image"):
                # If it's not, ignore
                continue

            # Get the response
            response = IsImageNSFW("ReceivedFiles/" + file["name"] + "_file", Index)

            # Return the response
            yield {"response": response, "files": []}

        # Return the response
        yield {"response": "", "files": []}
    elif (Service == "de" and len(cfg.GetAllInfosOfATask(Service)) > 0):
        # Calculate depth estimation for each file
        for file in Files:
            # Check if the file is an image file
            if (file["type"] != "image"):
                # If it's not, ignore
                continue

            # Get the response
            response = EstimateDepth(Index, "ReceivedFiles/" + file["name"] + "_file")

            # Return the response
            yield {"response": "", "files": [{"type": "image", "data": response}]}

        # Return the response
        yield {"response": "", "files": []}
    elif (Service == "od" and len(cfg.GetAllInfosOfATask(Service)) > 0):
        # Calculate object detection for each file
        for file in Files:
            # Check if the file is an image file
            if (file["type"] != "image"):
                # If it's not, ignore
                continue

            # Get the response
            response = DetectObjects(Index, "ReceivedFiles/" + file["name"] + "_file")

            # Return the response
            yield {"response": response["objects"], "files": [{"type": "image", "data": response["image"]}]}

        # Return the response
        yield {"response": "", "files": []}
    elif (Service == "rvc" and len(cfg.GetAllInfosOfATask(Service)) > 0):
        # Get RVC of each file
        for file in Files:
            # Check if the file is an audio file
            if (file["type"] != "audio"):
                # If it's not, ignore
                continue

            # Get the response
            promptFile = cfg.JSONDeserializer(Prompt)
            promptFile["input"] = "ReceivedFiles/" + file["name"] + "_file"

            response = DoRVC(Index, promptFile)

            # Return the response
            yield {"response": "", "files": [{"type": "audio", "data": response}]}
        
        # Return the response
        yield {"response": "", "files": []}
    elif (Service == "uvr" and len(cfg.GetAllInfosOfATask(Service)) > 0):
        # Get UVR of each file
        for file in Files:
            # Check if the file is an audio file
            if (file["type"] != "audio"):
                # If it's not, ignore
                continue

            # Get the response
            promptFile = cfg.JSONDeserializer(Prompt)
            promptFile["input"] = "ReceivedFiles/" + file["name"] + "_file"

            response = DoUVR(Index, promptFile)
            fs = []

            # For every file
            for fi in response:
                # Append it
                fs.append({"type": "audio", "data": fi})

            # Return the response
            yield {"response": "", "files": fs}
        
        # Return the response
        yield {"response": "", "files": []}
    elif (Service == "tts" and len(cfg.GetAllInfosOfATask(Service)) > 0):
        # Generate TTS
        response = DoTTS(Index, Prompt)

        # Return the response
        yield {"response": "", "files": [{"type": "audio", "data": response}]}
    elif (Service == "img2img" and len(cfg.GetAllInfosOfATask(Service)) > 0):
        # Get image to image for every file
        for file in Files:
            # Check if the file is an image file
            if (file["type"] != "image"):
                # If it's not, ignore
                continue

            # Get the response
            response = DoImg2Img(Index, json.dumps({"prompt": Prompt, "image": "ReceivedFiles/" + file["name"] + "_file"}))
            fs = []

            # For every file
            for fi in response:
                # Append it
                fs.append({"type": "image", "data": fi})

            # Return the response
            yield {"response": "", "files": fs}

        # Return the response
        yield {"response": "", "files": []}
    elif (Service == "qa" and len(cfg.GetAllInfosOfATask(Service)) > 0):
        # Process the prompt
        Prompt = cfg.JSONDeserializer(Prompt)
        response = qa.Inference(Index, Prompt["context"], Prompt["question"])

        # Return the response
        yield {"response": response, "files": []}
    elif (Service == "ld" and len(cfg.GetAllInfosOfATask(Service)) > 0):
        # Get the language
        lang = DetectLanguage(Index, Prompt)

        # Return the response
        yield {"response": lang, "files": []}
    else:
        raise Exception(f"Service not recognized.")

def GenerateImages(Index: int, Prompt: str) -> list[str]:
    # Get generated images
    imgs_response = agi.Inference(Prompt)
    images = []

    # Generate images
    for img in imgs_response:
        images.append(base64.b64encode(img).decode("utf-8"))
    
    # Return the generated images
    return images

def EstimateDepth(Index: int, Img: str) -> str:
    # Estimate depth
    img_response = de.Inference(Index, Img)
    # Encode the image in base64
    image = base64.b64encode(img_response).decode("utf-8")

    # Return the image
    return image

def GenerateAudio(Index: int, Prompt: str) -> str:
    # Get generated audio
    aud_response = aga.GenerateAudio(Index, Prompt)

    # Return generated audio
    return base64.b64encode(aud_response).decode("utf-8")

def ImageToText(Index: int, Img: str) -> str:
    # Get and return the text from an image
    return itt.Inference(Index, Img)

def RecognizeAudio(Index: int, Audio: str) -> dict[str, str]:
    # Recognize and return an audio
    return sr.Inference(Index, sr.GetAudioDataFromFile(Audio))

def DetectObjects(Index: int, Img: str) -> dict[str]:
    # Get objects data
    data = od.Inference(Index, Img)
    # Encode the image into base64
    image = base64.b64encode(data["image"]).decode("utf-8")

    # Return the data
    return {
        "objects": data["objects"],
        "image": image
    }

def DoRVC(Index: int, AudioData: str | dict[str, any]) -> str:
    if (type(AudioData) == str):
        # Convert audio data to json
        AudioData = cfg.JSONDeserializer(AudioData)

    # Get RVC audio response
    data = rvc.MakeRVC(AudioData)       # TODO
    # Encode the audio into base64
    audio = base64.b64encode(data).decode("utf-8")

    # Return the data
    return audio

def Translate(Translator: str, Prompt: str, Index: int = 0, IndexClassifier: int = -1) -> str:
    if (len(cfg.GetAllInfosOfATask("tr")) > 0):
        # Try to translate using the specified language
        return tns.AutoTranslate(Prompt, "unknown", Translator, Index, IndexClassifier)
    
    return Prompt

def ClassifyText(Index: int, Prompt: str) -> str:
    # Classify text
    if (len(cfg.GetAllInfosOfATask("sc")) > 0):
        return tc.Inference(Index, Prompt)
    
    # Return default class
    return "-1"

def DetectLanguage(Index: int, Prompt: str) -> str:
    # Get the language
    if (len(cfg.GetAllInfosOfATask("ld")) > 0):
        return tns.InferenceClassifier(Prompt, Index)
    
    # Return unknown language
    return "unknown"

def IsTextNSFW(Prompt: str, Index: int = -1) -> bool:
    # If the model is loaded, check NSFW
    if (len(cfg.GetAllInfosOfATask("nsfw_filter-text")) > 0):
        return filters.InferenceText(Prompt, Index)
    
    # If not, return none
    return None

# Check if an image prompt is NSFW
def IsImageNSFW(Image: str | Image.Image, Index: int = -1) -> bool:
    # If the model is loaded, check NSFW
    if (len(cfg.GetAllInfosOfATask("nsfw_filter-image")) > 0):
        return filters.InferenceImage(Image, Index)
    
    # If not, return none
    return None

def DoTTS(Index: int, Prompt: str):
    # Convert audio data to json
    Prompt = cfg.JSONDeserializer(Prompt)

    # Get TTS audio response
    data = tts.MakeTTS(Index, Prompt)
    # Encode the audio into base64
    audio = base64.b64encode(data).decode("utf-8")

    # Return the data
    return audio

def DoUVR(Index: int, AudioData: str) -> list[str]:
    # Convert audio data to json
    AudioData = cfg.JSONDeserializer(AudioData)

    # Get UVR audio response
    data = uvr.MakeUVR(Index, AudioData)
    
    for aud in data:
        # Encode the audio into base64
        data[data.index(aud)] = base64.b64encode(aud).decode("utf-8")

    # Return the data
    return data

def DoImg2Img(Index: int, Prompt: str) -> list[str]:
    # Convert image data to json
    img_data = cfg.JSONDeserializer(Prompt)

    # Get images
    imgs_response = img2img.Inference(Index, img_data)
    images = []

    # Generate images
    for img in imgs_response:
        images.append(base64.b64encode(img).decode("utf-8"))
    
    # Return the generated images
    return images