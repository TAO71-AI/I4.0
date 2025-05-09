# Import I4.0 utilities
import ai_config as cfg

# Import other libraries
from io import BytesIO
from transformers import AutoModelForTextToWaveform, AutoProcessor
import soundfile as sf

__models__: dict[int, tuple[AutoModelForTextToWaveform, AutoProcessor, str, str]] = {}

def __load_model__(Index: int) -> None:
    # Check if the model is already loaded
    if (Index in list(__models__.keys()) and __models__[Index] is not None):
        return
        
    # Load the model and add it to the list of models
    model, processor, device, dtype = cfg.LoadModel("text2audio", Index, AutoModelForTextToWaveform, AutoProcessor)
    __models__[Index] = (model, processor, device, dtype)

def LoadModels() -> None:
    # For each model
    for i in range(len(cfg.GetAllInfosOfATask("text2audio"))):
        __load_model__(i)

def __offload_model__(Index: int) -> None:
    # Check the index is valid
    if (Index not in list(__models__.keys()) or __models__[Index] is None):
        # Not valid, return
        return
    
    # Offload the model
    __models__[Index] = None
    
    # Delete from the models list
    __models__.pop(Index)

def GenerateAudio(Index: int, Prompt: str) -> bytes:
    # Load the model
    __load_model__(Index)

    # Cut the prompt
    if (Prompt.startswith("\"") or Prompt.startswith("'")):
        Prompt = Prompt[1:]
    
    if (Prompt.endswith("\"") or Prompt.endswith("'")):
        Prompt = Prompt[:-1]

    # Tokenize the prompt
    inputs = __models__[Index][1](text = [Prompt], return_tensors = "pt").to(__models__[Index][2]).to(__models__[Index][3])

    # Inference the model
    result = __models__[Index][0].generate(**inputs, do_sample = True)
    
    # Save the audio into a buffer
    buffer = BytesIO()
    sf.write(buffer, result.cpu().numpy().squeeze(), __models__[Index][0].generation_config.sample_rate, format = "WAV")

    buffer.seek(0)
    data = buffer.getvalue()
    
    buffer.close()

    # Return the bytes of the generated audio file
    return data