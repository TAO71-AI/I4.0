from transformers import Pipeline
import PIL.Image
import ai_config as cfg

pipe: Pipeline | None = None
device: str = "cpu"

def LoadModel() -> None:
    global pipe, device

    if (cfg.current_data["models"].count("img2text") == 0):
        raise Exception("Model is not in 'models'.")

    if (pipe != None):
        return

    data = cfg.LoadPipeline("image-to-text", "img2text", cfg.current_data["img_to_text_model"])

    pipe = data[0]
    device = data[1]

def MakePrompt(img: str) -> str:
    LoadModel()

    image = PIL.Image.open(img)
    response = pipe(image)[0]["generated_text"]

    return str(response)