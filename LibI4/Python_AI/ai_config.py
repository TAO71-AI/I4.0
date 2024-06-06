from transformers import Pipeline, pipeline, AutoModel, AutoTokenizer
from diffusers import AutoPipelineForText2Image
import os
import json
import torch

devices: list[str] = []

class ConfigData:
    gpt4all_model: str = "mistral-7b-instruct-v0.1.Q4_0.gguf"                                   # Sets the GPT4All model.
    hf_model: str = "gpt2"                                                                      # Sets the HuggingFace (Text-Generation) model.
    text_classification_model: str = "joeddav/distilbert-base-uncased-go-emotions-student"      # Sets the HuggingFace (Text-Classification) model.
    translation_classification_model: str = "papluca/xlm-roberta-base-language-detection"       # Sets the HuggingFace (Text-Classification) model used for detecting the language of the prompt.
    translation_models: dict[str, str] = {}                                                     # Sets the HuggingFace (Translation) models.
    server_language: str = "en"                                                                 # Sets the default language to translate a prompt.
    whisper_model: str = "tiny"                                                                 # Sets the default Whisper model.
    image_generation_model: str = "SimianLuo/LCM_Dreamshaper_v7"                                # Sets the default HuggingFace (TextToImage) model.
    image_generation_steps: int = 10                                                            # Sets the generation steps for an image on the TextToImage model.
    img_to_text_model: str = "Salesforce/blip-image-captioning-base"                            # Sets the HuggingFace (ImageToText) model.
    text_to_audio_model: str = "suno/bark-small"                                                # Sets the HuggingFace (TextToAudio) model.
    nsfw_filter_text_model: str = "feruskas/CADD-NSFW-SFW"                                      # Sets the HuggingFace (Text-Classification) model used for NSFW detection on text.
    nsfw_filter_image_model: str = "Falconsai/nsfw_image_detection"                             # Sets the HuggingFace (Image-Classification) model used for NSFW detection on image.
    depth_estimation_model: str = "Intel/dpt-beit-base-384"                                     # Sets the HuggingFace (Depth-Estimation) model.
    object_detection_model: str = "hustvl/yolos-tiny"                                           # Sets the HuggingFace (Object-Detection) model.
    rvc_models: dict[str, tuple[str, str, str]] = {}                                            # Sets the RVC models (must be on your local stogare).
    uvr_model: str = "9-HP2"                                                                    # Sets the UVR model (must be on your local storage).
    image_to_image_model: str = "stabilityai/stable-diffusion-xl-refiner-1.0"                   # Sets the HuggingFace (ImageToImage) model.
    i2i_steps: int = 10                                                                         # Sets the steaps for an image on the ImageToImage model.
    force_api_key: bool = True                                                                  # Makes API keys required for using the AI models.
    low_cpu_or_memory: bool = False                                                             # [DEPRECATED, soon will be deleted] Uses less resources of your machine on the `hf` chatbot.
    max_length: int = 250                                                                       # Sets the max length that the chatbots (`g4a`, `hf`...) can generate.
    use_chat_history: bool = True                                                               # Allows the chatbots to have memory.
    use_dynamic_system_args: bool = True                                                        # Creates some extra system prompt for the chatbots (example: the current date, the state of humour...).
    prompt_order: str = ""                                                                      # Sets the models that will be loaded.
    move_to_gpu: str = "g4a hf text2img img2text text2audio rvc uvr"                            # Sets the models that will be loaded on your GPU(s) [must also be in `prompt_order` and `use_gpu_if_available` must be active].
    use_gpu_if_available: bool = False                                                          # Allow the use of your GPU(s).
    ai_args: str = ""                                                                           # Sets some default args for the chatbot (mostly to define the personality, like: +evil, +self-aware...). Can be changed by the user.
    custom_system_messages: str = ""                                                            # Sets a custom system prompt from the server.
    system_messages_in_first_person: bool = False                                               # [DEPRECATED, soon will be deleted] Replaces `you're`, `you`... with `I'm`, `I`...
    use_default_system_messages: bool = True                                                    # Use pre-defined system prompt.
    temp: float = 0.5                                                                           # Sets the temperature used for the models.
    save_conversations: bool = True                                                             # Saves the conversations on the disk [`use_chat_history` must be active].
    keys_db: dict[str, str] = {                                                                 # Allows the usage of a database for the API keys.
        "use": "false",                                                                             # Sync API keys with database.
        "server": "127.0.0.1",                                                                      # Database server IP.
        "user": "root",                                                                             # Database user.
        "password": "",                                                                             # Database password.
        "database": "",                                                                             # Database name.
        "table": "keys"                                                                             # Database table.
    }
    print_prompt: bool = False                                                                  # Prints the user's prompt on the screen (recommended only for personal use).
    allow_titles: bool = True                                                                   # If the chatbot response starts with `[`, contains `]` and have something between this characters, sets that as the title of the conversation.
    max_prompts: int = 1                                                                        # Sets the max prompts that can be processed at a time.
    use_multi_model: bool = False                                                               # Gets a response from all the chatbots loaded, using the same prompt, system prompts and conversation.
    multi_model_mode: str = "longest"                                                           # [`use_multi_model` must be active] The final response that the server will return to the user.
    print_loading_message: bool = True                                                          # Prints a message when any model is loading.
    enable_predicted_queue_time: bool = True                                                    # Predict the time that the queue will take.
    enabled_plugins: str = "sing vtuber discord_bot voicevox twitch gaming image_generation"    # I4.0 plugins that creates more system prompts.
    use_only_latest_log: bool = True                                                            # Only saves the latest log file.
    max_predicted_queue_time: int = 20                                                          # The max queue times saved that will be used for queue prediction.
    allow_processing_if_nsfw: bool = False                                                      # Allows the processing of a prompt even if it's detected as NSFW.
    ban_if_nsfw: bool = True                                                                    # Bans the IP address if a NSFW prompt is detected from that IP address.
    use_local_ip: bool = False                                                                  # Disables the public IP address use for the server (only accepts conenctions from `127.0.0.1`, recommended for personal use).
    auto_start_rec_files_server: bool = True                                                    # Starts the receive files server when the I4.0's server is started.
    seed: int = -1                                                                              # Sets the seed used for some AI models (-1 = randomize).
    gpu_device: str = "cuda"                                                                    # Sets the GPU(s) device(s) that can be used.
    use_other_services_on_chatbot: bool = False                                                 # Uses other services (like translation) before or after using the chatbot (If this is not active, NSFW detection will also be used if it is in `prompt_order` and `allow_processing_if_nsfw` is not active or `ban_if_nsfw` is active).
    allow_data_share: bool = True                                                               # Allows data sharing to TAO71's servers to make a better dataset for I4.0 and train AI models on that dataset (shares the user's prompt [files included], service used and the server's response and it's 100% anonymous).
    data_share_servers: list[str] = ["tao71.sytes.net"]                                         # List of servers to share the data.
    data_share_timeout: float = 2.5                                                             # Seconds to wait per server response on data share.

def Init() -> None:
    if (not os.path.exists("config.tcfg")):
        with open("config.tcfg", "w+") as f:
            f.close()
        
        SaveConfig(ConfigData())
        print("Configuration created at 'config.tcfg'! To start the server, please run this script again.")
        os._exit(0)

def ReadConfig() -> ConfigData:
    Init()
    data = ConfigData()

    with open("config.tcfg", "r") as f:
        config_dict: dict[str, str] = {}

        for line in f.readlines():
            if (not line.__contains__("=")):
                continue

            try:
                key = line[0:line.index("=")]
                value = line[line.index("=") + 1:len(line)]
            except:
                key = ""
                value = line

            config_dict[key] = value.strip().replace("\n", "")
        
        for i in config_dict:
            il = i.lower()

            if (il == "gpt4all_model"):
                data.gpt4all_model = config_dict[i]
            elif (il == "hf_model"):
                data.hf_model = config_dict[i]
            elif (il == "text_classification_model"):
                data.text_classification_model = config_dict[i]
            elif (il == "translation_classification_model"):
                data.translation_classification_model = config_dict[i]
            elif (il == "translation_models"):
                try:
                    data.translation_models = json.loads(config_dict[i])
                except:
                    data.translation_models = {
                        "en-es": "Helsinki-NLP/opus-mt-en-es",
                        "es-en": "Helsinki-NLP/opus-mt-es-en"
                    }
            elif (il == "server_language"):
                data.server_language = config_dict[i]
            elif (il == "whisper_model"):
                data.whisper_model = config_dict[i]
            elif (il == "image_generation_model"):
                data.image_generation_model = config_dict[i]
            elif (il == "image_generation_steps"):
                try:
                    data.image_generation_steps = int(config_dict[i])
                except:
                    data.image_generation_steps = 10
            elif (il == "img_to_text_model"):
                data.img_to_text_model = config_dict[i]
            elif (il == "text_to_audio_model"):
                data.text_to_audio_model = config_dict[i]
            elif (il == "nsfw_filter_text_model"):
                data.nsfw_filter_text_model = config_dict[i]
            elif (il == "nsfw_filter_image_model"):
                data.nsfw_filter_image_model = config_dict[i]
            elif (il == "depth_estimation_model"):
                data.depth_estimation_model = config_dict[i]
            elif (il == "object_detection_model"):
                data.object_detection_model = config_dict[i]
            elif (il == "rvc_models"):
                try:
                    data.rvc_models = json.loads(config_dict[i])
                except:
                    data.rvc_models = {}
            elif (il == "uvr_model"):
                data.uvr_model = config_dict[i]
            elif (il == "image_to_image_model"):
                data.image_to_image_model = config_dict[i]
            elif (il == "i2i_steps"):
                try:
                    data.i2i_steps = int(config_dict[i])
                except:
                    data.i2i_steps = 10
            elif (il == "force_api_key"):
                data.force_api_key = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "low_cpu_or_memory"):
                data.low_cpu_or_memory = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "max_length"):
                try:
                    data.max_length = int(config_dict[i])
                except:
                    data.max_length = 250
            elif (il == "use_chat_history"):
                data.use_chat_history = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "use_dynamic_system_args"):
                data.use_dynamic_system_args = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "prompt_order"):
                data.prompt_order = config_dict[i]
            elif (il == "move_to_gpu"):
                data.move_to_gpu = config_dict[i]
            elif (il == "use_gpu"):
                data.use_gpu_if_available = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "ai_args"):
                data.ai_args = config_dict[i]
            elif (il == "custom_sys_msg"):
                data.custom_system_messages = config_dict[i]
            elif (il == "sys_msg_first_person"):
                data.system_messages_in_first_person = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "use_default_system_messages"):
                data.use_default_system_messages = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "temp"):
                try:
                    data.temp = float(config_dict[i])

                    if (data.temp < 0):
                        data.temp = 0
                    elif (data.temp > 1):
                        data.temp = 1
                except:
                    data.temp = 0.5
            elif (il == "save_conversations"):
                data.save_conversations = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "keys_db"):
                try:
                    kdb = json.loads(config_dict[i])
                    kdb_keys = list(kdb.keys())

                    if (kdb_keys.__contains__("use") and kdb_keys.__contains__("server") and kdb_keys.__contains__("user") and
                        kdb_keys.__contains__("password") and kdb_keys.__contains__("database") and kdb_keys.__contains__("table")):
                        data.keys_db = kdb
                except:
                    pass
            elif (il == "print_prompt"):
                data.print_prompt = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "allow_titles"):
                data.allow_titles = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "max_prompts"):
                try:
                    data.max_prompts = int(config_dict[i])

                    if (data.max_prompts <= 0):
                        data.max_prompts = 1
                except:
                    data.max_prompts = 1
            elif (il == "use_multi_model"):
                data.use_multi_model = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "multi_model_mode"):
                data.multi_model_mode = config_dict[i].lower()

                if (data.multi_model_mode != "shortest" and data.multi_model_mode != "longest"):
                    data.multi_model_mode = "longest"
            elif (il == "print_loading_message"):
                data.print_loading_message = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "enable_predicted_queue_time"):
                data.enable_predicted_queue_time = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "enabled_plugins"):
                data.enabled_plugins = config_dict[i].lower()
            elif (il == "use_only_latest_log"):
                data.use_only_latest_log = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "max_predicted_queue_time"):
                try:
                    data.max_predicted_queue_time = int(config_dict[i])

                    if (data.max_predicted_queue_time <= 0):
                        data.max_predicted_queue_time = 20
                except:
                    data.max_predicted_queue_time = 20
            elif (il == "allow_processing_if_nsfw"):
                data.allow_processing_if_nsfw = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "ban_if_nsfw"):
                data.ban_if_nsfw = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "use_local_ip"):
                data.use_local_ip = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "auto_start_rec_files_server"):
                data.auto_start_rec_files_server = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "seed"):
                try:
                    data.seed = int(config_dict[i])
                except:
                    data.seed = -1
            elif (il == "gpu_device"):
                data.gpu_device = config_dict[i]
            elif (il == "use_other_services_on_chatbot"):
                data.use_other_services_on_chatbot = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "allow_data_share"):
                data.allow_data_share = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "data_share_servers"):
                try:
                    data.data_share_servers = json.loads(config_dict[i])
                except:
                    pass
            elif (il == "data_share_timeout"):
                try:
                    data.data_share_timeout = float(config_dict[i])

                    if (data.data_share_timeout < 0):
                        data.data_share_timeout = 0
                except:
                    data.data_share_timeout = 2.5
        
        f.close()
    
    return data

def SaveConfig(cfg: ConfigData = None) -> None:
    global current_data
    Init()

    if (cfg == None):
        cfg = current_data

        if (current_data == None):
            return
    
    text = ""

    text += "gpt4all_model=" + cfg.gpt4all_model + "\n"
    text += "hf_model=" + cfg.hf_model + "\n"
    text += "text_classification_model=" + cfg.text_classification_model + "\n"
    text += "translation_classification_model=" + cfg.translation_classification_model + "\n"
    text += "translation_models=" + json.dumps(cfg.translation_models) + "\n"
    text += "server_language=" + cfg.server_language + "\n"
    text += "whisper_model=" + cfg.whisper_model + "\n"
    text += "image_generation_model=" + cfg.image_generation_model + "\n"
    text += "image_generation_steps=" + str(cfg.image_generation_steps) + "\n"
    text += "img_to_text_model=" + cfg.img_to_text_model + "\n"
    text += "text_to_audio_model=" + cfg.text_to_audio_model + "\n"
    text += "nsfw_filter_text_model=" + cfg.nsfw_filter_text_model + "\n"
    text += "nsfw_filter_image_model=" + cfg.nsfw_filter_image_model + "\n"
    text += "depth_estimation_model=" + cfg.depth_estimation_model + "\n"
    text += "object_detection_model=" + cfg.object_detection_model + "\n"
    text += "rvc_models=" + json.dumps(cfg.rvc_models) + "\n"
    text += "uvr_model=" + cfg.uvr_model + "\n"
    text += "image_to_image_model=" + cfg.image_to_image_model + "\n"
    text += "i2i_steps=" + str(cfg.i2i_steps) + "\n"
    text += "force_api_key=" + ("true" if cfg.force_api_key == True else "false") + "\n"
    text += "low_cpu_or_memory=" + ("true" if cfg.low_cpu_or_memory == True else "false") + "\n"
    text += "max_length=" + str(cfg.max_length) + "\n"
    text += "use_chat_history=" + ("true" if cfg.use_chat_history == True else "false") + "\n"
    text += "use_dynamic_system_args=" + ("true" if cfg.use_dynamic_system_args == True else "false") + "\n"
    text += "prompt_order=" + cfg.prompt_order + "\n"
    text += "move_to_gpu=" + cfg.move_to_gpu + "\n"
    text += "use_gpu=" + ("true" if cfg.use_gpu_if_available == True else "false") + "\n"
    text += "ai_args=" + cfg.ai_args + "\n"
    text += "custom_sys_msg=" + cfg.custom_system_messages + "\n"
    text += "sys_msg_first_person=" + ("true" if cfg.system_messages_in_first_person == True else "false") + "\n"
    text += "use_default_system_messages=" + ("true" if cfg.use_default_system_messages == True else "false") + "\n"
    text += "temp=" + str(cfg.temp) + "\n"
    text += "save_conversations=" + ("true" if cfg.save_conversations == True else "false") + "\n"
    text += "keys_db=" + str(cfg.keys_db).replace("'", "\"") + "\n"
    text += "print_prompt=" + ("true" if cfg.print_prompt == True else "false") + "\n"
    text += "allow_titles=" + ("true" if cfg.allow_titles == True else "false") + "\n"
    text += "max_prompts=" + str(cfg.max_prompts) + "\n"
    text += "use_multi_model=" + ("true" if cfg.use_multi_model == True else "false") + "\n"
    text += "multi_model_mode=" + cfg.multi_model_mode + "\n"
    text += "print_loading_message=" + ("true" if cfg.print_loading_message == True else "false") + "\n"
    text += "enable_predicted_queue_time=" + ("true" if cfg.enable_predicted_queue_time == True else "false") + "\n"
    text += "enabled_plugins=" + cfg.enabled_plugins + "\n"
    text += "use_only_latest_log=" + ("true" if cfg.use_only_latest_log == True else "false") + "\n"
    text += "max_predicted_queue_time=" + str(cfg.max_predicted_queue_time) + "\n"
    text += "allow_processing_if_nsfw=" + ("true" if cfg.allow_processing_if_nsfw == True else "false") + "\n"
    text += "ban_if_nsfw=" + ("true" if cfg.ban_if_nsfw == True else "false") + "\n"
    text += "use_local_ip=" + ("true" if cfg.use_local_ip == True else "false") + "\n"
    text += "auto_start_rec_files_server=" + ("true" if cfg.auto_start_rec_files_server == True else "false") + "\n"
    text += "seed=" + str(cfg.seed) + "\n"
    text += "gpu_device=" + cfg.gpu_device + "\n"
    text += "use_other_services_on_chatbot=" + ("true" if cfg.use_other_services_on_chatbot == True else "false") + "\n"
    text += "allow_data_share=" + ("true" if cfg.allow_data_share == True else "false") + "\n"
    text += "data_share_servers=" + json.dumps(cfg.data_share_servers) + "\n"
    text += "data_share_timeout=" + str(cfg.data_share_timeout) + "\n"

    with open("config.tcfg", "w") as f:
        f.write(text.strip())
        f.close()

def __get_gpu_devices__() -> None:
    devices.clear()
    
    if (current_data.gpu_device.count(";") > 0):
        devs = current_data.gpu_device.split(";")
    else:
        devs = [current_data.gpu_device]

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
    
    if (current_data.use_gpu_if_available and current_data.move_to_gpu.count(Task) > 0):
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