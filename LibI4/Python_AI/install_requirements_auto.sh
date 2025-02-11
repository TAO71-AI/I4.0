#!/bin/bash
# Automatically install I4.0's Python requirements.
ALLOW_GPU=true
ALLOW_EXTRA_REQUIREMENTS=true
MAX_TASKS=4

if [ "$ALLOW_EXTRA_REQUIREMENTS" = true ]; then
    echo "   Installing also extra requirements..."
    MAX_TASKS=5
fi

echo -e "\e[1m > Automatically instaling I4.0's requirements... \e[0m"
echo -e "\e[1m > WARNING! Make sure to have CMAKE installed! \e[0m"

# 1. Check GPU and select PyTorch wheel.
echo -e "\e[1m > Checking GPU... \e[0m"

GPU_INFO=$(lspci -nn | grep -E "VGA|3D|Display")
VULKAN_INFO=$(vulkaninfo)
INTEL_GPU_VARS="/opt/intel/oneapi/setvars.sh"       # Only used if you have a Intel GPU.

PYTORCH_PKG="torch torchaudio torchvision"
PYTORCH_WHL="https://download.pytorch.org/whl/cpu"                  # PyTorch CPU version.
LCPP_WHL="-DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS"               # LlamaCPP (Python) CPU version.
SDCPP_WHL="-DGGML_OPENBLAS=ON"                                      # StableDiffusionCPP (Python) CPU version.

if [ -z "${FORCE_CPU_PT}" ]; then
    FORCE_CPU_PT=0
fi

if [ -z "${FORCE_CPU_LLAMA}" ]; then
    FORCE_CPU_LLAMA=0
fi

if [ -z "${FORCE_CPU_SD}" ]; then
    FORCE_CPU_SD=0
fi

if [ -z "${FORCE_VULKAN_LLAMA}" ]; then
    FORCE_VULKAN_LLAMA=0
fi

if [ -z "${FORCE_VULKAN_SD}" ]; then
    FORCE_VULKAN_SD=0
fi

if [ -z "${EXTRA_PIP_ARGS}" ]; then
    EXTRA_PIP_ARGS=""
fi

if [ -z "${PIP_CMD}" ]; then
    PIP_CMD="pip"
fi

if [ "$ALLOW_GPU" = false ]; then
    GPU_INFO=""
    VULKAN_INFO=""
fi

if echo "$GPU_INFO" | grep -i nvidia; then
    echo -e "\e[1m > NVIDIA GPU detected! \e[0m"

    if [ $FORCE_CPU_PT -ne 1 ]; then
        echo "   Building PyTorch with CUDA support..."
        PYTORCH_WHL="https://download.pytorch.org/whl/cu124"
    else
        echo "   Building PyTorch with CPU support only..."
    fi

    if [ $FORCE_VULKAN_LLAMA -ne 1 ]; then
        echo "   Building LLaMA-CPP-Python with Vulkan support..."
        LCPP_WHL="-DGGML_VULKAN=on"
    elif [ $FORCE_CPU_LLAMA -ne 1 ]; then
        echo "   Building LLaMA-CPP-Python with CUDA support..."
        LCPP_WHL="-DGGML_CUDA=on"
    else
        echo "   Building LLaMA-CPP-Python with CPU support only..."
    fi

    if [ $FORCE_VULKAN_SD -ne 1 ]; then
        echo "   Building StableDiffusion-CPP-Python with Vulkan support..."
        SDCPP_WHL="-DSD_VULKAN=ON"
    elif [ $FORCE_CPU_SD -ne 1 ]; then
        echo "   Building StableDiffusion-CPP-Python with CUDA support..."
        SDCPP_WHL="-DSD_CUBLAS=ON"
    else
        echo "   Building StableDiffusion-CPP-Python with CPU support only..."
    fi
elif echo "$GPU_INFO" | grep -i amd; then
    echo -e "\e[1m > AMD GPU detected! \e[0m"

    if [ $FORCE_CPU_PT -ne 1 ]; then
        echo "   Building PyTorch with ROCm support..."
        PYTORCH_WHL="https://download.pytorch.org/whl/rocm6.2"
    else
        echo "   Building PyTorch with CPU support only..."
    fi

    if [ $FORCE_VULKAN_LLAMA -ne 1 ]; then
        echo "   Building LLaMA-CPP-Python with Vulkan support..."
        LCPP_WHL="-DGGML_VULKAN=on"
    elif [ $FORCE_CPU_LLAMA -ne 1 ]; then
        echo "   Building LLaMA-CPP-Python with ROCm support..."
        LCPP_WHL="-DGGML_HIPBLAS=on"
    else
        echo "   Building LLaMA-CPP-Python with CPU support only..."
    fi

    if [ $FORCE_VULKAN_SD -ne 1 ]; then
        echo "   Building StableDiffusion-CPP-Python with Vulkan support..."
        SDCPP_WHL="-DSD_VULKAN=ON"
    elif [ $FORCE_CPU_SD -ne 1 ]; then
        echo "   Building StableDiffusion-CPP-Python with ROCm support..."
        SDCPP_WHL="-G Ninja -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ -DSD_HIPBLAS=ON -DCMAKE_BUILD_TYPE=Release -DAMDGPU_TARGETS=gfx1101"
    else
        echo "   Building StableDiffusion-CPP-Python with CPU support only..."
    fi
elif echo "$GPU_INFO" | grep -i intel; then                                 # EXPERIMENTAL SUPPORT.
    echo -e "\e[1m > Intel GPU detected! \e[0m"
    source "$INTEL_GPU_VARS"

    if [ $FORCE_CPU_PT -ne 1 ]; then
        echo "   Building PyTorch with XPU support..."
        PYTORCH_WHL="https://pytorch-extension.intel.com/release-whl/stable/xpu/us/"
        PYTORCH_PKG="torch==2.3.1+cxx11.abi torchvision==0.18.1+cxx11.abi torchaudio==2.3.1+cxx11.abi intel-extension-for-pytorch==2.3.110+xpu oneccl_bind_pt==2.3.100+xpu"
    else
        echo "   Building PyTorch with CPU support only..."
    fi

    if [ $FORCE_VULKAN_LLAMA -ne 1 ]; then
        echo "   Building LLaMA-CPP-Python with Vulkan support..."
        LCPP_WHL="-DGGML_VULKAN=on"
    elif [ $FORCE_CPU_LLAMA -ne 1 ]; then
        echo "   Building LLaMA-CPP-Python with SYCL support..."
        LCPP_WHL="-DGGML_SYCL=on -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icpx -DGGML_SYCL_F16=on"
    else
        echo "   Building LLaMA-CPP-Python with CPU support only..."
    fi

    if [ $FORCE_VULKAN_SD -ne 1 ]; then
        echo "   Building StableDiffusion-CPP-Python with Vulkan support..."
        SDCPP_WHL="-DSD_VULKAN=ON"
    elif [ $FORCE_CPU_SD -ne 1 ]; then
        echo "   Building StableDiffusion-CPP-Python with SYCL support..."
        SDCPP_WHL="-DSD_SYCL=ON -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icpx"
    else
        echo "   Building StableDiffusion-CPP-Python with CPU support only..."
    fi
else
    echo -e "\e[1m > No valid GPU detected. PyTorch (CPU version) will be installed. \e[0m"

    if echo "$VULKAN_INFO" | grep -i 'vulkan'; then
        echo -e "\e[1m > It seems like your GPU is compatible with Vulkan. Install LlamaCPP-Python and StableDiffusionCPP-Python with Vulkan? \e[0m"
        echo "[Y/n] "
        read INSTALL_WITH_VULKAN

        if echo "$INSTALL_WITH_VULKAN" | grep -i y; then
            LCPP_WHL="-DGGML_VULKAN=on"
            SDCPP_WHL="-DSD_VULKAN=ON"
        fi
    else
        echo -e "\e[1m > It seems like your GPU is NOT compatible with Vulkan. CPU version of LlamaCPP-Python and StableDiffusionCPP-Python will be installed. \e[0m"
    fi
fi

# 2. Update PIP and install pre-requirements.
echo -e "\e[1m > Updating PIP... \e[0m"
"$PIP_CMD" install --upgrade $EXTRA_PIP_ARGS "pip<24.1" setuptools

# 3. Install PyTorch.
echo -e "\e[1m > Installing PyTorch... \e[0m"
"$PIP_CMD" install --upgrade $EXTRA_PIP_ARGS $PYTORCH_PKG --index-url "$PYTORCH_WHL"

rm -rf RVC/
git clone --branch intel_support --single-branch https://github.com/TAO71-AI/Retrieval-based-Voice-Conversion.git ./RVC     # TAO71-AI's fork; NVIDIA, AMD and Intel GPUs support.
#git clone --branch develop --single-branch https://github.com/RVC-Project/Retrieval-based-Voice-Conversion.git ./RVC       # Original repository; NVIDIA and AMD GPUs support only.
cd RVC
"$PIP_CMD" install --upgrade $EXTRA_PIP_ARGS --editable ./ --verbose --index-url "$PYTORCH_WHL" --extra-index-url "https://pypi.org/simple"
cd ..
rm -rf RVC/

rm -rf fairseq/
"$PIP_CMD" uninstall -y fairseq
git clone --branch main --single-branch https://github.com/Tps-F/fairseq.git ./fairseq
cd fairseq
"$PIP_CMD" install --upgrade $EXTRA_PIP_ARGS --editable ./ --verbose --index-url "$PYTORCH_WHL" --extra-index-url "https://pypi.org/simple"
cd ..
rm -rf fairseq/

if [ $? != 0 ]; then
    echo "PyTorch installation failed."
    exit 1
fi

# 4. Install LlamaCPP-Python.
echo -e "\e[1m > Installing LlamaCPP-Python... \e[0m"
CMAKE_ARGS="$LCPP_WHL" FORCE_CMAKE=1 "$PIP_CMD" install --verbose --upgrade $EXTRA_PIP_ARGS llama-cpp-python

if [ $? != 0 ]; then
    echo "LlamaCPP-Python installation failed."
    exit 1
fi

# 5. Install StableDiffusionCPP-Python.
echo -e "\e[1m > Installing StableDiffusionCPP-Python... \e[0m"
CMAKE_ARGS="$SDCPP_WHL" FORCE_CMAKE=1 "$PIP_CMD" install --verbose --upgrade $EXTRA_PIP_ARGS stable-diffusion-cpp-python

if [ $? != 0 ]; then
    echo "StableDiffusionCPP-Python installation failed."
    exit 1
fi

# 6. Install I4.0 requirements.
echo -e "\e[1m > Installing I4.0's requirements... \e[0m"
"$PIP_CMD" install -r requirements.txt --upgrade --verbose --index-url "$PYTORCH_WHL" --extra-index-url "https://pypi.org/simple"

if [ $? != 0 ]; then
    echo -e "\e[1m > Requirements installation failed. \e[0m"
    exit 1
fi

# 7. Install extra I4.0 requirements.
if [ "$ALLOW_EXTRA_REQUIREMENTS" = true ]; then
    echo -e "\e[1m > Installing I4.0's extra requirements... \e[0m"
    "$PIP_CMD" install -r requirements_optional.txt --upgrade --verbose --index-url "$PYTORCH_WHL" --extra-index-url "https://pypi.org/simple"

    if [ $? != 0 ]; then
        echo -e "\e[1m > Extra requirements installation failed. Ignoring. \e[0m"
    fi
fi

# 8. Completed!
echo -e "\e[1m > I4.0's requirements are now installed! \e[0m"