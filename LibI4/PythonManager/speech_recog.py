import speech_recognition as sr
import ai_config as cfg

recognizer = sr.Recognizer()

def __recognize__(data: sr.AudioData) -> str:
    try:
        return recognizer.recognize_whisper(data, cfg.current_data.whisper_model)
    except sr.UnknownValueError:
        return "Audio could not be recognized."
    except sr.RequestError as ex:
        return "Error requesting: " + str(ex)

def RecognizeUsingMicrophone() -> str:
    with sr.Microphone() as source:
        return __recognize__(recognizer.listen(source))

def RecognizeUsingAudio(audio_path: str) -> str:
    with sr.AudioFile(audio_path) as source:
        return __recognize__(recognizer.record(source))