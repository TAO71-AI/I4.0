# Import LLaMA-CPP-Python chatbot
from llama_cpp import Llama
import Inference.Text.Chatbot.lcpp as lcpp

# Import GPT4All chatbot
from gpt4all import GPT4All
import Inference.Text.Chatbot.g4a as g4a

# Import HuggingFace chatbot
from transformers import AutoModelForCausalLM, AutoTokenizer
import Inference.Text.Chatbot.hf as hf

# Import some other libraries
from collections.abc import Iterator
import psutil

# Import I4.0's utilities
import ai_config as cfg
import conversation_multimodal as conv

__models__: list[tuple[GPT4All | Llama | tuple[AutoModelForCausalLM, AutoTokenizer, str], dict[str, any]]] = []

def __load_model__(Index: int) -> None:
    info = cfg.GetInfoOfTask("chatbot", Index)
    device = cfg.GetAvailableGPUDeviceForTask("chatbot", Index) if (cfg.current_data["force_device_check"]) else info["device"]
    tokenizer = None

    # Check if the model allows files
    if (info["allows_files"]):
        # It does, return since this script doesn't allows files
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
    if (info["type"] == "gpt4all"):
        # Use GPT4All
        # Print loading message
        print(f"Loading model for 'chatbot [INDEX {Index}]' on the device '{device}'...")

        # Load the model
        model = g4a.__load_model__(info, threads, device)
    elif (info["type"] == "lcpp"):
        # Use Llama-CPP-Python
        # Print loading message
        print(f"Loading model for 'chatbot [INDEX {Index}]' on the device '{device}'...")

        # Load the model
        model = lcpp.LoadModel(info, threads, device)
    elif (info["type"] == "hf"):
        # Use Transformers
        # Load the model
        model, tokenizer, dev = hf.__load_model__(info, Index)
    else:
        raise Exception("Invalid chatbot type.")
    
    # Add the model to the list
    if (tokenizer != None):
        # The model also includes a tokenizer, add it too
        __models__.append(((model, tokenizer, dev), info))
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

def Inference(Index: int, Prompt: str, SystemPrompts: list[str], Conversation: list[str] = ["", ""]) -> Iterator[str]:
    # Load the models
    LoadModels()

    # Strip the prompt and set the system prompts
    Prompt = Prompt.strip()
    SystemPrompts = "".join(sp + "\n" for sp in SystemPrompts).strip()

    # Create the content for the model with the system prompts
    contentForModel = [{"role": "system", "content": SystemPrompts}]

    # Get the conversation of the user
    conversation = conv.GetConversationFromUser(Conversation[0], True)

    # For each message in the conversation
    for msg in range(conversation.GetLengthOfConversation(Conversation[1])):
        # Append the message in the old template to contentForModel
        contentForModel.append(conversation.GetFromID_Old(Conversation[1], msg))

    # Set the prompt that will be displayed (or passed to GPT4All)
    contentToShow = f"### Conversation:\n"

    for msg in contentForModel:
        if (msg["role"] == "user"):
            contentToShow += f"User: {msg['content']}\n"
        elif (msg["role"] == "assistant"):
            contentToShow += f"Assistant: {msg['content']}\n"
    
    contentForModel.append({"role": "user", "content": Prompt})
    contentToShow += f"\n\n### USER: {Prompt}"

    # Print the prompt
    print(f"### SYSTEM PROMPT:\n{SystemPrompts}\n\n{contentToShow}\n### RESPONSE:")
    
    # Get the model type to use
    if (type(__models__[Index][0]) == GPT4All):
        # Use GPT4All
        return g4a.__inference__(__models__[Index][0], __models__[Index][1], contentForModel, contentToShow)
    elif (type(__models__[Index][0]) == Llama):
        # Use Llama-CPP-Python
        return lcpp.__inference__(__models__[Index][0], __models__[Index][1], contentForModel)
    elif (type(__models__[Index][0]) == tuple or type(__models__[Index][0]) == tuple[AutoModelForCausalLM, AutoTokenizer, str]):
        # Use HF
        return hf.__inference__(__models__[Index][0][0], __models__[Index][0][1], __models__[Index][0][2], __models__[Index][1], contentForModel)
    else:
        # It's an invalid model type
        raise Exception("Invalid model.")