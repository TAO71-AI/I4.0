from transformers import AutoModelForTextToWaveform, AutoProcessor
import soundfile as sf
import os
import ai_config as cfg

__models__: list[tuple[AutoModelForTextToWaveform, AutoProcessor, str]] = []

def LoadModels() -> None:
    # For each model
    for i in range(len(cfg.GetAllInfosOfATask("text2audio"))):
        # Check if the model is already loaded
        if (i < len(__models__)):
            continue
        
        # Load the model and add it to the list of models
        model, processor, device = cfg.LoadModel("text2audio", i, AutoModelForTextToWaveform, AutoProcessor)
        __models__.append((model, processor, device))

def GenerateAudio(Index: int, Prompt: str) -> bytes:
    # Load the models
    LoadModels()

    # Cut the prompt
    if (Prompt.startswith("\"") or Prompt.startswith("'")):
        Prompt = Prompt[1:]
    
    if (Prompt.endswith("\"") or Prompt.endswith("'")):
        Prompt = Prompt[:-1]

    # Tokenize the prompt
    inputs = __models__[Index][1](text = [Prompt], return_tensors = "pt").to(__models__[Index][2])

    # Inference the model
    result = __models__[Index][0].generate(**inputs, do_sample = True)
    
    # Save the audio into a temporal file
    audio_name = "ta.wav"
    audio_n = 0

    while (os.path.exists(audio_name)):
        audio_n += 1
        audio_name = "ta_" + str(audio_n) + ".wav"

    sf.write(audio_name, result.cpu().numpy().squeeze(), __models__[Index][0].generation_config.sample_rate)

    # Read the bytes of the saved audio
    with open(audio_name, "rb") as f:
        audio = f.read()
        f.close()

    # Delete the temporal file
    os.remove(audio_name)

    # Return the bytes of the generated audio file
    return audio