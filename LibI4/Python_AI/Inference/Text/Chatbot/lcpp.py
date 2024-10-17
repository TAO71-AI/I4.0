# Import LLaMA-CPP-Python
from llama_cpp import Llama
from llama_cpp.llama_chat_format import hf_autotokenizer_to_chat_completion_handler

# Import some other libraries
from collections.abc import Iterator
import os

# Import I4.0's utilities
import ai_config as cfg

def __load_model__(Config: dict[str, any], Threads: int, Device: str) -> Llama:
    # Check the model's chat template path
    if (len(Config["model"][2].strip()) == 0):
        Config["model"][2] = Config["model"][0]
        
    # Set args
    args = dict(
        n_ctx = Config["ctx"],
        verbose = False,
        n_gpu_layers = Config["ngl"] if (Device != "cpu") else 0,
        n_batch = Config["batch"],
        chat_handler = hf_autotokenizer_to_chat_completion_handler(Config["model"][2]) if (len(Config["model"][2].strip()) > 0) else None,
        chat_format = Config["model"][3] if (len(Config["model"][2].strip()) == 0 and len(Config["model"][3].strip()) > 0) else None,
        logits_all = True,
        n_threads = Threads,
        n_threads_batch = Threads
    )

    # Check if the model is a local file
    if (os.path.exists(Config["model"][1]) and os.path.isfile(Config["model"][1])):
        # Load the model from the local file
        model = Llama(
            model_path = Config["model"][1],
            **args
        )
    else:
        # Load the model from the HuggingFace repository
        model = Llama.from_pretrained(
            repo_id = Config["model"][0],
            filename = Config["model"][1],
            **args
        )
    
    # Return the model
    return model

def __inference__(Model: Llama, Config: dict[str, any], ContentForModel: list[dict[str, str]]) -> Iterator[str]:
    # Get a response from the model
    response = Model.create_chat_completion(
        messages = ContentForModel,
        temperature = Config["temp"],
        max_tokens = cfg.current_data["max_length"],
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