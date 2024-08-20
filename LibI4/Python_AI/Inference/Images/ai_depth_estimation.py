from transformers import AutoImageProcessor, AutoModelForDepthEstimation
import PIL.Image
import torch
import torch.nn as nn
import numpy as np
import os
import ai_config as cfg

processor: AutoImageProcessor | None = None
model: AutoModelForDepthEstimation | None = None
device: str = "cpu"

def __load_model__(model_name: str, device: str):
    model = AutoModelForDepthEstimation.from_pretrained(model_name).to(device)
    return model

def LoadModel() -> None:
    global processor, model, device

    if (cfg.current_data["models"].count("de") == 0):
        raise Exception("Model is not in 'models'.")

    if (model != None and processor != None):
        return
    
    data = cfg.LoadModel("de", cfg.current_data["depth_estimation_model"], AutoModelForDepthEstimation, AutoImageProcessor)

    model = data[0]
    processor = data[1]
    device = data[2]

def EstimateDepth(image: str | PIL.Image.Image) -> bytes:
    LoadModel()

    if (type(image) == str):
        image = PIL.Image.open(image)
    elif (type(image) != PIL.Image.Image):
        raise Exception("Image is not 'str' or 'PIL.Image.Image'.")
    
    inputs = processor(images = [image], return_tensors = "pt")
    inputs = inputs.to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        predicted_depth = outputs.predicted_depth

    prediction = nn.functional.interpolate(predicted_depth.unsqueeze(1), size = image.size[::-1], mode = "bicubic", align_corners = False)
    output = prediction.squeeze().cpu().numpy()
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