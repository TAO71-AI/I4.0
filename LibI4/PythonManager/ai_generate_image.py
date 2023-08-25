from diffusers import DiffusionPipeline
import torch
import ai_config as cfg

pipeline = None

def LoadModel() -> None:
    global pipeline
    
    if (pipeline != None):
        return
    
    pipeline = DiffusionPipeline.from_pretrained(cfg.current_data.image_generation_model)
    pipeline.to("cuda" if torch.cuda.is_available() and cfg.current_data.use_gpu_if_available else "cpu")

def GenerateImage(prompt: str):
    LoadModel()

    image = pipeline(prompt, num_inference_steps = 5).images[0]
    return image