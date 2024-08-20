from transformers import Pipeline
import soundfile as sf
import os
import ai_config as cfg

model_pipeline: Pipeline | None = None

def LoadModel() -> None:
    global model_pipeline

    if (cfg.current_data["models"].count("text2audio") == 0):
        raise Exception("Model is not in 'models'.")

    if (model_pipeline != None):
        return

    data = cfg.LoadPipeline("text-to-audio", "text2audio", cfg.current_data["text_to_audio_model"])
    model_pipeline = data[0]

def GenerateAudio(prompt: str) -> bytes:
    LoadModel()

    if (prompt.startswith("\"") or prompt.startswith("'")):
        prompt = prompt[1:len(prompt)]
    
    if (prompt.endswith("\"") or prompt.endswith("'")):
        prompt = prompt[0:len(prompt) - 2]

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