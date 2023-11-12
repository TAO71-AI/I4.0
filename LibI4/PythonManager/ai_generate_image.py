from diffusers import DiffusionPipeline
import torch
import os
import ai_config as cfg

pipeline = None

def LoadModel() -> None:
    global pipeline
    
    if (pipeline != None):
        return
    
    pipeline = DiffusionPipeline.from_pretrained(cfg.current_data.image_generation_model)

    move_to_gpu = cfg.current_data.use_gpu_if_available and torch.cuda.is_available() and cfg.current_data.move_to_gpu.__contains__("text2img")
    device = "cuda" if (move_to_gpu) else "cpu"

    if (cfg.current_data.print_loading_message):
        print("Loading model 'text to image' on device '" + device + "'...")

    pipeline = pipeline.to(device)

def GenerateImage(prompt: str) -> bytes:
    LoadModel()

    if (prompt.startswith("\"") or prompt.startswith("'")):
        prompt = prompt[1:len(prompt)]
    
    if (prompt.endswith("\"") or prompt.endswith("'")):
        prompt = prompt[0:len(prompt) - 2]

    image = pipeline(prompt, num_inference_steps = cfg.current_data.image_generation_steps).images[0]

    with open("ti.png", "w+") as f:
        f.close()
    
    image.save("ti.png")

    with open("ti.png", "rb") as f:
        image = f.read()
        f.close()

    os.remove("ti.png")
    return image