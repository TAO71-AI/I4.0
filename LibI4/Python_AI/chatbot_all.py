# Import the models
from collections.abc import Iterator
import Inference.Text.chatbot as cb
import Inference.Text.text_classification as tc
import Inference.Text.translation as tns
import Inference.Images.ai_generate_image as text2img
import Inference.Images.ai_img_to_text as itt
import Inference.Audio.ai_generate_audio as text2audio
import Inference.Mixed.ai_filters as filters
import Inference.Images.ai_depth_estimation as de
import Inference.Images.ai_object_detection as od
import Inference.Audio.speech_recog as sr
import Inference.Audio.rvc_inf as rvc
import Inference.Audio.ai_vocal_separator as uvr
import Inference.Images.image_to_image as img2img
import Inference.Text.ai_question_answering as qa
import Inference.Mixed.multimodal_chatbot as mmcb
import internet_connection as internet
import ai_config as cfg
import conversation_multimodal as conv
import ai_memory as memories
import chatbot_basics as cbbasics
import PIL.Image as Image
import base64
import datetime
import calendar
import json
import os
import random

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
img2img - Image to Image.
qa - Question Answering.
"""

__cache_files__: list[str] = []

def EmptyCache() -> None:
    # Delete all the cache files
    for file in __cache_files__:
        try:
            os.remove(file)
            __cache_files__.remove(file)
        except:
            print(f"Could not delete cache file '{file}'. Ignoring.")

def __create_file__(FileType: str, FileData: bytes | str) -> str:
    # Set file extension
    if (FileType == "image"):
        ext = "png"
    elif (FileType == "audio"):
        ext = "wav"
    
    # Set file name
    fName = f"temp_input_file_0.{ext}"

    # Check if name exists
    while (os.path.exists(fName)):
        # It exists, change name
        fName = f"temp_input_file_{random.randint(-99999, 99999)}.{ext}"
    
    # Check bytes type
    if (type(FileData) == str):
        # Base64 encoded, decode
        FileData = base64.b64decode(FileData)

    # Add the bytes to the file
    with open(fName, "wb") as f:
        f.write(FileData)

    # Return the file name
    return fName

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
    mmcb.LoadModels()
    tc.LoadModels()
    tns.LoadModels()
    tns.LoadClassifiers()
    text2img.LoadModels()
    itt.LoadModels()
    sr.LoadModels()
    text2audio.LoadModels()
    filters.LoadModels()
    de.LoadModels()
    od.LoadModels()
    rvc.LoadModels()
    #uvr.LoadModels() # TODO
    img2img.LoadModels()
    qa.LoadModels()

def __offload_model__(Service: str, Index: int) -> None:
    # Call the function to offload of the model
    if (Service == "chatbot"):
        # Check if the chatbot is multimodal or not
        if (len(cfg.GetInfoOfTask("chatbot", Index)["multimodal"].strip()) > 0):
            # It is
            mmcb.__offload_model__(Index)
            pass
        else:
            # It isn't
            cb.__offload_model__(Index)
    elif (Service == "sc"):
        tc.__offload_model__(Index)
    elif (Service == "tr"):
        tns.__offload_model__(Index)
    elif (Service == "ld"):
        tns.__offload_classifier__(Index)
    elif (Service == "text2img"):
        text2img.__offload_model__(Index)
    elif (Service == "img2text"):
        itt.__offload_model__(Index)
    elif (Service == "speech2text"):
        sr.__offload_model__(Index)
    elif (Service == "text2audio"):
        text2audio.__offload_model__(Index)
    elif (Service == "nsfw_filter-text"):
        filters.__offload_text__(Index)
    elif (Service == "nsfw_filter-image"):
        filters.__offload_image__(Index)
    elif (Service == "de"):
        de.__offload_model__(Index)
    elif (Service == "od"):
        od.__offload_model__(Index)
    elif (Service == "rvc"):
        rvc.__offload_model__(Index)
    elif (Service == "img2img"):
        img2img.__offload_model__(Index)
    elif (Service == "qa"):
        qa.__offload_model__(Index)
    else:
        print(f"Invalid offload service '{Service}'; ignoring...")

def OffloadAll(Exclude: dict[str, list[int]]) -> None:
    # Get tasks
    tasks = cfg.GetAllTasks()

    # For each task
    for task in list(tasks.keys()):
        # For each index
        for index in range(len(tasks[task])):
            aOffloading = True

            try:
                # Get offloading from the config
                aOffloading = tasks[task][index]["allow_offloading"]
            except:
                # Error getting the offloading from the config; probable not specified. Default to True.
                pass

            # Check if the task and index is in the exclude list or if it doesn't allow offloading
            if ((task in list(Exclude.keys()) and index in Exclude[task]) or not aOffloading):
                # It is, continue
                continue

            # It isn't, offload
            __offload_model__(task, index)

def GetResponseFromInternet(Index: int, SearchPrompt: str, Question: str, SearchSystem: str, Count: int, AIArgs: str | list[str] | None = None, ExtraSystemPrompts: list[str] | str = [], UseDefaultSystemPrompts: bool | tuple[bool, bool] | list[bool] | None = None) -> Iterator[dict[str, any]]:
    # Delete empty conversation
    conv.DeleteConversation("", "")

    # Set limits
    minLength = cfg.current_data["internet"]["min_length"]
    maxLength = cfg.GetInfoOfTask("chatbot", Index)["ctx"]              # Chatbot context length
    maxLength -= len(cbbasics.GetDefaultSystemPrompts())                # Default I4.0 system prompts
    maxLength -= len(cbbasics.GetPersonalitySystemPrompts(AIArgs))      # I4.0 personality system prompts
    maxLength -= len(ExtraSystemPrompts)                                # Extra system prompts defined by the user
    maxLength -= len(cfg.current_data["custom_system_messages"])        # Extra system prompts defined by the server
    maxLength -= 22                                                     # Internet template
    maxLength -= 1                                                      # Just to make sure the ctx is not exceed

    # Check if max length is less than/equal to 0
    if (maxLength <= 0):
        raise Exception("Context length of the model is too small!")

    # Search over internet
    if (SearchSystem == "websites" or SearchSystem == "website"):
        # Search for websites
        internetResults = internet.Search__Websites(SearchPrompt, Count)
        internetResponse = ""

        # For each result
        for result in internetResults:
            try:
                # Try to append it to the internet response
                internetResponse += internet.ReadTextFromWebsite(result, maxLength, minLength) + "\n"
            except:
                # Ignore error
                continue
    elif (SearchSystem == "news"):
        # Search for news
        internetResults = internet.Search__News(SearchPrompt, Count)
        internetResponse = "\n".join(internetResults)

        # Check if internet response length is 0
        if (len(internetResponse.strip()) == 0):
            # It is, get the response from the websites
            return GetResponseFromInternet(Index, SearchPrompt, Question, "websites", Count, AIArgs, ExtraSystemPrompts, UseDefaultSystemPrompts)
        else:
            internetResponse = internet.__apply_limit_to_text__(internetResponse, maxLength, minLength)
    elif (SearchSystem == "chat"):
        # Obtain the response from the chat
        internetResponse = internet.Search__Chat(f"{SearchPrompt}\n{Question}", cfg.current_data["internet_chat"])
        internetResponse = internet.__apply_limit_to_text__(internetResponse, maxLength, minLength)
    elif (SearchSystem == "maps"):
        # Search for nearby places
        internetResults = internet.Search__Maps(SearchPrompt, 15, Count)
        internetResponse = "\n".join(internetResults)
        
        # Check if internet response length is 0
        if (len(internetResponse.strip()) == 0):
            # It is, get the response from the websites
            return GetResponseFromInternet(Index, SearchPrompt, Question, "websites", Count, AIArgs, ExtraSystemPrompts, UseDefaultSystemPrompts)
        else:
            internetResponse = internet.__apply_limit_to_text__(internetResponse, maxLength, minLength)
    else:
        # Raise error
        raise ValueError("Invalid SearchSystem. Use 'websites', 'answers', 'news', 'chat' or 'maps'.")

    # Return the response
    return MakePrompt(Index, f"Internet:\n{internetResponse}\n\nQuestion: {Question}", [], "chatbot", AIArgs, ExtraSystemPrompts, ["", ""], UseDefaultSystemPrompts, [])

def MakePrompt(Index: int, Prompt: str, Files: list[dict[str, str]], Service: str, AIArgs: str | list[str] | None = None, ExtraSystemPrompts: list[str] | str = [], Conversation: list[str] = ["", ""], UseDefaultSystemPrompts: bool | tuple[bool, bool] | list[bool] | None = None, AllowedTools: list[str] | str | None = None, ExtraTools: list[dict[str, str | dict[str, any]]] = [], MaxLength: int | None = None, Temperature: float | None = None) -> Iterator[dict[str, any]]:
    # Define I4.0's personality
    if (AIArgs == None):
        AIArgs = cfg.current_data["ai_args"].split("+")
    else:
        AIArgs = AIArgs.split("+")
    
    # Check conversation to prevent errors
    if (Conversation[0] is None):
        Conversation[0] = ""
    elif (type(Conversation[0]) != str):
        raise ValueError("Conversation [0] MUST be a string.")
    
    if (Conversation[1] is None):
        Conversation[1] = ""
    elif (type(Conversation[1]) != str):
        raise ValueError("Conversation [1] MUST be a string.")

    # Get the info of the model
    info = cfg.GetInfoOfTask(Service, Index)

    # Set system prompts
    sp = []

    # Get the tools
    tools = cbbasics.GetTools(AllowedTools)

    # Get the extra tools
    for etool in ExtraTools:
        if (cbbasics.IsToolValid(etool)):
            tools.append(etool)
    
    # Add system prompt if tools > 0
    if (len(tools) > 0):
        sp.append("You can use multiple tools in the same response.")

    # Get the personality
    sp.append(cbbasics.GetPersonalitySystemPrompts(AIArgs))

    # Define the use of the default system prompts
    if (UseDefaultSystemPrompts == None):
        UseDefaultSystemPrompts = cfg.current_data["use_default_system_messages"]
    
    if (type(UseDefaultSystemPrompts) == list or type(UseDefaultSystemPrompts) == list[bool] or type(UseDefaultSystemPrompts) == list[None]):
        UseDefaultSystemPrompts = (UseDefaultSystemPrompts[0], UseDefaultSystemPrompts[1])  # Ignore any other values of the list
    
    if (type(UseDefaultSystemPrompts) == bool):
        UseDefaultSystemPrompts = (UseDefaultSystemPrompts, UseDefaultSystemPrompts, UseDefaultSystemPrompts)
    
    if (UseDefaultSystemPrompts[0]):
        # Get default system prompts
        sp.append(cbbasics.GetDefaultSystemPrompts())
    
    # Add the system prompts from the configuration
    if (len(cfg.current_data["custom_system_messages"].strip()) > 0 and UseDefaultSystemPrompts[1]):
        sp += cfg.current_data["custom_system_messages"].split("\n")
    
    # Check if the info contains information about the model and it's not empty
    if (list(info.keys()).count("model_info") == 1 and len(str(info["model_info"]).strip()) > 0 and UseDefaultSystemPrompts[1]):
        # Add the model info to the model
        sp.append(str(info["model_info"]))
    
    # Add extra system prompts
    if ((type(ExtraSystemPrompts) == list or type(ExtraSystemPrompts) == list[str]) and len(ExtraSystemPrompts) > 0):
        sp += ExtraSystemPrompts
    elif (len(ExtraSystemPrompts) > 0):
        sp.append(str(ExtraSystemPrompts))
    
    if (cfg.current_data["use_dynamic_system_args"]):
        # Get dynamic system prompts (for current date, etc.)
        # Get the current date
        cDate = datetime.datetime.now()

        # Add sprompts
        sp += [
            "",
            f"The current date is {cDate.day} of {calendar.month_name[cDate.month]}, {cDate.year}.",
            f"The current time is {'0' + str(cDate.hour) if (cDate.hour < 10) else str(cDate.hour)}:{'0' + str(cDate.minute) if (cDate.minute < 10) else str(cDate.minute)}."
        ]

        if (cDate.day == 16 and cDate.month == 9 and UseDefaultSystemPrompts[0]):
            # I4.0's birthday!!!!
            sp.append("Today it's your birthday.")
    
    # Get the memories
    mems = memories.GetMemories(Conversation[0])

    # Check if the length of the memories is higher than 0
    if (len(mems) > 0):
        # It is
        sp.append("\n")

        # For each memory
        for mem in range(len(mems)):
            # Add the memory
            sp.append(f"Memory #{mem}: {mems[mem]}")
    
    # Check NSFW in prompt
    if ((Service == "chatbot" or Service == "sc" or Service == "tr" or Service == "text2img" or Service == "text2audio" or Service == "tts" or Service == "qa") and not cfg.current_data["allow_processing_if_nsfw"][0] and Service != "nsfw_filter-text" and len(cfg.GetAllInfosOfATask("nsfw_filter-text")) > 0):
        # Pick random text NSFW filter
        filterIdx = random.randint(0, len(cfg.GetAllInfosOfATask("nsfw_filter-text")) - 1)
        
        # Check if the prompt is NSFW
        isNSFW = IsTextNSFW(Prompt, filterIdx)

        # Return error if it's NSFW
        if (isNSFW):
            raise Exception("NSFW detected!")

    # For each file
    for file in Files:
        # Check file size
        if (len(file["data"]) > cfg.current_data["max_files_size"] * 1024 * 1024):
            # Bigger than the server allows, return an error
            raise Exception("File exceeds the maximum file size allowed by the server.")

        # Create file
        f = __create_file__(file["type"], file["data"])

        # Replace from the list
        Files[Files.index(file)]["data"] = f
        __cache_files__.append(f)

        # Check NSFW
        if (file["type"] == "image" and not cfg.current_data["allow_processing_if_nsfw"][1] and Service != "nsfw_filter-image"  and len(cfg.GetAllInfosOfATask("nsfw_filter-image")) > 0):
            # Pick random image NSFW filter
            filterIdx = random.randint(0, len(cfg.GetAllInfosOfATask("nsfw_filter-image")) - 1)

            # The file is an image
            isNSFW = IsImageNSFW(f, filterIdx)

            # Return error if it's NSFW
            if (isNSFW):
                raise Exception("NSFW detected!")
        elif (file["type"] == "audio"):
            # Ignore, the NSFW filter for audio is not created yet
            pass
    
    # Check service
    if (Service == "chatbot" and len(cfg.GetAllInfosOfATask(Service)) > 0):
        # Get chatbot response
        if (len(cfg.GetInfoOfTask(Service, Index)["multimodal"].strip()) > 0):
            # Use multimodal chatbot
            textResponse = mmcb.Inference(Index, Prompt, Files, sp, tools, Conversation, MaxLength, Temperature)
        else:
            # Use normal chatbot
            textResponse = cb.Inference(Index, Prompt, sp, tools, Conversation, MaxLength, Temperature)

        # For every token
        for token in textResponse:
            # Return the token
            yield {"response": token, "files": []}
        
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
        # Check file 0 type
        if (Files[0]["type"] != "image"):
            # Error, unexpected file type
            raise Exception("File must be an image.")

        # Get the response of file 0
        response = ImageToText(Index, Files[0]["data"])

        # Return the response
        yield {"response": response, "files": []}
    elif (Service == "speech2text" and len(cfg.GetAllInfosOfATask(Service)) > 0):
        # Check file 0 type
        if (Files[0]["type"] != "audio"):
            # Error, unexpected file type
            raise Exception("File must be an audio.")
        
        # Get the response of file 0
        response = RecognizeAudio(Index, Files[0]["data"])

        # Check if the language is unknown and at least one language detector is available
        if (response["lang"] == "unknown" and len(cfg.GetAllInfosOfATask("ld")) > 0):
            # Detect the language
            response["lang"] = DetectLanguage(random.randint(0, len(cfg.GetAllInfosOfATask("ld")) - 1), response["text"])

        # Return the response
        yield {"response": response, "files": []}
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
        # Check file 0 type
        if (Files[0]["type"] != "image"):
            # Error, unexpected file type
            raise Exception("File must be an image.")
        
        # Get the response of file 0
        response = IsImageNSFW(Files[0]["data"], Index)

        # Return the response
        yield {"response": response, "files": []}
    elif (Service == "de" and len(cfg.GetAllInfosOfATask(Service)) > 0):
        # Check file 0 type
        if (Files[0]["type"] != "image"):
            # Error, unexpected file type
            raise Exception("File must be an image.")
        
        # Get the response of file 0
        response = EstimateDepth(Index, Files[0]["data"])

        # Return the response
        yield {"response": "", "files": [{"type": "image", "data": response}]}
    elif (Service == "od" and len(cfg.GetAllInfosOfATask(Service)) > 0):
        # Check file 0 type
        if (Files[0]["type"] != "image"):
            # Error, unexpected file type
            raise Exception("File must be an image.")
        
        # Get the response of file 0
        response = DetectObjects(Index, Files[0]["data"])

        # Return the response
        yield {"response": response["objects"], "files": [{"type": "image", "data": response["image"]}]}
    elif (Service == "rvc" and len(cfg.GetAllInfosOfATask(Service)) > 0):
        # Check file 0 type
        if (Files[0]["type"] != "audio"):
            # Error, unexpected file type
            raise Exception("File must be an audio.")

        # Get the response of file 0
        promptFile = cfg.JSONDeserializer(Prompt)
        promptFile["input"] = Files[0]["data"]
        promptFile["index"] = Index

        response = DoRVC(promptFile)

        # Return the response
        yield {"response": "", "files": [{"type": "audio", "data": response}]}
    elif (Service == "uvr" and len(cfg.GetAllInfosOfATask(Service)) > 0):
        yield {"response": "TODO; UVR is under creation..."}
        """# Get UVR of each file
        for file in Files:
            # Check if the file is an audio file
            if (file["type"] != "audio"):
                # If it's not, ignore
                continue

            # Get the response
            promptFile = cfg.JSONDeserializer(Prompt)
            promptFile["input"] = file["name"]

            response = DoUVR(Index, promptFile)
            fs = []

            # For every file
            for fi in response:
                # Append it
                fs.append({"type": "audio", "data": fi})

            # Return the response
            yield {"response": "", "files": fs}
        
        # Return the response
        yield {"response": "", "files": []}"""
    elif (Service == "img2img" and len(cfg.GetAllInfosOfATask(Service)) > 0):
        # Check file 0 type
        if (Files[0]["type"] != "image"):
            # Error, unexpected file type
            raise Exception("File must be an image.")
        
        # Get the response of file 0
        response = DoImg2Img(Index, json.dumps({"prompt": Prompt, "image": Files[0]["data"]}))
        fs = []

        # For every file
        for fi in response:
            # Append it
            fs.append({"type": "image", "data": fi})

        # Return the response
        yield {"response": "", "files": fs}
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
        # Return an error
        yield {"response": "ERROR! Service not found.", "files": []}

    # For each file
    for file in Files:
        # Remove the file from the server
        os.remove(file["data"])
        
        try:
            # Try to remove from the cache
            __cache_files__.remove(file["data"])
        except:
            # Error removing the file
            print(f"   Error removing from cache '{file['data']}'. Ignoring.")

def GenerateImages(Index: int, Prompt: str) -> list[str]:
    # Get generated images
    imgs_response = text2img.Inference(Index, Prompt)
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
    aud_response = text2audio.GenerateAudio(Index, Prompt)

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

def DoRVC(AudioData: str | dict[str, any]) -> str:
    if (type(AudioData) == str):
        # Convert audio data to json
        AudioData = cfg.JSONDeserializer(AudioData)

    # Get RVC audio response
    data = rvc.MakeRVC(AudioData)
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

def IsTextNSFW(Prompt: str, Index: int) -> bool:
    # If the model is loaded, check NSFW
    if (len(cfg.GetAllInfosOfATask("nsfw_filter-text")) > 0):
        return filters.InferenceText(Prompt, Index)
    
    # If not, return none
    return None

# Check if an image prompt is NSFW
def IsImageNSFW(Image: str | Image.Image, Index: int) -> bool:
    # If the model is loaded, check NSFW
    if (len(cfg.GetAllInfosOfATask("nsfw_filter-image")) > 0):
        return filters.InferenceImage(Image, Index)
    
    # If not, return none
    return None

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