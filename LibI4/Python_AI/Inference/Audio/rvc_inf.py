# Import some utilities
from pathlib import Path
from scipy.io import wavfile

# Import RVC
from rvc.modules.vc.modules import VC

# Import other utilities
import logging
import os
import requests
import shutil

# Import I4.0 utilities
import ai_config as cfg

__models__: dict[str, tuple[VC, str, str]] = {}

def __download_asset__(URL: str, Name: str) -> None:
    # Check if the RVC assets folder exists
    if (not os.path.exists("rvc_assets/")):
        # Create it
        os.mkdir("rvc_assets/")

    # Ignore if the asset already exists
    if (os.path.exists(Name)):
        return
    
    # Download the RVC asset
    print("Downloading RVC asset: " + Name)
    response = requests.get(URL)

    # Save into the file
    with open(Name, "wb") as f:
        f.write(response.content)
        f.close()

def __move_file__(OriginalPath: str, NewPath: str) -> None:
    # Check if the file exists in the new path or if the original path doesn't exists
    if (os.path.exists(NewPath) or not os.path.exists(OriginalPath)):
        # One of the previous statements are True, return
        return

    # Copy the file
    shutil.copy(OriginalPath, NewPath)

def __get_file_name__(FilePath: str) -> str:
    # Check if the file path contains more or one /
    if (FilePath.count("/") > 0):
        # It does, cut the file path
        FilePath = FilePath[FilePath.rfind("/") + 1:]
    
    # Return the file path
    return FilePath

def __load_model__(ModelPath: str, ModelName: str, ModelIndex: str, ModelType: str, Index: int) -> None:
    # Set the environment variables
    os.environ["index_root"] = "rvc_assets"
    os.environ["rmvpe_root"] = "rvc_assets"

    # Get the available device for the model
    device = cfg.GetAvailableGPUDeviceForTask("rvc", Index)

    # Create the VC
    vc = VC()
    vc.version = "v2"

    # Set the device for the VC
    if (device == "cuda" or device == "xpu"):
        # Use CUDA
        vc.config.use_cuda()
    elif (device == "mps"):
        # Use MPS
        vc.config.use_mps()
    else:
        # Use CPU
        vc.config.use_cpu()

    # Set the VC
    vc.get_vc(os.getcwd() + "/rvc_assets/" + ModelPath)

    # Add to the models dict
    __models__[ModelName] = (vc, ModelIndex, ModelType)

def __make_rvc__(AudioPath: str, ModelName: str, Protect: float, FilterRadius: int, F0UpKey: int) -> bytes:
    # Load all the models
    LoadModels()

    # Check if the audio file exists
    if (not os.path.exists(AudioPath)):
        raise Exception("Audio file doesn't exists.")

    # Inference the model
    tgt_sr, audio_opt, _, _ = __models__[ModelName][0].vc_inference(1, Path(AudioPath), f0_up_key = F0UpKey, protect = Protect, filter_radius = FilterRadius, f0_method = __models__[ModelName][2], hubert_path = os.getcwd() + "/rvc_assets/hubert_base.pt", index_file = __models__[ModelName][1])
    
    # Write the audio file
    output_file_name = "tmp_rvc_"
    output_file_id = 0
    output_file_path = output_file_name + str(output_file_id) + ".wav"

    while (os.path.exists(output_file_path)):
        output_file_id += 1
        output_file_path = output_file_name + str(output_file_id) + ".wav"
    
    wavfile.write(output_file_path, tgt_sr, audio_opt)

    # Read the output file
    with open(output_file_path, "rb") as f:
        audio_bytes = f.read()
        f.close()
    
    # Delete the output file
    os.remove(output_file_path)

    # Return the bytes of the generated audio file
    return audio_bytes

def DownloadAssets() -> None:
    # Set the asset list to download
    assets = {
        "hubert_base.pt": "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt?download=true",
        "rmvpe.pt": "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.pt?download=true"
    }

    # For each asset
    for asset in assets:
        # Download the asset and save it
        __download_asset__(assets[asset], "rvc_assets/" + asset)

def LoadModels(AllowDownloads: bool = True) -> None:
    # Check if the downloads are enabled
    if (AllowDownloads):
        # Download the assets
        DownloadAssets()

    # For each model
    for i in range(len(cfg.GetAllInfosOfATask("rvc"))):
        # Check if the model is already loaded
        if (i < len(list(__models__.keys()))):
            continue

        # Get the info
        info = cfg.GetInfoOfTask("rvc", i)

        # Move the files
        __move_file__(info["model"][1], "rvc_assets/" + __get_file_name__(info["model"][1]))
        __move_file__(info["model"][2], "rvc_assets/" + __get_file_name__(info["model"][2]))

        # Update the info
        mPath = __get_file_name__(info["model"][1])
        mIndex = __get_file_name__(info["model"][2])

        # Load the model
        __load_model__(mPath, info["model"][0], mIndex, info["model"][3], i)

def MakeRVC(Data: dict[str]) -> bytes:
    # Get the input file name
    try:
        InputFile = Data["input"]
    except:
        raise Exception("Input file not found.")
    
    # Get the model name
    try:
        ModelName = Data["model"]
    except:
        try:
            ModelName = list(__models__.keys())[Data["index"]]
        except:
            raise Exception("Model name can't be NULL.")
    
    # Get the filter radius
    try:
        FilterRadius = int(Data["filter_radius"])

        # Clamp the filter radius
        if (FilterRadius > 5):
            FilterRadius = 5
        elif (FilterRadius < 0):
            FilterRadius = 0
    except:
        FilterRadius = 3
    
    # Get the f0 up key
    try:
        F0UpKey = int(Data["f0_up_key"])
    except:
        F0UpKey = 3

    # Get the protect
    try:
        Protect = float(Data["protect"])

        # Clamp the protect
        if (Protect < 0.05):
            Protect = 0.05
        elif (Protect > 0.5):
            Protect = 0.5
    except:
        Protect = 0.33
    
    # Inference the model
    return __make_rvc__(InputFile, ModelName, Protect, FilterRadius, F0UpKey)

# Disable logging
logging.disable(logging.CRITICAL)