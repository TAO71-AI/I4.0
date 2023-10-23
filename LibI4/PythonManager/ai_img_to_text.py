from transformers import AutoProcessor, AutoModelForCausalLM
import PIL.Image
import torch
import ai_config as cfg

processor = None
model = None

def LoadModel() -> None:
    global processor, model

    if (processor != None and model != None):
        return
    
    move_to_gpu = cfg.current_data.use_gpu_if_available and torch.cuda.is_available() and cfg.current_data.move_to_gpu.__contains__("9")
    device = "cuda" if (move_to_gpu) else "cpu"

    processor = AutoProcessor.from_pretrained(cfg.current_data.img_to_text_model)
    model = AutoModelForCausalLM.from_pretrained(cfg.current_data.img_to_text_model).to(device)

def MakePrompt(img: str) -> str:
    LoadModel()

    image = PIL.Image.open(img)
    pixel_values = processor(images = [image], return_tensors = "pt").pixel_values

    generated_ids = model.generate(pixel_values = pixel_values, max_length = cfg.current_data.max_length)
    generated_caption = processor.batch_decode(generated_ids, skip_special_tokes = True)[0]

    return str(generated_caption)