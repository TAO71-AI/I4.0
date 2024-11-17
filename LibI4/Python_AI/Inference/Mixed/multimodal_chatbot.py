# Import HuggingFace chatbot
from transformers import AutoModelForVision2Seq, AutoProcessor
import Inference.Mixed.MultimodalChatbot.hf as hf

# Import some other libraries
from collections.abc import Iterator
import psutil
import os

# Import I4.0's utilities
import ai_config as cfg
import conversation_multimodal as conv

__models__: list[tuple[tuple[AutoModelForVision2Seq, AutoProcessor, str], dict[str, any]]] = []

def __load_model__(Index: int) -> None:
    info = cfg.GetInfoOfTask("chatbot", Index)
    device = cfg.GetAvailableGPUDeviceForTask("chatbot", Index) if (cfg.current_data["force_device_check"]) else info["device"]
    processor = None

    # Check if the model allows files
    if (not info["allows_files"]):
        # It doesn't, return since this script ONLY allows files
        __models__.append(None)
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
    
    # Check if the batch size is valid
    if (info["batch"] <= 0):
        raise Exception("Invalid batch size.")
    
    # Set model
    if (info["type"] == "hf"):
        # Use Transformers
        # Load the model
        model, processor, dev = hf.__load_model__(info, Index)
    else:
        raise Exception("Invalid chatbot type.")
    
    # Add the model to the list
    if (processor != None):
        # The model also includes a tokenizer, add it too
        __models__.append(((model, processor, dev), info))
    else:
        # Add the model only
        __models__.append((model, info))

def LoadModels() -> None:
    # For each model of this service
    for i in range(len(cfg.GetAllInfosOfATask("chatbot"))):
        # Check if the model is already loaded
        if (i < len(__models__)):
            continue
        
        # Load the model and add it to the list of models
        __load_model__(i)

def Inference(Index: int, Prompt: str, Files: list[dict[str, str]], SystemPrompts: list[str], Conversation: list[str] = ["", ""]) -> Iterator[str]:
    # Load the models
    LoadModels()

    # Get the data from the files
    files = []

    for file in Files:
        with open(file["data"], "rb") as f:
            files.append({
                "type": file["type"],
                file["type"]: f"file://{os.getcwd()}/{file['data']}"
                #file["type"]: f"data:{file['type']};base64,{base64.b64encode(f.read()).decode("utf-8")}"
            })

    # Strip the prompt and set the system prompts
    Prompt = Prompt.strip()
    SystemPrompts = "".join(sp + "\n" for sp in SystemPrompts).strip()

    # Create the content for the model with the system prompts
    contentForModel = [{"role": "system", "content": [{"type": "text", "text": SystemPrompts}]}]

    # Get the conversation of the user
    conversation = conv.GetConversationFromUser(Conversation[0], True)

    # For each message in the conversation
    for msg in range(conversation.GetLengthOfConversation(Conversation[1])):
        # Get the file data
        msgFileData = conversation.GetFromID(Conversation[1], msg)
        msgFiles = []

        for mF in msgFileData["content"]:
            # Check if the file type
            if (mF["type"] in ["audio", "image", "video"]):
                # Add as a file
                msgFiles.append({"type": mF["type"], mF["type"]: f"data:{mF['type']};base64,{mF[mF['type']][5:]}"})
            else:
                # Add as a text
                msgFiles.append({"type": mF["type"], mF["type"]: mF[mF["type"]]})

        # Append the message in the new template to contentForModel
        contentForModel.append({
            "role": msgFileData["role"],
            "content": msgFiles
        })

    # Set the prompt that will be displayed
    contentToShow = "### Conversation:\n"

    for msg in contentForModel:
        # Find the text message in the conversation
        textMsg = ""

        # For each message in the content
        for m in msg["content"]:
            # Check if the type is text
            if (m["type"] == "text"):
                textMsg = m["text"]
                break

        if (msg["role"] == "user"):
            contentToShow += f"User: {textMsg}\n"
        elif (msg["role"] == "assistant"):
            contentToShow += f"Assistant: {textMsg}\n"

    contentForModel.append({"role": "user", "content": [file for file in files] + [{"type": "text", "text": Prompt}]})
    contentToShow += f"\n\n### USER: {Prompt}"

    # Print the prompt
    print(f"### SYSTEM PROMPT:\n{SystemPrompts}\n\n{contentToShow}\n### RESPONSE:")
    
    # Get the model type to use
    if (type(__models__[Index][0]) == tuple or type(__models__[Index][0]) == tuple[AutoModelForVision2Seq, AutoProcessor, str]):
        # Use HF
        return hf.__inference__(__models__[Index][0][0], __models__[Index][0][1], __models__[Index][0][2], __models__[Index][1], contentForModel)
    else:
        # It's an invalid model type
        raise Exception("Invalid model.")