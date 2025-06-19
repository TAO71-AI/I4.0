# Import I4.0 utilities
import ai_config as cfg
import temporal_files as tempFiles

# Import other libraries
from io import BytesIO
from pathlib import Path
from scipy.io import wavfile
from rvc.modules.vc.modules import VC
import logging
import os
import requests
import shutil
import psutil

__models__: dict[int, tuple[VC, str, str]] = {}

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

def __load_model__(ModelPath: str, ModelIndex: str, ModelType: str, Index: int) -> None:
    # Set the environment variables
    os.environ["index_root"] = "rvc_assets"
    os.environ["rmvpe_root"] = "rvc_assets"

    # Get the available device for the model
    device = cfg.GetAvailableGPUDeviceForTask("rvc", Index)
    info = cfg.GetInfoOfTask("rvc", Index)

    # Create the VC
    vc = VC()
    vc.version = "v2"

    # Set the device for the VC
    if (device == "cuda" or device == "xpu"):
        # Use CUDA
        vc.config.use_cuda()
    elif (device == "dml"):
        # Use DML
        vc.config.use_dml()
    elif (device == "mps"):
        # Use MPS
        vc.config.use_mps()
    else:
        # Use CPU
        vc.config.use_cpu()
        device = "cpu"
    
    # Print loading message
    print(f"Loading model for 'RVC [INDEX {Index}]' on the device '{device}'...")
    
    # Get threads and check if the number of threads are valid
    if (info["threads"] == -1):
        threads = psutil.cpu_count()
    elif (info["threads"] <= 0 or info["threads"] > psutil.cpu_count()):
        raise Exception("Invalid number of threads.")
    else:
        threads = info["threads"]
    
    # Set the threads number to use
    vc.config.n_cpu = threads

    # Set the VC
    vc.get_vc(f"{os.getcwd()}/rvc_assets/{ModelPath}")

    # Add to the models dict
    __models__[Index] = (vc, ModelIndex, ModelType)

    # Print loading message
    print("   Done!")

def __make_rvc__(Index: int, AudioData: bytes | str, Protect: float, FilterRadius: int, F0UpKey: int, IndexRate: float, MixRate: float) -> bytes:
    # Load the model
    __prepare_model__(Index)

    # Save temporal file
    if (isinstance(AudioData, bytes)):
        audioPath = tempFiles.CreateTemporalFile("audio", AudioData)
    elif (isinstance(AudioData, str)):
        # Check if the audio path is valid
        if (not os.path.exists(AudioData)):
            raise FileNotFoundError("Invalid audio path.")
        
        # Use the audio path as is
        audioPath = AudioData
    else:
        # Invalid audio data type
        raise ValueError("Invalid audio data type. Must be 'bytes' or 'str'.")

    # Inference the model
    tgt_sr, audio_opt, _, _ = __models__[Index][0].vc_inference(
        1,
        Path(audioPath),
        f0_up_key = F0UpKey,
        protect = Protect,
        filter_radius = FilterRadius,
        f0_method = __models__[Index][2],
        hubert_path = f"{os.getcwd()}/rvc_assets/hubert_base.pt",
        index_file = __models__[Index][1],
        index_rate = IndexRate,
        rms_mix_rate = MixRate
    )
    
    # Write the audio buffer
    buffer = BytesIO()
    wavfile.write(buffer, tgt_sr, audio_opt)

    buffer.seek(0)
    data = buffer.getvalue()
    
    buffer.close()

    # Return the bytes of the audio buffer
    return data

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

def __prepare_model__(Index: int) -> None:
    # Check if the model is already loaded
    if (Index in list(__models__.keys()) and __models__[Index] is not None):
        return

    # Get the info
    info = cfg.GetInfoOfTask("rvc", Index)

    # Move the files
    __move_file__(info["model"][1], "rvc_assets/" + __get_file_name__(info["model"][1]))
    __move_file__(info["model"][2], "rvc_assets/" + __get_file_name__(info["model"][2]))

    # Update the info
    mPath = __get_file_name__(info["model"][1])
    mIndex = f"{os.getcwd()}/rvc_assets/{__get_file_name__(info['model'][2])}"

    # Load the model
    __load_model__(mPath, mIndex, info["model"][3], Index)

def LoadModels(AllowDownloads: bool = True) -> None:
    # Check if the downloads are enabled
    if (AllowDownloads):
        # Download the assets
        DownloadAssets()

    # For each model
    for i in range(len(cfg.GetAllInfosOfATask("rvc"))):
        __prepare_model__(i)

def __offload_model__(Index: int) -> None:
    # Check the index is valid
    if (Index not in list(__models__.keys()) or __models__[Index] is None):
        # Not valid, return
        return
    
    # Offload the model
    __models__[Index] = None
    
    # Delete from the models list
    __models__.pop(Index)

def MakeRVC(Data: dict[str, any]) -> bytes:
    # Get the input bytes
    try:
        InputBytes = Data["input"]

        # Check if the input bytes are valid
        if ((not isinstance(InputBytes, bytes) and not isinstance(InputBytes, str)) or len(InputBytes) == 0):
            raise Exception()
    except:
        raise Exception("Input bytes not found.")

    # Get the index
    try:
        Index = Data["index"]

        if (Index >= len(cfg.GetAllInfosOfATask("rvc"))):
            raise Exception()
    except:
        raise Exception("Invalid Index.")
    
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
    
    # Get the index rate
    try:
        IndexRate = float(Data["index_rate"])

        # Clamp the index rate
        if (IndexRate < 0):
            Protect = 0
        elif (IndexRate > 1):
            IndexRate = 1
    except:
        IndexRate = 0.75
    
    # Get the mix rate
    try:
        MixRate = float(Data["mix_rate"])

        # Clamp the mix rate
        if (MixRate < 0):
            MixRate = 0
        elif (MixRate > 1):
            MixRate = 1
    except:
        MixRate = 0.25
    
    # Inference the model
    return __make_rvc__(Index, InputBytes, Protect, FilterRadius, F0UpKey, IndexRate, MixRate)

# Disable logging
logging.disable(logging.CRITICAL)