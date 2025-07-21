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
    "use_default_system_messages": True,                                                        # Use pre-defined system prompt.
    "db": {                                                                                     # Database. NOTE: From now on all the servers MUST HAVE a database in order to work as expected.
        "host": "127.0.0.1",                                                                        # Database host server.
        "user": "",                                                                                 # Database username.
        "password": "",                                                                             # Database password.
        "db": "",                                                                                   # Database name.
        "hash": "sha512",                                                                           # Hash algorithm to use, `sha512` is recommended.
        "keys": {                                                                                   # Table: Keys.
            "table": "",                                                                                # Name of the table.
            "key": "key",                                                                               # Name of the parameter "key".
            "tokens": "tokens",                                                                         # Name of the parameter "tokens".
            "daily": "daily",                                                                           # Name of the parameter "daily".
            "date": "key_date",                                                                         # Name of the parameter "date".
            "default": "default",                                                                       # Name of the parameter "default".
            "admin": "admin",                                                                           # Name of the parameter "admin".
            "temporal_conversations": "temp_conversations"                                              # Name of the parameter "temporal_conversations".
        },
        "conversations": {                                                                          # Table: Conversations.
            "table": "",                                                                                # Name of the table.
            "user": "key",                                                                              # Name of the parameter "user".
            "conversation_name": "conv_name",                                                           # Name of the parameter "conversation_name".
            "conversation_data": "conv_data",                                                           # Name of the parameter "conversation_data".
            "temporal": "temp"                                                                          # Name of the parameter "temporal".
        },
        "memories": {                                                                               # Table: Memories.
            "table": "",                                                                                # Name of the table.
            "user": "key",                                                                              # Name of the parameter "user".
            "memory": "memory"                                                                          # Name of the parameter "memory".
        },
        "data_save": {                                                                              # Table: Data save.
            "table": "",                                                                                # Name of the table.
            "message_user": "message_user",                                                             # Name of the parameter "message_user".
            "message_response": "message_response"                                                      # Name of the parameter "message_response".
        },
        "cache": {                                                                                  # Table: Cache.
            "table": "",                                                                                # Name of the table.
            "system_prompt": "system_prompt",                                                           # Name of the parameter "system_prompt".
            "user_prompt": "user_prompt",                                                               # Name of the parameter "user_prompt".
            "ai_response": "ai_response"                                                                # Name of the parameter "ai_response".
        },
        "dataset": {                                                                                # Table: Dataset.
            "table": "",                                                                                # Name of the table.
            "keywords": "keywords",                                                                     # Name of the parameter "keywords".
            "response": "response"                                                                      # Name of the parameter "response".
        }
    },
    "internet": {                                                                               # Internet configuration.
        "min_length": 10,                                                                           # Min length for each line.
        "min_results": 1,                                                                           # Min number websites to search.
        "max_results": 3,                                                                           # Max number of websites to search.
        "research": {                                                                               # Internet research configuration.
            "price": 40,                                                                                # Extra price of the internet research (WARNING: The tokens that this will take will be `[chatbot price] * ([internet max websites] + 1) + [this price]`).
            "reasoning_mode": -1                                                                        # -1 = Switch automatically between using reasoning or not. 0 = ALWAYS use reasoning. 1 = NEVER use reasoning.
        },
        "system": "auto"                                                                            # Library to use when searching from internet.
    },
    "enabled_tools": "image-generation audio-generation internet internet-url internet-research memory memory-edit memory-delete document-creator",
    # ^-- I4.0 tools.
    "allow_processing_if_nsfw": [False, False],                                                 # Allows the processing of a prompt even if it's detected as NSFW.
    #                           [Text, Image]
    "ban_if_nsfw": True,                                                                        # Bans the API key if a NSFW prompt is detected (requires `force_api_key` to be true).
    "ban_if_nsfw_ip": True,                                                                     # Bans the IP of the user if a NSFW prompt is detected.
    "use_local_ip": False,                                                                      # Disables the public IP address use for the server (only accepts connections from `127.0.0.1`, recommended for personal use).
    "server_port": 8060,                                                                        # Port of the server.
    "force_device_check": True,                                                                 # Will check if the device is compatible.
    "max_files_size": 250,                                                                      # Maximum size allowed for files in MB.
    "save_conversation_files": True,                                                            # Will save the files of the conversation, may require a lot of disk space and compute power.
    "offload_time": 3600,                                                                       # Time (in seconds) to wait before offloading a model that has not been used. Set to 0 to disable.
    "clear_queue_time": 600,                                                                    # Time (in seconds) to wait before clearing the queue. Set to 0 to disable.
    "clear_temporal_conversations_time": 1500,                                                  # Time (in seconds) to wait before clearing the queue. Set to 0 to disable.
    "allowed_hashes": [                                                                         # Allowed hashes for receive data. See documentation for more information.
        "none", "sha224", "sha256", "sha384", "sha512",
    ],
    "nokey_temporal_conversations": {                                                           # Temporal conversation dates
        "day": 7,                                                                                   # How many days the conversation will be saved?
        "month": 0,                                                                                 # How many months the conversation will be saved?
        "year": 0,                                                                                  # How many years the conversation will be saved?
        "hour": 0,                                                                                  # How many hours the conversation will be saved?
        "minute": 0                                                                                 # How many minutes the conversation will be saved?
    },
    "allow_data_save": True,                                                                    # Allow the usage of data save.
    "data_save_max_fs": 0,                                                                      # Max file size allowed (in MB) to use the data save. Set to 0 to don't save any files.
    "allow_response_cache": True,                                                               # Allow response cache.             WORKING ON THIS.
    "ssl": {                                                                                    # SSL configuration.
        "cert": "",                                                                                 # Path to the SSL certificate.
        "key": ""                                                                                   # Path to the SSL key.
    },
    "models": []                                                                                # Models to be used.
}

def Init() -> None:
    # Check if the config file exists
    if (not os.path.exists("config.json")):
        # It doesn't exist, create it
        with open("config.json", "w+") as f:
            f.write(json.dumps(current_data, indent = 4))

        print("Configuration created at 'config.json'! To start the server, please run this script again.")

        # Close the program
        os._exit(0)

def ReadConfig() -> dict[str, any]:
    # Initialize
    Init()
    
    # Read the config file
    with open("config.json", "r") as f:
        data: dict[str, any] = json.loads(f.read())
    
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

            # Save the configuration
            SaveConfig(data)

    # Return the config
    return data

def SaveConfig(Config: dict[str, any] | None = None) -> None:
    # Initialize
    Init()

    # Check if the configuration is null
    if (Config is None):
        # Set the current configuration
        Config = current_data
    
    # Save into the file
    with open("config.json", "w") as f:
        f.write(json.dumps(Config, indent = 4))

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
        print(f"WARNING! Tried to use the device '{device}', but torch doesn't support it. Returning 'cpu' instead.")
    
    # The device is not available, return the cpu
    return "cpu"

def __get_dtype_from_str__(Dtype: str) -> torch.dtype | None:
    if (Dtype == "fp64"):
        return torch.float64
    elif (Dtype == "fp32"):
        return torch.float32
    elif (Dtype == "fp16"):
        return torch.float16
    elif (Dtype == "bf16"):
        return torch.bfloat16
    elif (Dtype == "fp8_e4m3fn"):
        return torch.float8_e4m3fn
    elif (Dtype == "fp8_e4m3fnuz"):
        return torch.float8_e4m3fnuz
    elif (Dtype == "fp8_e5m2"):
        return torch.float8_e5m2
    elif (Dtype == "fp8_e5m2fnuz"):
        return torch.float8_e5m2fnuz
    elif (Dtype == "i64"):
        return torch.int64
    elif (Dtype == "i32"):
        return torch.int32
    elif (Dtype == "i16"):
        return torch.int16
    elif (Dtype == "i8"):
        return torch.int8
    elif (Dtype == "u64"):
        return torch.uint64
    elif (Dtype == "u32"):
        return torch.uint32
    elif (Dtype == "u16"):
        return torch.uint16
    elif (Dtype == "u8"):
        return torch.uint8

    return None

def LoadPipeline(PipeTask: str, Task: str, Index: int, ExtraKWargs: dict[str, any] | None = None) -> tuple[Pipeline, str]:
    # Get the device to use
    dev = GetAvailableGPUDeviceForTask(Task, Index)
    info = GetInfoOfTask(Task, Index)

    # Print the loading message
    print(f"Loading (transformers) pipeline for the service '{Task.upper()} [INDEX {Index}]' on the device '{dev}'...")

    # Set the args dict
    args = {}

    # Check if the extra kwargs are set
    if (ExtraKWargs != None):
        # It is, copy to the args
        args = ExtraKWargs.copy()
    
    # Set dtype
    try:
        args["torch_dtype"] = __get_dtype_from_str__(info["dtype"])
    except:
        args["torch_dtype"] = torch.float32

    # Set the required args
    args["task"] = PipeTask
    args["model"] = info["model"]
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
    info = GetInfoOfTask(Task, Index)

    # Print loading message
    print(f"Loading (diffusers) pipeline for the service '{Task.upper()} [INDEX {Index}]' on the device '{dev}'...")

    # Set args dict
    args = {}

    # Check if the extra kwargs are set
    if (ExtraKWargs != None):
        # It is, copy to the args
        args = ExtraKWargs.copy()
    
    # Set dtype
    try:
        args["torch_dtype"] = __get_dtype_from_str__(info["dtype"])
    except:
        args["torch_dtype"] = torch.float32
    
    # Set the required args
    args["pretrained_model_or_path"] = info["model"]
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

def LoadModel(Task: str, Index: int, ModelType: type | None = None, TokenizerType: type | None = None, ExtraKWargsModel: dict[str, any] | None = None, ExtraKWargsTokenizer: dict[str, any] | None = None) -> tuple[any, any, str, str]:
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
    info = GetInfoOfTask(Task, Index)

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
    
    # Set dtype
    try:
        argsModel["torch_dtype"] = __get_dtype_from_str__(info["dtype"])
    except:
        argsModel["torch_dtype"] = torch.float32
    
    # Set the model and tokenizer
    argsModel["pretrained_model_name_or_path"] = info["model"]
    argsTokenizer["pretrained_model_name_or_path"] = info["model"]

    # Print loading message
    print(f"Loading model for '{Task.upper()} [INDEX {Index}]' on the device '{dev}'...")

    # Load the model and tokenizer using the args
    model = ModelType.from_pretrained(**argsModel).to(dev)
    tokenizer = TokenizerType.from_pretrained(**argsTokenizer)

    # Print the done loading message
    print("   Done!")

    # Return the model, tokenizer and device where the model is loaded
    return (model, tokenizer, dev, argsModel["torch_dtype"])

def JSONDeserializer(SerializedText: str) -> dict[any, any] | list[any]:
    try:
        # Try to return the result loaded using JSON
        return json.loads(SerializedText)
    except:
        # Error, check if the text starts and ends with "{" and "}"
        if ((SerializedText.startswith("{") and SerializedText.endswith("}")) or (SerializedText.startswith("[") and SerializedText.endswith("]"))):
            # It does
            try:
                # Try to return the result loaded using eval
                return eval(SerializedText)
            except:
                # Error, return the result loaded using JSON, but replacing the quotes with double quotes
                return json.loads(SerializedText.replace("\'", "\""))
        
        # Return an error message
        raise Exception("No valid text.")

def GetAllTasks() -> dict[str, list[dict[str, any]]]:
    # Create dict
    tasks = {}

    # For each task
    for model in current_data["models"]:
        # Set the task
        try:
            # Try to append the task to the dictionary
            tasks[model["service"]].append(model)
        except:
            # Could not append it, probably the list doesn't exists, create it
            tasks[model["service"]] = [model]
    
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

# Check if the database is invalid
if (len(current_data["db"]["host"].strip()) == 0 or len(current_data["db"]["user"].strip()) == 0 or len(current_data["db"]["db"].strip()) == 0):
    # Invalid DB
    # Check if the config file exists
    if (not os.path.exists("config.json")):
        # It doesn't exist, create it
        with open("config.json", "w+") as f:
            f.write(json.dumps(current_data, indent = 4))
    
    # Return exception
    raise Exception("Invalid database configuration. Since v13.0.0 a MySQL database is required.")