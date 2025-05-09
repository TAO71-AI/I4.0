# Import HuggingFace Transformers
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer

# Import some other libraries
from collections.abc import Iterator
import threading

# Import I4.0's utilities
import ai_config as cfg

def __load_model__(Config: dict[str, any], Index: int) -> tuple[AutoModelForCausalLM, AutoTokenizer, str, str]:
    modelExtraKWargs = {}

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

    return cfg.LoadModel("chatbot", Index, AutoModelForCausalLM, AutoTokenizer, modelExtraKWargs)

def __inference__(
        Model: AutoModelForCausalLM,
        Tokenizer: AutoTokenizer,
        Device: str,
        Dtype: str,
        Config: dict[str, any],
        ContentForModel: list[dict[str, str]],
        MaxLength: int,
        Temperature: float,
        TopP: float,
        TopK: int
    ) -> Iterator[str]:
    # Apply the chat template using the tokenizer
    text = Tokenizer.apply_chat_template(ContentForModel, tokenize = False, add_generation_prompt = True)

    # Tokenize the prompt
    inputs = Tokenizer([text], return_tensors = "pt")
    inputs = inputs.to(Device).to(Dtype)

    # Set streamer
    streamer = TextIteratorStreamer(Tokenizer, skip_prompt = True, skip_special_tokens = True)

    # Set inference args
    generationKwargs = dict(
        inputs,
        temperature = Temperature,
        max_new_tokens = MaxLength,
        streamer = streamer,
        top_p = TopP,
        top_k = TopK,
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