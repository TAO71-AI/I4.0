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
import ai_conversation as conv
import conversation_template as convTemp

__models__: list[tuple[GPT4All | Llama | tuple[AutoModelForCausalLM, AutoTokenizer, str], dict[str, any]]] = []

def __load_model__(Index: int) -> None:
    info = cfg.GetInfoOfTask("chatbot", Index)
    device = cfg.GetAvailableGPUDeviceForTask("chatbot", Index) if (cfg.current_data["force_device_check"]) else info["device"]
    tokenizer = None

    # Check if the model allows files
    if (info["allows_files"]):
        # It does, return since this script doesn't allows files
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
        model = lcpp.__load_model__(info, threads, device)
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

    # Strip the prompt
    Prompt = Prompt.strip()

    # Get the template to use
    contentToShow = convTemp.GetTemplate(Prompt, "".join([sp + "\n" for sp in SystemPrompts])[:-1], conv.GetConversation(Conversation[0], Conversation[1]), False).strip()
    contentForModel = __get_content__(Prompt, Conversation, SystemPrompts)

    # Print the prompt
    print(contentToShow + "\n### RESPONSE: ")
    
    # Get the model type to use
    if (type(__models__[Index][0]) == GPT4All):
        # Use GPT4All
        # Get the conversation
        convT = convTemp.GetTemplate(Prompt, "", conv.GetConversation(Conversation[0], Conversation[1]), False)

        # Return the response
        return g4a.__inference__(__models__[Index][0], __models__[Index][1], contentForModel, convT)
    elif (type(__models__[Index][0]) == Llama):
        # Use Llama-CPP-Python
        return lcpp.__inference__(__models__[Index][0], __models__[Index][1], contentForModel)
    elif (type(__models__[Index][0]) == tuple or type(__models__[Index][0]) == tuple[AutoModelForCausalLM, AutoTokenizer, str]):
        # Use HF
        return hf.__inference__(__models__[Index][0][0], __models__[Index][0][1], __models__[Index][0][2], __models__[Index][1], contentForModel)
    else:
        # It's an invalid model type
        raise Exception("Invalid model.")

def __get_content__(Prompt: str, Conversation: list[str], SystemPrompts: list[str]) -> list[dict[str, str]]:
    # Set the content var
    content = []

    # Check if the system prompts are more than 0
    if (len(SystemPrompts) > 0):
        # Add the system prompts to the content
        content.append({"role": "system", "content": "".join([p.strip() + "\n" for p in SystemPrompts]).strip()[:-1]})

    # Get the conversation
    con = conv.GetConversation(Conversation[0], Conversation[1])

    # For each message of the conversation
    for c in con:
        # Get the role and content
        pRole = c["role"]
        pContent = c["content"]

        # Check if the role of the previous message is the same as this one
        if (con.index(c) - 1 >= 0 and pRole == con[con.index(c) - 1]["role"]):
            # It is, add this message to the previous one and delete this
            con[con.index(c) - 1]["content"] += "\n" + pContent

            # Delete this message
            con.remove(con[con.index(c)])

            # Ignore this message
            continue

        # Add the message to the content list
        content.append({"role": pRole, "content": pContent})
    
    # Add the user's prompt to the content list
    content.append({"role": "user", "content": Prompt})

    # Return the content list
    return content