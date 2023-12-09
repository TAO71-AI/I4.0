import speech_recognition as sr
import whisper
import os
import torch
import ai_config as cfg

recognizer = sr.Recognizer()

"""def __recognize_whisper__(audio_data: sr.AudioData | str, model: str = None, language: str = None, device: str = None) -> str:
    if (model == None):
        model = cfg.current_data.whisper_model
    
    if (device == None):
        device = "cuda" if (cfg.current_data.use_gpu_if_available and cfg.current_data.move_to_gpu.__contains__("whisper") and torch.cuda.is_available()) else "cpu"
    
    if (type(audio_data) == sr.AudioData):
        fid = 0

        while (os.path.exists(str(fid) + ".wav")):
            fid += 1

        with open(str(fid) + ".wav", "wb") as f:
            f.write(audio_data.get_wav_data())
            f.close()

        audio = str(fid) + ".wav"
        delete_file = True
    elif (type(audio_data) == str):
        audio = audio_data
        delete_file = False
    else:
        raise Exception("Audio data is not AudioData or str.")

    print("Loading model...")
    m = whisper.load_model(model).to(device)
    audio = whisper.load_audio(audio)
    audio = whisper.pad_or_trim(audio)
    mel = whisper.log_mel_spectrogram(audio).to(m.device)

    print("Set language...")
    if (language == None):
        _, probs = m.detect_language(mel)
        language = max(probs, key = probs.get)
    print("Language = " + language)
    
    print("Decoding...")
    options = whisper.DecodingOptions()
    result = whisper.decode(m, mel, options)
    print("Decoded!")

    if (delete_file):
        os.remove(str(fid) + ".wav")

    return result.text"""

def Recognize(data: sr.AudioData) -> str:
    try:
        if (cfg.current_data.use_google_instead_of_whisper):
            return recognizer.recognize_google(data)
        
        return recognizer.recognize_whisper(data, model = cfg.current_data.whisper_model)
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