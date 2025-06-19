# Import libraries
from io import BytesIO
import torch
import whisper
import numpy as np
import soundfile as sf

def LoadModel(ModelName: str, Dtype: torch.dtype, Device: str) -> whisper.Whisper:
    # Load the model
    print(f"Loading Whisper model on the device '{Device}'.")
    print("Warning! Using the `whisper` option doesn't allow batch size.")

    model = whisper.load_model(
        name = ModelName,
        device = Device,
        in_memory = True
    )

    # Set dtype
    try:
        # Check dtype
        if (Dtype == torch.float32):
            pass
        elif (Dtype == torch.int32 or Dtype == torch.uint32):
            Dtype = torch.qint32
        elif (Dtype == torch.int8):
            Dtype = torch.qint8
        elif (Dtype == torch.uint8):
            Dtype = torch.quint8
        elif (Dtype is not None):
            raise ValueError("Invalid dtype.")

        # Quantize the model, encoder and decoder to the desired dtype
        model = torch.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype = Dtype)
        model.encoder = torch.quantization.quantize_dynamic(model.encoder, {torch.nn.Linear}, dtype = Dtype)
        model.decoder = torch.quantization.quantize_dynamic(model.decoder, {torch.nn.Linear}, dtype = Dtype)
    except:
        # Ignore
        pass

    print("   Done!")

    # Return the model
    return model

def Inference(Model: whisper.Whisper, AudioPath: str | BytesIO | bytes, Temperature: float) -> dict[str, str]:
    # Convert the audio
    if (isinstance(AudioPath, bytes)):
        AudioPath = BytesIO(AudioPath)
    
    if (isinstance(AudioPath, BytesIO)):
        AudioPath.seek(0)
        AudioPath, _ = sf.read(AudioPath)

    # Inference the model
    result = Model.transcribe(AudioPath, temperature = Temperature, verbose = True)

    # Set the result
    result = {
        "text": result["text"],
        "lang": result["language"]
    }

    # Return the result
    return result