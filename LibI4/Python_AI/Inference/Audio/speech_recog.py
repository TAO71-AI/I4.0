# Import I4.0 utilities
import Inference.Audio.SpeechRecognition.whisper_lib as whisperl
import ai_config as cfg

# Import other libraries
from io import BytesIO
from pydub import AudioSegment
from transformers import Pipeline
import whisper
import speech_recognition as sr

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

def Inference(Index: int, Data: bytes | sr.AudioData) -> dict[str, str]:
    # Load the model
    __load_model__(Index)

    # Convert audio data into bytes
    if (isinstance(Data, sr.AudioData)):
        Data = Data.get_wav_data()

    # Save data into a buffer
    data = BytesIO(Data)
    data.seek(0)
    
    # Check the model type
    if (isinstance(__models__[Index][0], whisper.Whisper)):
        # Use whisper (library)
        result = whisperl.Inference(__models__[Index][0], data, __models__[Index][1]["temp"])
    elif (isinstance(__models__[Index][0], Pipeline)):
        # Use transformers
        # Inference the model
        result = __models__[Index][0](data)

        # Set the result
        result = {
            "text": result["text"],
            "lang": "unknown"
        }
    else:
        # Invalid model type
        data.close()
        raise Exception("Invalid model type.")
    
    # Return the result
    data.close()
    return result

def GetAudioDataFromFile(FilePath: str) -> sr.AudioData:
    # Convert to wav
    audio: AudioSegment = AudioSegment.from_file(FilePath)
    audio.export(FilePath, format = "wav")

    # Open the file
    with sr.AudioFile(FilePath) as source:
        # Return the audio data
        return sr.Recognizer().record(source)