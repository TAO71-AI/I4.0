from diffusers import AutoPipelineForImage2Image
from PIL import Image, ImageOps
import torch
import os
import json
import ai_config as cfg

pipeline: AutoPipelineForImage2Image = None
device: str = "cpu"

def LoadModel() -> None:
    global pipeline, device

    if (not cfg.current_data.prompt_order.__contains__("img2img")):
        raise Exception("Model is not in 'prompt_order'.")
    
    if (pipeline != None):
        return
    
    if (cfg.current_data.print_loading_message):
        print("Loading model 'image to image'...")
    
    data = cfg.LoadDiffusersPipeline("img2img", cfg.current_data.image_to_image_model, AutoPipelineForImage2Image)

    pipeline = data[0]
    device = data[1]

    if (cfg.current_data.print_loading_message):
        print("   Loaded model on device '" + device + "'.")

def Prompt(prompt: str | dict[str, str]) -> list[bytes]:
    if (type(prompt) == dict[str, str] or type(prompt) == dict):
        return __process__(prompt["prompt"], prompt["image"])
    
    try:
        p = dict(prompt.replace("\"", "\'"))
        return __process__(p["prompt"], p["image"])
    except:
        p = json.loads(prompt)
        return __process__(p["prompt"], p["image"])

def __process__(prompt: str, image: str | Image.Image) -> list[bytes]:
    LoadModel()

    if (prompt.startswith("\"") or prompt.startswith("\'")):
        prompt = prompt[1:]
    
    if (prompt.endswith("\"") or prompt.endswith("\'")):
        prompt = prompt[:-1]
    
    if (type(image) == str):
        image = Image.open(image)
    
    if (cfg.current_data.seed >= 0):
        generator = torch.manual_seed(cfg.current_data.seed)
    else:
        generator = torch.manual_seed(torch.seed())
    
    if (cfg.current_data.print_prompt):
        print("Prompt: " + prompt)
        print("Using seed: " + str(generator.seed()))
    
    image = ImageOps.exif_transpose(image)
    image = image.convert("RGB")

    images_generated = pipeline(prompt, image = image, num_inference_steps = cfg.current_data.i2i_steps).images
    images = []

    for image in images_generated:
        img_name = "ti.png"
        img_n = 0

        while (os.path.exists(img_name)):
            img_n += 1
            img_name = "ti_" + str(img_n) + ".png"

        with open(img_name, "w+") as f:
            f.close()
        
        image.save(img_name)

        with open(img_name, "rb") as f:
            images.append(f.read())
            f.close()

        os.remove(img_name)

    return images