#!/bin/bash
# Automatically install I4.0's Python requirements.
ALLOW_GPU=true
ALLOW_EXTRA_REQUIREMENTS=true
MAX_TASKS=4

if [ "$ALLOW_EXTRA_REQUIREMENTS" = true ]; then
    echo "   Installing also extra requirements..."
    MAX_TASKS=5
fi

echo "Automatically installing I4.0's Python requirements... [0/$MAX_TASKS]"

# 1. Check GPU and select PyTorch wheel.
echo "Checking GPU... [1/$MAX_TASKS]"
GPU_INFO=$(lspci -nn | grep -E "VGA|3D|Display")
PYTORCH_WHL="--index-url https://download.python.org/whl/cpu"

if [ "$ALLOW_GPU" = false ]; then
    GPU_INFO=""
fi

if echo "$GPU_INFO" | grep -i nvidia; then
    echo "   NVIDIA GPU detected. Selected CUDA version of PyTorch [2/$MAX_TASKS]"
    PYTORCH_WHL=""
elif echo "$GPU_INFO" | grep -i amd; then
    echo "   AMD GPU detected. Selected ROCM version of PyTorch [2/$MAX_TASKS]"
    PYTORCH_WHL="--index-url https://download.pytorch.org/whl/rocm6.0"
elif echo "$GPU_INFO" | grep -i intel; then
    echo "   Intel GPU detected. Selected ??? version of PyTorch [2/$MAX_TASKS]"
    PYTORCH_WHL="--index-url https://pytorch-extension.intel.com/release-whl/stable/xpu/us/"
else
    echo "   No valid GPU detected. Selected CPU version of PyTorch [2/$MAX_TASKS]"
fi

# 2. Install PyTorch.
echo "Installing PyTorch... [3/$MAX_TASKS]"
pip install --upgrade torch torchvision torchaudio $PYTORCH_WHL

if [ $? != 0 ]; then
    echo "PyTorch installation failed."
    exit 1
fi

# 3. Install I4.0 requirements.
echo "Installing I4.0 requirements... [4/$MAX_TASKS]"
pip install -r requirements.txt

if [ $? != 0 ]; then
    echo "Requirements installation failed."
    exit 1
fi

# 4. Install extra I4.0 requirements.
if [ "$ALLOW_EXTRA_REQUIREMENTS" = true ]; then
    echo "Installing I4.0 extra requirements... [5/$MAX_TASKS]"
    pip install -r requirements_optional.txt

    if [ $? != 0 ]; then
        echo "Extra requirements installation failed."
    fi
fi

# 5. Completed!
echo "I4.0's dependencies installed successfully!"