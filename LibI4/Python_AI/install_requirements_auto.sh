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

PYTORCH_WHL="--index-url https://download.pytorch.org/whl/cpu"      # PyTorch CPU version.
LCPP_WHL="-DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS"               # LlamaCPP (Python) CPU version.

if [ -z "${FORCE_CPU_PT}" ]; then
    FORCE_CPU_PT=0
fi

if [ -z "${FORCE_CPU_LLAMA}" ]; then
    FORCE_CPU_LLAMA=0
fi

if [ -z "${EXTRA_PIP_ARGS}" ]; then
    EXTRA_PIP_ARGS=""
fi

if [ -z "${PIP_CMD}" ]; then
    PIP_CMD="pip"
fi

if [ "$ALLOW_GPU" = false ]; then
    GPU_INFO=""
fi

if echo "$GPU_INFO" | grep -i nvidia; then
    echo -e "\e[1m > NVIDIA GPU detected! \e[0m"

    if [ "${FORCE_CPU_PT}" -ne 1 ]; then
        echo "   Building PyTorch with CUDA support..."
        PYTORCH_WHL="--index-url https://download.pytorch.org/whl/cu124"
    else
        echo "   Building PyTorch with CPU support only..."
    fi

    if [ "${FORCE_CPU_LLAMA}" -ne 1 ]; then
        echo "   Building LLaMA-CPP-Python with CUDA support..."
        LCPP_WHL="-DGGML_CUDA=on"
    else
        echo "   Building LLaMA-CPP-Python with CPU support only..."
    fi
elif echo "$GPU_INFO" | grep -i amd; then
    echo -e "\e[1m > AMD GPU detected! \e[0m"

    if [ "${FORCE_CPU_PT}" -ne 1 ]; then
        echo "   Building PyTorch with ROCm support..."
        PYTORCH_WHL="--index-url https://download.pytorch.org/whl/rocm6.1"
    else
        echo "   Building PyTorch with CPU support only..."
    fi

    if [ "${FORCE_CPU_LLAMA}" -ne 1 ]; then
        echo "   Building LLaMA-CPP-Python with ROCm support..."
        LCPP_WHL="-DGGML_HIPBLAS=on"
    else
        echo "   Building LLaMA-CPP-Python with CPU support only..."
    fi
#elif echo "$GPU_INFO" | grep -i intel; then
#    echo -e "\e[1m > INTEL GPU detected! Installing dependencies with ???. \e[0m"
#
#    if [ $FORCE_CPU_PT -ne 0 ]; then
#        PYTORCH_WHL="--index-url ???????????????"
#    fi
#
#    if [ $FORCE_CPU_LLAMA -ne 0 ]; then
#        LCPP_WHL="???????????????????"
#    fi
# ^--- Under creation!!!!!!!
else
    echo -e "\e[1m > No valid GPU detected. PyTorch (CPU version) will be installed. \e[0m"

    if echo "$VULKAN_INFO" | grep -i 'vulkan'; then
        echo -e "\e[1m > It seems like your GPU is compatible with Vulkan. Install LlamaCPP-Python with Vulkan? \e[0m"
        echo "[Y/n] "
        read INSTALL_WITH_VULKAN

        if echo "$INSTALL_WITH_VULKAN" | grep -i y; then
            LCPP_WHL="-DGGML_VULKAN=on"
        fi
    else
        echo -e "\e[1m > It seems like your GPU is NOT compatible with Vulkan. CPU version of LlamaCPP-Python will be installed. \e[0m"
    fi
fi

# 2. Update PIP
echo -e "\e[1m > Updating PIP... \e[0m"
"$PIP_CMD" install --upgrade $EXTRA_PIP_ARGS pip

# 3. Install PyTorch.
echo -e "\e[1m > Installing PyTorch... \e[0m"
"$PIP_CMD" install --upgrade $EXTRA_PIP_ARGS torch torchvision torchaudio $PYTORCH_WHL

if [ $? != 0 ]; then
    echo "PyTorch installation failed."
    exit 1
fi

# 4. Install LlamaCPP-Python
echo -e "\e[1m > Installing LlamaCPP-Python... \e[0m"
CMAKE_ARGS="$LCPP_WHL" FORCE_CMAKE=1 "$PIP_CMD" install --verbose --upgrade $EXTRA_PIP_ARGS llama-cpp-python

if [ $? != 0 ]; then
    echo "LlamaCPP-Python installation failed."
    exit 1
fi

# 5. Install I4.0 requirements.
echo -e "\e[1m > Installing I4.0's requirements... \e[0m"
"$PIP_CMD" install -r requirements.txt

if [ $? != 0 ]; then
    echo -e "\e[1m > Requirements installation failed. \e[0m"
    exit 1
fi

# 6. Install extra I4.0 requirements.
if [ "$ALLOW_EXTRA_REQUIREMENTS" = true ]; then
    echo -e "\e[1m > Installing I4.0's extra requirements... \e[0m"
    "$PIP_CMD" install -r requirements_optional.txt

    if [ $? != 0 ]; then
        echo -e "\e[1m > Extra requirements installation failed. Ignoring. \e[0m"
    fi
fi

# 7. Completed!
echo -e "\e[1m > I4.0's requirements are now installed! \e[0m"