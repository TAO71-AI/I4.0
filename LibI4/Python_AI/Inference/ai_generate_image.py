from diffusers import AutoPipelineForText2Image
import torch
import os
import json
import ai_config as cfg

pipeline: AutoPipelineForText2Image = None
device: str = "cpu"

def LoadModel() -> None:
    global pipeline, device

    if (not cfg.current_data["prompt_order"].__contains__("text2img")):
        raise Exception("Model is not in 'prompt_order'.")
    
    if (pipeline != None):
        return
    
    if (cfg.current_data["print_loading_message"]):
        print("Loading model 'text to image'...")
    
    data = cfg.LoadDiffusersPipeline("text2img", cfg.current_data["image_generation_model"], AutoPipelineForText2Image)

    pipeline = data[0]
    device = data[1]

    if (cfg.current_data["print_loading_message"]):
        print("   Loaded model on device '" + device + "'.")

def GenerateImages(prompt: str | dict[str, str]) -> list[bytes]:
    if (type(prompt) == dict[str, str]):
        return __generate_images__(prompt["prompt"], prompt["negative_prompt"])
    
    try:
        p = dict(prompt.replace("\"", "\'"))
        return __generate_images__(p["prompt"], p["negative_prompt"])
    except:
        p = json.loads(prompt)
        return __generate_images__(p["prompt"], p["negative_prompt"])

def __generate_images__(prompt: str, negative_prompt: str) -> list[bytes]:
    LoadModel()

    if (prompt.startswith("\"") or prompt.startswith("\'")):
        prompt = prompt[1:]
    
    if (prompt.endswith("\"") or prompt.endswith("\'")):
        prompt = prompt[:-1]
    
    if (negative_prompt.startswith("\"") or negative_prompt.startswith("\'")):
        negative_prompt = negative_prompt[1:]
    
    if (negative_prompt.endswith("\"") or negative_prompt.endswith("\'")):
        negative_prompt = negative_prompt[:-1]
    
    if (cfg.current_data["seed"] >= 0):
        generator = torch.manual_seed(cfg.current_data["seed"])
    else:
        generator = torch.manual_seed(torch.seed())
    
    if (cfg.current_data["print_prompt"]):
        print("Prompt: " + prompt)
        print("Negative prompt: " + negative_prompt)
        print("Using seed: " + str(generator.seed()))

    images_generated = pipeline(prompt, num_inference_steps = cfg.current_data["image_generation_steps"], output_type = "pil", negative_prompt = negative_prompt, generator = generator).images
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