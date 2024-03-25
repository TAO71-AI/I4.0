from transformers import AutoImageProcessor, AutoModelForDepthEstimation
import PIL.Image
import torch
import torch.nn as nn
import numpy as np
import os
import ai_config as cfg

processor: AutoImageProcessor = None
model: AutoModelForDepthEstimation = None
device: str = "cpu"

def __load_model__(model_name: str, device: str):
    model = AutoModelForDepthEstimation.from_pretrained(model_name).to(device)
    return model

def LoadModel() -> None:
    global processor, model, device

    if (not cfg.current_data.prompt_order.__contains__("de")):
        raise Exception("Model is not in 'prompt_order'.")

    if (model != None and processor != None):
        return
    
    device = cfg.GetGPUDevice("de")

    if (cfg.current_data.print_loading_message):
        print("Loading model 'depth estimation' on device '" + device + "'...")
    
    processor = AutoImageProcessor.from_pretrained(cfg.current_data.depth_estimation_model)
    model = __load_model__(cfg.current_data.depth_estimation_model, device)

def EstimateDepth(image: str | PIL.Image.Image) -> bytes:
    LoadModel()

    if (type(image) == str):
        image = PIL.Image.open(image)
    elif (type(image) != PIL.Image.Image):
        raise Exception("Image is not 'str' or 'PIL.Image.Image'.")
    
    if (cfg.current_data.print_prompt):
        print("Estimating depth...")
    
    inputs = processor(images = [image], return_tensors = "pt")
    inputs = inputs.to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        predicted_depth = outputs.predicted_depth

    prediction = nn.functional.interpolate(predicted_depth.unsqueeze(1), size = image.size[::-1], mode = "bicubic", align_corners = False)
    output = prediction.squeeze().to(device).numpy()
    output = (output * 255 / np.max(output)).astype("uint8")
    output = PIL.Image.fromarray(output)

    img_name = "tdi.png"
    img_n = 0

    while (os.path.exists(img_name)):
        img_n += 1
        img_name = "tdi_" + str(img_n) + ".png"

    with open(img_name, "w+") as f:
        f.close()
    
    output.save(img_name)

    with open(img_name, "rb") as f:
        output = f.read()
        f.close()

    os.remove(img_name)
    return output