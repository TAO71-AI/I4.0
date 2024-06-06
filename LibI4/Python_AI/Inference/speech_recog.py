import speech_recognition as sr
import whisper
import os
import ai_config as cfg

recognizer: sr.Recognizer = sr.Recognizer()
device: str = "cpu"
whisperM: whisper.Whisper = None

def LoadModel() -> None:
    global device, whisperM

    if (len(cfg.devices) == 0):
        cfg.__get_gpu_devices__()
    
    if (whisperM != None):
        return
    
    if (cfg.current_data.print_loading_message):
        print("Loading model 'whisper'...")

    for i in range(len(cfg.devices)):
        dev = cfg.GetAvailableGPUDeviceForTask("whisper", i)
        
        try:
            whisperM = whisper.load_model(cfg.current_data.whisper_model, dev, None, False)
            device = dev

            if (cfg.current_data.print_loading_message):
                print("   Loaded model on device '" + device + "'.")

            return
        except:
            pass
    
    raise Exception("Could not create Whisper.")

def Recognize(data: sr.AudioData) -> dict[str, str]:
    if (not cfg.current_data.prompt_order.__contains__("whisper")):
        raise Exception("Model is not loaded in 'prompt_order'.")
    
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
        
        result = whisperM.transcribe(audio_name, temperature = cfg.current_data.temp)
        result = {
            "text": result["text"],
            "lang": result["language"],
            "error": ""
        }

        if (cfg.current_data.print_prompt):
            print("RESULT FROM WHISPER: " + str(result))

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