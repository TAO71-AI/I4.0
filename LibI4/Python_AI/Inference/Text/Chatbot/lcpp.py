# Import I4.0's utilities
import Inference.PredefinedModels.models as models

# Import other libraries
from llama_cpp import (
    Llama,
    LlamaDiskCache,
    LlamaRAMCache,
    LLAMA_SPLIT_MODE_LAYER,
    LLAMA_SPLIT_MODE_ROW,
    LLAMA_SPLIT_MODE_NONE,
    LLAMA_ROPE_SCALING_TYPE_LINEAR,
    LLAMA_ROPE_SCALING_TYPE_LONGROPE,
    LLAMA_ROPE_SCALING_TYPE_MAX_VALUE,
    LLAMA_ROPE_SCALING_TYPE_NONE,
    LLAMA_ROPE_SCALING_TYPE_UNSPECIFIED,
    LLAMA_ROPE_SCALING_TYPE_YARN,
    LLAMA_POOLING_TYPE_UNSPECIFIED,
    LLAMA_POOLING_TYPE_NONE,
    LLAMA_POOLING_TYPE_MEAN,
    LLAMA_POOLING_TYPE_CLS,
    LLAMA_POOLING_TYPE_LAST,
    LLAMA_POOLING_TYPE_RANK,
    LLAMA_FTYPE_ALL_F32,
    LLAMA_FTYPE_MOSTLY_BF16,
    LLAMA_FTYPE_MOSTLY_F16,
    LLAMA_FTYPE_MOSTLY_Q2_K_S,
    LLAMA_FTYPE_MOSTLY_Q2_K,
    LLAMA_FTYPE_MOSTLY_Q3_K_S,
    LLAMA_FTYPE_MOSTLY_Q3_K_M,
    LLAMA_FTYPE_MOSTLY_Q3_K_L,
    LLAMA_FTYPE_MOSTLY_Q4_0,
    LLAMA_FTYPE_MOSTLY_Q4_1,
    LLAMA_FTYPE_MOSTLY_Q4_K_S,
    LLAMA_FTYPE_MOSTLY_Q4_K_M,
    LLAMA_FTYPE_MOSTLY_Q5_0,
    LLAMA_FTYPE_MOSTLY_Q5_1,
    LLAMA_FTYPE_MOSTLY_Q5_K_S,
    LLAMA_FTYPE_MOSTLY_Q5_K_M,
    LLAMA_FTYPE_MOSTLY_Q6_K,
    LLAMA_FTYPE_MOSTLY_Q8_0
)
from huggingface_hub import hf_hub_download
from collections.abc import Iterator
import os
import json

def __parse_llama_ftype__(Ftype: str | None) -> int | None:
    # Check if the ftype input is none
    if (Ftype is None):
        return None

    FTYPES = {
        "q2_k_s": LLAMA_FTYPE_MOSTLY_Q2_K_S,
        "q2_k": LLAMA_FTYPE_MOSTLY_Q2_K,
        "q3_k_s": LLAMA_FTYPE_MOSTLY_Q3_K_S,
        "q3_k_m": LLAMA_FTYPE_MOSTLY_Q3_K_M,
        "q3_k_l": LLAMA_FTYPE_MOSTLY_Q3_K_L,
        "q4_0": LLAMA_FTYPE_MOSTLY_Q4_0,
        "q4_1": LLAMA_FTYPE_MOSTLY_Q4_1,
        "q4_k_s": LLAMA_FTYPE_MOSTLY_Q4_K_S,
        "q4_k_m": LLAMA_FTYPE_MOSTLY_Q4_K_M,
        "q5_0": LLAMA_FTYPE_MOSTLY_Q5_0,
        "q5_1": LLAMA_FTYPE_MOSTLY_Q5_1,
        "q5_k_s": LLAMA_FTYPE_MOSTLY_Q5_K_S,
        "q5_k_m": LLAMA_FTYPE_MOSTLY_Q5_K_M,
        "q6_k": LLAMA_FTYPE_MOSTLY_Q6_K,
        "q8_0": LLAMA_FTYPE_MOSTLY_Q8_0,
        "fp16": LLAMA_FTYPE_MOSTLY_F16,
        "f16": LLAMA_FTYPE_MOSTLY_F16,
        "bf16": LLAMA_FTYPE_MOSTLY_BF16,
        "fp32": LLAMA_FTYPE_ALL_F32,
        "f32": LLAMA_FTYPE_ALL_F32
    }
    Ftype = Ftype.lower()

    # Return the Ftype or none if not found
    return FTYPES.get(Ftype, None)

def __load_model__(Config: dict[str, any], Repo: str, Model: str, Threads: int, BatchThreads: int, Device: str) -> Llama:
    # Set split mode
    try:
        # Get the split mode
        splitMode = Config["split_mode"].lower()

        # Check if the split mode is valid
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
            # Invalid split mode or is layer, set to default
            splitMode = LLAMA_SPLIT_MODE_LAYER
    except:
        # Error; probably `split_mode` is not configured, set to default
        splitMode = LLAMA_SPLIT_MODE_LAYER
    
    # Set mmap
    try:
        # Get the mmap
        mmap = Config["lcpp_use_mmap"]
    except:
        # Error; probably `lcpp_use_mmap` is not configured, set to default
        mmap = True
    
    # Set mlock
    try:
        # Get the mlock
        mlock = Config["lcpp_use_mlock"]
    except:
        # Error; probably `lcpp_use_mlock` is not configured, set to default
        mlock = False
    
    # Set offload_kqv
    try:
        # Get the offload_kqv
        offload_kqv = Config["lcpp_offload_kqv"]
    except:
        # Error; probably `lcpp_offload_kqv` is not configured, set to default
        offload_kqv = True
    
    # Set flash_attn
    try:
        # Get the flash_attn
        flash_attn = Config["lcpp_flash_attn"]
    except:
        # Error; probably `lcpp_flash_attn` is not configured, set to default
        flash_attn = False
    
    # Set rope scaling type
    try:
        # Get the rope scaling type
        rope = Config["lcpp_rope_scaling"].lower()

        # Check if the rope scaling type is valid
        if (rope == "linear"):
            # Set rope scaling to linear
            rope = LLAMA_ROPE_SCALING_TYPE_LINEAR
        elif (rope == "longrope"):
            # Set rope scaling to longrope
            rope = LLAMA_ROPE_SCALING_TYPE_LONGROPE
        elif (rope == "max_value"):
            # Set rope scaling to max_value
            rope = LLAMA_ROPE_SCALING_TYPE_MAX_VALUE
        elif (rope == "none"):
            # Set rope scaling to none
            rope = LLAMA_ROPE_SCALING_TYPE_NONE
        elif (rope == "yarn"):
            # Set rope scaling to yarn
            rope = LLAMA_ROPE_SCALING_TYPE_YARN
        else:
            # Invalid rope scaling type or is unspecified, set to default
            rope = LLAMA_ROPE_SCALING_TYPE_UNSPECIFIED
    except:
        # Error; probably `lcpp_rope_scaling` is not configured, set to default
        rope = LLAMA_ROPE_SCALING_TYPE_UNSPECIFIED
    
    # Set pooling type
    try:
        # Get the pooling type
        pooling = Config["lcpp_pooling_type"].lower()

        # Check if the pooling type is valid
        if (pooling == "none"):
            # Set pooling type to none
            pooling = LLAMA_POOLING_TYPE_NONE
        elif (pooling == "mean"):
            # Set pooling type to mean
            pooling = LLAMA_POOLING_TYPE_MEAN
        elif (pooling == "cls"):
            # Set pooling type to cls
            pooling = LLAMA_POOLING_TYPE_CLS
        elif (pooling == "last"):
            # Set pooling type to last
            pooling = LLAMA_POOLING_TYPE_LAST
        elif (pooling == "rank"):
            # Set pooling type to rank
            pooling = LLAMA_POOLING_TYPE_RANK
        else:
            # Invalid pooling type or is unspecified, set to default
            pooling = LLAMA_POOLING_TYPE_UNSPECIFIED
    except:
        # Error; probably `lcpp_pooling_type` is not configured, set to default
        pooling = LLAMA_POOLING_TYPE_UNSPECIFIED
    
    # Get the ftype_k
    ftype_k = __parse_llama_ftype__(Config.get("lcpp_ftype_k", None))
    
    # Get the ftype_v
    ftype_v = __parse_llama_ftype__(Config.get("lcpp_ftype_v", None))
    
    # Set cache type
    try:
        # Get the cache type
        cacheType = Config["lcpp_cache_type"].lower()

        # Check if the cache type is valid
        if (cacheType == "ram"):
            # Use RAM cache
            cacheType = LlamaRAMCache(capacity_bytes = 2 << 16)
        elif (cacheType == "disk"):
            # Use disk cache
            cacheType = LlamaDiskCache(capacity_bytes = 2 << 16)
        else:
            # Invalid cache type or is none, use default
            cacheType = None
    except:
        # Error; probably `lcpp_cache_type` is not configured, set to default
        cacheType = None

    # Set args
    args = dict(
        n_ctx = Config["ctx"],
        verbose = False,
        n_gpu_layers = Config["ngl"] if (Device != "cpu") else 0,
        n_batch = Config["batch"],
        n_ubatch = Config["ubatch"],
        split_mode = splitMode,
        chat_format = None,
        logits_all = False,
        n_threads = Threads,
        n_threads_batch = BatchThreads,
        use_mmap = mmap,
        use_mlock = mlock,
        rope_scaling_type = rope,
        offload_kqv = offload_kqv,
        flash_attn = flash_attn,
        pooling_type = pooling,
        type_k = ftype_k,
        type_v = ftype_v,
        embedding = False,
        no_perf = False
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
    
    # Apply the cache to the model
    model.set_cache(cacheType)
    
    # Return the model
    return model

def __load_custom_model__(Config: dict[str, any], Threads: int, BatchThreads: int, Device: str) -> Llama:
    # Get the model path
    modelRepo = Config["model"][0]
    modelName = Config["model"][1]

    # Model is expected to be:
    # [
    #     "Model repository (optional if you set model path)",
    #     "Model file name / model path"
    # ]

    # Load and return the model
    return __load_model__(Config, modelRepo, modelName, Threads, BatchThreads, Device)

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

def __get_model_from_pretrained__(Name: str, ModelQuantization: str) -> str | None:
    # Lower and strip the quantizations
    ModelQuantization = ModelQuantization.lower().strip()

    # Check if the model exists in the list
    if (Name not in list(models.Chatbot_NF_LCPP.keys())):
        return None
    
    # Model
    modelQ = __get_quantization_and_repo_from_dict__(models.Chatbot_NF_LCPP[Name]["model"], ModelQuantization)

    # Download everything
    modelPath = hf_hub_download(models.Chatbot_NF_LCPP[Name]["repo"], modelQ)

    # Return the data
    return modelPath

def __load_predefined_model__(Config: dict[str, any], Threads: int, BatchThreads: int, Device: str) -> Llama | None:
    # Model is expected to be:
    # [
    #     "Model name",
    #     "Model quantization"
    # ]

    # Lower the model name
    Config["model"][0] = Config["model"][0].lower()
    modelPath = __get_model_from_pretrained__(Config["model"][0], Config["model"][1])

    if (modelPath is None):
        return None

    # Load the model
    return __load_model__(Config, "", modelPath, Threads, BatchThreads, Device)

def LoadModel(Config: dict[str, any], Threads: int, BatchThreads: int, Device: str) -> Llama:
    # Try to load using the predefined list
    model = __load_predefined_model__(Config, Threads, BatchThreads, Device)

    if (model is None):
        # Error; invalid model
        # Load as a custom one
        model = __load_custom_model__(Config, Threads, BatchThreads, Device)
    
    return model

def __inference__(
        Model: Llama,
        Config: dict[str, any],
        ContentForModel: list[dict[str, str]],
        Seed: int | None,
        Tools: list[dict[str, str | dict[str, any]]],
        MaxLength: int,
        Temperature: float,
        TopP: float,
        TopK: int
    ) -> Iterator[str]:
    # Get a response from the model
    response = Model.create_chat_completion(
        messages = ContentForModel,
        temperature = Temperature,
        max_tokens = MaxLength,
        top_p = TopP,
        top_k = TopK,
        seed = Seed,
        tools = Tools,
        tool_choice = None,
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

        # Get the tools
        tools = token["choices"][0]["delta"].get("tool_calls")

        if (tools is not None):
            for tool in token["choices"][0]["delta"]["tool_calls"]:
                yield json.dumps(tool["function"])

        # Yield the token
        yield t
    
    # Print an empty message when done
    print("", flush = True)