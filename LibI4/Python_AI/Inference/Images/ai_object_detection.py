# Import I4.0 utilities
import ai_config as cfg

# Import other libraries
from io import BytesIO
from transformers import AutoImageProcessor, AutoModelForObjectDetection
import PIL.Image
import torch
import cv2
import numpy as np
import random

__models__: dict[int, tuple[AutoModelForObjectDetection, AutoImageProcessor, str, str]] = {}

def __get_random_color__() -> tuple[int, int, int]:
    # Get a random color (RGB)
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

def __load_model__(Index: int) -> None:
    # Check if the model is already loaded
    if (Index in list(__models__.keys()) and __models__[Index] is not None):
        return
        
    # Load the model and get the info
    model, processor, device, dtype = cfg.LoadModel("od", Index, AutoModelForObjectDetection, AutoImageProcessor)

    # Add the model to the list of models
    __models__[Index] = (model, processor, device, dtype)

def LoadModels() -> None:
    # For each model of this service
    for i in range(len(cfg.GetAllInfosOfATask("od"))):
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

def Inference(Index: int, Img: str | bytes | PIL.Image.Image) -> dict[str, str | bytes]:
    # Load the model
    __load_model__(Index)

    # Create empty buffer
    imgBuffer = None

    # Check the image type
    if (isinstance(Img, str)):
        # It's a string, open the file
        image = PIL.Image.open(Img)
    elif (isinstance(Img, bytes)):
        # It's an image from bytes
        imgBuffer = BytesIO(Img)
        image = PIL.Image.open(imgBuffer)
    elif (isinstance(Img, PIL.Image.Image)):
        image = Img
    else:
        # Invalid image type
        raise Exception("Invalid image type.")
    
    # Convert image to array
    cv_image = np.array(image)

    # Convert image to BGR
    cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)

    # Tokenize the image
    inputs = __models__[Index][1](images = [image], return_tensors = "pt")
    inputs = inputs.to(__models__[Index][2]).to(__models__[Index][3])

    # Inference the model
    outputs = __models__[Index][0](**inputs)
    target_sizes = torch.tensor([image.size[::-1]])

    # Get all the results from the processor
    results = __models__[Index][1].post_process_object_detection(outputs, target_sizes = target_sizes, threshold = 0.8)[0]
    result = []

    # For each result
    for label, box in zip(results["labels"], results["boxes"]):
        # Get the variables
        box = [round(i, 2) for i in box.tolist()]
        label = __models__[Index][0].config.id2label[label.item()]
        color = __get_random_color__()
        x = (int(box[0]), int(box[1]))
        y = (int(box[2]), int(box[3]))

        # Add variables to the results list
        result.append((str(label), (x[0], x[1], y[0], y[1])))

        # Put a rectangle and the label as text on the input image
        cv2.rectangle(cv_image, x, y, color = color, thickness = 2)
        cv2.putText(cv_image, str(label), (x[0] - 10, x[1] - 10), fontFace = cv2.FONT_HERSHEY_SIMPLEX, fontScale = 1, color = color, thickness = 2)
    
    # Save the result image in a buffer
    success, encodedImg = cv2.imencode(".png", cv_image, [cv2.IMWRITE_PNG_COMPRESSION, 0])

    # Close the image buffer if needed
    image.close()
    
    if (imgBuffer is not None):
        imgBuffer.close()

    if (not success):
        raise RuntimeError("Could not encode image.")
    
    # Return the objects and image
    return {
        "objects": result,
        "image": encodedImg.tobytes()
    }