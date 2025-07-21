# Import I4.0 utilities
import ai_config as cfg
import conversation_multimodal as conv

# Import LLaMA-CPP-Python chatbot
from llama_cpp import Llama
from Inference.Mixed.MultimodalChatbot.lcpp_model import LoadModel as LCPP_LoadModel
import Inference.Text.Chatbot.lcpp as lcpp

# Import HuggingFace chatbot
from transformers import AutoModelForCausalLM, AutoTokenizer
import Inference.Text.Chatbot.hf as hf

# Import other libraries
from collections.abc import Iterator
import psutil
import json

__models__: dict[int, tuple[Llama | tuple[AutoModelForCausalLM, AutoTokenizer, str, str], dict[str, any]]] = {}

def __load_model__(Index: int) -> None:
    # Check if the model is loaded
    if (Index in list(__models__.keys()) and __models__[Index] is not None):
        return

    # Get info about the model
    info = cfg.GetInfoOfTask("chatbot", Index)
    device = cfg.GetAvailableGPUDeviceForTask("chatbot", Index) if (cfg.current_data["force_device_check"]) else info["device"]
    tokenizer = None

    # Check if the model is multimodal
    if (len(info["multimodal"].strip()) > 0):
        # It is, return since this script doesn't support multimodal models
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
    if (info["type"] == "lcpp"):
        # Use Llama-CPP-Python
        # Print loading message
        print(f"Loading model for 'chatbot [INDEX {Index}]' on the device '{device}'...")

        # Load the model
        model = LCPP_LoadModel(info, threads, b_threads, device)
    elif (info["type"] == "hf"):
        # Use Transformers
        # Load the model
        model, tokenizer, dev, dtype = hf.__load_model__(info, Index)
    else:
        raise Exception("Invalid chatbot type.")
    
    # Add the model to the list
    if (tokenizer != None):
        # The model also includes a tokenizer, add it too
        __models__[Index] = ((model, tokenizer, dev, dtype), info)
    else:
        # Add the model only
        __models__[Index] = (model, info)
    
    # Fill the ctx if needed
    if ("fill_ctx_at_start" in info and info["fill_ctx_at_start"]):
        # Do inference
        response = Inference(Index, "a " * (info["ctx"] - 15), [], [], ["", ""], None, None, None, None, None, None)

        # Wait for it to respond
        for token in response:
            pass

def __offload_model__(Index: int) -> None:
    # Check the index is valid
    if (Index not in list(__models__.keys()) or __models__[Index] is None):
        # Not valid, return
        return
    
    # Offload the model
    if (type(__models__[Index][0]) == Llama):
        __models__[Index][0].close()
    elif (type(__models__[Index][0]) == tuple or type(__models__[Index][0]) == tuple[AutoModelForCausalLM, AutoTokenizer, str, str]):
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
        SystemPrompts: list[str],
        Tools: list[dict[str, str | dict[str, any]]],
        Conversation: list[str] = ["", ""],
        MaxLength: int | None = None,
        Temperature: float | None = None,
        TopP: float | None = None,
        TopK: int | None = None,
        MinP: float | None = None,
        TypicalP: float | None = None,
    ) -> Iterator[str]:
    # Load the model
    __load_model__(Index)

    # Strip the prompt and set the system prompts
    Prompt = Prompt.strip()
    SystemPrompts = "".join(f"{sp}\n" for sp in SystemPrompts).strip()

    # Create the content for the model with the system prompts
    contentForModel = [{"role": "system", "content": SystemPrompts}]

    # Get the conversation of the user
    conversation = conv.GetConversation(Conversation[0], Conversation[1]).copy()

    # For each message in the conversation
    for msg in conversation:
        # Get the role and content
        role = msg["role"]
        content = msg["content"]
        text = ""

        # For each message in the content
        for cont in content:
            # Check the content type
            if (cont["type"] != "text"):
                # Invalid, continue
                continue

            # Add the content text to the text
            text += cont["text"] + "\n"
        
        # Cut the text
        if (text.endswith("\n")):
            text = text[:-1]

        # Append the message in the old template to contentForModel
        contentForModel.append({"role": role, "content": text})
    
    # Append the user prompt
    contentForModel.append({"role": "user", "content": Prompt})

    # Set the seed
    try:
        # Get the seed
        seed = __models__[Index][1]["seed"]

        # Check the seed
        if (seed < 0):
            # Invalid seed, set to None
            seed = None
    except:
        # Error; probably `seed` is not configured. Set to None
        seed = None
    
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
        try:
            TopP = __models__[Index][1]["top_p"]

            if (TopP == None):
                raise Exception()
        except:
            TopP = 0.95
    
    # Set top_k
    if (TopK is None):
        try:
            TopK = __models__[Index][1]["top_k"]

            if (TopK == None):
                raise Exception()
        except:
            TopK = 40
    
    # Set min_p
    if (MinP is None):
        try:
            MinP = __models__[Index][1]["min_p"]

            if (MinP == None):
                raise Exception()
        except:
            MinP = 0.05
    
    # Set typical_p
    if (TypicalP is None):
        try:
            TypicalP = __models__[Index][1]["typical_p"]

            if (TypicalP == None):
                raise Exception()
        except:
            TypicalP = 1
    
    # Check if the tools must be in the system prompt
    if ("tools_in_system_prompt" in list(__models__[Index][1].keys()) and __models__[Index][1]["tools_in_system_prompt"] and len(Tools) > 0):
        # Add the tools to the system prompt
        contentForModel[0]["content"] = f"Available tools:\n```json\n{json.dumps(Tools, indent = 4)}\n```\n\n---\n\n{contentForModel[0]['content']}"
        Tools = None
    elif (len(Tools) == 0):
        # No tools, set to None
        Tools = None
    
    # Get the model type to use
    if (isinstance(__models__[Index][0], Llama)):
        # Use Llama-CPP-Python
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
            TypicalP
        )
    elif (isinstance(__models__[Index][0], tuple) or isinstance(__models__[Index][0], list)):
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
            TypicalP
        )
    else:
        # It's an invalid model type
        raise Exception("Invalid model.")