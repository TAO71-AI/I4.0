from diffusers import DiffusionPipeline
import torch
import os
import json
import ai_config as cfg

pipeline: DiffusionPipeline = None
device: str = "cpu"

def LoadModel() -> None:
    global pipeline, device

    if (not cfg.current_data.prompt_order.__contains__("text2img")):
        raise Exception("Model is not in 'prompt_order'.")
    
    if (pipeline != None):
        return
    
    pipeline = DiffusionPipeline.from_pretrained(cfg.current_data.image_generation_model)

    move_to_gpu = cfg.current_data.use_gpu_if_available and torch.cuda.is_available() and cfg.current_data.move_to_gpu.__contains__("text2img")
    device = "cuda" if (move_to_gpu) else "cpu"

    if (cfg.current_data.print_loading_message):
        print("Loading model 'text to image' on device '" + device + "'...")

    pipeline.to(device)

def GenerateImage(prompt: str | dict[str, str]) -> bytes:
    if (type(prompt) == dict[str, str]):
        return __generate_image__(prompt["prompt"], prompt["negative_prompt"])
    
    try:
        p = dict(prompt.replace("\"", "\'"))
        return __generate_image__(p["prompt"], p["negative_prompt"])
    except:
        p = json.loads(prompt)
        return __generate_image__(p["prompt"], p["negative_prompt"])

def __generate_image__(prompt: str, negative_prompt: str) -> bytes:
    LoadModel()

    if (prompt.startswith("\"") or prompt.startswith("'")):
        prompt = prompt[1:len(prompt)]
    
    if (prompt.endswith("\"") or prompt.endswith("'")):
        prompt = prompt[0:len(prompt) - 2]
    
    if (negative_prompt.startswith("\"") or negative_prompt.startswith("'")):
        negative_prompt = negative_prompt[1:len(negative_prompt)]
    
    if (negative_prompt.endswith("\"") or negative_prompt.endswith("'")):
        negative_prompt = negative_prompt[0:len(negative_prompt) - 2]
    
    if (cfg.current_data.print_prompt):
        print("Prompt: " + prompt)
        print("Negative prompt: " + negative_prompt)

    image = pipeline(prompt, num_inference_steps = cfg.current_data.image_generation_steps, output_type = "pil", negative_prompt = negative_prompt).images[0]
    img_name = "ti.png"
    img_n = 0

    while (os.path.exists(img_name)):
        img_n += 1
        img_name = "ti_" + str(img_n) + ".png"

    with open(img_name, "w+") as f:
        f.close()
    
    image.save(img_name)

    with open(img_name, "rb") as f:
        image = f.read()
        f.close()

    os.remove(img_name)
    return image