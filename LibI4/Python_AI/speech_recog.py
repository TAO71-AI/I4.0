import speech_recognition as sr
import whisper
import os
import torch
import ai_config as cfg

recognizer = sr.Recognizer()

def Recognize(data: sr.AudioData) -> str:
    try:
        audio_name = "tmp_whisper_audio_0.wav"
        audio_id = 0

        while (os.path.exists(audio_name)):
            audio_id += 1
            audio_name = "tmp_whisper_audio_" + str(audio_id) + ".wav"
        
        with open(audio_name, "wb") as f:
            f.write(data.get_wav_data())
            f.close()

        whisper_model = whisper.load_model(cfg.current_data.whisper_model, device = "cuda" if (cfg.current_data.use_gpu_if_available and cfg.current_data.move_to_gpu.__contains__("whisper") and torch.cuda.is_available()) else "cpu")
        result = whisper_model.transcribe(audio_name)["text"]

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