from transformers import Pipeline
from pydub import AudioSegment
import speech_recognition as sr
import torch
import whisper
import os
import ai_config as cfg

__models__: dict[int, tuple[whisper.Whisper | Pipeline, dict[str, any]]] = {}

def LoadModels() -> None:
    # For each model of this service
    for i in range(len(cfg.GetAllInfosOfATask("speech2text"))):
        # Check if the model is already loaded
        if (i in list(__models__.keys())):
            continue

        # Get the model info
        info = cfg.GetInfoOfTask("speech2text", i)

        # Check the model type
        if (info["type"] == "whisper"):
            # Load the model using whisper
            # Get device to use
            device = cfg.GetAvailableGPUDeviceForTask("speech2text", i)

            # Load the model
            print(f"Loading Whisper model on the device '{device}'.")
            print("Warning! Using the `whisper` option doesn't allow batch size.")

            model = whisper.load_model(
                name = info["model"],
                device = device,
                in_memory = True
            )

            # Set dtype
            try:
                # Get the desired dtype
                dt = cfg.__get_dtype_from_str__(info["dtype"])

                # Check dtype
                #if (dt == torch.float16 or dt == torch.bfloat16 or dt == torch.int16 or dt == torch.uint16):
                #    print("Invalid quantization.")
                #    raise Exception()
                #elif (dt == torch.float32 or dt == torch.int32 or dt == torch.uint32):
                #    dt = torch.qint32
                #elif (dt == torch.int8):
                #    dt = torch.qint8
                #elif (dt == torch.uint8):
                #    dt = torch.quint8

                # Quantize the model, encoder and decoder to the desired dtype
                model = torch.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype = dt)
                model.encoder = torch.quantization.quantize_dynamic(model.encoder, {torch.nn.Linear}, dtype = dt)
                model.decoder = torch.quantization.quantize_dynamic(model.decoder, {torch.nn.Linear}, dtype = dt)
            except:
                # Ignore
                pass

            print("   Done!")
        elif (info["type"] == "hf"):
            # Load the model using transformers
            model, _ = cfg.LoadPipeline("automatic-speech-recognition", "speech2text", i)
        else:
            # Invalid model type
            raise Exception("Invalid model type.")
        
        # Add the model to the list of models
        __models__[i] = (model, info)

def __offload_model__(Index: int) -> None:
    # Check the index is valid
    if (Index not in list(__models__.keys())):
        # Not valid, return
        return
    
    # Offload the model
    __models__[Index] = None
    
    # Delete from the models list
    __models__.pop(Index)

def Inference(Index: int, Data: sr.AudioData) -> dict[str, str]:
    # Load the models
    LoadModels()

    # Create temporal file
    audio_name = "tmp_whisper_audio_0.wav"
    audio_id = 0

    while (os.path.exists(audio_name)):
        audio_id += 1
        audio_name = "tmp_whisper_audio_" + str(audio_id) + ".wav"
        
    with open(audio_name, "wb") as f:
        f.write(Data.get_wav_data())
    
    # Check the model type
    if (type(__models__[Index][0]) == whisper.Whisper):
        # Use whisper
        # Inference the model
        result = __models__[Index][0].transcribe(audio_name, temperature = __models__[Index][1]["temp"], verbose = True)

        # Set the result
        result = {
            "text": result["text"],
            "lang": result["language"],
        }
    else:
        # Use transformers
        # Inference the model
        result = __models__[Index][0](audio_name)

        # Set the result
        result = {
            "text": result["text"],
            "lang": "unknown"
        }
    
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