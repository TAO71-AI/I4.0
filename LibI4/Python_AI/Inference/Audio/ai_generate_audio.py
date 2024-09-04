from transformers import Pipeline
import soundfile as sf
import os
import ai_config as cfg

__models__: list[Pipeline] = []

def LoadModels() -> None:
    # For each model
    for i in range(len(cfg.GetAllInfosOfATask("text2audio"))):
        # Check if the model is already loaded
        if (i < len(__models__)):
            continue
        
        # Load the model and add it to the list of models
        model, _ = cfg.LoadPipeline("text-to-audio", "text2audio", i)
        __models__.append(model)

def GenerateAudio(Index: int, Prompt: str) -> bytes:
    # Load the models
    LoadModels()

    # Cut the prompt
    if (Prompt.startswith("\"") or Prompt.startswith("'")):
        Prompt = Prompt[1:]
    
    if (Prompt.endswith("\"") or Prompt.endswith("'")):
        Prompt = Prompt[0:-2]

    # Inference the model
    result = __models__[Index](Prompt)
    
    # Save the audio into a temporal file
    audio_name = "ta.wav"
    audio_n = 0

    while (os.path.exists(audio_name)):
        audio_n += 1
        audio_name = "ta_" + str(audio_n) + ".wav"

    sf.write(audio_name, result["audio"][0].T, result["sampling_rate"])

    # Read the bytes of the saved audio
    with open(audio_name, "rb") as f:
        audio = f.read()
        f.close()

    # Delete the temporal file
    os.remove(audio_name)

    # Return the bytes of the generated audio file
    return audio