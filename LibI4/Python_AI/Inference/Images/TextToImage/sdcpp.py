# Import the libraries
from stable_diffusion_cpp import StableDiffusion, GGMLType
from huggingface_hub import hf_hub_download
from PIL.Image import Image

# Import I4.0's utilities
import ai_config as cfg
import Inference.PredefinedModels.models as models

def __load_model__(Type: str, DiffusionModel: str, VAE: str, ClipL: str, T5XXL: str, Threads: int) -> StableDiffusion:
    # Print loading message
    print("Loading StableDiffusion-CPP model (device is unknown)...")

    # Load the model
    model = StableDiffusion(
        diffusion_model_path = DiffusionModel,
        vae_path = VAE if (Type == "sdcpp-flux") else "",
        clip_l_path = ClipL,
        #clip_g_path = VAE if (Type == "sdcpp-sd") else "",
        t5xxl_path = T5XXL,
        n_threads = Threads,
        wtype = "default",
        verbose = True
    )

    # Print loading message
    print("    Done!")

    # Return the model
    return model

def __load_custom_model__(Index: int, Threads: int) -> StableDiffusion:
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

def __get_quantization_and_repo_from_dict__(Dict: dict[str, any], DesiredQuantization: str, DefaultRepo: str) -> tuple[str, str]:
    # Get repo
    if (list(Dict.keys()).count("repo") == 0 or Dict["repo"] == None):
        # Invalid repository, set default
        repo = DefaultRepo
    else:
        # Use the repository set in the dictionary
        repo = Dict["repo"]
    
    # Get quantization
    if (list(Dict.keys()).count(DesiredQuantization) == 0):
        # Invalid quantization, set default
        quantization = Dict[Dict["default"]]

        # Check that the quantization exists
        if (list(Dict.keys()).count(quantization) == 0):
            # It doesn't exists
            raise ValueError(f"Invalid quantization '{DesiredQuantization}'; '{quantization}'. Available quantizations are: {[i for i in list(Dict.keys()) if (i != 'repo' and i != 'default')]}.")
    else:
        # Use the desired quantization
        quantization = Dict[DesiredQuantization]
    
    # Return the quantization and repository
    return (quantization, repo)

def __get_model_from_pretrained__(Name: str, ModelQuantization: str, VaeQuantization: str, ClipLQuanization: str, T5XXLQuanization: str) -> tuple[str, str, str, str, str]:
    # Lower and strip the quantizations
    ModelQuantization = ModelQuantization.lower().strip()
    VaeQuantization = VaeQuantization.lower().strip()
    ClipLQuanization = ClipLQuanization.lower().strip()
    T5XXLQuanization = T5XXLQuanization.lower().strip()

    # Check if the model exists in the list
    if (list(models.Text2Image_SDCPP.keys()).count(Name) == 0):
        raise ValueError(f"Invalid model name. Available models are: {list(models.Text2Image_SDCPP.keys())}.")
    
    # Model
    modelQ, modelR = __get_quantization_and_repo_from_dict__(models.Text2Image_SDCPP[Name]["model"], ModelQuantization, models.Text2Image_SDCPP[Name]["repo"])

    # VAE
    vaeQ, vaeR = __get_quantization_and_repo_from_dict__(models.Text2Image_SDCPP[Name]["vae"], VaeQuantization, models.Text2Image_SDCPP[Name]["repo"])

    # Clip L
    cliplQ, cliplR = __get_quantization_and_repo_from_dict__(models.Text2Image_SDCPP[Name]["clip_l"], ClipLQuanization, models.Text2Image_SDCPP[Name]["repo"])

    # T5XXL
    t5xxlQ, t5xxlR = __get_quantization_and_repo_from_dict__(models.Text2Image_SDCPP[Name]["t5xxl"], T5XXLQuanization, models.Text2Image_SDCPP[Name]["repo"])

    # Download everything
    modelPath = hf_hub_download(modelR, modelQ)
    vaePath = hf_hub_download(vaeR, vaeQ)
    cliplPath = hf_hub_download(cliplR, cliplQ)
    t5xxlPath = hf_hub_download(t5xxlR, t5xxlQ)

    # Return the data
    return (models.Text2Image_SDCPP[Name]["type"], modelPath, vaePath, cliplPath, t5xxlPath)

def __load_predefined_model__(Index: int, Threads: int) -> StableDiffusion:
    # Get the model path
    mp = cfg.GetInfoOfTask("text2img", Index)["model"]

    # Model is expected to be:
    # [
    #     "Model name",
    #     "Model quantization",
    #     "VAE / Clip G quantization",
    #     "Clip L quantization",
    #     "T5XXL quantization"
    # ]

    # Lower the model name
    mp[0] = mp[0].lower()
    modelType, modelPath, vaePath, cliplPath, t5xxlPath = __get_model_from_pretrained__(mp[0], mp[1], mp[2], mp[3], mp[4])

    # Load the model
    return __load_model__(modelType, modelPath, vaePath, cliplPath, t5xxlPath, Threads)

def LoadModel(Index: int, Threads: int) -> StableDiffusion:
    try:
        # Try to load using the predefined list
        return __load_predefined_model__(Index, Threads)
    except ValueError:
        # Error; invalid model
        # Load as a custom one
        return __load_custom_model__(Index, Threads)

def __inference__(Model: StableDiffusion, Prompt: str, NegativePrompt: str, Width: int, Height: int, Guidance: float, Steps: int) -> list[Image]:
    # Inference
    return Model.txt_to_img(
        prompt = Prompt,
        negative_prompt = NegativePrompt,
        sample_steps = Steps,
        width = Width,
        height = Height,
        guidance = Guidance,
        sample_method = "euler"
    )