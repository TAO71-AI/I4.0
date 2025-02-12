from transformers import Pipeline
import PIL.Image
import ai_config as cfg

__models__: dict[int, Pipeline] = {}

def __load_model__(Index: int) -> None:
    # Check if the model is already loaded
    if (Index in list(__models__.keys()) and __models__[Index] is not None):
        return

    # Load the model and add it to the list of models
    model, _ = cfg.LoadPipeline("image-to-text", "img2text", Index)
    __models__[Index] = model

def LoadModels() -> None:
    # For each model of the service
    for i in range(len(cfg.GetAllInfosOfATask("img2text"))):
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

def Inference(Index: int, Img: str | PIL.Image.Image) -> str:
    # Load the model
    __load_model__(Index)

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