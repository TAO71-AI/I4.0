import speech_recognition as sr
import whisper
import os
import torch
import json
import ai_config as cfg

recognizer: sr.Recognizer = sr.Recognizer()
device: str = "cpu"
whisper_model: whisper.Whisper = None

def __load_model__(model: str, device: str) -> None:
    global whisper_model
    whisper_model = whisper.load_model(model, device = device)

def LoadModel() -> None:
    global device

    device = "cuda" if (cfg.current_data.use_gpu_if_available and cfg.current_data.move_to_gpu.__contains__("whisper") and torch.cuda.is_available()) else "cpu"
    __load_model__(cfg.current_data.whisper_model, device)

def Recognize(data: sr.AudioData) -> str:
    if (not cfg.current_data.prompt_order.__contains__("whisper")):
        raise Exception("Model is not loaded in 'prompt_order'.")

    try:
        audio_name = "tmp_whisper_audio_0.wav"
        audio_id = 0

        while (os.path.exists(audio_name)):
            audio_id += 1
            audio_name = "tmp_whisper_audio_" + str(audio_id) + ".wav"
        
        with open(audio_name, "wb") as f:
            f.write(data.get_wav_data())
            f.close()
        
        result = whisper_model.transcribe(audio_name, temperature = cfg.current_data.temp)
        result = {
            "text": result["text"],
            "lang": result["language"]
        }
        result = json.dumps(result)

        if (cfg.current_data.print_prompt):
            print("RESULT FROM WHISPER: " + str(result))

        os.remove(audio_name)
        return result
    except sr.UnknownValueError:
        return "Audio could not be recognized."
    except sr.RequestError as ex:
        return "Error requesting: " + str(ex)
    except Exception as ex:
        return "Unknown exception: " + str(ex)

def GetMicrophoneAudioData(timeout = None, phase_time_limit = None) -> sr.AudioData:
    with sr.Microphone() as source:
        return recognizer.listen(source, timeout = timeout, phrase_time_limit = phase_time_limit)

def FileToAudioData(audio_path: str) -> sr.AudioData:
    with sr.AudioFile(audio_path) as source:
        return recognizer.record(source)