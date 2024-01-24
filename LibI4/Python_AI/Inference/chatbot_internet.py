from transformers import AutoTokenizer, AutoModelForQuestionAnswering, TFAutoModelForQuestionAnswering
import requests
import torch
from bs4 import BeautifulSoup
import ai_config as cfg

model_name: str = cfg.current_data.internet_model
low_cpu_or_memory: bool = cfg.current_data.low_cpu_or_memory
websites: list[tuple[bool, str, int, str]] = [
    (False, "localhost", 80, "Datasets/webdata.php"),
    (False, "147.78.87.113", 120, "Datasets/webdata.php")
]

model: AutoModelForQuestionAnswering | TFAutoModelForQuestionAnswering = None
tokenizer: AutoTokenizer = None
device: str = "cpu"

def __load_model__(model_name: str, device: str):
    if (cfg.current_data.use_tf_instead_of_pt):
        return TFAutoModelForQuestionAnswering.from_pretrained(model_name)
    else:
        model = AutoModelForQuestionAnswering.from_pretrained(model_name).to(device)
        return model

def LoadModel() -> None:
    global model, tokenizer, device

    if (not cfg.current_data.prompt_order.__contains__("int")):
        raise Exception("Model is not in 'prompt_order'.")
        
    if (model != None and tokenizer != None):
        return
    
    move_to_gpu = cfg.current_data.use_gpu_if_available and torch.cuda.is_available() and cfg.current_data.move_to_gpu.__contains__("int")
    device = "cuda" if (move_to_gpu) else "cpu"

    if (cfg.current_data.print_loading_message):
        print("Loading model 'chatbot (internet)' on device '" + device + "'...")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = __load_model__(model_name, device)

def MakePrompt(prompt: str) -> str:
    LoadModel()

    # Get internet data
    internet_data = ""

    for website in websites:
        website_url = ("https:" if website[0] else "http:") + "//" + website[1] + ":" + str(website[2]) + "/" + website[3]
        req_response = requests.get(website_url)

        if (req_response.status_code == 200):
            idata = req_response.text
            idata = BeautifulSoup(internet_data, "html.parser")
            idl = idata.find_all("p")
            int_data = ""

            for p in idl:
                int_data += str(p).replace("<p>", "").replace("</p>", "") + "\n"
                
            if (len(int_data.strip()) > 0):
                internet_data = int_data
                break
    
    if (len(internet_data.strip()) == 0):
        raise Exception("ERROR: Internet data length is 0.")

    # Question answering with the internet data
    input_ids = tokenizer.encode(prompt, internet_data, return_tensors = ("tf" if cfg.current_data.use_tf_instead_of_pt else "pt"))

    if (not cfg.use_tf_instead_of_pt):
        input_ids = input_ids.to(device)

    output = model.generate(input_ids, max_new_tokens = cfg.current_data.max_length)
    response = tokenizer.decode(output[0], skip_special_tokens = True)

    return response