from diffusers import AutoPipelineForImage2Image
from PIL import Image, ImageOps
import os
import json
import ai_config as cfg

__models__: list[tuple[AutoPipelineForImage2Image, dict[str, any]]] = []

def LoadModels() -> None:
    # For each model of this service
    for i in range(len(cfg.GetAllInfosOfATask("img2img"))):
        # Check if the model is already loaded
        if (i < len(__models__)):
            continue
        
        # Load the model
        model, _ = cfg.LoadDiffusersPipeline("img2img", i, AutoPipelineForImage2Image)

        # Add the model and info to the list of models
        __models__.append((model, cfg.GetInfoOfTask("img2img", i)))

def Inference(Index: int, Prompt: str | dict[str, str]) -> list[bytes]:
    # Check the type of the prompt
    if (type(Prompt) == dict[str, str] or type(Prompt) == dict):
        # It's a dict, process the image directly
        return __process__(Index, Prompt["prompt"], Prompt["image"])
    
    try:
        # It's not a dict, try to convert it to a dict
        p = dict(Prompt.replace("\"", "\'"))
    except:
        # Try to convert into a dict using JSON
        p = json.loads(Prompt)
    
    # Try to get the steps of the user
    try:
        steps = int(p["steps"])
    except:
        steps = __models__[Index][1]["steps"]

    # Process the image
    return __process__(Index, p["prompt"], steps, p["image"])

def __process__(Index: int, Prompt: str, Steps: int, Image: str | Image.Image) -> list[bytes]:
    # Load the models
    LoadModels()

    # Cut the prompt
    if (Prompt.startswith("\"") or Prompt.startswith("\'")):
        Prompt = Prompt[1:]
    
    if (Prompt.endswith("\"") or Prompt.endswith("\'")):
        Prompt = Prompt[:-1]
    
    # Convert into an image if it's a string
    if (type(image) == str):
        image = Image.open(image)
    
    # Convert the image to RGB
    image = ImageOps.exif_transpose(image)
    image = image.convert("RGB")

    # Inference the model
    images_generated = __models__[Index][0](Prompt, image = image, num_inference_steps = Steps).images
    images = []

    # For each image generated
    for image in images_generated:
        # Save into a temporal file
        img_name = "ti.png"
        img_n = 0

        while (os.path.exists(img_name)):
            img_n += 1
            img_name = "ti_" + str(img_n) + ".png"

        with open(img_name, "w+") as f:
            f.close()
        
        image.save(img_name)

        # Read the bytes of the saved image and add it to the images list
        with open(img_name, "rb") as f:
            images.append(f.read())
            f.close()

        # Delete the temporal file
        os.remove(img_name)

    # Return all the generated images
    return images