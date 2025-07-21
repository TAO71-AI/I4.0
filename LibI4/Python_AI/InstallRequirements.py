# Import libraries
import subprocess
import sys
import os

def __str_cmd_to_list__(Cmd: str) -> list[str]:
    cmd = Cmd.strip().replace("\n", "\\n").replace("\\ ", "\n")
    cmd = cmd.split(" ")
    cmd = [c.replace("\n", " ").replace("\\n", "\n") for c in cmd]

    for c in cmd:
        if (len(c) == 0):
            cmd.remove(c)
    
    return cmd

def __detect_gpu__() -> str:
    try:
        result = subprocess.check_output(["lspci", "-nn"], text = True)
        result = [line for line in result.splitlines() if (any(k in line.lower() for k in ["vga", "3d", "display"]))]
        result = "\n".join(result).lower()

        if ("nvidia" in result):
            return "nvidia"
        elif ("amd" in result):
            return "amd"
        elif ("intel" in result):
            return "intel"
        
        return "unknown"
    except subprocess.CalledProcessError:
        print(f"Error trying to detect the GPU.")
        exit(1)
    except FileNotFoundError:
        print("'lspci' command not installed. Please install it first or use the '--gpu=none' argument.")
        exit(1)

def __vulkan_available__() -> bool:
    try:
        result = subprocess.check_output(["vulkaninfo"], text = True, stderr = subprocess.DEVNULL)

        for line in result.splitlines():
            if ("Vulkan API version" in line or "Vulkan Instance Version" in line):
                return True
        
        return False
    except subprocess.CalledProcessError:
        print(f"Error trying to detect Vulkan. If this error persists, try using the '--no-vulkan' argument.")
        exit(1)
    except FileNotFoundError:
        return False

def __find_pip__() -> str:
    def __execute_pip_cmd__(Cmd: list[str]) -> int:
        try:
            return subprocess.run(Cmd + ["--help"], capture_output = True).returncode
        except (subprocess.CalledProcessError, FileNotFoundError):
            return 1

    cmds = [
        "pip",
        "pip3",
        "python -m pip",
        "python3 -m pip"
    ]

    for cmd in cmds:
        result = __execute_pip_cmd__(cmd.split(" "))

        if (result == 0):
            return cmd
    
    print("Could not find PIP automatically. Please set it manually using the '--pip-cmd=' argument.")
    exit(1)

def InstallPackages(
        Packages: list[str] | str,
        Index: str | None = None,
        ExtraIndex: str | list[str] | None = None,
        PIPArgs: list[str] | str = "",
        PrePIPArgs: list[str] | str = "",
        EnvVars: dict[str, any] = {},
        Verbose: bool = False
    ) -> None:
    # Define globals
    global PIPCmd, VerboseFull, ShowCommandOutput

    # Set command
    cmd = f"{' '.join(PrePIPArgs) if (isinstance(PrePIPArgs, list)) else PrePIPArgs} {PIPCmd} install {' '.join(PIPArgs) if (isinstance(PIPArgs, list)) else PIPArgs}"
    cmd += f"{' --verbose' if Verbose else ''} {' '.join(Packages) if (isinstance(Packages, list)) else Packages}"
    cmd += f" --index-url {Index}" if (Index is not None) else ""
    cmd += "".join(f" --extra-index-url {eidx}" for eidx in ExtraIndex) if (isinstance(ExtraIndex, list)) else f" --extra-index-url {ExtraIndex}" if (ExtraIndex is not None) else ""
    cmd = __str_cmd_to_list__(cmd)

    # Set environment
    env = os.environ.copy()

    for varName, varVal in EnvVars.items():
        env[varName] = varVal

    # Execute command
    if (VerboseFull):
        print(f"^ RUNNING COMMAND '{' '.join(cmd)}'...")
    
    return subprocess.run(cmd, env = env, capture_output = not ShowCommandOutput).returncode

def UninstallPackages(Packages: list[str] | str) -> int:
    # Define globals
    global PIPCmd, VerboseFull, ShowCommandOutput

    # Set command
    cmd = f"{PIPCmd} uninstall -y {''.join(Packages) if (isinstance(Packages, list)) else Packages}"
    cmd = __str_cmd_to_list__(cmd)

    # Execute command
    if (VerboseFull):
        print(f"^ RUNNING COMMAND '{' '.join(cmd)}'...")
    
    return subprocess.run(cmd, capture_output = not ShowCommandOutput).returncode

# Set variables
Verbose: bool = False
VerboseFull: bool = False
GPUVendor: str | None = None
VulkanAvailable: bool | None = None
PIPCmd: str | None = None
TorchPackage: str | None = "torch>=2.0.0,<2.6.0 torchvision torchaudio"
TorchCUDA: str = "https://download.pytorch.org/whl/cu128"
TorchROCm: str = "https://download.pytorch.org/whl/rocm6.3"
TorchSycl: str = "https://download.pytorch.org/whl/xpu"
TorchCPU: str = "https://download.pytorch.org/whl/cpu"
TorchWhl: str | None = None
LcppPackage: str | None = "llama-cpp-python"
LcppWhl: str | None = None
LcppF16: bool = False
SdcppPackage: str | None = "stable-diffusion-cpp-python"
SdcppWhl: str | None = None
SdcppF16: bool = False
RVCPackage: str | None = "rvc"
FairseqPackage: str | None = "git+https://github.com/Tps-F/fairseq.git@main"
SkipOtherRequirements: bool = False
ShowCommandOutput: bool = False

# Check arguments
if (len(sys.argv) > 1):
    for arg in sys.argv[1:]:
        if (arg.startswith("--gpu=")):
            GPUVendor = arg[6:].lower().strip()

            if (GPUVendor != "nvidia" and GPUVendor != "amd" and GPUVendor != "intel"):
                GPUVendor = "unknown"
        elif (arg == "--no-vulkan"):
            VulkanAvailable = False
        elif (arg.startswith("--torch-cuda-whl=")):
            TorchCUDA = arg[17:].strip()
        elif (arg.startswith("--torch-rocm-whl=")):
            TorchROCm = arg[17:].strip()
        elif (arg.startswith("--torch-sycl-whl=")):
            TorchSycl = arg[17:].strip()
        elif (arg.startswith("--torch-cpu-whl=")):
            TorchCPU = arg[16:].strip()
        elif (arg == "--torch-cuda-only"):
            TorchWhl = "cuda"
        elif (arg == "--torch-rocm-only"):
            TorchWhl = "amd"
        elif (arg == "--torch-intel-only" or arg == "--torch-sycl-only"):
            TorchWhl = "intel"
        elif (arg == "--torch-cpu-only"):
            TorchWhl = "cpu"
        elif (arg.startswith("--torch-pkg=")):
            TorchPackage = arg[12:]
        elif (arg == "--lcpp-cuda-only"):
            LcppWhl = "cuda"
        elif (arg == "--lcpp-rocm-only"):
            LcppWhl = "amd"
        elif (arg == "--lcpp-intel-only" or arg == "--lcpp-sycl-only"):
            LcppWhl = "intel"
        elif (arg == "--lcpp-vulkan-only"):
            LcppWhl = "vulkan"
        elif (arg == "--lcpp-cpu-only"):
            LcppWhl = "cpu"
        elif (arg == "--sdcpp-cuda-only"):
            SdcppWhl = "cuda"
        elif (arg == "--sdcpp-rocm-only"):
            SdcppWhl = "amd"
        elif (arg == "--sdcpp-intel-only" or arg == "--sdcpp-sycl-only"):
            SdcppWhl = "intel"
        elif (arg == "--sdcpp-vulkan-only"):
            SdcppWhl = "vulkan"
        elif (arg == "--sdcpp-cpu-only"):
            SdcppWhl = "cpu"
        elif (arg == "--lcpp-git"):
            LcppPackage = "git+https://github.com/abetlen/llama-cpp-python.git@main"
        elif (arg.startswith("--lcpp-pkg=")):
            LcppPackage = arg[11:].strip()
        elif (arg == "--sdcpp-git"):
            SdcppPackage = "git+https://github.com/william-murray1204/stable-diffusion-cpp-python.git@main"
        elif (arg.startswith("--sdcpp-pkg=")):
            SdcppPackage = arg[12:].strip()
        elif (arg == "--lcpp-f16"):
            LcppF16 = True
        elif (arg == "--sdcpp-f16"):
            SdcppF16 = True
        elif (arg == "--rvc-git"):
            RVCPackage = "git+https://github.com/RVC-Project/Retrieval-based-Voice-Conversion.git@develop"
        elif (arg.startswith("--rvc-pkg=")):
            RVCPackage = arg[10:]
        elif (arg.startswith("--fairseq-pkg=")):
            FairseqPackage = arg[14:]
        elif (arg == "--verbose" or arg == "-v"):
            Verbose = True
        elif (arg == "--verbose-full" or arg == "--fverbose" or arg == "-vv"):
            Verbose = True
            VerboseFull = True
        elif (arg == "--skip-torch"):
            TorchPackage = None
        elif (arg == "--skip-lcpp"):
            LcppPackage = None
        elif (arg == "--skip-sdcpp"):
            SdcppPackage = None
        elif (arg == "--skip-rvc"):
            RVCPackage = None
        elif (arg == "--skip-fairseq"):
            FairseqPackage = None
        elif (arg == "--skip-other" or arg == "--skip-other-requirements"):
            SkipOtherRequirements = True
        elif (arg == "--show-command-output"):
            ShowCommandOutput = True
        elif (arg.startswith("--pip-cmd=")):
            PIPCmd = arg[10:]
        else:
            print(f"Unknown argument: {arg}")
            exit(1)

# Set the PIP command
if (PIPCmd is None):
    PIPCmd = __find_pip__()
    print(f"Automatically detected PIP command: '{PIPCmd}'.")

# Check the GPU vendor
if (GPUVendor is None):
    GPUVendor = __detect_gpu__()
    print(f"{GPUVendor.upper()} GPU detected." if (GPUVendor != "unknown") else "No GPU or invalid GPU detected.")

# Check if Vulkan is available
if (VulkanAvailable is None):
    VulkanAvailable = __vulkan_available__()
    print("Vulkan available." if (VulkanAvailable) else "Vulkan not available.")

# Set whls
if (GPUVendor == "unknown"):
    if (VulkanAvailable):
        if (LcppWhl is None):
            LcppWhl = "vulkan"
        
        if (SdcppWhl is None):
            SdcppWhl = "vulkan"
    else:
        if (LcppWhl is None):
            LcppWhl = "cpu"
        
        if (SdcppWhl is None):
            SdcppWhl = "cpu"
    
    if (TorchWhl is None):
        TorchWhl = "cpu"
else:
    if (LcppWhl is None):
        LcppWhl = GPUVendor
    
    if (SdcppWhl is None):
        SdcppWhl = GPUVendor
    
    if (TorchWhl is None):
        TorchWhl = GPUVendor

LcppWhl += f"+{'f16' if (LcppF16) else 'f32'}"
SdcppWhl += f"+{'f16' if (SdcppF16) else 'f32'}"

# Upgrade some packages
if (not SkipOtherRequirements):
    print("Upgrading some packages...")
    InstallPackages("setuptools", None, None, "--upgrade", "", {}, Verbose)

# Install PyTorch
if (TorchPackage is not None):
    print(f"Installing PyTorch for '{TorchWhl}'...")

    if (TorchWhl == "nvidia"):
        InstallPackages(TorchPackage, TorchCUDA, None, "--upgrade", "", {}, Verbose)
        TorchWhl = TorchCUDA
    elif (TorchWhl == "amd"):
        InstallPackages(TorchPackage, TorchROCm, None, "--upgrade", "", {}, Verbose)
        TorchWhl = TorchROCm
    elif (TorchWhl == "intel"):
        InstallPackages(TorchPackage, TorchSycl, None, "--upgrade", "", {}, Verbose)
        InstallPackages("intel-extension-for-pytorch==2.6.10+xpu oneccl_bind_pt==2.6.0+xpu", None, "https://pytorch-extension.intel.com/release-whl/stable/xpu/us/", "--upgrade", "", {}, Verbose)

        TorchWhl = TorchSycl
    elif (TorchWhl == "cpu"):
        InstallPackages(TorchPackage, TorchCPU, None, "--upgrade", "", {}, Verbose)
        TorchWhl = TorchCPU
    else:
        print("^ Error with PyTorch wheel.")
        exit(1)

# Install LCPP
if (LcppPackage is not None):
    print(f"Installing LCPP for '{LcppWhl}'...")

    if (LcppWhl == "nvidia+f32"):
        InstallPackages(
            LcppPackage,
            None,
            None,
            "--upgrade --force-reinstall --no-cache-dir",
            "",
            {"CMAKE_ARGS": "-DGGML_CUDA=on -DGGML_CUDA_F16=0 -DGGML_CUDA_FORCE_CUBLAS=0 -DGGML_CUDA_FORCE_MMQ=0 -DGGML_CUDA_FA_ALL_QUANTS=1"},
            Verbose
        )
    elif (LcppWhl == "nvidia+f16"):
        InstallPackages(
            LcppPackage,
            None,
            None,
            "--upgrade --force-reinstall --no-cache-dir",
            "",
            {"CMAKE_ARGS": "-DGGML_CUDA=on -DGGML_CUDA_F16=1 -DGGML_CUDA_FORCE_CUBLAS=0 -DGGML_CUDA_FORCE_MMQ=0 -DGGML_CUDA_FA_ALL_QUANTS=1"},
            Verbose
        )
    elif (LcppWhl.startswith("amd")):
        if(LcppWhl.endswith("+f16")):
            print("^ WARNING! F16 is not supported in AMD GPUs for now. Using F32.")

        InstallPackages(
            LcppPackage,
            None,
            None,
            "--upgrade --force-reinstall --no-cache-dir",
            "",
            {"CMAKE_ARGS": "-DGGML_HIPBLAS=on"},
            Verbose
        )
    elif (LcppWhl == "intel+f32"):
        InstallPackages(
            LcppPackage,
            None,
            None,
            "--upgrade --force-reinstall --no-cache-dir",
            "",
            {"CMAKE_ARGS": "-DGGML_SYCL=on -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icpx -DGGML_SYCL_F16=OFF"},
            Verbose
        )
    elif (LcppWhl == "intel+f16"):
        InstallPackages(
            LcppPackage,
            None,
            None,
            "--upgrade --force-reinstall --no-cache-dir",
            "",
            {"CMAKE_ARGS": "-DGGML_SYCL=on -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icpx -DGGML_SYCL_F16=ON"},
            Verbose
        )
    elif (LcppWhl.startswith("vulkan")):
        if(LcppWhl.endswith("+f16")):
            print("^ WARNING! F16 is not supported in Vulkan for now. Using F32.")
        
        InstallPackages(
            LcppPackage,
            None,
            None,
            "--upgrade --force-reinstall --no-cache-dir",
            "",
            {"CMAKE_ARGS": "-DGGML_VULKAN=on"},
            Verbose
        )
    elif (LcppWhl.startswith("cpu")):
        if(LcppWhl.endswith("+f16")):
            print("^ WARNING! F16 is not supported in CPU for now. Using F32.")
        
        InstallPackages(
            LcppPackage,
            None,
            None,
            "--upgrade --force-reinstall --no-cache-dir",
            "",
            {"CMAKE_ARGS": "-DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS"},
            Verbose
        )
    else:
        print("^ Error with LCPP wheel.")
        exit(1)

# Install SDCPP
if (SdcppPackage is not None):
    print(f"Installing SDCPP for '{SdcppWhl}'...")

    if (SdcppWhl.startswith("nvidia")):
        if(SdcppWhl.endswith("+f16")):
            print("^ WARNING! F16 is not supported in NVIDIA GPUs for now. Using F32.")
        
        InstallPackages(
            SdcppPackage,
            None,
            None,
            "--upgrade --force-reinstall --no-cache-dir",
            "",
            {"CMAKE_ARGS": "-DSD_CUDA=ON"},
            Verbose
        )
    elif (SdcppWhl.startswith("amd")):
        if(SdcppWhl.endswith("+f16")):
            print("^ WARNING! F16 is not supported in AMD GPUs for now. Using F32.")

        InstallPackages(
            SdcppPackage,
            None,
            None,
            "--upgrade --force-reinstall --no-cache-dir",
            "",
            {"CMAKE_ARGS": "-G Ninja -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ -DSD_HIPBLAS=ON -DCMAKE_BUILD_TYPE=Release -DAMDGPU_TARGETS=gfx1101"},
            Verbose
        )
    elif (SdcppWhl == "intel+f32"):
        InstallPackages(
            SdcppPackage,
            None,
            None,
            "--upgrade --force-reinstall --no-cache-dir",
            "",
            {"CMAKE_ARGS": "-DSD_SYCL=ON -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icpx"},
            Verbose
        )
    elif (SdcppWhl == "intel+f16"):
        InstallPackages(
            SdcppPackage,
            None,
            None,
            "--upgrade --force-reinstall --no-cache-dir",
            "",
            {"CMAKE_ARGS": "-DSD_SYCL=ON -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icpx -DGGML_SYCL_F16=ON"},
            Verbose
        )
    elif (SdcppWhl.startswith("vulkan")):
        if(SdcppWhl.endswith("+f16")):
            print("^ WARNING! F16 is not supported in Vulkan for now. Using F32.")
        
        InstallPackages(
            SdcppPackage,
            None,
            None,
            "--upgrade --force-reinstall --no-cache-dir",
            "",
            {"CMAKE_ARGS": "-DSD_VULKAN=ON"},
            Verbose
        )
    elif (SdcppWhl.startswith("cpu")):
        if(SdcppWhl.endswith("+f16")):
            print("^ WARNING! F16 is not supported in CPU for now. Using F32.")
        
        InstallPackages(
            SdcppPackage,
            None,
            None,
            "--upgrade --force-reinstall --no-cache-dir",
            "",
            {"CMAKE_ARGS": "-DGGML_OPENBLAS=ON"},
            Verbose
        )
    else:
        print("^ Error with SDCPP wheel.")
        exit(1)

# Install RVC
if (RVCPackage is not None):
    print("Uninstalling current RVC...")
    UninstallPackages("rvc")

    print("Installing RVC...")
    InstallPackages(f"{RVCPackage} {TorchPackage}", TorchWhl, "https://pypi.org/simple", "--upgrade --force-reinstall --no-cache-dir", "", {}, Verbose)

# Install fairseq
if (FairseqPackage is not None):
    print("Uninstalling current fairseq...")
    UninstallPackages("fairseq")

    print("Installing fairseq...")
    InstallPackages(f"{FairseqPackage} {TorchPackage}", TorchWhl, "https://pypi.org/simple", "--upgrade --force-reinstall --no-cache-dir", "", {}, Verbose)

# Install other requirements
if (not SkipOtherRequirements):
    print("Installing other requirements...")
    InstallPackages("-r requirements.txt", TorchWhl, "https://pypi.org/simple", "", "", {}, Verbose)