# Import LLaMA-CPP-Python
from gpt4all import GPT4All

# Import some other libraries
from collections.abc import Iterator
import os

# Import I4.0's utilities
import ai_config as cfg

def __load_model__(Config: dict[str, any], Threads: int, Device: str) -> GPT4All:
    # Get the device
    if (Device != "cpu"):
        Device = "gpu"

    # Load the model
    model = GPT4All(
        model_name = Config["model"],
        model_path = Config["model"] if (os.path.exists(Config["model"]) and os.path.isfile(Config["model"])) else None,
        allow_download = True,
        n_threads = Threads,
        device = Device,
        n_ctx = Config["ctx"],
        ngl = Config["ngl"],
        verbose = False
    )

    # Return the model
    return model

def __inference__(Model: GPT4All, Config: dict[str, any], ContentForModel: list[dict[str, str]], Conv: str) -> Iterator[str]:
    # Transform system prompts to a string
    sp = ""

    for p in ContentForModel:
        if (p["role"] == "system"):
            sp += p["content"] + "\n"
        
    sp = sp.strip()

    # Inference the model
    with Model.chat_session(system_prompt = sp, prompt_template = "{0}\n### RESPONSE: "):
        # Get a response from the model
        response = Model.generate(
            prompt = Conv,
            max_tokens = cfg.current_data["max_length"],
            temp = Config["temp"],
            n_batch = Config["batch"],
            streaming = True
        )

        # Print every token and yield it
        for token in response:
            print(token, end = "", flush = True)
            yield token
            
        # Print an empty message when done
        print("", flush = True)