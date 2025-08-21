# Import HuggingFace chatbot
from transformers import AutoModelForImageTextToText, AutoProcessor
import Inference.Mixed.MultimodalChatbot.hf as hf

# Import LLaMA-CPP-Python chatbot
from llama_cpp import Llama
from Inference.Mixed.MultimodalChatbot.utils import (
    LoadModel as LCPP_LoadModel,
    GetReasoningMode
)
import Inference.Mixed.MultimodalChatbot.lcpp as lcpp

# Import some other libraries
from collections.abc import Iterator
from PIL import Image
import psutil
import base64
import json
import requests
import os

# Import I4.0's utilities
import ai_config as cfg
import conversation_multimodal as conv

__models__: dict[int, Llama | tuple[tuple[AutoModelForImageTextToText, AutoProcessor, str, str], dict[str, any]]] = {}

def __download_sample_file__(URL: str, SaveInDisk: tuple[bool, str] = (False, "")) -> bytes:
    # Make sure the file doesn't exists
    if (SaveInDisk[0] and os.path.exists(SaveInDisk[1])):
        with open(SaveInDisk[1], "rb") as f:
            data = f.read()
        
        return data

    # Request the URL
    response = requests.get(URL)

    # Save in the disk
    if (SaveInDisk[0]):
        with open(SaveInDisk[1], "wb") as f:
            f.write(response.content)
    
    # Return the bytes
    return response.content

def __load_model__(Index: int) -> None:
    # Check if the model is loaded
    if (Index in list(__models__.keys()) and __models__[Index] is not None):
        return

    # Get info about the model
    info = cfg.GetInfoOfTask("chatbot", Index)
    device = cfg.GetAvailableGPUDeviceForTask("chatbot", Index) if (cfg.current_data["force_device_check"]) else info["device"]
    processor = None

    # Check if the model is multimodal
    if (len(info["multimodal"].strip()) == 0):
        # It isn't, return since this script ONLY supports multimodal models
        __models__[Index] = None
        return

    # Get threads and check if the number of threads are valid
    if (info["threads"] == -1):
        threads = psutil.cpu_count()
    elif (info["threads"] == -2):
        threads = None
    elif (info["threads"] <= 0 or info["threads"] > psutil.cpu_count()):
        raise Exception("Invalid number of threads.")
    else:
        threads = info["threads"]
    
    # Get batch threads and check if the number of batch threads are valid
    if (info["b_threads"] == -1):
        b_threads = psutil.cpu_count()
    elif (info["b_threads"] == -2):
        b_threads = threads
    elif (info["b_threads"] == -3):
        b_threads = None
    elif (info["b_threads"] <= 0 or info["b_threads"] > psutil.cpu_count()):
        raise Exception("Invalid number of b_threads.")
    else:
        b_threads = info["b_threads"]
    
    # Check if the batch size is valid
    if (info["batch"] <= 0):
        raise Exception("Invalid batch size.")
    
    # Check if the ubatch size is valid
    if (info["ubatch"] <= 0):
        raise Exception("Invalid ubatch size.")
    
    # Set model
    if (info["type"] == "hf"):
        # Use Transformers
        # Load the model
        model, processor, dev, dtype = hf.__load_model__(info, Index)
        
        # Get the chat template
        ct = processor.chat_template
        cts = len(processor.tokenize(ct))
    elif (info["type"] == "lcpp"):
        # Use LLaMA-CPP-Python
        # Print loading message
        print(f"Loading model for 'chatbot [INDEX {Index}]' on the device '{device}'...")

        # Load the model
        model = LCPP_LoadModel(info, threads, b_threads, device)
        
        # Get the chat template
        ct = model.metadata["tokenizer.chat_template"]
        cts = len(model.tokenize(ct.encode("utf-8")))
    else:
        raise Exception(f"Invalid chatbot type '{info['type']}'.")
    
    # Add the model to the list
    if (processor != None):
        # The model also includes a tokenizer, add it too
        __models__[Index] = ((model, processor, dev, dtype), info)
    else:
        # Add the model only
        __models__[Index] = (model, info)
    
    # Fill the ctx if needed
    if ("fill_ctx_at_start" in list(info.keys()) and info["fill_ctx_at_start"]):
        # Download sample files
        __download_sample_file__(
            "https://raw.githubusercontent.com/TAO71-AI/I4.0/refs/heads/main/Assets/Thumbnails/v15.0.0.png",
            (True, "multimodal_cb_sample_image.png")
        )
        __download_sample_file__(
            "https://cloud.video.taobao.com/vod/4szTT1B0LqXvJzmuEURfGRA-nllnqN_G2AT0ZWkQXoQ.mp4",
            (True, "multimodal_cb_sample_video.mp4")
        )
        __download_sample_file__(
            "https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/samples/HEARME.wav",
            (True, "multimodal_cb_sample_audio.wav")
        )
        files = []

        img = Image.open("multimodal_cb_sample_image.png")
        img = img.resize((128, 128))
        img.save("multimodal_cb_sample_image.png")
        img.close()

        if ("image" in info["multimodal"].strip().split(" ")):
            files.append({"type": "image", "data": "multimodal_cb_sample_image.png"})
        
        if ("video" in info["multimodal"].strip().split(" ")):
            files.append({"type": "video", "data": "multimodal_cb_sample_video.mp4"})
        
        if ("audio" in info["multimodal"].strip().split(" ")):
            files.append({"type": "audio", "data": "multimodal_cb_sample_audio.wav"})

        # Do inference
        response = Inference(Index, "a " * (info["ctx"] - cts - 1), files, [], [], ["", ""], 1, None, None, None, None, None, True)

        # Wait for it to respond
        for token in response:
            pass

def __offload_model__(Index: int) -> None:
    # Check the index is valid
    if (Index not in list(__models__.keys())):
        # Not valid, return
        return
    
    # Offload the model
    if (isinstance(__models__[Index][0], tuple)):
        __models__[Index] = None
    
    # Delete from the models list
    __models__.pop(Index)

def LoadModels() -> None:
    # For each model of this service
    for i in range(len(cfg.GetAllInfosOfATask("chatbot"))):
        # Check if the model is already loaded
        if (i in list(__models__.keys())):
            continue
        
        # Load the model and add it to the list of models
        __load_model__(i)

def Inference(
        Index: int,
        Prompt: str,
        Files: list[dict[str, str | bytes]],
        SystemPrompts: list[str],
        Tools: list[dict[str, str | dict[str, any]]],
        Conversation: list[str] = ["", ""],
        MaxLength: int | None = None,
        Temperature: float | None = None,
        TopP: float | None = None,
        TopK: int | None = None,
        MinP: float | None = None,
        TypicalP: float | None = None,
        Reasoning: str | int | bool | None = None,
        ToolsInSystemPrompt: bool = False
    ) -> Iterator[tuple[str, list[dict[str, any]]]]:
    # Load the model
    __load_model__(Index)

    # Get the data from the files
    files = []

    for file in Files:
        if (isinstance(file["data"], str)):
            with open(file["data"], "rb") as f:
                files.append({
                    "type": file["type"],
                    file["type"]: f"data:{file['type']};base64,{base64.b64encode(f.read()).decode('utf-8')}"
                })
        elif (isinstance(file["data"], bytes)):
            files.append({
                "type": file["type"],
                file["type"]: f"data:{file['type']};base64,{base64.b64encode(file['data']).decode('utf-8')}"
            })
        else:
            # Invalid file type, raise an error
            raise Exception(f"Invalid file type '{type(file['data'])}' for file '{file['name']}'.")

    # Strip the prompt and set the system prompts
    Prompt = Prompt.strip()
    SystemPrompts = "\n".join(SystemPrompts).strip()

    # Set extra kwargs variable
    extraKwargs = {}

    # Set extra kwargs
    if ("extra_kwargs" in list(__models__[Index][1].keys())):
        for kw_n, kw_v in __models__[Index][1]["extra_kwargs"].values():
            extraKwargs[kw_n] = kw_v

    # Set reasoning
    if ("reasoning" in list(__models__[Index][1].keys())):
        # Get all the reasoning variables
        rKW, rSP, rUP = GetReasoningMode(__models__[Index][1], Reasoning)
        
        # Append all the kwargs
        for kw_n, kw_v in rKW.values():
            extraKwargs[kw_n] = kw_v
        
        # Set the system prompt
        SystemPrompts = rSP.replace("[SYSTEM PROMPT]", SystemPrompts)

        # Set the user prompt
        Prompt = rUP.replace("[USER PROMPT]", Prompt)

    # Create the content for the model with the system prompts
    contentForModel = [{"role": "system", "content": SystemPrompts}]

    # Get the conversation of the user
    conversation = conv.GetConversation(Conversation[0], Conversation[1]).copy()

    # For each message in the conversation
    for msg in conversation:
        # Get the role and content
        role = msg["role"]
        content = msg["content"]

        # Get the file data
        msgFiles = []

        for mF in content:
            # Check if the file type
            if (mF["type"] in __models__[Index][1]["multimodal"].strip().split(" ")):
                # Add as a file
                msgFiles.append({"type": mF["type"], mF["type"]: f"data:{mF['type']};base64,{mF[mF['type']][5:]}"})
            elif (mF["type"] == "text"):
                # Add as a text
                msgFiles.append({"type": mF["type"], mF["type"]: mF[mF["type"]]})

        # Append the message in the new template to contentForModel
        contentForModel.append({"role": role, "content": msgFiles})

    contentForModel.append({"role": "user", "content": files + [{"type": "text", "text": Prompt}]})

    # Set the seed
    if ("seed" in list(__models__[Index][1].keys())):
        seed = __models__[Index][1]["seed"]

        if (seed is not None and seed < 0):
            seed = None
    else:
        seed = None
    
    # Set the maximum length
    if (MaxLength is None):
        if ("max_length" in list(__models__[Index][1].keys())):
            maxLength = __models__[Index][1]["max_length"]

            if (maxLength is None or maxLength <= 0):
                maxLength = cfg.current_data["max_length"]
        else:
            maxLength = cfg.current_data["max_length"]
    else:
        maxLength = MaxLength

        if (
            "max_length" in list(__models__[Index][1].keys()) and
            __models__[Index][1]["max_length"] is not None and
            __models__[Index][1]["max_length"] > 0 and
            maxLength > __models__[Index][1]["max_length"]
        ):
            maxLength = __models__[Index][1]["max_length"]

            if (maxLength is None or maxLength <= 0):
                maxLength = cfg.current_data["max_length"]
        elif (maxLength > cfg.current_data["max_length"]):
            maxLength = cfg.current_data["max_length"]
    
    # Set the temperature
    if (Temperature is None):
        temp = __models__[Index][1]["temp"] if ("temp" in list(__models__[Index][1].keys())) else 0.5
    else:
        temp = Temperature

    # Set top_p
    if (TopP is None):
        if ("top_p" in list(__models__[Index][1].keys()) and __models__[Index][1]["top_p"] is not None):
            TopP = __models__[Index][1]["top_p"]
        else:
            TopP = 0.95
    
    # Set top_k
    if (TopK is None):
        if ("top_k" in list(__models__[Index][1].keys()) and __models__[Index][1]["top_k"] is not None):
            TopK = __models__[Index][1]["top_k"]
        else:
            TopK = 40
    
    # Set min_p
    if (MinP is None):
        if ("min_p" in list(__models__[Index][1].keys()) and __models__[Index][1]["min_p"] is not None):
            MinP = __models__[Index][1]["min_p"]
        else:
            MinP = 0.05
    
    # Set typical_p
    if (TypicalP is None):
        if ("typical_p" in list(__models__[Index][1].keys()) and __models__[Index][1]["typical_p"] is not None):
            TypicalP = __models__[Index][1]["typical_p"]
        else:
            TypicalP = 1
    
    # Check if the tools must be in the system prompt
    if (
        (
            "tools_in_system_prompt" in list(__models__[Index][1].keys()) and __models__[Index][1]["tools_in_system_prompt"] or
            ToolsInSystemPrompt
        ) and len(Tools) > 0
    ):
        # Add the tools to the system prompt
        contentForModel[0]["content"] = f"Available tools:\n```json\n{json.dumps(Tools, indent = 4)}\n```\n\n---\n\n{contentForModel[0]['content']}"
        Tools = None
    elif (len(Tools) == 0):
        # No tools, set to None
        Tools = None
    
    # Get the model type to use
    if (isinstance(__models__[Index][0], tuple)):
        # Use HF
        return hf.__inference__(
            __models__[Index][0][0],
            __models__[Index][0][1],
            __models__[Index][0][2],
            __models__[Index][0][3],
            __models__[Index][1],
            contentForModel,
            seed,
            Tools,
            maxLength,
            temp,
            TopP,
            TopK,
            MinP,
            TypicalP,
            extraKwargs
        )
    elif (isinstance(__models__[Index][0], Llama)):
        # Use lcpp
        return lcpp.__inference__(
            __models__[Index][0],
            __models__[Index][1],
            contentForModel,
            seed,
            Tools,
            maxLength,
            temp,
            TopP,
            TopK,
            MinP,
            TypicalP,
            extraKwargs
        )
    else:
        # It's an invalid model type
        raise Exception("Invalid model.")