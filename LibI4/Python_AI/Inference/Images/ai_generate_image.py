from diffusers import AutoPipelineForText2Image
import torch
import os
import json
import ai_config as cfg

pipeline: AutoPipelineForText2Image | None = None
device: str = "cpu"

def LoadModel() -> None:
    global pipeline, device

    if (cfg.current_data["models"].count("text2img") == 0):
        raise Exception("Model is not in 'models'.")
    
    if (pipeline != None):
        return
    
    data = cfg.LoadDiffusersPipeline("text2img", cfg.current_data["image_generation"]["model"], AutoPipelineForText2Image)

    pipeline = data[0]
    device = data[1]

def GenerateImages(prompt: str | dict[str, str]) -> list[bytes]:
    p = ""
    np = ""
    width = cfg.current_data["image_generation"]["width"]
    height = cfg.current_data["image_generation"]["height"]
    guidance = cfg.current_data["image_generation"]["guidance"]
    steps = cfg.current_data["image_generation"]["steps"]
    
    if (type(prompt) != dict[str, str] and type(prompt) != dict):
        prompt = cfg.JSONDeserializer(prompt)
    
    p = prompt["prompt"]
    np = prompt["negative_prompt"]

    if (len(p.strip()) == 0):
        raise Exception("Prompt is empty.")

    try:
        width = int(prompt["width"])

        if (width < 512):
            width = cfg.current_data["image_generation"]["width"]
    except:
        width = cfg.current_data["image_generation"]["width"]

    try:
        height = int(prompt["height"])

        if (height < 512):
            height = cfg.current_data["image_generation"]["height"]
    except:
        height = cfg.current_data["image_generation"]["height"]

    try:
        guidance = float(prompt["guidance"])

        if (guidance < 1):
            guidance = cfg.current_data["image_generation"]["guidance"]
    except:
        guidance = cfg.current_data["image_generation"]["guidance"]

    try:
        steps = int(prompt["steps"])

        if (steps < 1):
            steps = cfg.current_data["image_generation"]["steps"]
    except:
        steps = cfg.current_data["image_generation"]["steps"]

    return __generate_images__(p, np, width, height, guidance, steps)

def __generate_images__(prompt: str, negative_prompt: str, width: int, height: int, guidance: float, steps: int) -> list[bytes]:
    LoadModel()

    images_generated = pipeline(
        prompt,
        num_inference_steps = steps,
        width = width,
        height = height,
        guidance_scale = guidance,
        output_type = "pil",
        negative_prompt = negative_prompt
    ).images
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