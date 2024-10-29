# Import the libraries
from diffusers import AutoPipelineForText2Image
from PIL.Image import Image

# Import I4.0's utilities
import ai_config as cfg

def __load_model__(Index: int) -> AutoPipelineForText2Image:
    # Create the model
    model = cfg.LoadDiffusersPipeline("text2img", Index, AutoPipelineForText2Image, None)[0]

    # Return the model
    return model

def __inference__(Model: AutoPipelineForText2Image, Prompt: str, NegativePrompt: str, Width: int, Height: int, Guidance: float, Steps: int) -> list[Image]:
    # Inference
    return Model(
        Prompt,
        num_inference_steps = Steps,
        width = Width,
        height = Height,
        guidance_scale = Guidance,
        output_type = "pil",
        negative_prompt = NegativePrompt
    ).images