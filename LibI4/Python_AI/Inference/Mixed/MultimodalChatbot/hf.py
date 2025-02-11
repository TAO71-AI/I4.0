# Import HuggingFace Transformers
from transformers import AutoModelForVision2Seq, AutoProcessor, TextIteratorStreamer
from qwen_vl_utils import process_vision_info

# Import some other libraries
from collections.abc import Iterator
import threading
import torch

# Import I4.0's utilities
import ai_config as cfg

def __load_model__(Config: dict[str, any], Index: int) -> tuple[AutoModelForVision2Seq, AutoProcessor, str]:
    modelExtraKWargs = {}
    processorExtraKWargs = {
        "min_pixels": 256 * 28 * 28,
        "max_pixels": 1280 * 28 * 28
    }

    try:
        # Set the specs to use
        modelExtraKWargs["low_cpu_mem_usage"] = Config["hf_low"] != None and Config["hf_low"]
    except:
        # Ignore
        pass

    # Check if the model's extra kwargs are empty
    if (len(modelExtraKWargs) == 0):
        # They're, delete
        modelExtraKWargs = None
    
    # Check if the processor's extra kwargs are empty
    if (len(processorExtraKWargs) == 0):
        # They're, delete
        processorExtraKWargs = None

    return cfg.LoadModel("chatbot", Index, AutoModelForVision2Seq, AutoProcessor, modelExtraKWargs, processorExtraKWargs)

def __inference__(Model: AutoModelForVision2Seq, Processor: AutoProcessor, Device: str, Config: dict[str, any], ContentForModel: list[dict[str, list[dict[str, str]]]]) -> Iterator[str]:
    # Apply the chat template using the processor
    text = Processor.apply_chat_template(ContentForModel, tokenize = False, add_generation_prompt = True)

    # Tokenize the prompt
    image_inputs, video_inputs = process_vision_info(ContentForModel)  # Should work for all models, even if it's not a Qwen model
    inputs = Processor(text = [text], images = image_inputs, videos = video_inputs, padding = True, return_tensors = "pt")  # Doesn't support audios for now
    inputs = inputs.to(Device)

    # Set streamer
    streamer = TextIteratorStreamer(Processor)

    # Set inference args
    generationKwargs = dict(
        **inputs,
        temperature = Config["temp"],
        max_new_tokens = cfg.current_data["max_length"],
        streamer = streamer,
        do_sample = True
    )

    # Create new thread for the model and generate
    generationThread = threading.Thread(target = Model.generate, kwargs = generationKwargs)
    generationThread.start()
    firstToken = True

    # For each token
    for token in streamer:
        # Ignore if it's the same as the input
        if (firstToken):
            firstToken = False
            continue

        # Cut the response
        if (token.count("<|im_end|>")):
            token = token[:token.index("<|im_end|>")]

        if (token.count("<|im_start|>")):
            token = token[token.index("<|im_start|>") + 12:]

        # Print the token and yield it
        print(token, end = "", flush = True)
        yield token
    
    # Print an empty message when done
    print("", flush = True)