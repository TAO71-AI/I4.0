# Import I4.0 utilities
import ai_config as cfg

# Import `hf` text2audio library
import Inference.Audio.Text2Audio.hf as t2a_hf
import Inference.Audio.Text2Audio.kokoro as t2a_kkr

# Import other libraries
from collections.abc import Iterator
from kokoro import KPipeline
from transformers import AutoModelForTextToWaveform, AutoProcessor

__models__: dict[int, tuple[tuple[AutoModelForTextToWaveform, AutoProcessor, str, str] | KPipeline, dict[str, any]] | None] = {}

def __load_model__(Index: int) -> None:
    # Check if the model is already loaded
    if (Index in list(__models__.keys()) and __models__[Index] is not None):
        return
    
    # Get configuration
    config = cfg.GetInfoOfTask("text2audio", Index)
    
    # Check and load the model type
    if (config["type"] == "hf"):
        model, processor, device, dtype = t2a_hf.LoadModel(Index)
        model = (model, processor, device, dtype)
    elif (config["type"] == "kokoro"):
        model = t2a_kkr.LoadModel(Index, config)
    else:
        raise RuntimeError("Unknown text2audio type.")
        
    # Append the model to the list of models
    __models__[Index] = (model, config)

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

def GenerateAudio(Index: int, Prompt: str) -> Iterator[bytes]:
    # Load the model
    __load_model__(Index)

    # Inference the model
    if (__models__[Index][1]["type"] == "hf"):
        yield t2a_hf.InferenceModel(Prompt, __models__[Index][0][0], __models__[Index][0][1], __models__[Index][0][2], __models__[Index][0][3])
    elif (__models__[Index][1]["type"] == "kokoro"):
        try:
            # Try to convert the prompt to a JSON
            Prompt = cfg.JSONDeserializer(Prompt)
            prompt = Prompt["prompt"]
            voice = Prompt["voice"] if ("voice" in list(Prompt.keys())) else None
            speed = Prompt["speed"] if ("voice" in list(Prompt.keys())) else None
        except:
            prompt = Prompt
            voice = None
            speed = None

        # Get the response
        response = t2a_kkr.Inference(__models__[Index][0], __models__[Index][1], prompt, voice, speed)

        # Yield all the tokens
        for token in response:
            yield token
    else:
        raise RuntimeError("Unknown text2audio type.")