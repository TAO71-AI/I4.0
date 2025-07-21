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
    LLAMA_FTYPE_MOSTLY_Q8_0,
    LLAMA_FTYPE_MOSTLY_Q6_K,
    LLAMA_FTYPE_MOSTLY_Q5_K_M,
    LLAMA_FTYPE_MOSTLY_Q5_K_S,
    LLAMA_FTYPE_MOSTLY_Q5_1,
    LLAMA_FTYPE_MOSTLY_Q5_0,
    LLAMA_FTYPE_MOSTLY_Q4_K_M,
    LLAMA_FTYPE_MOSTLY_Q4_K_S,
    LLAMA_FTYPE_MOSTLY_IQ4_NL,
    LLAMA_FTYPE_MOSTLY_IQ4_XS,
    LLAMA_FTYPE_MOSTLY_Q4_1,
    LLAMA_FTYPE_MOSTLY_Q4_0,
    LLAMA_FTYPE_MOSTLY_Q3_K_L,
    LLAMA_FTYPE_MOSTLY_Q3_K_M,
    LLAMA_FTYPE_MOSTLY_Q3_K_S,
    LLAMA_FTYPE_MOSTLY_IQ3_M,
    LLAMA_FTYPE_MOSTLY_IQ3_S,
    LLAMA_FTYPE_MOSTLY_IQ3_XS,
    LLAMA_FTYPE_MOSTLY_IQ3_XXS,
    LLAMA_FTYPE_MOSTLY_Q2_K,
    LLAMA_FTYPE_MOSTLY_Q2_K_S,
    LLAMA_FTYPE_MOSTLY_IQ2_M,
    LLAMA_FTYPE_MOSTLY_IQ2_S,
    LLAMA_FTYPE_MOSTLY_IQ2_XS,
    LLAMA_FTYPE_MOSTLY_IQ2_XXS,
    LLAMA_FTYPE_MOSTLY_TQ2_0,
    LLAMA_FTYPE_MOSTLY_IQ1_M,
    LLAMA_FTYPE_MOSTLY_IQ1_S,
    LLAMA_FTYPE_MOSTLY_TQ1_0
)
from llama_cpp.llama_chat_format import (
    Llava15ChatHandler,
    Llava16ChatHandler,
    MoondreamChatHandler,
    NanoLlavaChatHandler,
    Llama3VisionAlphaChatHandler,
    MiniCPMv26ChatHandler,
    Qwen25VLChatHandler
)

def LoadModel(Config: dict[str, any], Threads: int, BatchThreads: int, Device: str) -> Llama:
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
    
    # Set main GPU
    try:
        # Get the main GPU
        mainGPU = int(Config["split_mode"])
    except:
        # Error; probably `main_gpu` is not configured, set to default
        mainGPU = 0
    
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
    
    # Set chat handler
    chatHandler = None

    if ("multimodal" in list(Config.keys()) and len(Config["multimodal"].strip()) > 0):
        if (
            isinstance(Config["model"], dict) and
            Config["multimodal"].strip() == "image" and
            "model_path" in list(Config["model"].keys()) and
            "mmproj" in list(Config["model"].keys()) and
            "handler" in list(Config["model"].keys())
        ):
            model = Config["model"]["model_path"]
            mmproj = Config["model"]["mmproj"]
            handler = Config["model"]["handler"].strip().lower()

            if (handler == "llava-1.5" or handler == "llava1.5" or handler == "llava-15" or handler == "llava15"):
                chatHandler = Llava15ChatHandler(
                    clip_model_path = mmproj,
                    verbose = False
                )
            elif (handler == "llava-1.6" or handler == "llava1.6" or handler == "llava-16" or handler == "llava16"):
                chatHandler = Llava16ChatHandler(
                    clip_model_path = mmproj,
                    verbose = False
                )
            elif (handler == "moondream2"):
                chatHandler = MoondreamChatHandler(
                    clip_model_path = mmproj,
                    verbose = False
                )
            elif (handler == "nanollava"):
                chatHandler = NanoLlavaChatHandler(
                    clip_model_path = mmproj,
                    verbose = False
                )
            elif (handler == "llama-3-vision-alpha"):
                chatHandler = Llama3VisionAlphaChatHandler(
                    clip_model_path = mmproj,
                    verbose = False
                )
            elif (handler == "minicpm-v-2.6" or handler == "minicpm-v-26"):
                chatHandler = MiniCPMv26ChatHandler(
                    clip_model_path = mmproj,
                    verbose = False
                )
            elif (handler == "qwen2.5-vl"):
                chatHandler = Qwen25VLChatHandler(
                    clip_model_path = mmproj,
                    verbose = False
                )
        
        if (chatHandler is None):
            raise ValueError("Multimodal is set for llama.cpp, but the model parameter is not valid or the chat handler is not valid. Please keep in mind that lcpp only supports image multimodal models for now, so make sure the `multimodal` parameter is only `image`, if you see this error it might also be due to this.")
    else:
        model = Config["model"]

    # Load the model from the local file
    model = Llama(
        model_path = model,
        n_ctx = Config["ctx"],
        verbose = False,
        main_gpu = mainGPU,
        n_gpu_layers = Config["ngl"] if (Device != "cpu") else 0,
        n_batch = Config["batch"],
        n_ubatch = Config["ubatch"],
        split_mode = splitMode,
        chat_format = None,
        chat_handler = chatHandler,
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
        no_perf = True
    )
    
    # Apply the cache to the model
    model.set_cache(cacheType)
    
    # Return the model
    return model