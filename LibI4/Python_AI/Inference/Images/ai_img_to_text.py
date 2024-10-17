from transformers import Pipeline
import PIL.Image
import ai_config as cfg

__models__: list[Pipeline] = []

def LoadModels() -> None:
    # For each model of the service
    for i in range(len(cfg.GetAllInfosOfATask("img2text"))):
        # Check if the model is already loaded
        if (i < len(__models__)):
            # It is, continue
            continue

        # Load the model and add it to the list of models
        model, _ = cfg.LoadPipeline("image-to-text", "img2text", i)
        __models__.append(model)

def Inference(Index: int, Img: str | PIL.Image.Image) -> str:
    # Load the models
    LoadModels()

    # Check the image type
    if (type(Img) == str):
        # The image is a string, open the file
        image = PIL.Image.open(Img)
    elif (type(Img) == PIL.Image.Image):
        # The image is already an image, set the variable
        image = Img
    else:
        # Invalid image type
        raise Exception("Invalid image type.")

    # Get the response from the model
    response = __models__[Index](image)[0]["generated_text"]

    # Return the response as a string
    return str(response)