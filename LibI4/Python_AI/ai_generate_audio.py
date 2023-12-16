from transformers import pipeline, Pipeline
import soundfile as sf
import torch
import os
import ai_config as cfg

model_pipeline: Pipeline = None

def __load_model__(model_name: str, device: str):
    model = pipeline("text-to-audio", model_name, device = device)
    return model

def LoadModel() -> None:
    global model_pipeline

    if (not cfg.current_data.prompt_order.__contains__("text2audio")):
        raise Exception("Model is not in 'prompt_order'.")

    if (model_pipeline != None):
        return
    
    move_to_gpu = torch.cuda.is_available() and cfg.current_data.use_gpu_if_available and cfg.current_data.move_to_gpu.__contains__("text2audio")
    device = "cuda" if (move_to_gpu) else "cpu"

    if (cfg.current_data.print_loading_message):
        print("Loading model 'text to audio' on device '" + device + "'...")
    
    model_pipeline = __load_model__(cfg.current_data.text_to_audio_model, device)

def GenerateAudio(prompt: str) -> bytes:
    LoadModel()

    if (prompt.startswith("\"") or prompt.startswith("'")):
        prompt = prompt[1:len(prompt)]
    
    if (prompt.endswith("\"") or prompt.endswith("'")):
        prompt = prompt[0:len(prompt) - 2]
    
    if (cfg.current_data.print_prompt):
        print("AUDIO GENERATION: " + prompt)

    result = model_pipeline(prompt)
    
    audio_name = "ta.wav"
    audio_n = 0

    while (os.path.exists(audio_name)):
        audio_n += 1
        audio_name = "ta_" + str(audio_n) + ".wav"

    sf.write(audio_name, result["audio"][0].T, result["sampling_rate"])

    with open(audio_name, "rb") as f:
        audio = f.read()
        f.close()

    os.remove(audio_name)
    return audio