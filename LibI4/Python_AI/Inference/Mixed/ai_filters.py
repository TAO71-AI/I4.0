# Import some dependencies
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Pipeline
from PIL import Image
import torch

# Import I4.0's utilities
import ai_config as cfg

__models_text__: dict[int, tuple[AutoModelForSequenceClassification, AutoTokenizer, str, dict[str, any]]] = {}
__models_image__: dict[int, tuple[Pipeline, str, dict[str, any]]] = {}

def LoadTextModels() -> None:
    # For each model
    for i in range(len(cfg.GetAllInfosOfATask("nsfw_filter-text"))):
        # Check if the model is already loaded
        if (i in list(__models_text__.keys())):
            continue

        # Load the model
        model, tokenizer, device = cfg.LoadModel("nsfw_filter-text", i, AutoModelForSequenceClassification, AutoTokenizer)

        # Add the model to the list
        __models_text__[i] = (model, tokenizer, device, cfg.GetInfoOfTask("nsfw_filter-text", i))

def LoadImageModels() -> None:
    # For each model
    for i in range(len(cfg.GetAllInfosOfATask("nsfw_filter-image"))):
        # Check if the model is already loaded
        if (i in list(__models_image__.keys())):
            continue

        # Load the model
        pipe, device = cfg.LoadPipeline("image-classification", "nsfw_filter-image", i)

        # Add the model to the list
        __models_image__[i] = (pipe, device, cfg.GetInfoOfTask("nsfw_filter-image", i))

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
    # Load the models
    LoadTextModels()

    # Set model, tokenizer, device and info
    model, tokenizer, device, info = __models_text__[Index]

    # Tokenize the prompt
    inputs = tokenizer.encode(Prompt, return_tensors = "pt").to(device)

    # Inference the model
    result = model(inputs).logits

    # Get the predicted class
    predicted_class = result.argmax().item()
    predicted_class = model.config.id2label[predicted_class].lower()

    # Return the response
    return predicted_class == info["nsfw_label"].lower()

def InferenceImage(Prompt: str | Image.Image, Index: int) -> bool:
    # Load the models
    LoadImageModels()

    # Check the image variable type
    if (type(Prompt) == str):
        # It's a string, open the image
        Prompt = Image.open(Prompt)
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

    # Return the response
    return predicted_class == info["nsfw_label"].lower()