# Import libraries
from transformers import Pipeline
from pydub import AudioSegment
import speech_recognition as sr
import os
import whisper

# Import I4.0 utilities
import Inference.Audio.SpeechRecognition.whisper_lib as whisperl
import ai_config as cfg

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

def Inference(Index: int, Data: sr.AudioData) -> dict[str, str]:
    # Load the model
    __load_model__(Index)

    # Create temporal file
    audio_name = "tmp_whisper_audio_0.wav"
    audio_id = 0

    while (os.path.exists(audio_name)):
        audio_id += 1
        audio_name = "tmp_whisper_audio_" + str(audio_id) + ".wav"
        
    with open(audio_name, "wb") as f:
        f.write(Data.get_wav_data())
    
    # Check the model type
    if (isinstance(__models__[Index][0], whisper.Whisper)):
        # Use whisper (library)
        result = whisperl.Inference(__models__[Index][0], audio_name, __models__[Index][1]["temp"])
    elif (isinstance(__models__[Index][0], Pipeline)):
        # Use transformers
        # Inference the model
        result = __models__[Index][0](audio_name)

        # Set the result
        result = {
            "text": result["text"],
            "lang": "unknown"
        }
    else:
        # Invalid model type
        raise Exception("Invalid model type.")
    
    # Return the result
    return result

def GetAudioDataFromFile(FilePath: str) -> sr.AudioData:
    # Convert to wav
    audio: AudioSegment = AudioSegment.from_file(FilePath)
    audio.export(FilePath, format = "wav")

    # Open the file
    with sr.AudioFile(FilePath) as source:
        # Return the audio data
        return sr.Recognizer().record(source)