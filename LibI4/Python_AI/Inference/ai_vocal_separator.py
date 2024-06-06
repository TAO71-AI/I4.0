"""
THIS IS UNDER DEVELOPMENT, PLEASE DO NOT USE BECAUSE IT CONTAINS ERRORS AND IT'S NOT FINISHED.
"""

from pathlib import Path
from scipy.io import wavfile
from rvc.modules.uvr5.vr import AudioPreprocess
import logging
import os
import sys
import requests
import shutil
import platform
import ai_config as cfg

uvr: AudioPreprocess = None

def __download_asset__(URL: str, Name: str) -> None:
    if (not os.path.exists("uvr_assets/")):
        os.mkdir("uvr_assets/")

    if (os.path.exists(Name)):
        return
    
    print("Downloading UVR asset: " + Name)
    response = requests.get(URL)

    with open(Name, "wb") as f:
        f.write(response.content)
        f.close()

def __move_file__(OriginalPath: str, NewPath: str) -> None:
    if (os.path.exists(NewPath) or not os.path.exists(OriginalPath)):
        return

    shutil.copy(OriginalPath, NewPath)

def __get_file_name__(FilePath: str) -> str:
    if (FilePath.count("/") > 0):
        FilePath = FilePath[FilePath.rfind("/") + 1:]
    
    return FilePath

def __load_model__(ModelPath: str, Agg: int) -> None:
    global uvr

    if (uvr != None):
        uvr = None

    if (cfg.current_data.print_loading_message):
        print("Loading UVR...")

    if (len(cfg.devices) == 0):
        cfg.__get_gpu_devices__()

    for i in range(len(cfg.devices)):
        device = cfg.GetAvailableGPUDeviceForTask("uvr", i)

        if (device.count(":") > 0):
            device = device.split(":")[0].strip()

        try:
            uvr = AudioPreprocess(ModelPath, Agg)
        
            if (device == "cuda"):
                uvr.config.use_cuda()
            elif (device == "mps"):
                uvr.config.use_mps()
            else:
                if (device != "cpu"):
                    print("Device not supported for UVR. Using CPU.")
                    device = "cpu"
                
                uvr.config.use_cpu()
            
            uvr.model.to(uvr.config.device)

            if (cfg.current_data.print_loading_message):
                print("   Loaded model on device '" + device + "'.")

            return
        except Exception as ex:
            print("ERROR: " + str(ex))
    
    raise Exception("Could not create UVR.")

def __write_output_file__(Type: str, sr: int, output: any) -> bytes:
    output_file_name = "tmp_uvr_"
    output_file_id = 0
    output_file_path = output_file_name + str(output_file_id) + "_" + Type + ".wav"
    
    wavfile.write(output_file_path, sr, output)

    with open(output_file_path, "rb") as f:
        audio_bytes = f.read()
        f.close()
    
    os.remove(output_file_path)
    return audio_bytes

def __make_uvr__(AudioPath: str, Agg: int) -> list[bytes]:
    DownloadAssets()

    currentCWD = os.getcwd()
    path = sys.prefix
    system = platform.system().lower()

    if (system == "windows"):
        path = path + "\\Lib\\site-packages"
    else:
        pythonVersion = sys.version_info
        path = path + "/lib/python" + str(pythonVersion[0]) + "." + str(pythonVersion[1]) + "/site-packages"
    
    os.chdir(path)

    os.environ["TEMP"] = currentCWD
    os.environ["weight_uvr5_root"] = currentCWD + "/uvr_assets"

    try:
        LoadModel(Agg)
        inst, vocals, sr, agg = uvr.process(music_file = currentCWD + "/" + AudioPath)

        os.chdir(currentCWD)

        wavfile.write("vocals.wav", sr, vocals)
        wavfile.write("inst.wav", sr, inst)

        #inst = __write_output_file__("inst", sr, inst)
        #vocals = __write_output_file__("vocals", sr, vocals)

        return [inst, vocals]
    except Exception as ex:
        os.chdir(currentCWD)
        raise ex

def DownloadAssets() -> None:
    assets = {
        "1-HP": "https://huggingface.co/seanghay/uvr_models/resolve/main/1_HP-UVR.pth?download=true",
        "2-HP": "https://huggingface.co/seanghay/uvr_models/resolve/main/2_HP-UVR.pth?download=true",
        "7-HP2": "https://huggingface.co/seanghay/uvr_models/resolve/main/7_HP2-UVR.pth?download=true",
        "8-HP2": "https://huggingface.co/seanghay/uvr_models/resolve/main/8_HP2-UVR.pth?download=true",
        "9-HP2": "https://huggingface.co/seanghay/uvr_models/resolve/main/9_HP2-UVR.pth?download=true" # Recommended
    }

    for asset in assets:
        __download_asset__(assets[asset], "uvr_assets/" + asset)

def LoadModel(Agg: int) -> None:
    __move_file__(cfg.current_data.uvr_model, "uvr_assets/" + __get_file_name__(cfg.current_data.uvr_model))
    cfg.current_data.uvr_model = __get_file_name__(cfg.current_data.uvr_model)

    __load_model__(cfg.current_data.uvr_model, Agg)

def MakeUVR(Data: dict[str]) -> list[bytes]:
    try:
        InputFile = Data["input"]
    except:
        raise Exception("Input file not found.")
    
    try:
        Agg = int(Data["agg"])
    except:
        Agg = 10
    
    return __make_uvr__(InputFile, Agg)

logging.disable(logging.CRITICAL)