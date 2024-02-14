from transformers import Pipeline, pipeline
import torch
import ai_config as cfg

model_name: str = cfg.current_data.text_classification_model

pipe: Pipeline = None
device: str = "cpu"

def __load_model__(model_name: str, device: str):
    return pipeline(task = "text-classification", model = model_name, device = device)

def LoadModel() -> None:
    global pipe, device

    if (not cfg.current_data.prompt_order.__contains__("sc")):
        raise Exception("Model is not in 'prompt_order'.")

    if (pipe != None or len(model_name.strip()) == 0):
        return
    
    move_to_gpu = torch.cuda.is_available() and cfg.current_data.use_gpu_if_available and cfg.current_data.move_to_gpu.__contains__("sc")
    device = "cuda" if (move_to_gpu) else "cpu"

    if (cfg.current_data.print_loading_message):
        print("Loading model 'text classification' on device '" + device + "'...")

    pipe = __load_model__(model_name, device)

def DoPrompt(prompt: str) -> str:
    LoadModel()

    if (pipe == None):
        return "-1"

    result = pipe(prompt)
    result = result[0]["label"]

    return str(result).lower()