from transformers import AutoProcessor, AutoModelForCausalLM, TFAutoModelForCausalLM
import PIL.Image
import torch
import ai_config as cfg

processor: AutoProcessor = None
model: AutoModelForCausalLM | TFAutoModelForCausalLM = None
device: str = "cpu"

def __load_model__(model_name: str, device: str):
    if (cfg.current_data.use_tf_instead_of_pt):
        return TFAutoModelForCausalLM.from_pretrained(model_name)
    else:
        model = AutoModelForCausalLM.from_pretrained(model_name).to(device)
        return model

def LoadModel() -> None:
    global processor, model, device

    if (not cfg.current_data.prompt_order.__contains__("img2text")):
        raise Exception("Model is not in 'prompt_order'.")

    if (processor != None and model != None):
        return
    
    move_to_gpu = cfg.current_data.use_gpu_if_available and torch.cuda.is_available() and cfg.current_data.move_to_gpu.__contains__("img2text")
    device = "cuda" if (move_to_gpu) else "cpu"

    if (cfg.current_data.print_loading_message):
        print("Loading model 'image to text' on device '" + device + "'...")

    processor = AutoProcessor.from_pretrained(cfg.current_data.img_to_text_model)
    model = __load_model__(cfg.current_data.img_to_text_model, device)

def MakePrompt(img: str) -> str:
    LoadModel()

    image = PIL.Image.open(img)
    pixel_values = processor(images = [image], return_tensors = ("tf" if cfg.current_data.use_tf_instead_of_pt else "pt"))

    if (not cfg.current_data.use_tf_instead_of_pt):
        pixel_values = pixel_values.to(device)
    
    pixel_values = pixel_values.pixel_values

    generated_ids = model.generate(pixel_values = pixel_values, max_length = cfg.current_data.max_length)
    generated_caption = processor.batch_decode(generated_ids, skip_special_tokes = True)[0]

    return str(generated_caption)