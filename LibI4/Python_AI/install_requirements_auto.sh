#!/bin/bash
# Check GPU
echo "Checking GPU..."

GPU_INFO=$(lspci -nn | grep -E "VGA|3D|Display")
VULKAN_INFO=$(vulkaninfo)

if echo "$GPU_INFO" | grep -i nvidia; then
    GPU_VENDOR="nvidia"
elif echo "$GPU_INFO" | grep -i amd; then
    GPU_VENDOR="amd"
elif echo "$GPU_INFO" | grep -i intel; then
    GPU_VENDOR="intel"
    SYCL_INIT="/opt/intel/oneapi/setvars.sh"
else
    GPU_VENDOR="unknown"
fi

echo "   GPU Vendor: $GPU_VENDOR"

# Set GPU variables
if [ "$GPU_VENDOR" = "nvidia" ]; then
    TORCH_PKG="torch torchaudio torchvision"
    TORCH_IDX="https://download.pytorch.org/whl/cu126"
    LCPP_CMK_ARGS="-DGGML_CUDA=on"
    SDCPP_CMK_ARGS="-DSD_CUDA=ON"
    RVC_URL="https://github.com/RVC-Project/Retrieval-based-Voice-Conversion"
elif [ "$GPU_VENDOR" = "amd" ]; then
    TORCH_PKG="torch torchaudio torchvision"
    TORCH_IDX="https://download.pytorch.org/whl/rocm6.2.4"
    LCPP_CMK_ARGS="-DGGML_HIPBLAS=on"
    SDCPP_CMK_ARGS="-G Ninja -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ -DSD_HIPBLAS=ON -DCMAKE_BUILD_TYPE=Release -DAMDGPU_TARGETS=gfx1101"
    RVC_URL="https://github.com/RVC-Project/Retrieval-based-Voice-Conversion"
elif [ "$GPU_VENDOR" = "intel" ]; then
    source "$SYCL_INIT"

    TORCH_PKG="torch==2.3.1+cxx11.abi torchvision==0.18.1+cxx11.abi torchaudio==2.3.1+cxx11.abi intel-extension-for-pytorch==2.3.110+xpu oneccl_bind_pt==2.3.100+xpu"
    TORCH_IDX="https://pytorch-extension.intel.com/release-whl/stable/xpu/us/"
    TORCH_E_IDX="https://pypi.org/simple"
    LCPP_CMK_ARGS="-DGGML_SYCL=on -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icpx -DGGML_SYCL_F16=on"
    SDCPP_CMK_ARGS="-DSD_SYCL=ON -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icpx -DGGML_SYCL_F16=ON"
    RVC_URL="https://github.com/TAO71-AI/Retrieval-based-Voice-Conversion"
else
    TORCH_PKG="torch torchaudio torchvision"
    TORCH_IDX="https://download.pytorch.org/whl/cpu"
    RVC_URL="https://github.com/RVC-Project/Retrieval-based-Voice-Conversion"

    if [[ -z "$VULKAN_INFO" ]]; then
        LCPP_CMK_ARGS="-DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS"
        SDCPP_CMK_ARGS="-DGGML_OPENBLAS=ON"
    else
        LCPP_CMK_ARGS="-DGGML_VULKAN=on"
        SDCPP_CMK_ARGS="-DSD_VULKAN=ON"
    fi
fi

# Set variables
PIP_CMD="pip"

# Update some requirements
"$PIP_CMD" install --upgrade pip setuptools

# Install requirements
"$PIP_CMD" install --upgrade -r requirements.txt

if [ $? -ne 0 ];
    echo "Error installing requirements. Closing program."
    exit 1
fi

# Install RVC
"$PIP_CMD" uninstall -y rvc
git clone "$RVC_URL.git" ./RVC
cd ./RVC/
"$PIP_CMD" install --upgrade --verbose .

if [ $? -ne 0 ];
    echo "Error installing RVC. Closing program."
    exit 1
fi

cd ../
rm -rf ./RVC/

# Install fairseq
"$PIP_CMD" uninstall -y fairseq
git clone "https://github.com/Tps-F/fairseq.git" ./fairseq
cd ./fairseq/
"$PIP_CMD" install --upgrade --verbose .

if [ $? -ne 0 ];
    echo "Error installing fairseq. Closing program."
    exit 1
fi

cd ../
rm -rf ./fairseq/

# Install torch
"$PIP_CMD" uninstall -y torch torchvision torchaudio

if [ -z "$TORCH_E_IDX" ]; then
    "$PIP_CMD" install --upgrade "$TORCH_PKG" --index-url "$TORCH_IDX"
else
    "$PIP_CMD" install --upgrade "$TORCH_PKG" --index-url "$TORCH_IDX" --extra-index-url "$TORCH_E_IDX"
fi

if [ $? -ne 0 ];
    echo "Error installing torch. Closing program."
    exit 1
fi

# Install LlamaCPP-Python
FORCE_CMAKE=1 CMAKE_ARGS="$LCPP_CMK_ARGS" "$PIP_CMD" install --upgrade --verbose llama-cpp-python

if [ $? -ne 0 ];
    echo "Error installing LlamaCPP-Python. Closing program."
    exit 1
fi

# Install StableDiffusionCPP-Python
FORCE_CMAKE=1 CMAKE_ARGS="$SDCPP_CMK_ARGS" "$PIP_CMD" install --upgrade --verbose stable-diffusion-cpp-python

if [ $? -ne 0 ];
    echo "Error installing StableDiffusionCPP-Python. Closing program."
    exit 1
fi

# Done!
echo "Everything is now installed!"