# Import I4.0 utilities
import ai_config as cfg

# Import other libraries
from kokoro import KPipeline, KModel
from collections.abc import Iterator
from io import BytesIO
import soundfile as sf
import torch
import os

__global_kmodel__: KModel | None = None

def LoadModel(Index: int, Config: dict[str, any] | None = None) -> KPipeline:
    # Define globals
    global __global_kmodel__

    # Make sure the config is not None
    if (Config is None):
        Config = cfg.GetInfoOfTask("text2audio", Index)
    
    # Get device
    dev = cfg.GetAvailableGPUDeviceForTask("text2audio", Index)

    # Set the dtype
    if ("dtype" in list(Config.keys())):
        dtype = cfg.__get_dtype_from_str__(Config["dtype"])

        # Make sure the dtype is valid
        if (dtype is None):
            raise RuntimeError("Invalid dtype.")
    else:
        dtype = cfg.__get_dtype_from_str__("fp32")

    # Load the model
    if (__global_kmodel__ is None):
        # Print note
        print(f"No global kokoro model set; creating.", flush = True)

        # Create model
        __global_kmodel__ = KModel(repo_id = Config["model"]).to(device = dev, dtype = dtype).eval()
        model = __global_kmodel__
    elif (str(__global_kmodel__.device) != dev + (":0" if (dev != "cpu" and ":" not in dev) else "") or next(__global_kmodel__.parameters()).dtype != dtype):
        # Model device or dtype doesn't match the ones in the global kokoro model. Create new kokoro model instance.
        # Print note
        print(f"Kokoro global model device and dtype is '{__global_kmodel__.device} / {next(__global_kmodel__.parameters()).dtype}', while the device and dtype in the config is '{dev} / {dtype}'. A new instance will be created.", flush = True)

        # Create model
        model = KModel(repo_id = Config["model"]).to(device = dev, dtype = dtype).eval()
    else:
        # Both the device and dtype match the ones in the global kokoro model. Use global kokoro model
        # Print note
        print("Using global kokoro model.", flush = True)
        model = __global_kmodel__

    # Create the pipeline
    pipe = KPipeline(lang_code = Config["lang"], repo_id = Config["model"], model = model, device = dev)

    # Return the pipeline
    return pipe

def Inference(Pipe: KPipeline, Config: dict[str, any], Prompt: str, Voice: str | None = None, Speed: float | None = None) -> Iterator[bytes]:
    # Set custom voice model
    if ("custom_voice_model" in list(Config.keys()) and (Voice is None or Voice.lower() == "custom")):
        # Make sure the custom voice model exists
        if (not os.path.exists(Config["custom_voice_model"])):
            raise FileNotFoundError("Custom voice model doesn't exists.")
        
        # Load the custom voice model
        Voice = (torch.load(Config["custom_voice_model"], weights_only = True), True)
    elif (Voice is None):
        raise RuntimeError("No voice set. Please set a voice for TTS.")
    else:
        Voice = (Voice, False)
    
    # Set speed
    if ("default_speed" in list(Config.keys()) and Speed is None):
        Speed = Config["default_speed"]
    elif (Speed is None):
        Speed = 1
    elif (round(Speed, 2) <= 0):
        raise RuntimeError("Speed can't be less than 0, 0, or to near to 0.")

    # Inference the pipeline
    response = Pipe(text = Prompt, voice = Voice[0], speed = Speed)

    # For each token
    for (_, _, audio) in response:
        # Create buffer for the audio
        buffer = BytesIO()

        # Write the audio in the buffer
        sf.write(buffer, audio, 24000, format = "WAV", subtype = "PCM_16")

        # Get the buffer bytes
        bbytes = buffer.getvalue()

        # Close the buffer
        buffer.close()

        # Yield the audio bytes
        yield bbytes
    
    # Unload the voice tensors if a custom model is set
    if (Voice[1]):
        Voice[0] = None