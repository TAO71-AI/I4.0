from transformers import Pipeline, pipeline, AutoModel, AutoTokenizer
from diffusers import AutoPipelineForText2Image
import os
import json
import torch

devices: list[str] = []
__config_data__: dict[str] = {
    "server_language": "en",                                                                    # Sets the default language to translate a prompt.
    "force_api_key": True,                                                                      # Makes API keys required for using the AI models.
    "max_length": 250,                                                                          # Sets the max length that the chatbots (`g4a`, `hf`...) can generate.
    "use_dynamic_system_args": True,                                                            # Creates some extra system prompt for the chatbots (example: the current date, the state of humour...).
    "ai_args": "",                                                                              # Sets some default args for the chatbot (mostly to define the personality, like: +evil, +self-aware...). Can be changed by the user.
    "custom_system_messages": "",                                                               # Sets a custom system prompt from the server.
    "custom_api_admin_system_messages": "",                                                     # Sets a custom system prompt if the user's key is set as admin.
    "custom_api_nadmin_system_messages": "",                                                    # Sets a custom system prompt if the user's key is NOT set as admin.
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
    "enabled_plugins": "sing vtuber discord_bot twitch gaming image_generation audio_generation internet",
    # ^-- I4.0 plugins that creates more system prompts.
    "allow_processing_if_nsfw": [False, False],                                                 # Allows the processing of a prompt even if it's detected as NSFW.
    #                           [Text, Image]
    "ban_if_nsfw": True,                                                                        # Bans the API key if a NSFW prompt is detected (requires `force_api_key` to be true).
    "ban_if_nsfw_ip": True,                                                                     # Bans the IP of the user if a NSFW prompt is detected.
    "use_local_ip": False,                                                                      # Disables the public IP address use for the server (only accepts connections from `127.0.0.1`, recommended for personal use).
    "allow_data_share": True,                                                                   # Allows data sharing to TAO71's servers to make a better dataset for I4.0 and train AI models on that dataset (shares the user's prompt [files included], service used and the server's response and it's 100% anonymous).
    "data_share_servers": ["tao71.sytes.net"],                                                  # List of servers to share the data.
    "data_share_timeout": 2.5,                                                                  # Seconds to wait per server response on data share.
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
        "prefix": "!i4",                                                                            # Command prefix.
    },
    "force_device_check": True,                                                                 # Will check if the device is compatible.
    "max_files_size": 250,                                                                      # Maximum size allowed for files in MB.
    "save_conversation_files": True,                                                            # Will save the files of the conversation, may require a lot of disk space and compute power.
    "models": [                                                                                 # Models to be used.
        # Examples:
        #{
        #    "service": "chatbot",
        #    "type": "lcpp",
        #    "ctx": 2048,
        #    "threads": -1,
        #    "ngl": -1,
        #    "batch": 8,
        #    "model": [
        #        "MODEL REPOSITORY (leave empty if you're going to use a path)",
        #        "MODEL FILE NAME / MODEL PATH",
        #        "TEMPLATE REPOSITORY",
        #        "CHAT TEMPLATE"  # Set if you're going to leave the template repository empty!
        #        # ^-- If `TEMPLATE REPOSITORY` and `CHAT TEMPLATE` are both empty, LLaMA-CPP-Python will use the tokenizer's chat template. Might fail in most of old GGUF models.
        #    ],
        #    "temp": 0.5,
        #    "device": "cpu",
        #    "allows_files": false,  # Doesn't support multimodal models
        #    "price": 20
        #},
        #{
        #    "service": "chatbot",
        #    "type": "g4a",
        #    "ctx": 2048,
        #    "threads": -1,
        #    "ngl": -1,
        #    "batch": 8,
        #    "model": "MODEL REPOSITORY / MODEL PATH",
        #    "temp": 0.5,
        #    "device": "cpu",
        #    "allows_files": false,  # Doesn't support multimodal models
        #    "price": 20
        #},
        #{
        #    "service": "chatbot",
        #    "type": "hf",
        #    "ctx": 2048,
        #    "threads": -1,
        #    "ngl": -1,
        #    "batch": 8,
        #    "model": "MODEL REPOSITORY / MODEL PATH",
        #    "hf_dtype": "",                # Set the torch.dtype to use (leave empty to set automatically).
        #    "hf_low": False,               # False loads the model normally, True if you have low specs.
        #    "temp": 0.5,
        #    "device": "cpu",
        #    "allows_files": (false or true),
        #    "price": 20
        #},
        #{
        #    "service": "qa",
        #    "model": "MODEL REPOSITORY",
        #    "device": "cpu",
        #    "price": 5
        #},
        #{
        #    "service": "img2img",
        #    "model": "MODEL REPOSITORY",
        #    "steps": 4,
        #    "device": "cpu",
        #    "price": 20
        #},
        #{
        #    "service": "uvr",
        #    "model": "MODEL NAME",
        #    "device": "cpu",
        #    "price": 15
        #},
        #{
        #    "service": "rvc",
        #    "model": [
        #        "MODEL NAME",
        #        "MODEL PATH",
        #        "INDEX PATH",
        #        "MODEL TYPE (rmvpe, harvest, pm, etc.)"
        #    ],
        #    "device": "cpu",
        #    "price": 15
        #},
        #{
        #    "service": "od",
        #    "model": "MODEL REPOSITORY",
        #    "device": "cpu",
        #    "price": 7.5
        #},
        #{
        #    "service": "de",
        #    "model": "MODEL REPOSITORY",
        #    "device": "cpu",
        #    "price": 10
        #},
        #{
        #    "service": "nsfw_filter-text",
        #    "model": "MODEL REPOSITORY",
        #    "device": "cpu",
        #    "nsfw_label": "",
        #    "price": 2.5
        #},
        #{
        #    "service": "nsfw_filter-image",
        #    "model": "MODEL REPOSITORY",
        #    "device": "cpu",
        #    "nsfw_label": "",
        #    "price": 2.5
        #},
        #{
        #    "service": "text2audio",
        #    "model": "MODEL REPOSITORY",
        #    "device": "cpu",
        #    "price": 20
        #},
        #{
        #    "service": "img2text",
        #    "model": "MODEL REPOSITORY",
        #    "device": "cpu",
        #    "price": 7.5
        #},
        #{
        #    "service": "text2img",
        #    "type": "hf",
        #    "model": "MODEL REPOSITORY",
        #    "device": "cpu",
        #    "steps": 8,
        #    "guidance": 3,
        #    "width": 1024,
        #    "height": 1024,
        #    "threads": -1,
        #    "price": 20
        #},
        #{
        #    "service": "text2img",
        #    "type": "`sdcpp-sd` for StableDiffusion models or `sdcpp-flux` for flux models",
        #    "model": [
        #        "model path",
        #        "vae / clip_g model path",
        #        "clip_l model path",
        #        "t5xxl model path"
        #     ],
        #    "device": "cpu",
        #    "steps": 8,
        #    "guidance": 3,
        #    "width": 1024,
        #    "height": 1024,
        #    "threads": -1,
        #    "price": 20
        #},
        #{
        #    "service": "text2img",
        #    "type": "`sdcpp-sd` for StableDiffusion models or `sdcpp-flux` for flux models",
        #    "model": [
        #        "model name",
        #        "model quantization",
        #        "vae / clip_g quantization",
        #        "clip_l quantization",
        #        "t5xxl quantization"
        #     ],
        #    "device": "cpu",
        #    "steps": 8,
        #    "guidance": 3,
        #    "width": 1024,
        #    "height": 1024,
        #    "threads": -1,
        #    "price": 20
        #},
        #{
        #    "service": "speech2text",
        #    "type": "[`whisper` or `hf`]",
        #    "model": "MODEL NAME / MODEL REPOSITORY",
        #    "batch": 8,
        #    "temp": 0.5,
        #    "device": "cpu",
        #    "price": 12
        #},
        #{
        #    "service": "ld",
        #    "model": "MODEL REPOSITORY",
        #    "device": "cpu",
        #    "price": 1.5
        #},
        #{
        #    "service": "tr",
        #    "model": "MODEL REPOSITORY",
        #    "lang": "[INPUT LANGUAGE]-[OUTPUT LANGUAGE]",
        #    "device": "cpu",
        #    "price": 7.5
        #},
        #{
        #    "service": "sc",
        #    "model": "MODEL REPOSITORY",
        #    "device": "cpu",
        #    "price": 1.5
        #},
        #{
        #    "service": "tts",
        #    "price": 1
        #}
        #
        #
        # NOTE: You can also add a description and information of the model for each model, expample:
        #{
        #    "service": "sc",
        #    "model": "MODEL REPOSITORY",
        #    "device": "cpu",
        #    "price": 1.5,
        #    "description": "DESCRIPTION HERE",
        #    "model_info": ""  # This is some extra info about the model that will be sent to the model when inference via System Prompts.
        #}
    ]
}

def Init() -> None:
    # Check if the config file exists
    if (not os.path.exists("config.json")):
        # It doesn't exist, create it
        with open("config.json", "w+") as f:
            f.close()
        
        # Save the config
        SaveConfig(__config_data__)
        print("Configuration created at 'config.json'! To start the server, please run this script again.")

        # Close the program
        os._exit(0)

def ReadConfig() -> dict[str]:
    # Initialize
    Init()
    
    # Read the config file
    with open("config.json", "r") as f:
        data: dict[str, any] = json.loads(f.read())
        f.close()
    
    # For each option in the data
    for dkey in list(data.keys()):
        # Check if the option exists in the config template
        if (dkey not in list(__config_data__.keys())):
            # It doesn't exist, delete the option from the data
            data.pop(dkey)
            continue

    # For each option in the config template
    for dkey in list(__config_data__.keys()):
        # Check if the option exists in the data
        if (dkey not in list(data.keys())):
            # It doesn't exist, add it with the default value from the config template
            data[dkey] = __config_data__[dkey]
    
    # Save the config
    SaveConfig(data)

    # Return the config
    return data

def SaveConfig(Config: dict[str] = {}) -> None:
    # Initialize
    Init()

    # Check if the length of the config is 0
    if (len(list(Config.keys())) == 0):
        # It is, set the config to the current config
        Config = current_data.copy()

        # Check if the current config exists
        if (current_data == None):
            # If it doesn't, return
            return
    
    # Convert the config dict to a JSON text with indent
    text = json.dumps(Config, indent = 4)

    # Save the config into the config file
    with open("config.json", "w") as f:
        f.write(text)
        f.close()

def GetAvailableGPUDeviceForTask(Task: str, Index: int) -> str:
    # Get the device set for the task
    device = GetInfoOfTask(Task, Index)["device"]

    # Check if the force_device_check flag is set to true in the config
    if (list(current_data.keys()).count("force_device_check") > 0 and not current_data["force_device_check"]):
        # Return the device without checking
        return device

    # Check if the device specified for this model is available
    if (
        (device == "cuda" and torch.cuda.is_available()) or             # Check for NVIDIA or AMD GPUs
        (device == "xpu" and torch.xpu.is_available())                  # Check for Intel GPUs
    ):
        # The device set is compatible, return the device
        return device
    elif (device != "cpu"):
        # Print message
        print(f"WARNING! Tryed to use the device '{device}', but torch doesn't support it. Returning 'cpu' instead.")
    
    # The device is not available, return the cpu
    return "cpu"

def LoadPipeline(PipeTask: str, Task: str, Index: int, ExtraKWargs: dict[str, any] | None = None) -> tuple[Pipeline, str]:
    # Get the device to use
    dev = GetAvailableGPUDeviceForTask(Task, Index)

    # Print the loading message
    print(f"Loading (transformers) pipeline for the service '{Task.upper()} [INDEX {Index}]' on the device '{dev}'...")

    # Set the args dict
    args = {}

    # Check if the extra kwargs are set
    if (ExtraKWargs != None):
        # It is, copy to the args
        args = ExtraKWargs.copy()
    
    # Set the required args
    args["task"] = PipeTask
    args["model"] = GetInfoOfTask(Task, Index)["model"]
    args["device"] = dev

    # Load the pipeline using the specified args
    pipe = pipeline(**args)

    # Print the done loading message
    print("   Done!")

    # Return the pipeline and the device where the model is loaded
    return (pipe, dev)

def LoadDiffusersPipeline(Task: str, Index: int, CustomPipelineType: type | None = None, ExtraKWargs: dict[str, any] | None = None) -> tuple[any, str]:
    # Check the pipeline type
    if (CustomPipelineType == None):
        # No pipeline type set, use an automatic pipeline for text to image
        CustomPipelineType = AutoPipelineForText2Image
    
    # Get the device to use
    dev = GetAvailableGPUDeviceForTask(Task, Index)

    # Print loading message
    print(f"Loading (diffusers) pipeline for the service '{Task.upper()} [INDEX {Index}]' on the device '{dev}'...")

    # Set args dict
    args = {}

    # Check if the extra kwargs are set
    if (ExtraKWargs != None):
        # It is, copy to the args
        args = ExtraKWargs.copy()
    
    # Set the required args
    args["pretrained_model_or_path"] = GetInfoOfTask(Task, Index)["model"]
    args["device"] = dev

    # Check the pipeline type
    if (Task == "img2img"):
        # It's for image to image, set some extra args
        args["safety_checker"] = None
        args["requires_safety_checker"] = False
    
    # Load the pipeline using the specified args
    pipe = CustomPipelineType.from_pretrained(**args)
    
    # Print the done loading message
    print("   Done!")

    # Return the pipeline and the device where the model is loaded
    return (pipe, dev)

def LoadModel(Task: str, Index: int, ModelType: type | None = None, TokenizerType: type | None = None, ExtraKWargsModel: dict[str, any] | None = None, ExtraKWargsTokenizer: dict[str, any] | None = None) -> tuple[any, any, str]:
    # Check the model type
    if (ModelType == None):
        # No model type specified, set a default model type
        ModelType = AutoModel
    
    # Check the tokenizer type
    if (TokenizerType == None):
        # No tokenizer type specified, set a default tokenizer type
        TokenizerType = AutoTokenizer

    # Get the available GPU to use for this model
    dev = GetAvailableGPUDeviceForTask(Task, Index)

    # Set args dicts
    argsModel = {}
    argsTokenizer = {}

    # Check if the extra kwargs are set for the model
    if (ExtraKWargsModel != None):
        # It is, copy to the args
        argsModel = ExtraKWargsModel.copy()
    
    # Check if the extra kwargs are set for the tokenizer
    if (ExtraKWargsTokenizer != None):
        # It is, copy to the args
        argsTokenizer = ExtraKWargsTokenizer.copy()
    
    # Set the model and tokenizer
    argsModel["pretrained_model_name_or_path"] = GetInfoOfTask(Task, Index)["model"]
    argsTokenizer["pretrained_model_name_or_path"] = GetInfoOfTask(Task, Index)["model"]

    # Print loading message
    print(f"Loading model for '{Task.upper()} [INDEX {Index}]' on the device '{dev}'...")

    # Load the model and tokenizer using the args
    model = ModelType.from_pretrained(**argsModel).to(dev)
    tokenizer = TokenizerType.from_pretrained(**argsTokenizer)

    # Print the done loading message
    print("   Done!")

    # Return the model, tokenizer and device where the model is loaded
    return (model, tokenizer, dev)

def JSONDeserializer(SerilizedText: str) -> dict:
    try:
        # Try to return the result loaded using JSON
        return json.loads(SerilizedText)
    except:
        # Error, check if the text starts and ends with "{" and "}"
        if (SerilizedText.startswith("{") and SerilizedText.endswith("}")):
            # It does
            try:
                # Try to return the result loaded using eval
                return eval(SerilizedText)
            except:
                # Error, return the result loaded using JSON, but replacing the quotes with double quotes
                return json.loads(SerilizedText.replace("\'", "\""))
        
        # Return an error message
        raise Exception("No valid text.")

def GetAllTasks() -> dict[str, list[dict[str, any]]]:
    # Create dict
    tasks = {}

    # For each task
    for task in GetAllInfosOfATask():
        try:
            # Try to append the task to the dictionary
            tasks[task["service"]].append(task)
        except:
            # Could not append it, probably the list doesn't exists, create it
            tasks[task["service"]] = [task]
    
    # Return the tasks
    return tasks

def GetAllInfosOfATask(Service: str) -> list[dict[str, any]]:
    # Create the list
    infos = []

    # For each model in the current data
    for model in current_data["models"]:
        # Check if the model belongs to the specified service
        if (model["service"] == Service):
            # It does, append it to the list of infos for the service
            infos.append(model)
    
    # Return the list of infos for the service
    return infos

def GetInfoOfTask(Service: str, Index: int) -> dict[str, any] | None:
    # Get the list of infos for the specified service
    tasks = GetAllInfosOfATask(Service)

    # Check if the index is valid
    if (Index >= len(tasks) and len(tasks) > 0):
        raise ValueError("Index > len(tasks)")
    elif (Index < 0):
        raise ValueError("Index < 0")
    elif (len(tasks) == 0):
        return None
    
    # Return the info of the task at the specified index
    return tasks[Index]

# Load the config
current_data = ReadConfig()