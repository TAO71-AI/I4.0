# Import I4.0 utilities
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
import Inference.Images.image_to_image as img2img
import Inference.Text.ai_question_answering as qa
import Inference.Mixed.multimodal_chatbot as mmcb
import internet_connection as internet
import ai_config as cfg
import conversation_multimodal as conv
import ai_memory as memories
import chatbot_basics as cbbasics
import db_dataset as dts
import documents as docs

# Import other libraries
from collections.abc import Iterator
import PIL.Image as Image
import base64
import datetime
import calendar
import json
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
uvr - Uses UVR on an audio file.  <--- WORKING ON IT
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

def OffloadAll(Exclude: dict[str, list[int]], Force: bool = False) -> None:
    # Get tasks
    tasks = cfg.GetAllTasks()

    # For each task
    for task in list(tasks.keys()):
        # For each index
        for index in range(len(tasks[task])):
            aOffloading = True

            if (not Force):
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

def GetResponseFromInternet(
        Index: int,
        Keywords: str,
        Question: str,
        Count: int, AIArgs: str | list[str] | None,
        ExtraSystemPrompts: list[str] | str,
        UseDefaultSystemPrompts: bool | tuple[bool, bool] | list[bool] | None,
        Conversation: list[str],
        MaxLength: int | None,
        Temperature: float | None,
        TopP: float | None,
        TopK: int | None,
        MinP: float | None = None,
        TypicalP: float | None = None
    ) -> Iterator[dict[str, any]]:
    # Get response from the dataset
    datasetResponses = dts.GetResponse(Keywords)

    # Check responses length
    if (len(datasetResponses) > 0):
        # Save all the dataset responses into a string
        datasetResponse = "\n".join(datasetResponses)
        datasetResponse = datasetResponse.strip()

        # Send the prompt to I4.0
        return MakePrompt(
            Index,
            f"Internet data:\n{datasetResponse}\nQuestion to answer: {Question}",
            [],
            "chatbot",
            AIArgs,
            ExtraSystemPrompts,
            Conversation,
            UseDefaultSystemPrompts,
            [],
            [],
            MaxLength,
            Temperature,
            TopP,
            TopK,
            MinP,
            TypicalP
        )
    
    # Search for websites
    internetResults = internet.Search__Websites(Keywords, Count, None)
    return GetResponseFromInternet_URL(
        Index,
        internetResults,
        Question,
        AIArgs,
        ExtraSystemPrompts,
        UseDefaultSystemPrompts,
        Conversation,
        MaxLength,
        Temperature,
        TopP,
        TopK,
        MinP,
        TypicalP
    )

def GetResponseFromInternet_URL(
        Index: int,
        URL: str | list[str],
        Question: str,
        AIArgs: str | list[str] | None,
        ExtraSystemPrompts: list[str] | str,
        UseDefaultSystemPrompts: bool | tuple[bool, bool] | list[bool] | None,
        Conversation: list[str],
        MaxLength: int | None,
        Temperature: float | None,
        TopP: float | None,
        TopK: int | None,
        MinP: float | None = None,
        TypicalP: float | None = None
    ) -> Iterator[dict[str, any]]:
    # Set system prompt
    if (isinstance(ExtraSystemPrompts, list)):
        ExtraSystemPrompts = "\n".join(ExtraSystemPrompts)
    
    if (isinstance(URL, str)):
        sysPrompt = f"You're answering a question with the results obtained from the website `{URL}`.\n{ExtraSystemPrompts}".strip()
    else:
        sysPrompt = f"You're answering a question with the results obtained from internet.\n{ExtraSystemPrompts}".strip()

    # Set limits
    minLength = cfg.current_data["internet"]["min_length"]
    maxLength = cfg.GetInfoOfTask("chatbot", Index)["ctx"]              # Chatbot context length
    maxLength -= len(sysPrompt)                                         # System prompts
    maxLength -= 51 + len(Question)                                     # Internet template
    maxLength -= 1                                                      # Just to make sure the ctx is not exceed

    # Check if max length is less than/equal to 0
    if (maxLength <= 0):
        raise Exception("Context length of the model is too small!")
    
    # Read the website or websites
    if (isinstance(URL, str)):
        try:
            internetData = f"```plaintext\n{internet.ReadTextFromWebsite(URL, maxLength, minLength)}\n```"
        except:
            internetData = "Error reading data from the internet."
    else:
        internetData = ""

        for url in URL:
            try:
                internetData += f"Website `{url}`:\n```plaintext\n{internet.ReadTextFromWebsite(url, maxLength, minLength)}\n```"
            except:
                internetData += f"Error reading data from the website `{url}`."
            
            internetData += "\n\n"
    
    # Return the response
    return MakePrompt(
        Index,
        f"Internet data:\n{internetData}\nQuestion to answer: {Question}",
        [],
        "chatbot",
        AIArgs,
        sysPrompt,
        Conversation,
        UseDefaultSystemPrompts,
        [],
        [],
        MaxLength,
        Temperature,
        TopP,
        TopK,
        MinP,
        TypicalP
    )

def InternetResearch(
        Index: int,
        Keywords: str,
        Question: str,
        AIArgs: str | list[str] | None,
        ExtraSystemPrompts: list[str] | str,
        UseDefaultSystemPrompts: bool | tuple[bool, bool] | list[bool] | None,
        Conversation: list[str],
        MaxLength: int | None,
        Temperature: float | None,
        TopP: float | None,
        TopK: int | None,
        MinP: float | None = None,
        TypicalP: float | None = None
    ) -> Iterator[dict[str, any]]:
    # Get the internet results
    internetResults = internet.Search__Websites(Keywords, cfg.current_data["internet"]["max_results"], None)
    internetResponses = []

    # Yield a token
    yield {"response": f"[INTERNET RESEARCH (0/{len(internetResults)})]\n", "files": []}

    # For each internet result
    for id, website in enumerate(internetResults):
        # Clear the conversation
        conv.DeleteConversation("", "")

        # Get the chatbot response from the internet
        response = GetResponseFromInternet_URL(
            Index,
            website,
            Question,
            "",
            "",
            False,
            Conversation,
            None,
            Temperature,
            TopP,
            TopK
        )
        strResponse = ""

        # For each token
        for token in response:
            # Append to the strResponse
            strResponse += str(token["response"])
        
        # Append the full response
        internetResponses.append(strResponse.strip())

        # Yield a token
        yield {"response": f"[INTERNET RESEARCH ({id + 1}/{len(internetResults)})]\n", "files": []}
    
    # Set system prompt
    if (isinstance(ExtraSystemPrompts, list)):
        ExtraSystemPrompts = "\n".join(ExtraSystemPrompts)
    
    sysPrompt = f"You're answering a question with the results obtained from internet.\n{ExtraSystemPrompts}".strip()
    
    # Set limits and other variables
    maxLength = cfg.GetInfoOfTask("chatbot", Index)["ctx"]              # Chatbot context length
    maxLength -= len(sysPrompt)                                         # System prompts
    maxLength -= 51 + len(Question)                                     # Internet template
    maxLength -= 1                                                      # Just to make sure the ctx is not exceed
    reasoningMode = cfg.current_data["internet"]["research"]["reasoning_mode"]

    # Convert results list to string
    results = "".join([f"Website #{wID} response:\n```plaintext\n{wRes}\n```\n" for wID, wRes in enumerate(internetResponses)])

    # Check length and change the reasoning mode if needed
    if (len(results) > maxLength and reasoningMode < 0):
        reasoningMode = 1
    
    # Cut the results if the reasoning is disabled
    while (reasoningMode == 1 and results.count("<think>") > 0 and results.count("</think>") > 0):
        results = results[results.index("</think>") + 8:]
    
    # Check length and cut the response if needed
    if (len(results) > maxLength):
        results = results[:maxLength]
        results = results[:results.rfind("```")]
    
    # Send prompt to the chatbot
    response = MakePrompt(
        Index,
        f"Internet data:\n{results}\nQuestion to answer: {Question}",
        [],
        "chatbot",
        AIArgs,
        sysPrompt,
        Conversation,
        UseDefaultSystemPrompts,
        [],
        [],
        MaxLength,
        Temperature,
        TopP,
        TopK,
        MinP,
        TypicalP
    )

    # For each token
    for token in response:
        # Yield the token
        yield token

def MakePrompt(
        Index: int,
        Prompt: str,
        Files: list[dict[str, str]],
        Service: str,
        AIArgs: str | list[str] | None = None,
        ExtraSystemPrompts: list[str] | str = [],
        Conversation: list[str] = ["", ""],
        UseDefaultSystemPrompts: bool | tuple[bool, bool] | list[bool] | None = None,
        AllowedTools: list[str] | str | None = None,
        ExtraTools: list[dict[str, str | dict[str, any]]] = [],
        MaxLength: int | None = None,
        Temperature: float | None = None,
        TopP: float | None = None,
        TopK: int | None = None,
        MinP: float | None = None,
        TypicalP: float | None = None
    ) -> Iterator[dict[str, any]]:
    # Define I4.0's personality
    if (AIArgs == None):
        AIArgs = cfg.current_data["ai_args"].split("+")
    else:
        AIArgs = AIArgs.split("+")
    
    # Check conversation to prevent errors
    if (Conversation[0] is None):
        Conversation[0] = ""
    elif (not isinstance(Conversation[0], str)):
        raise ValueError("Conversation [0] MUST be a string.")
    
    if (Conversation[1] is None):
        Conversation[1] = ""
    elif (not isinstance(Conversation[1], str)):
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
        #sp.append("To use any tool, write something like this:\n```plaintext\n<tool_call>\n{function}\n</tool_call>\n```")
        sp.append("You can respond to the user's prompt before or after using any tool.")
    
    # Get the personality
    sp.append(cbbasics.GetPersonalitySystemPrompts(AIArgs))

    # Define the use of the default system prompts
    if (isinstance(UseDefaultSystemPrompts, list) or isinstance(UseDefaultSystemPrompts, tuple)):
        udsp1 = udsp2 = udsp3 = cfg.current_data["use_default_system_messages"]
        udsp4 = cfg.current_data["use_dynamic_system_args"]

        if (len(UseDefaultSystemPrompts) >= 1 and UseDefaultSystemPrompts[0] is not None):
            udsp1 = bool(UseDefaultSystemPrompts[0])
            
        if (len(UseDefaultSystemPrompts) >= 2 and UseDefaultSystemPrompts[1] is not None):
            udsp2 = bool(UseDefaultSystemPrompts[1])
            
        if (len(UseDefaultSystemPrompts) >= 3 and UseDefaultSystemPrompts[2] is not None):
            udsp3 = bool(UseDefaultSystemPrompts[2])
            
        if (len(UseDefaultSystemPrompts) >= 4 and UseDefaultSystemPrompts[3] is not None):
            udsp4 = bool(UseDefaultSystemPrompts[3])

        UseDefaultSystemPrompts = (udsp1, udsp2, udsp3, udsp4)
    elif (isinstance(UseDefaultSystemPrompts, bool)):
        UseDefaultSystemPrompts = (UseDefaultSystemPrompts, UseDefaultSystemPrompts, UseDefaultSystemPrompts, UseDefaultSystemPrompts)
    else:
        UseDefaultSystemPrompts = (cfg.current_data["use_default_system_messages"], cfg.current_data["use_default_system_messages"], cfg.current_data["use_default_system_messages"], cfg.current_data["use_dynamic_system_args"])
    
    if (UseDefaultSystemPrompts[0]):
        # Get default system prompts
        sp.append(cbbasics.GetDefaultSystemPrompts())
    
    # Add the system prompts from the configuration
    if (len(cfg.current_data["custom_system_messages"].strip()) > 0 and UseDefaultSystemPrompts[1]):
        sp += cfg.current_data["custom_system_messages"].split("\n")
    
    # Check if the info contains information about the model and it's not empty
    if (list(info.keys()).count("model_info") == 1 and len(str(info["model_info"]).strip()) > 0 and UseDefaultSystemPrompts[2]):
        # Add the model info to the model
        sp.append(str(info["model_info"]))
    
    # Add extra system prompts
    if (isinstance(ExtraSystemPrompts, list) and len(ExtraSystemPrompts) > 0):
        sp += ExtraSystemPrompts
    elif (len(ExtraSystemPrompts) > 0):
        sp.append(str(ExtraSystemPrompts))
    
    if (UseDefaultSystemPrompts[3]):
        # Get dynamic system prompts (for current date, etc.)
        # Get the current date
        cDate = datetime.datetime.now()

        # Add sprompts
        sp += [
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
    if (
        (
            Service == "chatbot" or
            Service == "sc" or
            Service == "tr" or
            Service == "text2img" or
            Service == "text2audio" or
            Service == "tts" or
            Service == "qa"
        ) and
        not cfg.current_data["allow_processing_if_nsfw"][0] and
        Service != "nsfw_filter-text" and
        len(cfg.GetAllInfosOfATask("nsfw_filter-text")) > 0
    ):
        # Pick random text NSFW filter
        filterIdx = random.randint(0, len(cfg.GetAllInfosOfATask("nsfw_filter-text")) - 1)
        
        # Check if the prompt is NSFW
        isNSFW = IsTextNSFW(Prompt, filterIdx)

        # Return error if it's NSFW
        if (isNSFW):
            raise Exception("NSFW detected!")
    
    # Create document files count
    documentFiles = 0

    # For each file
    for file in Files:
        # Check file size
        if (len(file["data"]) > cfg.current_data["max_files_size"] * 1024 * 1024):
            # Bigger than the server allows, return an error
            raise Exception("File exceeds the maximum file size allowed by the server.")

        # Get file bytes
        f = base64.b64decode(file["data"])

        # Replace from the list
        file["data"] = f

        # Lower the file type
        file["type"] = file["type"].lower()

        # Check file type
        if (
            file["type"] == "image" and
            not cfg.current_data["allow_processing_if_nsfw"][1] and
            Service != "nsfw_filter-image" and
            len(cfg.GetAllInfosOfATask("nsfw_filter-image")) > 0
        ):
            # Check NSFW
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
        elif (file["type"] == "video"):
            # Ignore, the NSFW filter for video is not created yet
            pass
        elif (file["type"] == "pdf"):
            # Add one to the document files count
            documentFiles += 1

            # Extract PDF text
            pdfPages = docs.PDF2PLAINTEXT(f)
            pdfText = "\n".join(pdfPages)

            # Strip the text
            pdfText = pdfText.strip()

            # Add to the system prompt
            sp.append(f"Document file #{documentFiles} (PDF file):\n```plaintext\n{pdfText}\n```")
        elif (file["type"] == "csv"):
            # Add one to the document files count
            documentFiles += 1

            # Convert the data to text
            csvText = f.decode("utf-8")

            # Add to the system prompt
            sp.append(f"Document file #{documentFiles} (CSV file):\n```csv\n{csvText}\n```")
        elif (file["type"] == "xlsx"):
            # Add one to the document files count
            documentFiles += 1

            # Convert the file to CSV
            csvText = docs.XLSX2CSV(f)

            # Add to the system prompt
            sp.append(f"Document file #{documentFiles} (XLSX file):\n```csv\n{csvText}\n```")
    
    # Check service
    if (Service == "chatbot" and len(cfg.GetAllInfosOfATask(Service)) > 0):
        # Get chatbot response
        if (len(cfg.GetInfoOfTask(Service, Index)["multimodal"].strip()) > 0):
            # Use multimodal chatbot
            textResponse = mmcb.Inference(Index, Prompt, Files, sp, tools, Conversation, MaxLength, Temperature, TopP, TopK, MinP, TypicalP)
        else:
            # Use normal chatbot
            textResponse = cb.Inference(Index, Prompt, sp, tools, Conversation, MaxLength, Temperature, TopP, TopK, MinP, TypicalP)

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

def GenerateImages(Index: int, Prompt: str) -> list[str]:
    # Get generated images
    imgs_response = text2img.Inference(Index, Prompt)
    images = []

    # Generate images
    for img in imgs_response:
        images.append(base64.b64encode(img).decode("utf-8"))
    
    # Return the generated images
    return images

def EstimateDepth(Index: int, Img: bytes) -> str:
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

def ImageToText(Index: int, Img: bytes) -> str:
    # Get and return the text from an image
    return itt.Inference(Index, Img)

def RecognizeAudio(Index: int, Audio: bytes) -> dict[str, str]:
    # Recognize and return an audio
    return sr.Inference(Index, Audio)

def DetectObjects(Index: int, Img: bytes) -> dict[str]:
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
def IsImageNSFW(Image: bytes, Index: int) -> bool:
    # If the model is loaded, check NSFW
    if (len(cfg.GetAllInfosOfATask("nsfw_filter-image")) > 0):
        return filters.InferenceImage(Image, Index)
    
    # If not, return none
    return None

"""def DoUVR(Index: int, AudioData: str) -> list[str]:
    # Convert audio data to json
    AudioData = cfg.JSONDeserializer(AudioData)

    # Get UVR audio response
    data = uvr.MakeUVR(Index, AudioData)
    
    for aud in data:
        # Encode the audio into base64
        data[data.index(aud)] = base64.b64encode(aud).decode("utf-8")

    # Return the data
    return data"""

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