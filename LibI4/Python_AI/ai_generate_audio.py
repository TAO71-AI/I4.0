from transformers import AutoProcessor, AutoModel, TFAutoModel
import torch
import os
import ai_config as cfg

model: AutoModel | TFAutoModel = None
processor: AutoProcessor = None
device: str = "cpu"

def __load_model__(model_name: str, device: str):
    if (cfg.current_data.use_tf_instead_of_pt):
        return TFAutoModel.from_pretrained(model_name)
    
    model = AutoModel.from_pretrained(model_name).to(device)
    return model

def LoadModel() -> None:
    global model, processor, device

    if (model != None and processor != None):
        return
    
    move_to_gpu = torch.cuda.is_available() and cfg.current_data.use_gpu_if_available and cfg.current_data.move_to_gpu.__contains__("text2audio")
    device = "cuda" if (move_to_gpu) else "cpu"

    if (cfg.current_data.print_loading_message):
        print("Loading model 'text to audio' on device '" + device + "'...")
    
    processor = AutoProcessor.from_pretrained(cfg.current_data.text_to_audio_model)
    model = __load_model__(cfg.current_data.text_to_audio_model, device)

def GenerateAudio(prompt: str) -> bytes:
    LoadModel()

    if (prompt.startswith("\"") or prompt.startswith("'")):
        prompt = prompt[1:len(prompt)]
    
    if (prompt.endswith("\"") or prompt.endswith("'")):
        prompt = prompt[0:len(prompt) - 2]

    input_ids = processor([processor], return_tensors = ("tf" if cfg.current_data.use_tf_instead_of_pt else "pt"))

    if (not cfg.current_data.use_tf_instead_of_pt):
        input_ids = input_ids.to(device)

    audio = model.generate(**input_ids, do_sample = True)
    
    audio_name = "ta.wav"
    audio_n = 0

    while (os.path.exists(audio_name)):
        audio_n += 1
        audio_name = "ta_" + str(audio_n) + ".wav"

    with open(audio_name, "w+") as f:
        f.close()
    
    audio.save(audio_name)

    with open(audio_name, "rb") as f:
        audio = f.read()
        f.close()

    os.remove(audio_name)
    return audio