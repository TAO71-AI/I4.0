from transformers import AutoTokenizer, AutoModelForTextToWaveform
import torch
import os
import ai_config as cfg

model: AutoModelForTextToWaveform = None
tokenizer: AutoTokenizer = None

def __load_model__(model_name: str, device: str):
    model = AutoModelForTextToWaveform.from_pretrained(model_name)
    model.to(device)
        
    return model

def LoadModel() -> None:
    global model, tokenizer

    if (model != None and tokenizer != None):
        return
    
    move_to_gpu = torch.cuda.is_available() and cfg.current_data.use_gpu_if_available and cfg.current_data.move_to_gpu.__contains__("hf")
    device = "cuda" if (move_to_gpu) else "cpu"

    if (cfg.current_data.print_loading_message):
        print("Loading model 'chatbot (hf)' on device '" + device + "'...")
    
    tokenizer = AutoTokenizer.from_pretrained(cfg.current_data.text_to_audio_model)
    model = __load_model__(cfg.current_data.text_to_audio_model, device)

def GenerateAudio(prompt: str) -> bytes:
    LoadModel()

    if (prompt.startswith("\"") or prompt.startswith("'")):
        prompt = prompt[1:len(prompt)]
    
    if (prompt.endswith("\"") or prompt.endswith("'")):
        prompt = prompt[0:len(prompt) - 2]

    input_ids = tokenizer.encode(prompt, return_tensors = "pt")
    audio = model.generate(input_ids, max_new_tokens = cfg.current_data.max_length)

    audio_name = "ta.png"
    audio_n = 0

    while (os.path.exists(audio_name)):
        audio_n += 1
        audio_name = "ta_" + str(audio_n) + ".png"

    with open(audio_name, "w+") as f:
        f.close()
    
    audio.save(audio_name)

    with open(audio_name, "rb") as f:
        audio = f.read()
        f.close()

    os.remove(audio_name)
    return audio