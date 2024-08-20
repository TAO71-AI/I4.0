from GoogleTTS import GoogleTTS
from GoogleTTS.google_tts import SsmlGender
#from styletts2.tts import StyleTTS2
import pySpeakNG as espeak
import subprocess as sp
import os
import ai_config as cfg

tts_loaded: bool = False
tts_google: GoogleTTS | None = None
#tts_styletts2: StyleTTS2 = None

def LoadTTS() -> None:
    global tts_loaded, tts_google

    if (tts_loaded and tts_google != None):
        return

    if (not cfg.current_data["models"].__contains__("tts")):
        raise Exception("Model is not in 'prompt_order'.")
    
    tts_google = GoogleTTS()
    tts_loaded = True

"""def LoadStyleTTS2(ModelPath: str, ConfigPath: str) -> None:
    global tts_styletts2

    if (not cfg.current_data["prompt_order"].__contains__("tts")):
        raise Exception("Model is not in 'prompt_order'.")

    if (cfg.current_data["print_loading_message"]):
        print("Loading TTS (StyleTTS2)...")
    
    if (len(cfg.devices) == 0):
        cfg.__get_gpu_devices__()
    
    tts_styletts2 = StyleTTS2()

    tts_styletts2.device = cfg.GetAvailableGPUDeviceForTask("tts", 0)
    tts_styletts2.load_model(ModelPath, ConfigPath)

    if (cfg.current_data["print_loading_message"]):
        print("   Loaded model on device '" + tts_styletts2.device + "'.")"""

def GetVoices() -> list[dict[str]]:
    LoadTTS()
    voices = []

    for voice in list(espeak.VOICES):
        for language in list(espeak.LANGUAGES.keys()):
            voices.append({
                "voice": "espeak-" + voice,
                "language": language
            })
    
    voices += [
        {"voice": "google-male", "language": "unknown"},
        {"voice": "google-female", "language": "unknown"}
    ]

    """for stts2_mn in cfg.current_data["styletts2"]["models"]:
        try:
            stts2_mp = cfg.current_data["styletts2"]["models"][stts2_mn][0]
            stts2_mc = cfg.current_data["styletts2"]["models"][stts2_mn][1]

            if (not os.path.exists(stts2_mp) or not os.path.exists(stts2_mc)):
                raise Exception("StyleTTS2 model not found.")
            
            voices.append({"voice": "styletts2-" + stts2_mn, "language": "unknown"})
        except:
            continue"""

    return voices

def __voice_and_language_exists__(voice: str, language: str) -> bool:
    for v in GetVoices():
        if (voice == v["voice"] and (v["language"] == "any" or v["language"] == language)):
            return True
    
    return False

def __generate_tts_espeak__(path: str, prompt: str, voice: str, language: str, pitch: float, speed: float) -> None:
    sp.run(["espeak-ng", "-z", "-v", language + "+" + voice, "-p", str(int(pitch * 100)), "-s", str(int(speed * 100)), "-w", path, "\"" + prompt + "\""])

def __generate_tts_google__(path: str, prompt: str, voice: str, language: str, pitch: float, speed: float) -> None:
    # Pitch and speed are not supported yet.
    voice = voice.lower().strip()
    
    if (voice == "male" or voice == "m"):
        voice = SsmlGender.MALE
    elif (voice == "female" or voice == "f"):
        voice = SsmlGender.FEMALE
    else:
        voice = SsmlGender.UNSPECIFIED

    tts_google.set_key(cfg.current_data["google_tts_apikey"])
    tts_google.set_language_code(language)
    tts_google.set_ssml_gender(voice)

    response = tts_google.tts(prompt, path)

    if (not "audioContent" in response):
        error = response["error"]
        error = str(error)

        raise Exception("Error on Google TTS: " + error)

"""def __generate_tts_styletts2__(path: str, prompt: str, voice: str, pitch: float, speed: float) -> None:
    # Pitch and speed are not supported yet.
    LoadStyleTTS2(cfg.current_data["styletts2"]["models"][voice][0], cfg.current_data["styletts2"]["models"][voice][1])
    tts_styletts2.inference(text = prompt, output_wav_file = path, diffusion_steps = cfg.current_data["styletts2"]["steps"])"""

def __generate_tts__(prompt: str, voice: str, language: str, pitch: float, speed: float) -> bytes:
    LoadTTS()
    exists = __voice_and_language_exists__(voice, language)

    if (not exists):
        raise Exception("Voice and language combination does not exist.")
    
    audio_name = "ta.wav"
    audio_n = 0

    while (os.path.exists(audio_name)):
        audio_n += 1
        audio_name = "ta_" + str(audio_n) + ".wav"
    
    if (voice.startswith("espeak-")):
        __generate_tts_espeak__(audio_name, prompt, voice[7:], language, pitch, speed)
    elif (voice.startswith("google-")):
        __generate_tts_google__(audio_name, prompt, voice[7:], language, pitch, speed)
    """elif (voice.startswith("styletts2-")):
        __generate_tts_styletts2__(audio_name, prompt, voice[10:], pitch, speed)"""

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