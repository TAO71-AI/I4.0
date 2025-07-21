# Import I4.0 utilities
import ai_config as cfg

# Import other libraries
from transformers import AutoImageProcessor, AutoModelForDepthEstimation
from io import BytesIO
import PIL.Image
import torch
import torch.nn as nn
import numpy as np

__models__: dict[int, tuple[AutoModelForDepthEstimation, AutoImageProcessor, str, str]] = {}

def __load_model__(Index: int) -> None:
    # Check if the model is loaded
    if (Index in list(__models__.keys()) and __models__[Index] is not None):
        return

    # Load the model
    model, processor, device, dtype = cfg.LoadModel("de", Index, AutoModelForDepthEstimation, AutoImageProcessor)

    # Add the model to the list of models
    __models__[Index] = (model, processor, device, dtype)

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

def Inference(Index: int, Image: str | bytes | PIL.Image.Image) -> bytes:
    # Load the model
    __load_model__(Index)

    # Create empty buffer
    imgBuffer = None

    # Check the type of the image
    if (isinstance(Image, str)):
        # It's an image from a path
        image = PIL.Image.open(Image)
    elif (isinstance(Image, bytes)):
        # It's an image from bytes
        imgBuffer = BytesIO(Image)
        image = PIL.Image.open(imgBuffer)
    elif (isinstance(Image, PIL.Image.Image)):
        image = Image
    else:
        # It's not a valid image
        raise Exception("Image is not 'str', 'bytes' or 'PIL.Image.Image'.")
    
    # Tokenize the image and move to the device
    inputs = __models__[Index][1](images = [image], return_tensors = "pt")
    inputs = inputs.to(__models__[Index][2]).to(__models__[Index][3])

    # Inference the model
    with torch.no_grad():
        outputs = __models__[Index][0](**inputs)
        predicted_depth = outputs.predicted_depth

    # Get the output
    prediction = nn.functional.interpolate(predicted_depth.unsqueeze(1), size = image.size[::-1], mode = "bicubic", align_corners = False)
    output = prediction.squeeze().cpu().numpy().astype(np.float32)
    maxVal = np.max(output)

    # Make sure maxVal is not infinite or 0
    if (not np.isfinite(maxVal) or maxVal == 0):
        maxVal = 1

    # Get the output
    output = (output * 255.0 / maxVal).clip(0, 255).astype(np.uint8)
    output = PIL.Image.fromarray(output)

    # Save a temporal image
    buffer = BytesIO()
    output.save(buffer, format = "PNG")

    buffer.seek(0)
    data = buffer.getvalue()

    buffer.close()

    # Close the image buffer if needed
    image.close()
    
    if (imgBuffer is not None):
        imgBuffer.close()

    # Return the bytes of the output image
    return data