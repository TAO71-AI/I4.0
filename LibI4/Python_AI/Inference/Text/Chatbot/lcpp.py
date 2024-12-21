# Import LLaMA-CPP-Python
from llama_cpp import Llama, LLAMA_SPLIT_MODE_LAYER, LLAMA_SPLIT_MODE_ROW, LLAMA_SPLIT_MODE_NONE

# Import some other libraries
from huggingface_hub import hf_hub_download
from collections.abc import Iterator
import os

# Import I4.0's utilities
import Inference.PredefinedModels.models as models
import ai_config as cfg

def __load_model__(Config: dict[str, any], Repo: str, Model: str, ChatTemplate: str | None, Threads: int, Device: str) -> Llama:
    # Set split mode
    try:
        # Get the split mode
        splitMode = Config["split_mode"].lower()

        # Check if the split mode is valid
        if (splitMode != "layer" and splitMode != "row" and splitMode != "none"):
            # Invalid split mode, set to default (layer)
            splitMode = "layer"
    except:
        # Error; probably `split_mode` is not configured, set to default (layer)
        splitMode = "layer"
    
    if (splitMode == "layer"):
        # Set split mode to layer
        splitMode = LLAMA_SPLIT_MODE_LAYER
    elif (splitMode == "row"):
        # Set split mode to row
        splitMode = LLAMA_SPLIT_MODE_ROW
    elif (splitMode == "none"):
        # Set split mode to none
        splitMode = LLAMA_SPLIT_MODE_NONE
    else:
        # Invalid split mode, set to default (layer)
        splitMode = LLAMA_SPLIT_MODE_LAYER

    # Set args
    args = dict(
        n_ctx = Config["ctx"],
        verbose = False,
        n_gpu_layers = Config["ngl"] if (Device != "cpu") else 0,
        n_batch = Config["batch"],
        n_ubatch = Config["batch"],
        split_mode = splitMode,
        chat_format = ChatTemplate if (ChatTemplate != None and len(ChatTemplate) > 0) else None,
        logits_all = True,
        n_threads = Threads,
        n_threads_batch = Threads
    )

    # Check if the model is a local file
    if (os.path.exists(Model) and os.path.isfile(Model)):
        # Load the model from the local file
        model = Llama(
            model_path = Model,
            **args
        )
    else:
        # Load the model from the HuggingFace repository
        model = Llama.from_pretrained(
            repo_id = Repo,
            filename = Model,
            **args
        )
    
    # Return the model
    return model

def __load_custom_model__(Config: dict[str, any], Threads: int, Device: str) -> Llama:
    # Get the model path
    modelRepo = Config["model"][0]
    modelName = Config["model"][1]
    modelTemplate = Config["model"][2]

    # Model is expected to be:
    # [
    #     "Model repository (optional if you set model path)",
    #     "Model file name / model path",
    #     "Chat template"
    # ]

    # Load and return the model
    return __load_model__(Config, modelRepo, modelName, modelTemplate, Threads, Device)

def __get_quantization_and_repo_from_dict__(Dict: dict[str, any], DesiredQuantization: str) -> str:
    # Get quantization
    if (list(Dict.keys()).count(DesiredQuantization) == 0):
        # Invalid quantization, set default
        quantization = Dict[Dict["default"]]

        # Check that the quantization exists
        if (list(Dict.keys()).count(quantization) == 0):
            # It doesn't exists
            raise ValueError(f"Invalid quantization '{DesiredQuantization}'; '{quantization}'. Available quantizations are: {[i for i in list(Dict.keys()) if (i != 'default')]}.")
    else:
        # Use the desired quantization
        quantization = Dict[DesiredQuantization]
    
    # Return the quantization and repository
    return quantization

def __get_model_from_pretrained__(Name: str, ModelQuantization: str) -> tuple[str, str]:
    # Lower and strip the quantizations
    ModelQuantization = ModelQuantization.lower().strip()

    # Check if the model exists in the list
    if (list(models.Chatbot_NF_LCPP.keys()).count(Name) == 0):
        raise ValueError(f"Invalid model name. Available models are: {list(models.Chatbot_NF_LCPP.keys())}.")
    
    # Model
    modelQ = __get_quantization_and_repo_from_dict__(models.Chatbot_NF_LCPP[Name]["model"], ModelQuantization)

    # Download everything
    modelPath = hf_hub_download(models.Chatbot_NF_LCPP[Name]["repo"], modelQ)

    # Return the data
    return (modelPath, models.Chatbot_NF_LCPP[Name]["template"])

def __load_predefined_model__(Config: dict[str, any], Threads: int, Device: str) -> Llama:
    # Model is expected to be:
    # [
    #     "Model name",
    #     "Model quantization"
    # ]

    # Lower the model name
    Config["model"][0] = Config["model"][0].lower()
    modelPath, modelTemplate = __get_model_from_pretrained__(Config["model"][0], Config["model"][1])

    # Load the model
    return __load_model__(Config, "", modelPath, modelTemplate, Threads, Device)

def LoadModel(Config: dict[str, any], Threads: int, Device: str) -> Llama:
    try:
        # Try to load using the predefined list
        return __load_predefined_model__(Config, Threads, Device)
    except ValueError:
        # Error; invalid model
        # Load as a custom one
        return __load_custom_model__(Config, Threads, Device)

def __inference__(Model: Llama, Config: dict[str, any], ContentForModel: list[dict[str, str]], Seed: int | None) -> Iterator[str]:
    # Get a response from the model
    response = Model.create_chat_completion(
        messages = ContentForModel,
        temperature = Config["temp"],
        max_tokens = cfg.current_data["max_length"],
        seed = Seed,
        stream = True
    )

    # For every token
    for token in response:
        # Check if it's valid (contains a response)
        if (not "content" in token["choices"][0]["delta"]):
            continue
            
        # Print the token
        t = token["choices"][0]["delta"]["content"]
        print(t, end = "", flush = True)

        # Yield the token
        yield t
        
    # Print an empty message when done
    print("", flush = True)