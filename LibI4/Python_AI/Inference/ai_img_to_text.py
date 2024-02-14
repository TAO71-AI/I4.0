from transformers import pipeline, Pipeline
import PIL.Image
import torch
import ai_config as cfg

pipe: Pipeline = None
device: str = "cpu"

def __load_model__(model_name: str, device: str) -> Pipeline:
    return pipeline("image-to-text", model = model_name, device = device)

def LoadModel() -> None:
    global pipe, device

    if (not cfg.current_data.prompt_order.__contains__("img2text")):
        raise Exception("Model is not in 'prompt_order'.")

    if (pipe != None):
        return
    
    move_to_gpu = cfg.current_data.use_gpu_if_available and torch.cuda.is_available() and cfg.current_data.move_to_gpu.__contains__("img2text")
    device = "cuda" if (move_to_gpu) else "cpu"

    if (cfg.current_data.print_loading_message):
        print("Loading model 'image to text' on device '" + device + "'...")

    pipe = __load_model__(cfg.current_data.img_to_text_model, device)

def MakePrompt(img: str) -> str:
    LoadModel()

    if (cfg.current_data.print_prompt):
        print("Image To Text file: " + img)

    image = PIL.Image.open(img)
    response = pipe(image)[0]["generated_text"]

    if (cfg.current_data.print_prompt):
        print("Image to Text response: " + str(response))

    return str(response)