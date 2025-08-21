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

def GetFtype(Ftype: str) -> int | None:
    Ftype = Ftype.lower()

    if (Ftype == "tq1_0"):
        return LLAMA_FTYPE_MOSTLY_TQ1_0
    elif (Ftype == "iq1_s"):
        return LLAMA_FTYPE_MOSTLY_IQ1_S
    elif (Ftype == "iq1_m"):
        return LLAMA_FTYPE_MOSTLY_IQ1_M
    elif (Ftype == "tq2_0"):
        return LLAMA_FTYPE_MOSTLY_TQ2_0
    elif (Ftype == "iq2_xxs"):
        return LLAMA_FTYPE_MOSTLY_IQ2_XXS
    elif (Ftype == "iq2_xs"):
        return LLAMA_FTYPE_MOSTLY_IQ2_XS
    elif (Ftype == "iq2_s"):
        return LLAMA_FTYPE_MOSTLY_IQ2_S
    elif (Ftype == "iq2_m"):
        return LLAMA_FTYPE_MOSTLY_IQ2_M
    elif (Ftype == "q2_k_s"):
        return LLAMA_FTYPE_MOSTLY_Q2_K_S
    elif (Ftype == "q2_k"):
        return LLAMA_FTYPE_MOSTLY_Q2_K
    elif (Ftype == "iq3_xxs"):
        return LLAMA_FTYPE_MOSTLY_IQ3_XXS
    elif (Ftype == "iq3_xs"):
        return LLAMA_FTYPE_MOSTLY_IQ3_XS
    elif (Ftype == "iq3_s"):
        return LLAMA_FTYPE_MOSTLY_IQ3_S
    elif (Ftype == "iq3_m"):
        return LLAMA_FTYPE_MOSTLY_IQ3_M
    elif (Ftype == "q3_k_s"):
        return LLAMA_FTYPE_MOSTLY_Q3_K_S
    elif (Ftype == "q3_k_m"):
        return LLAMA_FTYPE_MOSTLY_Q3_K_M
    elif (Ftype == "q3_k_l"):
        return LLAMA_FTYPE_MOSTLY_Q3_K_L
    elif (Ftype == "q4_0"):
        return LLAMA_FTYPE_MOSTLY_Q4_0
    elif (Ftype == "q4_1"):
        return LLAMA_FTYPE_MOSTLY_Q4_1
    elif (Ftype == "iq4_xs"):
        return LLAMA_FTYPE_MOSTLY_IQ4_XS
    elif (Ftype == "iq4_nl"):
        return LLAMA_FTYPE_MOSTLY_IQ4_NL
    elif (Ftype == "q4_k_s"):
        return LLAMA_FTYPE_MOSTLY_Q4_K_S
    elif (Ftype == "q4_k_m" or Ftype == "q4_k"):
        return LLAMA_FTYPE_MOSTLY_Q4_K_M
    elif (Ftype == "q5_0"):
        return LLAMA_FTYPE_MOSTLY_Q5_0
    elif (Ftype == "q5_1"):
        return LLAMA_FTYPE_MOSTLY_Q5_1
    elif (Ftype == "q5_k_s"):
        return LLAMA_FTYPE_MOSTLY_Q5_K_S
    elif (Ftype == "q5_k_m" or Ftype == "q5_k"):
        return LLAMA_FTYPE_MOSTLY_Q5_K_M
    elif (Ftype == "q6_k"):
        return LLAMA_FTYPE_MOSTLY_Q6_K
    elif (Ftype == "q8_0"):
        return LLAMA_FTYPE_MOSTLY_Q8_0
    elif (Ftype == "fp16" or Ftype == "f16"):
        return LLAMA_FTYPE_MOSTLY_F16
    elif (Ftype == "bf16"):
        return LLAMA_FTYPE_MOSTLY_BF16
    elif (Ftype == "fp32" or Ftype == "f32"):
        return LLAMA_FTYPE_ALL_F32
    
    return None

def LoadModel(Config: dict[str, any], Threads: int, BatchThreads: int, Device: str) -> Llama:
    # Set split mode
    if ("split_mode" in list(Config.keys())):
        splitMode = Config["split_mode"].lower()

        if (splitMode == "row"):
            splitMode = LLAMA_SPLIT_MODE_ROW
        elif (splitMode == "layer"):
            splitMode = LLAMA_SPLIT_MODE_LAYER
        else:
            splitMode = LLAMA_SPLIT_MODE_NONE
    else:
        splitMode = LLAMA_SPLIT_MODE_NONE
    
    # Set main GPU
    if ("main_gpu" in list(Config.keys())):
        try:
            mainGPU = int(Config["split_mode"])
        except:
            mainGPU = 0
    else:
        mainGPU = 0
    
    # Set mmap
    if ("lcpp_use_mmap" in list(Config.keys())):
        mmap = Config["lcpp_use_mmap"]
    else:
        mmap = True
    
    # Set mlock
    if ("lcpp_use_mlock" in list(Config.keys())):
        mlock = Config["lcpp_use_mlock"]
    else:
        mlock = False
    
    # Set offload_kqv
    if ("lcpp_offload_kqv" in list(Config.keys())):
        offload_kqv = Config["lcpp_offload_kqv"]
    else:
        offload_kqv = True
    
    # Set flash_attn
    if ("flash_attn" in list(Config.keys())):
        flash_attn = Config["flash_attn"]
    else:
        flash_attn = False
    
    # Set rope scaling type
    if ("lcpp_rope_scaling" in list(Config.keys())):
        rope = Config["lcpp_rope_scaling"].lower()

        if (rope == "linear"):
            rope = LLAMA_ROPE_SCALING_TYPE_LINEAR
        elif (rope == "longrope"):
            rope = LLAMA_ROPE_SCALING_TYPE_LONGROPE
        elif (rope == "max_value"):
            rope = LLAMA_ROPE_SCALING_TYPE_MAX_VALUE
        elif (rope == "unspecified"):
            rope = LLAMA_ROPE_SCALING_TYPE_UNSPECIFIED
        elif (rope == "yarn"):
            rope = LLAMA_ROPE_SCALING_TYPE_YARN
        else:
            rope = LLAMA_ROPE_SCALING_TYPE_NONE
    else:
        rope = LLAMA_ROPE_SCALING_TYPE_NONE
    
    # Set pooling type
    if ("lcpp_pooling_type" in list(Config.keys())):
        pooling = Config["lcpp_pooling_type"].lower()

        if (pooling == "unspecified"):
            pooling = LLAMA_POOLING_TYPE_UNSPECIFIED
        elif (pooling == "mean"):
            pooling = LLAMA_POOLING_TYPE_MEAN
        elif (pooling == "cls"):
            pooling = LLAMA_POOLING_TYPE_CLS
        elif (pooling == "last"):
            pooling = LLAMA_POOLING_TYPE_LAST
        elif (pooling == "rank"):
            pooling = LLAMA_POOLING_TYPE_RANK
        else:
            pooling = LLAMA_POOLING_TYPE_NONE
    else:
        pooling = LLAMA_POOLING_TYPE_NONE
    
    # Set cache type
    if ("lcpp_cache_type" in list(Config.keys())):
        cacheType = Config["lcpp_cache_type"].lower()

        if (cacheType == "ram"):
            cacheType = LlamaRAMCache(capacity_bytes = 2 << 16)
        elif (cacheType == "disk"):
            cacheType = LlamaDiskCache(capacity_bytes = 2 << 16)
        else:
            cacheType = None
    else:
        cacheType = None
    
    # Set ftype k
    if ("lcpp_ftype_k" in list(Config.keys())):
        ftype_k = GetFtype(Config["lcpp_ftype_k"])
    else:
        ftype_k = None
    
    # Set ftype v
    if ("lcpp_ftype_v" in list(Config.keys())):
        ftype_v = GetFtype(Config["lcpp_ftype_v"])
    else:
        ftype_v = None
    
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
        type_k = ftype_k,
        type_v = ftype_v,
        embedding = False,
        no_perf = True
    )
    
    # Apply the cache to the model
    model.set_cache(cacheType)
    
    # Return the model
    return model

def GetReasoningMode(Config: dict[str, any], Reasoning: str | int | bool | None) -> tuple[dict[str, any], str, str]:
    """
    Example template:
    ```json
    {
        "modes": ["high", "medium", "low", "disabled", ...],
        "default_reasoning_mode": "high",
        "default_noreasoning_mode": "disabled",
        "default_mode": "r",
        "extra_kwargs": {
            "high": {
                "enable_thinking": true,
                ...
            },
            ...
        },
        "system_prompt": {
            "position": "end",
            "separator": " ",
            "high": "/think_high",
            ...
        },
        "user_prompt": {
            "position": "end",
            "separator": " ",
            "high": "/think_high",
            ...
        }
    }
    ```
    """
    # Get all the config
    reasoningModes: list[str] = Config["reasoning"]["modes"]  # WARNING! DO NOT USE `default`, `default_reasoning`, `default_noreasoning`, AND `custom` AS MODES.
    defaultReasoningMode: str | int = Config["reasoning"]["default_reasoning_mode"]  # Name or index in the modes list
    defaultNoReasoningMode: str | int = Config["reasoning"]["default_noreasoning_mode"]  # Name or index in the modes list
    defaultMode: str | int | bool = Config["reasoning"]["default_mode"]  # Only possible values are "r", 1, or true for reasoning, "nr", 0, or false for no reasoning
    modesKwargs: dict[str, dict[str, any]] = Config["reasoning"]["extra_kwargs"]
    modesSystemPrompt: dict[str, str] = Config["reasoning"]["system_prompt"]
    modesUserPrompt: dict[str, str] = Config["reasoning"]["user_prompt"]

    # Make sure the reasoning is valid
    if (Reasoning is None):
        Reasoning = "default"
    
    if (isinstance(Reasoning, bool)):
        if (Reasoning):
            Reasoning = "default_reasoning"
        else:
            Reasoning = "default_noreasoning"

    if (isinstance(Reasoning, int) and Reasoning >= 0 and Reasoning < len(reasoningModes)):
        Reasoning = reasoningModes[Reasoning]
    elif (Reasoning == -1):
        Reasoning = "default"
    elif (Reasoning == -2):
        Reasoning = "default_reasoning"
    elif (Reasoning == -3):
        Reasoning == "default_noreasoning"

    if (Reasoning == "default"):
        if (defaultMode == True or defaultMode == 1 or defaultMode == "r"):
            Reasoning = defaultReasoningMode
        elif (defaultMode == False or defaultMode == 0 or defaultMode == "nr"):
            Reasoning = defaultNoReasoningMode
        else:
            raise ValueError("Error in server configuration. Default mode must be `r` or `nr`.")
    elif (Reasoning == "default_reasoning"):
        Reasoning = defaultReasoningMode
    elif (Reasoning == "default_noreasoning"):
        Reasoning = defaultNoReasoningMode
    elif (Reasoning == "custom"):
        return ({}, "[SYSTEM PROMPT]", "[USER PROMPT]")
    
    if (Reasoning not in reasoningModes):
        raise ValueError(f"Reasoning value ({Reasoning}) not found in {reasoningModes} nor it's indexes.")
    
    # Get the variables from this reasoning mode
    kwargs = modesKwargs[Reasoning]
    systemPrompt = modesSystemPrompt[Reasoning]
    userPrompt = modesUserPrompt[Reasoning]

    # Make sure the system prompt token position is valid
    if (modesSystemPrompt["position"] != "start" and modesSystemPrompt["position"] != "end" and len(systemPrompt.strip()) > 0):
        raise ValueError("Error in server configuration. Reasoning token position is neither `start` nor `end` (system prompt).")
    
    # Make sure the user prompt token position is valid
    if (modesUserPrompt["position"] != "start" and modesUserPrompt["position"] != "end" and len(userPrompt.strip()) > 0):
        raise ValueError("Error in server configuration. Reasoning token position is neither `start` nor `end` (user prompt).")
    
    # Return all the values
    return (
        # Return kwargs
        kwargs,

        # Return system prompt
        (f"{systemPrompt}{modesSystemPrompt['separator']}" if (modesSystemPrompt["position"] == "start") else "") +
            "[SYSTEM PROMPT]" +
            (f"{modesSystemPrompt['separator']}{systemPrompt}" if (modesSystemPrompt["position"] == "end") else ""),
        
        # Return user prompt
        (f"{userPrompt}{modesUserPrompt['separator']}" if (modesUserPrompt["position"] == "start") else "") +
            "[USER PROMPT]" +
            (f"{modesUserPrompt['separator']}{userPrompt}" if (modesUserPrompt["position"] == "end") else "")
    )