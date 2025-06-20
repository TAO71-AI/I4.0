# Import I4.0's utilities
import ai_config as cfg

# Import other libraries
from io import BytesIO
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Pipeline
from PIL import Image
import torch

__models_text__: dict[int, tuple[AutoModelForSequenceClassification, AutoTokenizer, str, str, dict[str, any]]] = {}
__models_image__: dict[int, tuple[Pipeline, str, dict[str, any]]] = {}

def __load_text_model__(Index: int) -> None:
    # Check if the model is already loaded
    if (Index in list(__models_text__.keys()) and __models_text__[Index] is not None):
        return

    # Load the model
    model, tokenizer, device, dtype = cfg.LoadModel("nsfw_filter-text", Index, AutoModelForSequenceClassification, AutoTokenizer)

    # Add the model to the list
    __models_text__[Index] = (model, tokenizer, device, dtype, cfg.GetInfoOfTask("nsfw_filter-text", Index))

def __load_image_model__(Index: int) -> None:
    # Check if the model is already loaded
    if (Index in list(__models_image__.keys()) and __models_image__[Index] is not None):
        return

    # Load the model
    pipe, device = cfg.LoadPipeline("image-classification", "nsfw_filter-image", Index)

    # Add the model to the list
    __models_image__[Index] = (pipe, device, cfg.GetInfoOfTask("nsfw_filter-image", Index))

def LoadTextModels() -> None:
    # For each model
    for i in range(len(cfg.GetAllInfosOfATask("nsfw_filter-text"))):
        __load_text_model__(i)

def LoadImageModels() -> None:
    # For each model
    for i in range(len(cfg.GetAllInfosOfATask("nsfw_filter-image"))):
        __load_image_model__(i)

def LoadModels() -> None:
    # Load both text and image filters
    LoadTextModels()
    LoadImageModels()

def __offload_text__(Index: int) -> None:
    # Check the index is valid
    if (Index not in list(__models_text__.keys())):
        # Not valid, return
        return
    
    # Offload the model
    __models_text__[Index] = None
    
    # Delete from the models list
    __models_text__.pop(Index)

def __offload_image__(Index: int) -> None:
    # Check the index is valid
    if (Index not in list(__models_image__.keys())):
        # Not valid, return
        return
    
    # Offload the model
    __models_image__[Index] = None
    
    # Delete from the models list
    __models_image__.pop(Index)

def InferenceText(Prompt: str, Index: int) -> bool:
    # Load the model
    __load_text_model__(Index)

    # Set model, tokenizer, device and info
    model, tokenizer, device, dtype, info = __models_text__[Index]

    # Tokenize the prompt
    inputs = tokenizer.encode(Prompt, return_tensors = "pt").to(device).to(dtype)

    # Inference the model
    result = model(inputs).logits

    # Get the predicted class
    predicted_class = result.argmax().item()
    predicted_class = model.config.id2label[predicted_class].lower()

    # Return the response
    return predicted_class == info["nsfw_label"].lower()

def InferenceImage(Prompt: str | bytes | Image.Image, Index: int) -> bool:
    # Load the model
    __load_image_model__(Index)

    # Create empty buffer
    imgBuffer = None

    # Check the image variable type
    if (type(Prompt) == str):
        # It's a string, open the image
        Prompt = Image.open(Prompt)
    elif (type(Prompt) == bytes):
        # It's an image from bytes
        imgBuffer = BytesIO(Prompt)
        image = Image.open(imgBuffer)
    elif (type(Prompt) != Image.Image):
        # Invalid type
        raise Exception("The image in the NSFW filter must be 'str' or 'PIL.Image.Image'.")
    
    # Get the pipeline and the info
    pipe, device, info = __models_image__[Index]

    # Inference the model
    result = pipe(Prompt)
    result = [item["score"] for item in result]
    result = torch.log(torch.tensor(result) / (1 - torch.tensor(result))).to(device).unsqueeze(0)

    # Get the predicted class
    predicted_class = result.argmax().item()
    predicted_class = pipe.model.config.id2label[predicted_class].lower()

    # Close the image buffer if needed
    image.close()
    
    if (imgBuffer is not None):
        imgBuffer.close()

    # Return the response
    return predicted_class == info["nsfw_label"].lower()