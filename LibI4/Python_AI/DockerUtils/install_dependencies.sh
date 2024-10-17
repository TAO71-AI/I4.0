#!/bin/bash

GPU_INFO=$(lspci -nn | grep -E "VGA|3D|Display")
PIP_EINDEX="--extra-index-url https://download.pytorch.org/whl/cpu"
LCPP_ARGS="-DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS"

if echo "$GPU_INFO" | grep -i nvidia; then
    # Get index for NVIDIA GPUs
    PIP_EINDEX="--extra-index-url https://download.pytorch.org/whl/cu124"
    LCPP_ARGS="-DGGML_CUDA=on"
elif echo "$GPU_INFO" | grep -i amd; then
    # Get index for AMD GPUs
    # WARNING: There's currently a bug that doesn't compile llama-cpp-python with ROCm support. It will only be usable with the CPU
    # ^--- This bug only affects Docker tho
    # Also, PyTorch seems to work fine with ROCm on Docker :)
    PIP_EINDEX="--extra-index-url https://download.pytorch.org/whl/rocm6.1"
# No Intel GPUs support yet
fi

CMAKE_ARGS="$LCPP_ARGS" FORCE_CMAKE=1 pip install --upgrade --root-user-action ignore -r requirements.txt $PIP_EINDEX
pip install --root-user-action ignore -r requirements_optional.txt $PIP_EINDEX