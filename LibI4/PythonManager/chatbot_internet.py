from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import requests
import torch
from bs4 import BeautifulSoup
import translation as t
import ai_config as cfg

model_name: str = cfg.current_data.internet_model
low_cpu_or_memory: bool = cfg.current_data.low_cpu_or_memory
website_url: str = "http://147.78.87.113:120/Browser/index.php?auto=1&search="

model: AutoModelForSeq2SeqLM = None
tokenizer: AutoTokenizer = None

def LoadModel() -> None:
    global model, tokenizer

    if (cfg.current_data.prompt_order.__contains__("5")):
        t.LoadModels()

    if (model != None and tokenizer != None):
        return
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name, low_cpu_mem_usage = low_cpu_or_memory, trust_remote_code = True)

    move_to_gpu = cfg.current_data.use_gpu_if_available and torch.cuda.is_available() and cfg.current_data.move_to_gpu.__contains__("6")
    device = "cuda" if (move_to_gpu) else "cpu"

    model = model.to(device)

def MakePrompt(prompt: str) -> str:
    LoadModel()

    # Get internet data
    try:
        req_response = requests.get(website_url + prompt)

        if (req_response.status_code == 200):
            internet_data = req_response.text
            internet_data = BeautifulSoup(internet_data, "html.parser")
            idl = internet_data.find_all("p")
            internet_data = ""

            for p in idl:
                internet_data += str(p).replace("<p>", "").replace("</p>", "") + "\n"
        else:
            raise Exception("Response status isn't 200.")
    except:
        return "ERROR"
    
    # Translate received data to english if available
    if (cfg.current_data.prompt_order.__contains__("5")):
        internet_data = t.TranslateFrom1To2(internet_data)

    # Summarization
    input_ids = tokenizer.encode(internet_data, return_tensors = "pt", truncation = True)
    output = model.generate(input_ids, max_new_tokens = cfg.current_data.max_length)
    response = tokenizer.decode(output[0], skip_special_tokens = True)

    return response