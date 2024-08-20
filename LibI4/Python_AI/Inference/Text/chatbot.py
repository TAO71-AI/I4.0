# Import chatbots
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
from llama_cpp import Llama
from llama_cpp.llama_chat_format import hf_autotokenizer_to_chat_completion_handler
import gpt4all

# Import some other libraries
from typing import Iterator
import psutil
import os
import threading

# Import I4.0's chatbot utilities
import ai_config as cfg
import ai_conversation as conv
import conversation_template as convTemp

Device: str = "cpu"
Model: gpt4all.GPT4All | Llama | tuple[AutoModelForCausalLM, AutoTokenizer] | None = None
SystemPrompts: list[str] = []

def LoadModel() -> None:
    global Model, Device

    if (cfg.current_data["models"].count("chatbot") == 0):
        raise Exception("Model is not in 'models'.")

    if (Model != None):
        return

    threads = cfg.current_data["chatbot"]["threads"]
    path = __get_model_path__(False)
    Device = cfg.GetAvailableGPUDeviceForTask("chatbot")

    print(f"Loading model for 'chatbot' on the device '{Device}'...")

    if (threads == -1):
        threads = psutil.cpu_count() - 1
    elif (threads == -2):
        threads = None
    elif (threads <= 0 or threads > psutil.cpu_count() - 1):
        raise Exception("Invalid number of threads.")
    
    if (cfg.current_data["chatbot"]["batch"] <= 0):
        raise Exception("Invalid batch size.")

    if (cfg.current_data["chatbot"]["type"] == "gpt4all"):
        if (Device != "cpu"):
            Device = "gpu"
        
        print("   Using chatbot 'GPT4All'...")

        if (os.path.exists(path) and os.path.isfile(path)):
            Model = gpt4all.GPT4All(
                model_name = path,
                model_path = path,
                allow_download = True,
                n_threads = threads,
                device = Device,
                n_ctx = cfg.current_data["chatbot"]["ctx"],
                ngl = cfg.current_data["chatbot"]["ngl"],
                verbose = False
            )
        else:
            Model = gpt4all.GPT4All(
                model_name = path,
                allow_download = True,
                n_threads = threads,
                device = Device,
                n_ctx = cfg.current_data["chatbot"]["ctx"],
                ngl = cfg.current_data["chatbot"]["ngl"],
                verbose = False
            )
    elif (cfg.current_data["chatbot"]["type"] == "lcpp"):
        if (len(path[2].strip()) == 0):
            path[2] = path[0]
        
        print("   Using chatbot 'LLaMA-CPP-Python'...")

        Model = Llama.from_pretrained(
            repo_id = path[0],
            filename = path[1],
            n_ctx = cfg.current_data["chatbot"]["ctx"],
            verbose = False,
            n_gpu_layers = cfg.current_data["chatbot"]["ngl"] if (Device != "cpu") else 0,
            n_batch = cfg.current_data["chatbot"]["batch"],
            chat_handler = hf_autotokenizer_to_chat_completion_handler(path[2]),
            logits_all = True,
            n_threads = threads,
            n_threads_batch = threads
        )
        Device = "Unknown"
    elif (cfg.current_data["chatbot"]["type"] == "hf"):
        print("   Using chatbot 'HuggingFace (Transformers)'...")
        model, tokenizer, dev = cfg.LoadModel("chatbot", cfg.current_data["chatbot"]["hf"], AutoModelForCausalLM, AutoTokenizer)

        Model = (model, tokenizer)
        Device = dev
    else:
        raise Exception("Invalid chatbot type.")

def ProcessPrompt(Prompt: str, Conversation: list[str] = ["", ""]) -> Iterator[str]:
    LoadModel()
    Prompt = Prompt.strip()

    contentToShow = convTemp.GetTemplate(Prompt, "".join([sp + "\n" for sp in SystemPrompts]), conv.GetConversation(Conversation[0], Conversation[1])).strip()
    contentForModel = __get_content__(Prompt, Conversation)
    response = ""

    print(contentToShow + "\n### RESPONSE: ")
    
    if (type(Model) == gpt4all.GPT4All):
        sp = ""

        for p in contentForModel:
            if (p["role"] == "system"):
                sp += p + "\n"
        
        sp = sp.strip()

        with Model.chat_session(system_prompt = sp, prompt_template = "{0}\n### RESPONSE: "):
            response = Model.generate(
                prompt = contentToShow,
                max_tokens = cfg.current_data["max_length"],
                temp = cfg.current_data["chatbot"]["temp"],
                n_batch = cfg.current_data["chatbot"]["batch"],
                streaming = True
            )

            for token in response:
                print(token, end = "", flush = True)
                yield token
                
            print("", flush = True)
    elif (type(Model) == Llama):
        response = Model.create_chat_completion(
            messages = contentForModel,
            temperature = cfg.current_data["chatbot"]["temp"],
            max_tokens = cfg.current_data["max_length"],
            stream = True
        )

        for token in response:
            if (not "content" in token["choices"][0]["delta"]):
                continue

            t = token["choices"][0]["delta"]["content"]
            print(t, end = "", flush = True)

            yield t
        
        print("", flush = True)
    elif (type(Model) == tuple or type(Model) == tuple[AutoModelForCausalLM, AutoTokenizer]):
        model, tokenizer = Model
        text = tokenizer.apply_chat_template(contentForModel, tokenize = False, add_generation_prompt = True)
        inputs = tokenizer([text], return_tensors = "pt").to(Device)
        streamer = TextIteratorStreamer(tokenizer)
        generationKwargs = dict(
            inputs,
            temperature = cfg.current_data["chatbot"]["temp"],
            max_new_tokens = cfg.current_data["max_length"],
            streamer = streamer,
            do_sample = True
        )

        generationThread = threading.Thread(target = model.generate, kwargs = generationKwargs)
        generationThread.start()

        for token in streamer:
            if (token == text):
                continue

            if (token.count("<|im_end|>")):
                token = token[:token.index("<|im_end|>")]

            if (token.count("<|im_start|>")):
                token = token[token.index("<|im_start|>") + 12:]

            print(token, end = "", flush = True)
            yield token
        
        print("", flush = True)
    else:
        raise Exception("Invalid model.")

def __get_content__(Prompt: str, Conversation: list[str]) -> str | list[dict[str, str]]:
    if (cfg.current_data["chatbot"]["type"] == "gpt4all"):
        return conv.ConversationToStr(Conversation[0], Conversation[1])

    content = []

    if (len(SystemPrompts) > 0):
        content.append({"role": "system", "content": "".join([p.strip() + "\n" for p in SystemPrompts]).strip()})

    con = conv.GetConversation(Conversation[0], Conversation[1])

    for c in con:
        pRole = c["role"]
        pContent = c["content"]

        if (con.index(c) - 1 >= 0 and pRole == con[con.index(c) - 1]["role"]):
            con[con.index(c) - 1]["content"] += "\n" + pContent
            con[con.index(c)]["content"] = ""
            continue

        content.append({"role": pRole, "content": pContent})
        
    content.append({"role": "user", "content": Prompt})
    return content

def __get_model_path__(ForceSTR: bool) -> str | list[str]:
    if (cfg.current_data["chatbot"]["type"] == "gpt4all" or cfg.current_data["chatbot"]["type"] == "hf"):
        return cfg.current_data["chatbot"][cfg.current_data["chatbot"]["type"]]
    elif (cfg.current_data["chatbot"]["type"] == "lcpp"):
        if (ForceSTR):
            return cfg.current_data["chatbot"]["lcpp"][0] + "/" + cfg.current_data["chatbot"]["lcpp"][1]
        
        return cfg.current_data["chatbot"]["lcpp"]
    else:
        raise Exception("Invalid chatbot type.")