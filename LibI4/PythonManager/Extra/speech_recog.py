import os
import sys

try:
    import speech_recognition as sr
except:
    os.system("python -m pip install SpeechRecognition")
    print("Try restarting the script.")

    sys.exit()

# Variables
whisper_model = "tiny"
recognition_engine = "whisper"
language = "es"

def Recognize():
    global whisper_model, recognition_engine, language

    r = sr.Recognizer()
    audio: sr.AudioData

    with sr.Microphone() as source:
        print("Say something...")
        audio = r.listen(source, phrase_time_limit = 5)

    try:
        text = ""
        recognition_engine = recognition_engine.strip().lower()

        if (recognition_engine == "google"):
            #text = r.recognize_google_cloud(audio, language = language)
            pass
        else:
            text = r.recognize_whisper(audio, language = language, model = whisper_model)
        
        return text
    except sr.UnknownValueError:
        print("An error has ocurred! Whisper could not understand you.")
    except sr.RequestError as e:
        print("ERROR: " + str(e))
    
    return "ERROR"