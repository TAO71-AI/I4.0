# NOTE: The next version will allow Image + Text to Text chatbots!!!!
# The next version will probably have some more options and configuration for the chatbot (like load_in_4bit or 8bit for `hf` chatbots)!!!
# The next version will focus on the chatbot and bug fixes.

# Import chatbots
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
from llama_cpp import Llama
from llama_cpp.llama_chat_format import hf_autotokenizer_to_chat_completion_handler
from gpt4all import GPT4All

# Import some other libraries
from collections.abc import Iterator
import psutil
import os
import threading

# Import I4.0's utilities
import ai_config as cfg
import ai_conversation as conv
import conversation_template as convTemp

__models__: list[tuple[GPT4All | Llama | tuple[AutoModelForCausalLM, AutoTokenizer, str], dict[str, any]]] = []
SystemPrompts: list[str] = []

def __load_model__(Index: int) -> None:
    device = cfg.GetAvailableGPUDeviceForTask("chatbot", Index)
    info = cfg.GetInfoOfTask("chatbot", Index)
    tokenizer = None

    # Get threads and check if the number of threads are valid
    if (info["threads"] == -1):
        threads = psutil.cpu_count() - 1
    elif (info["threads"] == -2):
        threads = None
    elif (info["threads"] <= 0 or info["threads"] > psutil.cpu_count() - 1):
        raise Exception("Invalid number of threads.")
    
    # Check if the batch size is valid
    if (info["batch"] <= 0):
        raise Exception("Invalid batch size.")
    
    # Set model
    if (info["type"] == "gpt4all"):
        # Use GPT4All
        # Get the device
        if (device != "cpu"):
            device = "gpu"

        # Load the model
        model = GPT4All(
            model_name = info["model"],
            model_path = info["model"] if (os.path.exists(info["model"]) and os.path.isfile(info["model"])) else None,
            allow_download = True,
            n_threads = threads,
            device = device,
            n_ctx = info["ctx"],
            ngl = info["ngl"],
            verbose = False
        )
    elif (info["type"] == "lcpp"):
        # Use Llama-CPP-Python
        # Check the model's chat template path
        if (len(info["model"][2].strip()) == 0):
            info["model"][2] = info["model"][0]

        # Check if the model is a local file
        if (os.path.exists(info["model"][1]) and os.path.isfile(info["model"][1])):
            # Load the model from the local file
            model = Llama(
                model_path = info["model"][1],
                n_ctx = info["ctx"],
                verbose = False,
                n_gpu_layers = info["ngl"] if (device != "cpu") else 0,
                n_batch = info["batch"],
                chat_handler = hf_autotokenizer_to_chat_completion_handler(info["model"][2]),
                logits_all = True,
                n_threads = threads,
                n_threads_batch = threads
            )
        else:
            # Load the model from the HuggingFace repository
            model = Llama.from_pretrained(
                repo_id = info["model"][0],
                filename = info["model"][1],
                n_ctx = info["ctx"],
                verbose = False,
                n_gpu_layers = info["ngl"] if (device != "cpu") else 0,
                n_batch = info["batch"],
                chat_handler = hf_autotokenizer_to_chat_completion_handler(info["model"][2]),
                logits_all = True,
                n_threads = threads,
                n_threads_batch = threads
            )
    elif (info["type"] == "hf"):
        # Use Transformers
        # Set the model and tokenizer
        model, tokenizer, dev = cfg.LoadModel("chatbot", Index, AutoModelForCausalLM, AutoTokenizer)
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

def Inference(Index: int, Prompt: str, Conversation: list[str] = ["", ""]) -> Iterator[str]:
    # Load the models
    LoadModels()

    # Strip the prompt
    Prompt = Prompt.strip()

    # Get the template to use
    contentToShow = convTemp.GetTemplate(Prompt, "".join([sp + "\n" for sp in SystemPrompts]), conv.GetConversation(Conversation[0], Conversation[1])).strip()
    contentForModel = __get_content__(Prompt, Conversation)
    response = ""

    # Print the prompt
    print(contentToShow + "\n### RESPONSE: ")
    
    # Get the model type to use
    if (type(__models__[Index][0]) == GPT4All):
        # Use GPT4All
        # Transform system prompts to a string
        sp = ""

        for p in contentForModel:
            if (p["role"] == "system"):
                sp += p["content"] + "\n"
        
        sp = sp.strip()

        # Inference the model
        with __models__[Index][0].chat_session(system_prompt = sp, prompt_template = "{0}\n### RESPONSE: "):
            # Get a response from the model
            response = __models__[Index][0].generate(
                prompt = convTemp.GetTemplate(Prompt, "", conv.GetConversation(Conversation[0], Conversation[1])),
                max_tokens = cfg.current_data["max_length"],
                temp = __models__[Index][1]["temp"],
                n_batch = __models__[Index][1]["batch"],
                streaming = True
            )

            # Print every token and yield it
            for token in response:
                print(token, end = "", flush = True)
                yield token
            
            # Print an empty message when done
            print("", flush = True)
    elif (type(__models__[Index][0]) == Llama):
        # Use Llama-CPP-Python
        # Get a response from the model
        response = __models__[Index][0].create_chat_completion(
            messages = contentForModel,
            temperature = __models__[Index][1]["temp"],
            max_tokens = cfg.current_data["max_length"],
            stream = True
        )

        # For every token
        for token in response:
            # Check if it's valid (contains a response)
            if (not "content" in token["choices"][0]["delta"]):
                continue
            
            # Print the token
            t = token["choices"][0]["delta"]["content"]
            print(t, end = "", flush = True)

            # Yield the token
            yield t
        
        # Print an empty message when done
        print("", flush = True)
    elif (type(__models__[Index][0]) == tuple or type(__models__[Index][0]) == tuple[AutoModelForCausalLM, AutoTokenizer]):
        # Get the model
        model, tokenizer, dev = __models__[Index][0]

        # Apply the chat template using the tokenizer
        text = tokenizer.apply_chat_template(contentForModel, tokenize = False, add_generation_prompt = True)

        # Tokenize the prompt
        inputs = tokenizer([text], return_tensors = "pt").to(dev)

        # Set streamer
        streamer = TextIteratorStreamer(tokenizer)

        # Set inference args
        generationKwargs = dict(
            inputs,
            temperature = __models__[Index][1]["temp"],
            max_new_tokens = cfg.current_data["max_length"],
            streamer = streamer,
            do_sample = True
        )

        # Create new thread for the model and generate
        generationThread = threading.Thread(target = model.generate, kwargs = generationKwargs)
        generationThread.start()

        # For each token
        for token in streamer:
            # Ignore if it's the same as the input
            if (token == text):
                continue

            # Cut the response
            if (token.count("<|im_end|>")):
                token = token[:token.index("<|im_end|>")]

            if (token.count("<|im_start|>")):
                token = token[token.index("<|im_start|>") + 12:]

            # Print the token and yield it
            print(token, end = "", flush = True)
            yield token
        
        # Print an empty message when done
        print("", flush = True)
    else:
        # It's an invalid model type
        raise Exception("Invalid model.")

def __get_content__(Prompt: str, Conversation: list[str]) -> str | list[dict[str, str]]:
    # Set the content var
    content = []

    # Check if the system prompts are more than 0
    if (len(SystemPrompts) > 0):
        # Add the system prompts to the content
        content.append({"role": "system", "content": "".join([p.strip() + "\n" for p in SystemPrompts]).strip()})

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
            con[con.index(c)]["content"] = ""

            # Ignore this message
            continue

        # Add the message to the content list
        content.append({"role": pRole, "content": pContent})
    
    # Add the user's prompt to the content list
    content.append({"role": "user", "content": Prompt})

    # Return the content list
    return content