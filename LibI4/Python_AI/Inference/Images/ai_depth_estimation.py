from transformers import AutoImageProcessor, AutoModelForDepthEstimation
import PIL.Image
import torch
import torch.nn as nn
import numpy as np
import os
import ai_config as cfg

__models__: dict[int, tuple[AutoModelForDepthEstimation, AutoImageProcessor, str]] = {}

def __load_model__(Index: int) -> None:
    # Check if the model is loaded
    if (Index in list(__models__.keys()) and __models__[Index] is not None):
        return

    # Load the model
    model, processor, device = cfg.LoadModel("de", Index, AutoModelForDepthEstimation, AutoImageProcessor)

    # Add the model to the list of models
    __models__[Index] = (model, processor, device)

def LoadModels() -> None:
    # For each model of this service
    for i in range(len(cfg.GetAllInfosOfATask("de"))):
        # Load the model
        __load_model__(i)

def __offload_model__(Index: int) -> None:
    # Check the index is valid
    if (Index not in list(__models__.keys()) or __models__[Index] is None):
        # Not valid, return
        return
    
    # Offload the model
    __models__[Index] = None
    
    # Delete from the models list
    __models__.pop(Index)

def Inference(Index: int, Image: str | PIL.Image.Image) -> bytes:
    # Load the model
    __load_model__(Index)

    # Check the type of the image
    if (type(Image) == str):
        # It's an image from a path
        # Open it
        Image = PIL.Image.open(Image)
    elif (type(Image) != PIL.Image.Image):
        # It's not a valid image
        raise Exception("Image is not 'str' or 'PIL.Image.Image'.")
    
    # Tokenize the image and move to the device
    inputs = __models__[Index][1](images = [Image], return_tensors = "pt")
    inputs = inputs.to(__models__[Index][2])

    # Inference the model
    with torch.no_grad():
        outputs = __models__[Index][0](**inputs)
        predicted_depth = outputs.predicted_depth

    # Get the output
    prediction = nn.functional.interpolate(predicted_depth.unsqueeze(1), size = Image.size[::-1], mode = "bicubic", align_corners = False)
    output = prediction.squeeze().cpu().numpy()
    output = (output * 255 / np.max(output)).astype("uint8")
    output = PIL.Image.fromarray(output)

    # Save a temporal image
    img_name = "tdi.png"
    img_n = 0

    while (os.path.exists(img_name)):
        img_n += 1
        img_name = "tdi_" + str(img_n) + ".png"

    with open(img_name, "w+") as f:
        f.close()
    
    output.save(img_name)

    # Read the bytes of the saved image
    with open(img_name, "rb") as f:
        output = f.read()
        f.close()

    # Delete the temporal image
    os.remove(img_name)

    # Return the bytes of the output image
    return output