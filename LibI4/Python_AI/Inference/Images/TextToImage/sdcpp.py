# Import I4.0's utilities
import ai_config as cfg

# Import the libraries
from stable_diffusion_cpp import StableDiffusion
from huggingface_hub import hf_hub_download
from PIL.Image import Image

def __load_model__(Type: str, DiffusionModel: str, VAE: str, ClipL: str, T5XXL: str, Threads: int) -> StableDiffusion:
    # Print loading message
    print("Loading StableDiffusion-CPP model (device is unknown)...")

    # Load the model
    model = StableDiffusion(
        diffusion_model_path = DiffusionModel,
        vae_path = VAE if (Type == "sdcpp-flux") else "",
        clip_l_path = ClipL,
        clip_g_path = VAE if (Type == "sdcpp-sd") else "",
        t5xxl_path = T5XXL,
        n_threads = Threads,
        wtype = "default",
        verbose = True
    )

    # Print loading message
    print("    Done!")

    # Return the model
    return model

def LoadModel(Index: int, Threads: int) -> StableDiffusion:
    # Get the model path
    info = cfg.GetInfoOfTask("text2img", Index)
    mp = info["model"]
    mt = info["type"]

    # Model is expected to be:
    # [
    #     "Diffusion model path",
    #     "VAE / Clip G",
    #     "Clip L path",
    #     "T5XXL path"
    # ]

    # Load and return the model
    return __load_model__(mt, mp[0], mp[1], mp[2], mp[3], Threads)

def __inference__(
        Model: StableDiffusion,
        Prompt: str,
        NegativePrompt: str,
        Width: int,
        Height: int,
        Guidance: float,
        Steps: int,
        CFGScale: float
    ) -> list[Image]:
    # Inference
    return Model.txt_to_img(
        prompt = Prompt,
        negative_prompt = NegativePrompt,
        sample_steps = Steps,
        width = Width,
        height = Height,
        guidance = Guidance,
        cfg_scale = CFGScale,
        sample_method = "euler",
        batch_count = 1,
        seed = -1
    )