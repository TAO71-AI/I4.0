from transformers import Pipeline
import PIL.Image
import ai_config as cfg

pipe: Pipeline = None
device: str = "cpu"

def LoadModel() -> None:
    global pipe, device

    if (not cfg.current_data.prompt_order.__contains__("img2text")):
        raise Exception("Model is not in 'prompt_order'.")

    if (pipe != None):
        return

    if (cfg.current_data.print_loading_message):
        print("Loading model 'image to text'...")

    data = cfg.LoadPipeline("image-to-text", "img2text", cfg.current_data.img_to_text_model)

    pipe = data[0]
    device = data[1]

    if (cfg.current_data.print_loading_message):
        print("   Loaded model on device '" + device + "'.")

def MakePrompt(img: str) -> str:
    LoadModel()

    if (cfg.current_data.print_prompt):
        print("Image To Text file: " + img)

    image = PIL.Image.open(img)
    response = pipe(image)[0]["generated_text"]

    if (cfg.current_data.print_prompt):
        print("Image to Text response: " + str(response))

    return str(response)