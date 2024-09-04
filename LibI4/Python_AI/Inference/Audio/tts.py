import pySpeakNG as espeak
import subprocess as sp
import os
import ai_config as cfg

tts_loaded: bool = False

def LoadTTS() -> None:
    global tts_loaded

    # Check if the TTS is loaded
    if (tts_loaded):
        # Return
        return

    # Check if the TTS is available
    if (len(cfg.GetAllInfosOfATask("tts")) > 0):
        # Set the loaded to true
        print("TTS loaded!")
        tts_loaded = True
    
    # NOTE: It doesn't matter how many times you create a TTS service in the config, the above `if` just checks if it's created at least once

def GetVoices() -> list[dict[str]]:
    # Load the tts
    LoadTTS()

    # Set the voices list
    voices = []

    # For each voice
    for voice in list(espeak.VOICES):
        # For each language
        for language in list(espeak.LANGUAGES.keys()):
            # Append it to the list
            voices.append({
                "voice": "espeak-" + voice,
                "language": language
            })

    # Return the list of voices
    return voices

def __voice_and_language_exists__(Voice: str, Language: str) -> bool:
    # For each voice
    for v in GetVoices():
        # If the voice and the language are the same
        if (Voice == v["voice"] and (v["language"] == "any" or v["language"] == Language)):
            # Return true
            return True
    
    # Else, return false
    return False

def __generate_tts_espeak__(Path: str, Prompt: str, Voice: str, Language: str, Pitch: float, Speed: float) -> None:
    # Generate a wav audio file with the voice
    sp.run(["espeak-ng", "-z", "-v", Language + "+" + Voice, "-p", str(int(Pitch * 100)), "-s", str(int(Speed * 100)), "-w", Path, "\"" + Prompt + "\""])

def __generate_tts__(Prompt: str, Voice: str, Language: str, Pitch: float, Speed: float) -> bytes:
    # Load the models
    LoadTTS()

    # Check if the voice and the language exists
    exists = __voice_and_language_exists__(Voice, Language)

    # If the combination of the voice and the language does not exist
    if (not exists):
        # Return an error
        raise Exception("Voice and language combination does not exist.")
    
    # Set the audio file name
    audio_name = "ta.wav"
    audio_n = 0

    while (os.path.exists(audio_name)):
        audio_n += 1
        audio_name = "ta_" + str(audio_n) + ".wav"
    
    # Check the TTS system to use
    if (Voice.startswith("espeak-")):
        # Use ESpeak
        # Inference ESpeak
        __generate_tts_espeak__(audio_name, Prompt, Voice[7:], Language, Pitch, Speed)

    # Read the audio bytes
    with open(audio_name, "rb") as f:
        audio = f.read()
        f.close()

    # Delete the temporary audio file
    os.remove(audio_name)

    # Return the generated audio file bytes
    return audio

def MakeTTS(Prompt: dict[str]) -> bytes:
    # Set voice to use
    try:
        voice = Prompt["voiceID"]
    except:
        try:
            voice = Prompt["voice"]
        except:
            raise Exception("Voice not found.")
    
    # Set language
    try:
        language = str(Prompt["language"])
    except:
        try:
            language = str(Prompt["lang"])
        except:
            raise Exception("Language not found.")

    # Set the prompt
    try:
        text = str(Prompt["text"])
    except:
        raise Exception("Text not found.")
    
    # Set the pitch
    try:
        pitch = float(Prompt["pitch"])
    except:
        pitch = 0.5
    
    # Set the speed
    try:
        speed = float(Prompt["speed"])
    except:
        try:
            speed = float(Prompt["velocity"])
        except:
            speed = 1
    
    # Inference the model
    return __generate_tts__(text, voice, language, pitch, speed)