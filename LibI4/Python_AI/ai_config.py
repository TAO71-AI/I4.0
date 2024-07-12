from transformers import Pipeline, pipeline, AutoModel, AutoTokenizer
from diffusers import AutoPipelineForText2Image
import os
import json
import torch

devices: list[str] = []
__config_data__: dict[str] = {
    "gpt4all_model": "mistral-7b-instruct-v0.1.Q4_0.gguf",                                      # Sets the GPT4All model.
    "hf_model": "gpt2",                                                                         # Sets the HuggingFace (Text-Generation) model.
    "text_classification_model": "joeddav/distilbert-base-uncased-go-emotions-student",         # Sets the HuggingFace (Text-Classification) model.
    "translation_classification_model": "papluca/xlm-roberta-base-language-detection",          # Sets the HuggingFace (Text-Classification) model used for detecting the language of the prompt.
    "translation_models": {},                                                                   # Sets the HuggingFace (Translation) models.
        # Example:
        # {"es-en": "MODEL", "en-es": "MODEL", "en-ru": "MODEL"}
    "server_language": "en",                                                                    # Sets the default language to translate a prompt.
    "whisper_model": "tiny",                                                                    # Sets the default Whisper model.
    "image_generation_model": "SimianLuo/LCM_Dreamshaper_v7",                                   # Sets the default HuggingFace (TextToImage) model.
    "image_generation_steps": 8,                                                                # Sets the generation steps for an image on the TextToImage model.
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
    "image_to_image_model": "stabilityai/stable-diffusion-xl-refiner-1.0",                      # Sets the HuggingFace (ImageToImage) model.
    "i2i_steps": 10,                                                                            # Sets the steps for an image on the ImageToImage model.
    "qa_model": "google-bert/bert-large-uncased-whole-word-masking-finetuned-squad",            # Sets the HuggingFace (Question Answering) model.
    "force_api_key": True,                                                                      # Makes API keys required for using the AI models.
    "low_cpu_or_memory": False,                                                                 # [DEPRECATED, soon will be deleted] Uses less resources of your machine on the `hf` chatbot.
    "max_length": 250,                                                                          # Sets the max length that the chatbots (`g4a`, `hf`...) can generate.
    "use_chat_history": True,                                                                   # Allows the chatbots to have memory.
    "use_dynamic_system_args": True,                                                            # Creates some extra system prompt for the chatbots (example: the current date, the state of humour...).
    "prompt_order": "",                                                                         # Sets the models that will be loaded.
    "move_to_gpu": "",                                                                          # Sets the models that will be loaded on your GPU(s) [must also be in `prompt_order` and `use_gpu_if_available` must be active].
    "use_gpu_if_available": True,                                                               # Allow the use of your GPU(s).
    "ai_args": "",                                                                              # Sets some default args for the chatbot (mostly to define the personality, like: +evil, +self-aware...). Can be changed by the user.
    "custom_system_messages": "",                                                               # Sets a custom system prompt from the server.
    "system_messages_in_first_person": False,                                                   # [DEPRECATED, soon will be deleted] Replaces `you're`, `you`... with `I'm`, `I`...
    "use_default_system_messages": True,                                                        # Use pre-defined system prompt.
    "temp": 0.5,                                                                                # Sets the temperature used for the models.
    "save_conversations": True,                                                                 # Saves the conversations on the disk [`use_chat_history` must be active].
    "keys_db": {                                                                                # Allows the usage of a database for the API keys.
        "use": "false",                                                                             # Sync API keys with database.
        "server": "127.0.0.1",                                                                      # Database server IP.
        "user": "root",                                                                             # Database user.
        "password": "",                                                                             # Database password.
        "database": "",                                                                             # Database name.
        "table": "keys"                                                                             # Database table.
    },
    "print_prompt": False,                                                                      # Prints the user's prompt on the screen (recommended only for personal use).
    "allow_titles": True,                                                                       # If the chatbot response starts with `[`, contains `]` and have something between this characters, sets that as the title of the conversation.
    "max_prompts": 1,                                                                           # Sets the max prompts that can be processed at a time.
    "use_multi_model": False,                                                                   # Gets a response from all the chatbots loaded, using the same prompt, system prompts and conversation.
    "multi_model_mode": "longest",                                                              # [`use_multi_model` must be active] The final response that the server will return to the user.
    "print_loading_message": True,                                                              # Prints a message when any model is loading.
    "enable_predicted_queue_time": True,                                                        # Predict the time that the queue will take.
    "enabled_plugins": "sing vtuber discord_bot voicevox twitch gaming image_generation",       # I4.0 plugins that creates more system prompts.
    "use_only_latest_log": True,                                                                # Only saves the latest log file.
    "max_predicted_queue_time": 20,                                                             # The max queue times saved that will be used for queue prediction.
    "allow_processing_if_nsfw": False,                                                          # Allows the processing of a prompt even if it's detected as NSFW.
    "ban_if_nsfw": True,                                                                        # Bans the IP address if a NSFW prompt is detected from that IP address.
    "use_local_ip": False,                                                                      # Disables the public IP address use for the server (only accepts connections from `127.0.0.1`, recommended for personal use).
    "auto_start_rec_files_server": True,                                                        # Starts the receive files server when the I4.0's server is started.
    "seed": -1,                                                                                 # Sets the seed used for some AI models (-1 = randomize).
    "gpu_device": "cuda",                                                                       # Sets the GPU(s) device(s) that can be used.
    "use_other_services_on_chatbot": False,                                                     # Uses other services (like translation) before or after using the chatbot (If this is not active, NSFW detection will also be used if it is in `prompt_order` and `allow_processing_if_nsfw` is not active or `ban_if_nsfw` is active).
    "allow_data_share": True,                                                                   # Allows data sharing to TAO71's servers to make a better dataset for I4.0 and train AI models on that dataset (shares the user's prompt [files included], service used and the server's response and it's 100% anonymous).
    "data_share_servers": ["tao71.sytes.net"],                                                  # List of servers to share the data.
    "data_share_timeout": 2.5,                                                                  # Seconds to wait per server response on data share.
    "google_tts_apikey": "",                                                                    # Google TTS API key.
    "styletts2": {                                                                              # StyleTTS2 configuration.
        "models": {},                                                                               # StyleTTS2 models.
            # Example:
            # {"MODEL NAME": ["MODEL PATH", "CONFIG PATH"]}
        "steps": 5                                                                                  # Number of diffusion steps.
    },
    "allow_thinking": True,                                                                     # Allows the chatbot to think.
    "use_new_conversation_template": True,                                                      # Uses a new conversation template on all the chatbots (required for thinking).
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
        data = json.loads(f.read())
        f.close()
    
    for dkey in __config_data__.keys():
        if (list(data.keys()).count(dkey) == 0):
            data[dkey] = __config_data__[dkey]
    
    return data

def SaveConfig(Config: dict[str] = None) -> None:
    Init()

    if (Config == None):
        Config = current_data.copy()

        if (current_data == None):
            return
    
    text = json.dumps(Config, indent = 4)

    with open("config.json", "w") as f:
        f.write(text)
        f.close()

def __get_gpu_devices__() -> None:
    devices.clear()
    
    if (current_data["gpu_device"].count(";") > 0):
        devs = current_data["gpu_device"].split(";")
    else:
        devs = [current_data["gpu_device"]]

    for dev in devs:
        dev = dev.strip().lower()
        
        if (dev.count(":") > 0):
            devc = dev.split(":")[0].strip()
        else:
            devc = dev

        move_to_gpu = False

        if (devc == "cuda"):
            move_to_gpu = torch.cuda.is_available()
        elif (devc == "mps"):
            move_to_gpu = torch.backends.mps.is_available()
        elif (devc == "vulkan"):
            move_to_gpu = torch.is_vulkan_available()
        elif (devc == "openmp"):
            move_to_gpu = torch.backends.openmp.is_available()
        elif (devc == "cudnn"):
            move_to_gpu = torch.backends.cudnn.is_available()
        
        if (move_to_gpu):
            devices.append(dev)

def GetAvailableGPUDeviceForTask(Task: str, Index: int) -> str:
    if (len(devices) == 0):
        __get_gpu_devices__()
    
    if (Index < 0):
        Index = 0
    elif (Index >= len(devices)):
        Index = len(devices) - 1
    
    if (current_data["use_gpu_if_available"] and current_data["move_to_gpu"].count(Task) > 0):
        return devices[Index]

    return "cpu"

def LoadPipeline(PipeTask: str, Task: str, ModelName: str) -> tuple[Pipeline, str]:
    errors = []

    if (len(devices) == 0):
        __get_gpu_devices__()

    for i in range(len(devices)):
        dev = GetAvailableGPUDeviceForTask(Task, i)

        try:
            pipe = pipeline(task = PipeTask, model = ModelName, device = dev)
            return (pipe, dev)
        except Exception as ex:
            errors.append(str(ex))
    
    raise Exception("Error creating transformers pipeline. Errors: " + str(errors))

def LoadDiffusersPipeline(Task: str, ModelName: str, CustomPipelineType: type = None) -> tuple[any, str]:
    errors = []

    if (CustomPipelineType == None):
        CustomPipelineType = AutoPipelineForText2Image
    
    if (len(devices) == 0):
        __get_gpu_devices__()

    for i in range(len(devices)):
        dev = GetAvailableGPUDeviceForTask(Task, i)

        try:
            if (Task == "img2img"):
                pipe = CustomPipelineType.from_pretrained(ModelName, safety_checker = None, requires_safety_checker = False)
            else:
                pipe = CustomPipelineType.from_pretrained(ModelName)

            pipe = pipe.to(dev)
            return (pipe, dev)
        except Exception as ex:
            errors.append(str(ex))
    
    raise Exception("Error creating diffusers pipeline. Errors: " + str(errors))

def LoadModel(Task: str, ModelName: str, ModelType: type = None, TokenizerType: type = None) -> tuple[any, any, str]:
    errors = []

    if (ModelType == None):
        ModelType = AutoModel
    
    if (TokenizerType == None):
        TokenizerType = AutoTokenizer
    
    if (len(devices) == 0):
        __get_gpu_devices__()

    for i in range(len(devices)):
        dev = GetAvailableGPUDeviceForTask(Task, i)

        try:
            model = ModelType.from_pretrained(ModelName).to(dev)
            tokenizer = TokenizerType.from_pretrained(ModelName)

            return (model, tokenizer, dev)
        except Exception as ex:
            errors.append(str(ex))
    
    raise Exception("Error creating model. Errors: " + str(errors))

def JSONDeserializer(SerilizedText: str) -> dict:
    try:
        return json.loads(SerilizedText)
    except:
        if (SerilizedText.startswith("{") and SerilizedText.endswith("}")):
            try:
                return eval(SerilizedText)
            except:
                pass
        
        return json.loads(SerilizedText.replace("\'", "\""))

current_data = ReadConfig()