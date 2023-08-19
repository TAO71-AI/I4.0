import speech_recognition as sr
import sys

ip = ip = sys.argv[1]
api_key = api_key = sys.argv[2]
lang = api_key = sys.argv[3]
max_time = api_key = sys.argv[4]
model = api_key = sys.argv[5]
r = sr.Recognizer()

with sr.Microphone() as source:
    r.adjust_for_ambient_noise(source)
    audio = r.listen(source, phrase_time_limit = int(max_time))

try:
    msg = ""
    
    try:
        if (model == "google"):
            msg = r.recognize_google(audio, language = lang)
        else:
            msg = r.recognize_whisper(audio, language = lang, model = model)
        
        msg = str(msg)
    except sr.UnknownValueError:
        msg = "An error has ocurred! Whisper could not understand you."
    except sr.RequestError as e:
        msg = "ERROR: " + str(e)
    
    print(msg)
except Exception as ex:
    print("ERROR: " + str(ex))