import speech_recognition as sr
import whisper
import os
import ai_config as cfg

recognizer: sr.Recognizer = sr.Recognizer()
device: str = "cpu"
whisperM: whisper.Whisper | None = None

def LoadModel() -> None:
    global device, whisperM
    
    if (cfg.current_data["models"].count("speech2text") == 0):
        raise Exception("Model is not in 'models'.")

    if (whisperM != None):
        return
    
    device = cfg.GetAvailableGPUDeviceForTask("speech2text")
    whisperM = whisper.load_model(cfg.current_data["whisper_model"], device, None, False)

def Recognize(data: sr.AudioData) -> dict[str, str]:
    LoadModel()
    
    result = {
        "text": "",
        "lang": "",
        "error": ""
    }

    try:
        audio_name = "tmp_whisper_audio_0.wav"
        audio_id = 0

        while (os.path.exists(audio_name)):
            audio_id += 1
            audio_name = "tmp_whisper_audio_" + str(audio_id) + ".wav"
        
        with open(audio_name, "wb") as f:
            f.write(data.get_wav_data())
            f.close()
        
        result = whisperM.transcribe(audio_name, temperature = cfg.current_data["temp"])
        result = {
            "text": result["text"],
            "lang": result["language"],
            "error": ""
        }

        os.remove(audio_name)
    except sr.UnknownValueError:
        result = {
            "text": "",
            "lang": "",
            "error": "Could not recognize audio."
        }
    except sr.RequestError as ex:
        result = {
            "text": "",
            "lang": "",
            "error": "Error requesting: " + str(ex)
        }
    except Exception as ex:
        result = {
            "text": "",
            "lang": "",
            "error": "Unknown exception: " + str(ex)
        }
    
    return result

def GetMicrophoneAudioData(timeout = None, phase_time_limit = None) -> sr.AudioData:
    with sr.Microphone() as source:
        return recognizer.listen(source, timeout = timeout, phrase_time_limit = phase_time_limit)

def FileToAudioData(audio_path: str) -> sr.AudioData:
    with sr.AudioFile(audio_path) as source:
        return recognizer.record(source)