# Import I4.0 utilities
import Inference.Audio.SpeechRecognition.whisper_lib as whisperl
import temporal_files as tempFiles
import ai_config as cfg

# Import other libraries
from io import BytesIO
from pydub import AudioSegment
from transformers import Pipeline
import whisper
import os

__models__: dict[int, tuple[whisper.Whisper | Pipeline, dict[str, any]]] = {}

def __load_model__(Index: int) -> None:
    # Check if the model is already loaded
    if (Index in list(__models__.keys()) and __models__[Index] is not None):
        return

    # Get the model info
    info = cfg.GetInfoOfTask("speech2text", Index)

    # Check the model type
    if (info["type"] == "whisper"):
        # Load the model using whisper (library)
        # Get device to use
        device = cfg.GetAvailableGPUDeviceForTask("speech2text", Index)

        # Get the desired dtype
        dt = cfg.__get_dtype_from_str__(info["dtype"])

        # Get the model
        model = whisperl.LoadModel(info["model"], dt, device)
    elif (info["type"] == "hf"):
        # Load the model using transformers
        model, _ = cfg.LoadPipeline("automatic-speech-recognition", "speech2text", Index)
    else:
        # Invalid model type
        raise Exception("Invalid model type.")
        
    # Add the model to the list of models
    __models__[Index] = (model, info)

def LoadModels() -> None:
    # For each model of this service
    for i in range(len(cfg.GetAllInfosOfATask("speech2text"))):
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

def Inference(Index: int, Data: bytes) -> dict[str, str]:
    # Load the model
    __load_model__(Index)

    # Convert to WAV
    ConvertToWAV(Data)

    # Save data into a buffer
    data = BytesIO(Data)
    data.seek(0)
    
    # Check the model type
    if (isinstance(__models__[Index][0], whisper.Whisper)):
        # Use whisper (library)
        result = whisperl.Inference(__models__[Index][0], data, __models__[Index][1]["temp"])
    elif (isinstance(__models__[Index][0], Pipeline)):
        # Use transformers
        # Save the buffer into a temporal file
        dataInput = tempFiles.CreateTemporalFile("wav", data.getvalue())

        # Inference the model
        result = __models__[Index][0](dataInput, return_timestamps = True)

        # Set the result
        result = {
            "text": result["text"],
            "lang": "unknown"
        }

        # Remove the temporal file
        os.remove(dataInput)
    else:
        # Invalid model type
        data.close()
        raise Exception("Invalid model type.")
    
    # Return the result
    data.close()
    return result

def ConvertToWAV(Data: bytes) -> bytes:
    # Create a buffer from the data
    inputBuffer = BytesIO(Data)

    # Convert the data to WAV format
    audio = AudioSegment.from_file(inputBuffer)
    
    # Export the audio to WAV format
    outputBuffer = BytesIO()
    audio.export(outputBuffer, format = "wav")
    
    # Get the bytes from the output buffer
    output = outputBuffer.getvalue()

    # Close the buffers
    inputBuffer.close()
    outputBuffer.close()

    # Return the output
    return output