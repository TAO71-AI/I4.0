# Import HuggingFace chatbot
from transformers import AutoModelForImageTextToText, AutoProcessor
import Inference.Mixed.MultimodalChatbot.hf as hf

# Import some other libraries
from collections.abc import Iterator
import psutil
import base64

# Import I4.0's utilities
import ai_config as cfg
import conversation_multimodal as conv

__models__: dict[int, tuple[tuple[AutoModelForImageTextToText, AutoProcessor, str, str], dict[str, any]]] = {}

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
    
    # Check if the batch size is valid
    if (info["batch"] <= 0):
        raise Exception("Invalid batch size.")
    
    # Set model
    if (info["type"] == "hf"):
        # Use Transformers
        # Load the model
        model, processor, dev, dtype = hf.__load_model__(info, Index)
    else:
        raise Exception(f"Invalid chatbot type '{info['type']}'.")
    
    # Add the model to the list
    if (processor != None):
        # The model also includes a tokenizer, add it too
        __models__[Index] = ((model, processor, dev, dtype), info)
    else:
        # Add the model only
        __models__[Index] = (model, info)

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
        Files: list[dict[str, str]],
        SystemPrompts: list[str],
        Tools: list[dict[str, str | dict[str, any]]],
        Conversation: list[str] = ["", ""],
        MaxLength: int | None = None,
        Temperature: float | None = None,
        TopP: float | None = None,
        TopK: int | None = None
    ) -> Iterator[tuple[str, list[dict[str, any]]]]:
    # Load the model
    __load_model__(Index)

    # Get the data from the files
    files = []

    for file in Files:
        with open(file["data"], "rb") as f:
            files.append({
                "type": file["type"],
                file["type"]: f"data:{file['type']};base64,{base64.b64encode(f.read()).decode('utf-8')}"
            })

    # Strip the prompt and set the system prompts
    Prompt = Prompt.strip()
    SystemPrompts = "".join(sp + "\n" for sp in SystemPrompts).strip()

    # Create the content for the model with the system prompts
    contentForModel = [{"role": "system", "content": [{"type": "text", "text": SystemPrompts}]}]

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

    contentForModel.append({"role": "user", "content": files + [{"type": "text", "text": Prompt}]})
    contentToShow += f"\n\n### USER: {Prompt}"

    # Set the maximum length
    if (MaxLength is None):
        try:
            # Get the max length
            maxLength = __models__[Index][1]["max_length"]

            # Check the max length
            if (maxLength is None or maxLength <= 0):
                # Invalid max length, set to the server's default
                maxLength = cfg.current_data["max_length"]
        except:
            # Error; probably `max_length` is not configured. Set to the server's default
            maxLength = cfg.current_data["max_length"]
    else:
        # Set max length to the user's config
        maxLength = MaxLength

        try:
            # Check if max length is greater than the model's max length
            if (maxLength > __models__[Index][1]["max_length"]):
                # Set max length to the model's max length
                maxLength = __models__[Index][1]["max_length"]

                # Check the max length
                if (maxLength is None or maxLength <= 0):
                    # Invalid max length, set to the server's default
                    maxLength = cfg.current_data["max_length"]
        except:
            # Error; probably `max_length` is not configured. Check if max length is greater than the servers's max length
            if (maxLength > cfg.current_data["max_length"]):
                # Set max length to the server's max length
                maxLength = cfg.current_data["max_length"]
    
    # Set the temperature
    if (Temperature is None):
        temp = __models__[Index][1]["temp"]
    else:
        temp = Temperature
    
    # Set top_p
    if (TopP is None):
        TopP = 0.95
    
    # Set top_k
    if (TopK is None):
        TopK = 40

    # Print the prompt
    print(f"### SYSTEM PROMPT:\n{SystemPrompts}\n\n{contentToShow}\n### RESPONSE:")
    
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
            maxLength,
            temp,
            TopP,
            TopK
        )
    else:
        # It's an invalid model type
        raise Exception("Invalid model.")