from transformers import Pipeline, pipeline, AutoModel, AutoTokenizer
from diffusers import AutoPipelineForText2Image
import os
import json
import torch

devices: list[str] = []
__config_data__: dict[str] = {
    "text_classification_model": "joeddav/distilbert-base-uncased-go-emotions-student",         # Sets the HuggingFace (Text-Classification) model.
    "translation_classification_model": "papluca/xlm-roberta-base-language-detection",          # Sets the HuggingFace (Text-Classification) model used for detecting the language of the prompt.
    "translation_models": {},                                                                   # Sets the HuggingFace (Translation) models.
        # Example:
        # {"es-en": "MODEL", "en-es": "MODEL", "en-ru": "MODEL"}
    "server_language": "en",                                                                    # Sets the default language to translate a prompt.
    "whisper_model": "tiny",                                                                    # Sets the default Whisper model.
    "image_generation": {                                                                       # Sets the config for the Image Generation model.
        "model": "SimianLuo/LCM_Dreamshaper_v7",                                                    # HuggingFace (TextToImage) model.
        "steps": 8,                                                                                 # The number of steps for the model.
        "guidance": 3,                                                                              # The guidance scale.
        "width": 768,                                                                               # Image width.
        "height": 768,                                                                              # Image height.
    },
    "img_to_text_model": "Salesforce/blip-image-captioning-base",                               # Sets the HuggingFace (ImageToText) model.
    "text_to_audio_model": "suno/bark-small",                                                   # Sets the HuggingFace (TextToAudio) model.
    "nsfw_filter_text_model": "feruskas/CADD-NSFW-SFW",                                         # Sets the HuggingFace (Text-Classification) model used for NSFW detection on text.
    "nsfw_filter_image_model": "Falconsai/nsfw_image_detection",                                # Sets the HuggingFace (Image-Classification) model used for NSFW detection on image.
    "depth_estimation_model": "Intel/dpt-beit-base-384",                                        # Sets the HuggingFace (Depth-Estimation) model.
    "object_detection_model": "hustvl/yolos-tiny",                                              # Sets the HuggingFace (Object-Detection) model.
    "rvc_models": {},                                                                           # Sets the RVC models (must be on your local storage).
        # Example:
        # {"MODEL NAME": ["MODEL PATH", "INDEX PATH", "MODEL TYPE (rmvpe, crepe, pm, etc)"]}
    "uvr_model": "9-HP2",                                                                       # Sets the UVR model (must be on your local storage).
    "image_to_image_model": "stabilityai/stable-diffusion-xl-refiner-1.0",                      # Sets the model for the image to image service.
    "qa_model": "google-bert/bert-large-uncased-whole-word-masking-finetuned-squad",            # Sets the HuggingFace (Question Answering) model.
    "force_api_key": True,                                                                      # Makes API keys required for using the AI models.
    "max_length": 250,                                                                          # Sets the max length that the chatbots (`g4a`, `hf`...) can generate.
    "use_dynamic_system_args": True,                                                            # Creates some extra system prompt for the chatbots (example: the current date, the state of humour...).
    "models": "",                                                                               # Sets the models that will be loaded.
    "ai_args": "",                                                                              # Sets some default args for the chatbot (mostly to define the personality, like: +evil, +self-aware...). Can be changed by the user.
    "custom_system_messages": "",                                                               # Sets a custom system prompt from the server.
    "system_messages_in_first_person": False,                                                   # [DEPRECATED, soon will be deleted] Replaces `you're`, `you`... with `I'm`, `I`...
    "use_default_system_messages": True,                                                        # Use pre-defined system prompt.
    "keys_db": {                                                                                # Allows the usage of a database for the API keys.
        "use": "false",                                                                             # Sync API keys with database.
        "server": "127.0.0.1",                                                                      # Database server IP.
        "user": "root",                                                                             # Database user.
        "password": "",                                                                             # Database password.
        "database": "",                                                                             # Database name.
        "table": "keys"                                                                             # Database table.
    },
    "max_prompts": 1,                                                                           # Sets the max prompts that can be processed at a time for each service.
    "enabled_plugins": "sing vtuber discord_bot voicevox twitch gaming image_generation",       # I4.0 plugins that creates more system prompts.
    "allow_processing_if_nsfw": [False, False],                                                 # Allows the processing of a prompt even if it's detected as NSFW.
    #                           [Text, Image]
    "ban_if_nsfw": True,                                                                        # Bans the API key if a NSFW prompt is detected (requires `force_api_key` to be true).
    "ban_if_nsfw_ip": True,                                                                     # Bans the IP of the user if a NSFW prompt is detected.
    "use_local_ip": False,                                                                      # Disables the public IP address use for the server (only accepts connections from `127.0.0.1`, recommended for personal use).
    "allow_data_share": True,                                                                   # Allows data sharing to TAO71's servers to make a better dataset for I4.0 and train AI models on that dataset (shares the user's prompt [files included], service used and the server's response and it's 100% anonymous).
    "data_share_servers": ["tao71.sytes.net"],                                                  # List of servers to share the data.
    "data_share_timeout": 2.5,                                                                  # Seconds to wait per server response on data share.
    "google_tts_apikey": "",                                                                    # Google TTS API key.
    "device": {                                                                                 # Set the device to load the models.
        "chatbot": "cpu",
        "text2img": "cpu",
        "img2text": "cpu",
        "de": "cpu",
        "tr": "cpu",
        "sc": "cpu",
        "text2audio": "cpu",
        "speech2text": "cpu",
        "od": "cpu",
        "rvc": "cpu",
        "uvr": "cpu",
        "img2img": "cpu",
        "qa": "cpu",
        "nsfw_filter-text": "cpu",
        "nsfw_filter-image": "cpu",
    },
    "styletts2": {                                                                              # StyleTTS2 configuration.
        "models": {},                                                                               # StyleTTS2 models.
            # Example:
            # {"MODEL NAME": ["MODEL PATH", "CONFIG PATH"]}
        "steps": 5                                                                                  # Number of diffusion steps.
    },
    "discord_bot": {                                                                            # Discord bot configuration. Most of this settings are server-configurable by ONLY the server's owner. This is just the default settings if not configured.
        "token": "",                                                                                # Discord's API key.
        "server_api_key": "",                                                                       # I4.0 server's API key.
        "allow_rfiles": True,                                                                       # Allows the Discord bot to receive files (required for file2any services).
        "allow_sfiles": True,                                                                       # Allows the Discord bot to send files (required for any2file) services.
        "welcome": {                                                                                # The Discord bot will send a welcome message for any new user.
            "preprogrammed": True,                                                                      # The bot will send a random-selected pre-programmed message instead of processing a prompt.
            "preprogrammed_messages": [                                                                 # Preprogrammed welcome messages.
                "Hello $USER! How are you?",
                "Welcome, $USER! Tell me about you!"
            ],
            "enabled": True,                                                                            # Enables the welcome message.
        },
        "auto_mod": False,                                                                          # The bot will check for NSFW texts & images (if the services are available). If found something NSFW, it will automatically isolate the user from the server and contact mods.
        "mods_role": "",                                                                            # The role of the mods I4.0 will contact (empty to disable).
        "allow_vc": True,                                                                           # Allows the bot to connect to a voice chat, talk and listen.
        "auto-talk": True,                                                                          # Allows the bot to talk without the command prefix, activated at random moments.
        "prefix": "!i4",                                                                            # Command prefix.
    },
    "chatbot": {                                                                                    # Chatbot configuration.
        "ctx": 2048,                                                                                    # Maximum size of the context window.
        "threads": -1,                                                                                  # Number of CPU threads to use. Set to -1 to use all, set to -2 to determine automatically.
        "ngl": 100,                                                                                     # Number of GPU layers to use.
        "batch": 8,                                                                                     # Prompt tokens processed in parallel.
        "type": "gpt4all",                                                                              # Chatbot library to use. Available: `gpt4all` (SLOW on CPU, FAST on GPU, MAY NOT BE tested), `hf` (FAST for both CPU and GPU, LESS tested, it may broke depending on the model you're using), `lcpp` (VERY FAST on GPU, VERY SLOW on CPU, MORE tested, also can't change the device, so in order to use this one on another device you need to re-install the package).
        "gpt4all": "Phi-3-mini-4k-instruct.Q4_0.gguf",                                                  # GPT4All's model path or name.
        "hf": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",                                                     # HuggingFace's model name.
        "lcpp": [                                                                                       # LlamaCPP-Python's model.
            "TheBloke/Mistral-7B-Instruct-v0.2-GGUF",                                                       # Model repository on HuggingFace or model path.
            "mistral-7b-instruct-v0.2.Q4_K_M.gguf",                                                         # File of the model to use/download.
            "mistralai/Mistral-7B-Instruct-v0.2",                                                           # HuggingFace repository for the chat format. Leave empty to use the repository of the model.
        ],
        "temp": 0.5,                                                                                    # Sets the temperature used for the models.
    },
    "price": {                                                                                          # Set the price of the services (in tokens of API key).
        "chatbot": 20,
        "text2img": 20,
        "img2text": 10,
        "de": 10,
        "tr": 5,
        "sc": 5,
        "text2audio": 20,
        "speech2text": 15,
        "od": 10,
        "rvc": 20,
        "uvr": 15,
        "img2img": 20,
        "qa": 10,
        "nsfw_filter-text": 2.5,
        "nsfw_filter-image": 2.5,
        "tts": 7.5
    },
}

def Init() -> None:
    if (not os.path.exists("config.json")):
        with open("config.json", "w+") as f:
            f.close()
        
        SaveConfig(__config_data__)
        print("Configuration created at 'config.json'! To start the server, please run this script again.")

        os._exit(0)

def ReadConfig() -> dict[str]:
    Init()
    
    with open("config.json", "r") as f:
        data: dict[str, any] = json.loads(f.read())
        f.close()
    
    for dkey in list(data.keys()):
        if (dkey not in list(__config_data__.keys())):
            data.pop(dkey)
            continue

    for dkey in list(__config_data__.keys()):
        if (dkey not in list(data.keys())):
            data[dkey] = __config_data__[dkey]
    
    SaveConfig(data)
    return data

def SaveConfig(Config: dict[str] = {}) -> None:
    Init()

    if (len(list(Config.keys())) == 0):
        Config = current_data.copy()

        if (current_data == None):
            return
    
    text = json.dumps(Config, indent = 4)

    with open("config.json", "w") as f:
        f.write(text)
        f.close()

def GetAvailableGPUDeviceForTask(Task: str) -> str:
    device = current_data["device"][Task]

    if (not (device == "cuda" and torch.cuda.is_available()) and not device == "cpu"):
        print("Invalid device or not available. Please use `cpu` or `cuda`. Changing to `cpu`.")
        device = "cpu"
    
    return device

def LoadPipeline(PipeTask: str, Task: str, ModelName: str) -> tuple[Pipeline, str]:
    dev = GetAvailableGPUDeviceForTask(Task)

    print(f"Loading (transformers) pipeline for the service '{Task.upper()}' on the device '{dev}'...")
    pipe = pipeline(task = PipeTask, model = ModelName, device = dev)
    print("   Done!")

    return (pipe, dev)

def LoadDiffusersPipeline(Task: str, ModelName: str, CustomPipelineType: type | None = None) -> tuple[any, str]:
    if (CustomPipelineType == None):
        CustomPipelineType = AutoPipelineForText2Image
    
    dev = GetAvailableGPUDeviceForTask(Task)
    print(f"Loading (diffusers) pipeline for the service '{Task.upper()}' on the device '{dev}'...")

    if (Task == "img2img"):
        pipe = CustomPipelineType.from_pretrained(ModelName, safety_checker = None, requires_safety_checker = False)
    else:
        pipe = CustomPipelineType.from_pretrained(ModelName)

    pipe = pipe.to(dev)
    print("   Done!")

    return (pipe, dev)

def LoadModel(Task: str, ModelName: str, ModelType: type | None = None, TokenizerType: type | None = None) -> tuple[any, any, str]:
    if (ModelType == None):
        ModelType = AutoModel
    
    if (TokenizerType == None):
        TokenizerType = AutoTokenizer

    dev = GetAvailableGPUDeviceForTask(Task)
    print(f"Loading model for '{Task.upper()}' on the device '{dev}'...")

    model = ModelType.from_pretrained(ModelName).to(dev)
    tokenizer = TokenizerType.from_pretrained(ModelName)

    print("   Done!")
    return (model, tokenizer, dev)

def JSONDeserializer(SerilizedText: str) -> dict:
    try:
        return json.loads(SerilizedText)
    except:
        if (SerilizedText.startswith("{") and SerilizedText.endswith("}")):
            try:
                return eval(SerilizedText)
            except:
                return json.loads(SerilizedText.replace("\'", "\""))

current_data = ReadConfig()