from diffusers import AutoPipelineForText2Image
import os
import ai_config as cfg

__models__: list[tuple[AutoPipelineForText2Image, dict[str, any]]] = []

def LoadModels() -> None:
    # For each model of this service
    for i in range(len(cfg.GetAllInfosOfATask("text2img"))):
        # Check if the model is already loaded
        if (i < len(__models__)):
            continue
        
        # Load the model and get the info
        model, _ = cfg.LoadDiffusersPipeline("text2img", i, AutoPipelineForText2Image)
        info = cfg.GetInfoOfTask("text2img", i)

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

    # Generate the images using the model pipeline
    images_generated = __models__[Index][0](
        Prompt,
        num_inference_steps = Steps,
        width = Width,
        height = Height,
        guidance_scale = Guidance,
        output_type = "pil",
        negative_prompt = NegativePrompt
    ).images
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