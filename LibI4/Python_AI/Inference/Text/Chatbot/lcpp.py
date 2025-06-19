# Import I4.0's utilities
import Inference.PredefinedModels.gguf_model_parser as ggufParser

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
    LLAMA_POOLING_TYPE_RANK
)
from collections.abc import Iterator
import json

def __load_model__(Config: dict[str, any], Model: str, Threads: int, BatchThreads: int, Device: str) -> Llama:
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

    # Load the model from the local file
    model = Llama(
        model_path = Model,
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
        embedding = False,
        no_perf = False
    )
    
    # Apply the cache to the model
    model.set_cache(cacheType)
    
    # Return the model
    return model

def LoadModel(Config: dict[str, any], Threads: int, BatchThreads: int, Device: str) -> Llama:
    # Parse the model
    model = ggufParser.AutoParse(Config["model"], True)

    # Make sure the model is a string
    if (isinstance(model, tuple)):
        model = model[1]

    # Load the model
    model = __load_model__(Config, model, Threads, BatchThreads, Device)
    
    # Return the model
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
        TopK: int,
        MinP: float,
        TypicalP: float
    ) -> Iterator[str]:
    # Check if the tools must be in the system prompt
    if ("lcpp_tools_in_system_prompt" in list(Config.keys()) and Config["lcpp_tools_in_system_prompt"] and len(Tools) > 0):
        # Add the tools to the system prompt
        ContentForModel[0]["content"] = f"Available tools:\n```json\n{json.dumps(Tools, indent = 4)}\n```\n\n---\n\n{ContentForModel[0]['content']}"
        Tools = None
    elif (len(Tools) == 0):
        # No tools, set to None
        Tools = None

    # Get a response from the model
    response = Model.create_chat_completion(
        messages = ContentForModel,
        temperature = Temperature,
        max_tokens = MaxLength,
        top_p = TopP,
        top_k = TopK,
        min_p = MinP,
        typical_p = TypicalP,
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