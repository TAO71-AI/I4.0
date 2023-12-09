from transformers import AutoTokenizer, AutoModelForSequenceClassification, TFAutoModelForSequenceClassification, pipeline, Pipeline
from PIL import Image
import torch
import ai_config as cfg

text_filter: AutoModelForSequenceClassification | TFAutoModelForSequenceClassification = None
image_filter: Pipeline = None
tokenizer_text: AutoTokenizer = None

def __load_model__(model_name: str, device: str, type: str):
    if (cfg.current_data.use_tf_instead_of_pt):
        if (type == "text"):
            return TFAutoModelForSequenceClassification.from_pretrained(model_name)
        elif (type == "image"):
            return pipeline("image-classification", model = model_name, device = device)
        
        raise Exception("Filter model type is not 'text' or 'image'.")
    else:
        if (type == "text"):
            model = AutoModelForSequenceClassification.from_pretrained(model_name)
        elif (type == "image"):
            return pipeline("image-classification", model = model_name, device = device)
        else:
            raise Exception("Filter model type is not 'text' or 'image'.")

        model.to(device)
        return model

def LoadTextModel() -> None:
    global text_filter, tokenizer_text

    if (text_filter != None and tokenizer_text != None):
        return
    
    move_to_gpu = cfg.current_data.use_gpu_if_available and torch.cuda.is_available() and cfg.current_data.move_to_gpu.__contains__("nsfw_filter-text")
    device = "cuda" if (move_to_gpu) else "cpu"

    if (cfg.current_data.print_loading_message):
        print("Loading model 'NSFW Filter (Text)' on device '" + device + "'...")
    
    tokenizer_text = AutoTokenizer.from_pretrained(cfg.current_data.nsfw_filter_text_model)
    text_filter = __load_model__(cfg.current_data.nsfw_filter_text_model, device, "text")

def LoadImageModel() -> None:
    global image_filter

    if (image_filter != None):
        return
    
    move_to_gpu = cfg.current_data.use_gpu_if_available and torch.cuda.is_available() and cfg.current_data.move_to_gpu.__contains__("nsfw_filter-image")
    device = "cuda" if (move_to_gpu) else "cpu"

    if (cfg.current_data.print_loading_message):
        print("Loading model 'NSFW Filter (Image)' on device '" + device + "'...")
    
    image_filter = __load_model__(cfg.current_data.nsfw_filter_image_model, device, "image")

def IsTextNSFW(prompt: str) -> bool:
    # NOTE: The value 0 means NSFW, the value 1 means SFW.
    LoadTextModel()

    if (tokenizer_text == None or text_filter == None):
        return None

    inputs = tokenizer_text.encode(prompt, return_tensors = ("tf" if cfg.current_data.use_tf_instead_of_pt else "pt"))
    response = text_filter(inputs).logits
    predicted_class = response.argmax().item()

    return predicted_class == 0

def IsImageNSFW(image: str | Image.Image) -> bool:
    # NOTE: The value 0 means NSFW, the value 1 means SFW.
    if (type(image) == str):
        image = Image.open(image)
    elif (type(image) != Image.Image):
        raise Exception("The image in the NSFW filter must be 'str' or 'PIL.Image.Image'.")
    
    LoadImageModel()

    if (image_filter == None):
        return None
    
    result = image_filter(image)
    lr = -float("inf")
    lrt = ""

    for r in result:
        score = float(r["score"])
        tag = str(r["label"])

        if (score >= lr):
            lr = score
            lrt = tag
    
    return (lrt.lower().strip() == "nsfw" or lrt.strip() == "0")