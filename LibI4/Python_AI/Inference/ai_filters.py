from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline, Pipeline
from PIL import Image
import ai_config as cfg

text_filter: AutoModelForSequenceClassification = None
image_filter: Pipeline = None
tokenizer_text: AutoTokenizer = None
device_text: str = "cpu"
device_image: str = "cpu"

def __load_model__(model_name: str, device: str, type: str):
    if (type == "text"):
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
    elif (type == "image"):
        return pipeline("image-classification", model = model_name, device = device)
    else:
        raise Exception("Filter model type is not 'text' or 'image'.")

    model = model.to(device)
    return model

def LoadTextModel() -> None:
    global text_filter, tokenizer_text, device_text

    if (not cfg.current_data.prompt_order.__contains__("nsfw_filter-text")):
        raise Exception("Model is not in 'prompt_order'.")

    if (text_filter != None and tokenizer_text != None):
        return
    
    device_text = cfg.GetGPUDevice("nsfw_filter-text")

    if (cfg.current_data.print_loading_message):
        print("Loading model 'NSFW Filter (Text)' on device '" + device_text + "'...")
    
    tokenizer_text = AutoTokenizer.from_pretrained(cfg.current_data.nsfw_filter_text_model)
    text_filter = __load_model__(cfg.current_data.nsfw_filter_text_model, device_text, "text")

def LoadImageModel() -> None:
    global image_filter, device_image

    if (not cfg.current_data.prompt_order.__contains__("nsfw_filter-image")):
        raise Exception("Model is not in 'prompt_order'.")

    if (image_filter != None):
        return
    
    device_image = cfg.GetGPUDevice("nsfw_filter-image")

    if (cfg.current_data.print_loading_message):
        print("Loading model 'NSFW Filter (Image)' on device '" + device_image + "'...")
    
    image_filter = __load_model__(cfg.current_data.nsfw_filter_image_model, device_image, "image")

def IsTextNSFW(prompt: str) -> bool:
    # NOTE: The value 0 means NSFW, the value 1 means SFW.
    LoadTextModel()

    if (tokenizer_text == None or text_filter == None):
        return None

    inputs = tokenizer_text.encode(prompt, return_tensors = "pt")
    inputs = inputs.to(device_text)

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