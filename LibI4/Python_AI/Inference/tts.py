from pathlib import Path
import pySpeakNG as espeak
import subprocess as sp
import os
import ai_config as cfg

tts_loaded: bool = False

def LoadTTS() -> None:
    global tts_loaded

    if (tts_loaded):
        return

    if (not cfg.current_data.prompt_order.__contains__("tts")):
        raise Exception("Model is not in 'prompt_order'.")

    if (cfg.current_data.print_loading_message):
        print("Loading TTS...")
    
    tts_loaded = True

def GetVoices() -> list[dict[str]]:
    LoadTTS()

    voices = []

    for voice in list(espeak.VOICES):
        for language in list(espeak.LANGUAGES.keys()):
            voices.append({
                "voice": voice,
                "language": language
            })
    
    return voices

def __voice_and_language_exists__(voice: str, language: str) -> bool:
    return GetVoices().count({"voice": voice, "language": language}) > 0

def __generate_tts__(prompt: str, voice: str, language: str, pitch: float, speed: float) -> bytes:
    LoadTTS()

    exists = __voice_and_language_exists__(voice, language)

    if (not exists):
        raise Exception("Voice and language combination does not exist.")
    
    if (cfg.current_data.print_prompt):
        print("TTS: \"" + prompt + "\" (Voice: " + voice + "; Language: " + language + "; Pitch: " + str(pitch) + "; Speed: " + str(speed) + ").")
    
    audio_name = "ta.wav"
    audio_n = 0

    while (os.path.exists(audio_name)):
        audio_n += 1
        audio_name = "ta_" + str(audio_n) + ".wav"

    sp.run(["espeak-ng", "-z", "-v", language + "+" + voice, "-p", str(int(pitch * 100)), "-s", str(int(speed * 100)), "-w", audio_name, "\"" + prompt + "\""])

    with open(audio_name, "rb") as f:
        audio = f.read()
        f.close()

    os.remove(audio_name)
    return audio

def MakeTTS(prompt: dict[str]) -> bytes:
    try:
        voice = prompt["voiceID"]
    except:
        try:
            voice = prompt["voice"]
        except:
            raise Exception("Voice not found.")
    
    try:
        language = str(prompt["language"])
    except:
        try:
            language = str(prompt["lang"])
        except:
            raise Exception("Language not found.")

    try:
        text = str(prompt["text"])
    except:
        raise Exception("Text not found.")
    
    try:
        pitch = float(prompt["pitch"])
    except:
        pitch = 0.5
    
    try:
        speed = float(prompt["speed"])
    except:
        try:
            speed = float(prompt["velocity"])
        except:
            speed = 1
    
    return __generate_tts__(text, voice, language, pitch, speed)