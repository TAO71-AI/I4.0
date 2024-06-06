from pathlib import Path
from scipy.io import wavfile
from rvc.modules.vc.modules import VC
import logging
import os
import requests
import shutil
import ai_config as cfg

vc: VC = None

def __download_asset__(URL: str, Name: str) -> None:
    if (not os.path.exists("rvc_assets/")):
        os.mkdir("rvc_assets/")

    if (os.path.exists(Name)):
        return
    
    print("Downloading RVC asset: " + Name)
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

def __load_model__(ModelPath: str, ModelName: str) -> None:
    global vc

    if (vc != None):
        vc = None

    os.environ["index_root"] = "rvc_assets"
    os.environ["rmvpe_root"] = "rvc_assets"

    if (cfg.current_data.print_loading_message):
        print("Loading RVC model '" + ModelName + "'...")

    device = cfg.GetAvailableGPUDeviceForTask("rvc", 0)

    if (device.count(":") > 0):
        device = device.split(":")[0].strip()
    
    if (device.count("-") > 0):
        device = device.split("-")[0].strip()

    vc = VC()
    vc.version = "v2"

    if (device == "cuda"):
        vc.config.use_cuda()
    elif (device == "mps"):
        vc.config.use_mps()
    else:
        if (device != "cpu"):
            print("Device not supported for RVC. Using CPU.")
            device = "cpu"
        
        vc.config.use_cpu()

    vc.get_vc(os.getcwd() + "/rvc_assets/" + ModelPath)

    if (cfg.current_data.print_loading_message):
        print("   Loaded model on device '" + device + "'.")

def __make_rvc__(AudioPath: str, ModelName: str, Protect: float, FilterRadius: int, f0_up_key: int) -> bytes:
    LoadModel(ModelName)

    if (not os.path.exists(AudioPath)):
        raise Exception("Audio file doesn't exists.")

    try:
        tgt_sr, audio_opt, _, _ = vc.vc_inference(1, Path(AudioPath), f0_up_key = f0_up_key, protect = Protect, filter_radius = FilterRadius, f0_method = cfg.current_data.rvc_models[ModelName][2], hubert_path = os.getcwd() + "/rvc_assets/hubert_base.pt", index_file = cfg.current_data.rvc_models[ModelName][1])

        print(str(tgt_sr == None) + " " + str(audio_opt == None))
    except Exception as ex:
        print("\n\n" + str(ex) + "\n\n")
    
    output_file_name = "tmp_rvc_"
    output_file_id = 0
    output_file_path = output_file_name + str(output_file_id) + ".wav"

    while (os.path.exists(output_file_path)):
        output_file_id += 1
        output_file_path = output_file_name + str(output_file_id) + ".wav"
    
    wavfile.write(output_file_path, tgt_sr, audio_opt)

    with open(output_file_path, "rb") as f:
        audio_bytes = f.read()
        f.close()
    
    os.remove(output_file_path)
    return audio_bytes

def DownloadAssets() -> None:
    assets = {
        "hubert_base.pt": "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/hubert_base.pt?download=true",
        "rmvpe.pt": "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/rmvpe.pt?download=true"
    }

    for asset in assets:
        __download_asset__(assets[asset], "rvc_assets/" + asset)

def LoadModel(ModelName: str, AllowDownloads: bool = True) -> None:
    if (AllowDownloads):
        DownloadAssets()
    
    if (list(cfg.current_data.rvc_models.keys()).count(ModelName) == 0):
        raise Exception("Model '" + ModelName + "' not found.")
    
    __move_file__(cfg.current_data.rvc_models[ModelName][0], "rvc_assets/" + __get_file_name__(cfg.current_data.rvc_models[ModelName][0]))
    __move_file__(cfg.current_data.rvc_models[ModelName][1], "rvc_assets/" + __get_file_name__(cfg.current_data.rvc_models[ModelName][1]))

    cfg.current_data.rvc_models[ModelName][0] = __get_file_name__(cfg.current_data.rvc_models[ModelName][0])
    cfg.current_data.rvc_models[ModelName][1] = __get_file_name__(cfg.current_data.rvc_models[ModelName][1])

    __load_model__(cfg.current_data.rvc_models[ModelName][0], ModelName)

def MakeRVC(Data: dict[str]) -> bytes:
    try:
        InputFile = Data["input"]
    except:
        raise Exception("Input file not found.")
    
    try:
        ModelName = Data["model"]
    except:
        raise Exception("Model name can't be NULL.")
    
    try:
        FilterRadius = int(Data["filter_radius"])
    except:
        FilterRadius = 3
    
    try:
        F0UpKey = int(Data["f0_up_key"])
    except:
        F0UpKey = 3

    try:
        Protect = float(Data["protect"])

        if (Protect < 0.05):
            Protect = 0.05
        elif (Protect > 0.5):
            Protect = 0.5
    except:
        Protect = 0.33
    
    return __make_rvc__(InputFile, ModelName, Protect, FilterRadius, F0UpKey)

logging.disable(logging.CRITICAL)