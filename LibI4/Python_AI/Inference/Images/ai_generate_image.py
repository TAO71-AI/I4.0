# Import the text to image systems
import Inference.Images.TextToImage.hf as hf
import Inference.Images.TextToImage.sdcpp as sdcpp

# Import I4.0's utilities
from diffusers import AutoPipelineForText2Image
from stable_diffusion_cpp import StableDiffusion
import ai_config as cfg

# Import some libraries
import os
import psutil

__models__: list[tuple[AutoPipelineForText2Image | StableDiffusion, dict[str, any]]] = []

def LoadModels() -> None:
    # For each model of this service
    for i in range(len(cfg.GetAllInfosOfATask("text2img"))):
        # Check if the model is already loaded
        if (i < len(__models__)):
            continue
        
        # Get info about the model
        info = cfg.GetInfoOfTask("text2img", i)

        # Get threads and check if the number of threads are valid
        if (list(info.keys()).count("threads") == 0 or info["threads"] == -1):
            threads = psutil.cpu_count()
        elif (info["threads"] <= 0 or info["threads"] > psutil.cpu_count()):
            raise Exception("Invalid number of threads.")
        else:
            threads = info["threads"]

        # Load the model
        if (info["type"] == "hf"):
            # Load the model using HuggingFace
            model = hf.__load_model__(i)
        elif (info["type"] == "sdcpp-flux" or info["type"] == "sdcpp-sd"):
            # Load the model using Stable-Diffusion-CPP-Python
            model = sdcpp.LoadModel(i, threads)
        else:
            raise Exception("Invalid text2img type.")

        # Add the model to the list of models
        __models__.append((model, info))

def Inference(Index: int, Prompt: str | dict[str, str]) -> list[bytes]:
    # Set some variables
    p = ""
    np = ""
    width = -1
    height = -1
    guidance = -1
    steps = -1
    
    # Deserialize the prompt if it's not a dict
    if (type(Prompt) != dict[str, str] and type(Prompt) != dict):
        Prompt = cfg.JSONDeserializer(Prompt)
    
    # Set the prompt and negative prompt
    p = Prompt["prompt"]
    np = Prompt["negative_prompt"]

    # Check if the prompt is empty
    if (len(p.strip()) == 0):
        raise Exception("Prompt is empty.")

    # Set the width
    try:
        width = int(Prompt["width"])

        if (width < 512):
            width = __models__[Index][1]["width"]
    except:
        width = __models__[Index][1]["width"]

    # Set the height
    try:
        height = int(Prompt["height"])

        if (height < 512):
            height = __models__[Index][1]["height"]
    except:
        height = __models__[Index][1]["height"]

    # Set the guidance scale
    try:
        guidance = float(Prompt["guidance"])

        if (guidance < 1):
            guidance = __models__[Index][1]["guidance"]
    except:
        guidance = __models__[Index][1]["guidance"]

    # Set the number of steps
    try:
        steps = int(Prompt["steps"])

        if (steps < 1):
            steps = __models__[Index][1]["steps"]
    except:
        steps = __models__[Index][1]["steps"]

    # Return the output
    return __generate_images__(Index, p, np, width, height, guidance, steps)

def __generate_images__(Index: int, Prompt: str, NegativePrompt: str, Width: int, Height: int, Guidance: float, Steps: int) -> list[bytes]:
    # Load the models
    LoadModels()

    # Get the info
    info = cfg.GetInfoOfTask("text2img", Index)

    # Generate the images
    if (info["type"] == "hf"):
        # Generate the images using HuggingFace
        images_generated = hf.__inference__(__models__[Index][0], Prompt, NegativePrompt, Width, Height, Guidance, Steps)
    elif (info["type"] == "sdcpp-flux" or info["type"] == "sdcpp-sd"):
        # Generate the images using Stable-Diffusion-CPP-Python
        images_generated = sdcpp.__inference__(__models__[Index][0], Prompt, NegativePrompt, Width, Height, Guidance, Steps)
    else:
        raise Exception("Invalid text2img type.")
    
    images = []

    # For each image
    for image in images_generated:
        # Create a temporal file with the image
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