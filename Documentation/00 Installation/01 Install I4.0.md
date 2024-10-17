# Install I4.0
> [!NOTE]
> If you're having troubles using the `python` command, try `python3`.
> If you're having troubles using the `pip` command, try `pip3`, `python -m pip` or `python3 -m pip`.

# Clone I4.0
```bash
git clone https://github.com/TAO71-AI/I4.0.git
cd I4.0/LibI4/Python_AI/
```

# Create VENV
A Python VENV is not required for I4.0, but it's recommended to be used.
Otherwise, you might experience bugs, errors or crashes.
```bash
python -m venv .env
source .env/bin/activate
```

# Install I4.0's python requirements
## Install using the script
```bash
sh install_requirements_auto.sh
```

This should automatically detect your GPU and install the requirements.
Make sure you have CUDA, ROCm or SYCL installed in your system before running this.

If you have a GPU that is not compatible with CUDA, ROCm nor SYCL, but it's compatible with Vulkan, the script will ask you if you want to install the requirements for Vulkan compatibility.

> [!WARNING]
> Intel GPUs support is still experimental, you may experience errors or bugs.
> For LLaMA-CPP-Python we recommend to install it using Vulkan compatibility.

### Installation options
#### PyTorch for CPU only
You can install PyTorch for CPU support only, even if you have a GPU.
To do this, run the following command:
```bash
FORCE_CPU_PT=1 sh install_requirements_auto.sh
```

#### LLaMA-CPP-Python for CPU only
You can install LLaMA-CPP-Python for CPU support only, even if you have a GPU.
To do this, run the following command:
```bash
FORCE_CPU_LLAMA=1 sh install_requirements_auto.sh
```

#### LLaMA-CPP-Python for Vulkan
You can install LLaMA-CPP-Python for CPU support only, even if you have a GPU.
To do this, run the following command:
```bash
FORCE_VULKAN_LLAMA=1 sh install_requirements_auto.sh
```

#### Extra PIP arguments
You can pass extra arguments to pip using this.
Example:
```bash
pip install package $ARGUMENTS
```

To do this, run the following command:
```bash
EXTRA_PIP_ARGS="[ARGS HERE]" sh install_requirements_auto.sh
```

#### Change PIP command
If the command `pip` is not recognized by your system, you can change the command to whatever you want.
To do this, run the following command:
```bash
PIP_CMD="[COMMAND]" sh install_requirements_auto.sh
```

## Install manually
### Install PyTorch
```bash
pip install torch torchvision torchaudio  # For NVIDIA GPUs
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.0  # For AMD GPUs
pip install torch==2.3.1+cxx11.abi torchvision==0.18.1+cxx11.abi torchaudio==2.3.1+cxx11.abi intel-extension-for-pytorch==2.3.110+xpu oneccl_bind_pt==2.3.100+xpu --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/xpu/us/  # For Intel GPUs
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu  # Without GPU support
```

### Install LLaMA-CPP-Python
```bash
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python  # For NVIDIA GPUs
CMAKE_ARGS="-DGGML_HIPBLAS=on" pip install llama-cpp-python  # For AMD GPUs

# For Intel GPUs
source /opt/intel/oneapi/setvars.sh   
CMAKE_ARGS="-DGGML_SYCL=on -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icpx" pip install llama-cpp-python

CMAKE_ARGS="-DGGML_VULKAN=on" pip install llama-cpp-python  # For Vulkan support (all GPUs, recommended)
CMAKE_ARGS="-DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS" pip install llama-cpp-python  # Without GPU support
```

### Install requirements
```bash
pip install -r requirements.txt
pip install -r requirements_optional.txt  # For extra requirements
```