# Import I4.0's utilities
import ai_config as cfg

# Import other libraries
from transformers import AutoModelForImageTextToText, AutoProcessor, TextIteratorStreamer
from qwen_omni_utils import process_mm_info
from collections.abc import Iterator
import threading
import json

def __load_model__(Config: dict[str, any], Index: int) -> tuple[AutoModelForImageTextToText, AutoProcessor, str, str]:
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

    return cfg.LoadModel("chatbot", Index, AutoModelForImageTextToText, AutoProcessor, modelExtraKWargs, processorExtraKWargs)

def __inference__(
        Model: AutoModelForImageTextToText,
        Processor: AutoProcessor,
        Device: str,
        Dtype: str,
        Config: dict[str, any],
        ContentForModel: list[dict[str, list[dict[str, str]]]],
        Seed: int | None,
        Tools: list[dict[str, str | dict[str, any]]],
        MaxLength: int,
        Temperature: float,
        TopP: float,
        TopK: int,
        MinP: float,
        TypicalP: float
    ) -> Iterator[tuple[str, list[dict[str, any]]]]:
    # Apply the chat template using the processor
    text = Processor.apply_chat_template(ContentForModel, xml_tools = Tools, tokenize = False, add_generation_prompt = True)

    # Tokenize the prompt
    audio_inputs, image_inputs, video_inputs = process_mm_info(ContentForModel, use_audio_in_video = True)  # Should work for all models, even if it's not a Qwen model
    inputs = Processor(text = text, audios = audio_inputs, images = image_inputs, videos = video_inputs, padding = True, return_tensors = "pt")
    inputs = inputs.to(Device).to(Dtype)

    # Set streamer
    streamer = TextIteratorStreamer(Processor, skip_prompt = True, skip_special_tokens = True)

    # Set inference args
    generationKwargs = dict(
        **inputs,
        temperature = Temperature,
        max_new_tokens = MaxLength,
        top_p = TopP,
        top_k = TopK,
        min_p = MinP,
        typical_p = TypicalP,
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

        # Print the token and yield it
        print(token, end = "", flush = True)
        yield token
    
    # Print an empty message when done
    print("", flush = True)