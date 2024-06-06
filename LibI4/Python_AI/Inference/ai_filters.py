from transformers import AutoTokenizer, AutoModelForSequenceClassification, Pipeline
from PIL import Image
import ai_config as cfg

text_filter: AutoModelForSequenceClassification = None
image_filter: Pipeline = None
tokenizer_text: AutoTokenizer = None
device_text: str = "cpu"
device_image: str = "cpu"

def LoadTextModel() -> None:
    global text_filter, tokenizer_text, device_text

    if (not cfg.current_data.prompt_order.__contains__("nsfw_filter-text")):
        raise Exception("Model is not in 'prompt_order'.")

    if (text_filter != None and tokenizer_text != None):
        return

    if (cfg.current_data.print_loading_message):
        print("Loading model 'NSFW Filter (Text)'...")
    
    data = cfg.LoadModel("nsfw_filter-text", cfg.current_data.nsfw_filter_text_model, AutoModelForSequenceClassification, AutoTokenizer)

    text_filter = data[0]
    tokenizer_text = data[1]
    device_text = data[2]

    if (cfg.current_data.print_loading_message):
        print("   Loaded model on device '" + device_text + "'.")

def LoadImageModel() -> None:
    global image_filter, device_image

    if (not cfg.current_data.prompt_order.__contains__("nsfw_filter-image")):
        raise Exception("Model is not in 'prompt_order'.")

    if (image_filter != None):
        return

    if (cfg.current_data.print_loading_message):
        print("Loading model 'NSFW Filter (Image)'...")
    
    data = cfg.LoadPipeline("image-classification", "nsfw_filter-image", cfg.current_data.nsfw_filter_image_model)

    image_filter = data[0]
    device_image = data[1]

    if (cfg.current_data.print_loading_message):
        print("   Loaded model on device '" + device_image + "'.")

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