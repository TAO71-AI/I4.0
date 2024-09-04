from transformers import Pipeline
import speech_recognition as sr
import whisper
import os
import ai_config as cfg

__models__: list[tuple[whisper.Whisper | Pipeline, dict[str, any]]] = []

def LoadModels() -> None:
    # For each model of this service
    for i in range(len(cfg.GetAllInfosOfATask("speech2text"))):
        # Check if the model is already loaded
        if (i < len(__models__)):
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

            print("   Done!")
        elif (info["type"] == "hf"):
            # Load the model using transformers
            model, _ = cfg.LoadPipeline("automatic-speech-recognition", "speech2text", i)
        else:
            # Invalid model type
            raise Exception("Invalid model type.")
        
        # Add the model to the list of models
        __models__.append((model, info))

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
        f.close()
    
    # Check the model type
    if (__models__[Index][1]["type"] == "whisper"):
        # Use whisper
        # Inference the model
        result = __models__[Index][0].transcribe(audio_name, temperature = __models__[Index][1]["temp"])

        # Set the result
        result = {
            "text": result["text"],
            "lang": result["language"],
        }
    elif (__models__[Index][1]["type"] == "hf"):
        # Use transformers
        # Inference the model
        result = __models__[Index][0](audio_name)

        # Set the result
        result = {
            "text": result["text"],
            "lang": result["language"],
        }
    
    # Return the result
    return result

def GetAudioDataFromFile(FilePath: str) -> sr.AudioData:
    # Open the file
    with sr.AudioFile(FilePath) as source:
        # Return the audio data
        return sr.Recognizer().record(source)