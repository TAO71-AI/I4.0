from transformers import Pipeline
from io import BytesIO
import PIL.Image
import ai_config as cfg

__models__: dict[int, tuple[Pipeline, dict[str, any]] | None] = {}

def __load_model__(Index: int) -> None:
    # Check if the model is already loaded
    if (Index in list(__models__.keys()) and __models__[Index] is not None):
        return

    # Load the model and add it to the list of models
    model, _ = cfg.LoadPipeline("image-to-text", "img2text", Index)
    __models__[Index] = (model, cfg.GetInfoOfTask("img2text", Index))

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

def Inference(
        Index: int,
        Img: str | bytes | PIL.Image.Image,
        MaxLength: int | None
    ) -> str:
    # Load the model
    __load_model__(Index)

    # Create empty buffer
    imgBuffer = None

    # Check the image type
    if (isinstance(Img, str)):
        # The image is a string, open the file
        image = PIL.Image.open(Img)
    elif (isinstance(Img, bytes)):
        # It's an image from bytes
        imgBuffer = BytesIO(Img)
        image = PIL.Image.open(imgBuffer)
    elif (isinstance(Img, PIL.Image.Image)):
        # The image is already an image, set the variable
        image = Img
    else:
        # Invalid image type
        raise ValueError("Invalid image type.")
    
    # Set max length
    if (
        MaxLength is None and
        "max_length" in __models__[Index][1] and
        __models__[Index][1]["max_length"] is not None and
        __models__[Index][1]["max_length"] > 0
    ):
        maxLength = __models__[Index][1]["max_length"]
    elif (
        MaxLength is not None and
        MaxLength > 0
    ):
        if ("max_length" in __models__[Index][1] and MaxLength > __models__[Index][1]["max_length"]):
            maxLength = __models__[Index][1]["max_length"]
        elif (MaxLength > cfg.current_data["max_length"]):
            maxLength = cfg.current_data["max_length"]
        else:
            maxLength = MaxLength
    elif (cfg.current_data["max_length"] > 0):
        maxLength = cfg.current_data["max_length"]

    # Get the response from the model
    response = __models__[Index][0](
        image,
        max_new_tokens = maxLength
    )[0]["generated_text"]

    # Close the image buffer if needed
    image.close()
    
    if (imgBuffer is not None):
        imgBuffer.close()

    # Return the response as a string
    return str(response)