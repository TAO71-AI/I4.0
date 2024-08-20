from transformers import AutoTokenizer, AutoModelForSequenceClassification, Pipeline
from PIL import Image
import ai_config as cfg

text_filter: AutoModelForSequenceClassification | None = None
image_filter: Pipeline | None = None
tokenizer_text: AutoTokenizer | None = None
device_text: str = "cpu"
device_image: str = "cpu"

def LoadTextModel() -> None:
    global text_filter, tokenizer_text, device_text

    if (cfg.current_data["models"].count("nsfw_filter-text") == 0):
        raise Exception("Model is not in 'models'.")

    if (text_filter != None and tokenizer_text != None):
        return

    data = cfg.LoadModel("nsfw_filter-text", cfg.current_data["nsfw_filter_text_model"], AutoModelForSequenceClassification, AutoTokenizer)

    text_filter = data[0]
    tokenizer_text = data[1]
    device_text = data[2]

def LoadImageModel() -> None:
    global image_filter, device_image

    if (cfg.current_data["models"].count("nsfw_filter-image") == 0):
        raise Exception("Model is not in 'models'.")

    if (image_filter != None):
        return

    data = cfg.LoadPipeline("image-classification", "nsfw_filter-image", cfg.current_data["nsfw_filter_image_model"])

    image_filter = data[0]
    device_image = data[1]

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