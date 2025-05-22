# Import I4.0 utilities
import ai_config as cfg

# Import other libraries
import soundfile as sf
from io import BytesIO
from transformers import AutoModelForTextToWaveform, AutoProcessor

def LoadModel(Index: int) -> tuple[AutoModelForTextToWaveform, AutoProcessor, str, str]:
    # Load and return the model
    return cfg.LoadModel("text2audio", Index, AutoModelForTextToWaveform, AutoProcessor)

def InferenceModel(Prompt: str, Model: AutoModelForTextToWaveform, Processor: AutoProcessor, Device: str, Dtype: str) -> bytes:
    # Tokenize the prompt
    inputs = Processor(text = [Prompt], return_tensors = "pt").to(Device).to(Dtype)

    # Inference the model
    result = Model.generate(**inputs, do_sample = True)
    
    # Save the audio into a buffer
    buffer = BytesIO()
    sf.write(buffer, result.cpu().numpy().squeeze(), Model.generation_config.sample_rate, format = "WAV")

    buffer.seek(0)
    data = buffer.getvalue()
    
    buffer.close()

    # Return the data
    return data