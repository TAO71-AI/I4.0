# TAO71 I4.0
## What is this?
TAO71 I4.0 is an AI created by TAO71 in C# and Python. It uses GPT4All, Hugging Face Transformers, Hugging Face Diffusers, etc.

> [!IMPORTANT]
> In order to use I4.0 as expected, you must create a Python VENV.
> It's recommended to use Python 3.11.9 (or Python 3.11), but Python 3.12 is also compatible (unless you have an Intel GPU).
> I4.0 is compatible with ROCm and SYCL, but you may experience problems using it.

## Requirements
CPU: Any x86_64 CPU with AVX or AVX2 and 2+ cores.

GPU (optional): Any GPU with NVIDIA CUDA or ROCm for Hugging Face Transformers, Hugging Face Diffusers or any GPU compatible with Vulkan for GPT4All or LLaMA-CPP-Python.

RAM: At least 8GB.

# Development Environment
This is the official tested hardware and software with I4.0:

## Main development computer
### OS
Arch Linux (`linux` kernel)

### RAM
16GB DDR4

### CPU
AMD Ryzen 5 3600

### GPU
NVIDIA RTX 3050 8GB

### Python Version
Python 3.11.9

### Notes
This is the (main) computer where I4.0 is programmed and tested using CUDA.

### Python Version
Python 3.12.4

## TAO71 main server
### OS
Arch Linux (`linux` kernel)

### RAM
32GB DDR4

### CPU
Intel Core i5 10600KF

### GPU
Intel Arc A770 16GB

### Python Version
Python 3.11.9

### Notes
This is the primary TAO71 server (`tao71.sytes.net`), where you can use I4.0 without having the minimum requirements.
Sometimes I4.0 goes down on this server, usually this happens because we are testing a new I4.0 version.

This is the (main) computer where I4.0 is tested using SYCL.

# License
TAO71 License 111

# Small FAQ
## If I don't want a plugin, can I remove it?
Yes, you can remove every plugin of the AI and you will not need to fix bugs in the AI code.

## What is a plugin?
Everything on the LibI4/Plugins/ directory is a plugin.

# Contributors/Helpers:
## Alcoft
[![AlcoftTAO](https://github.com/TAO71-AI/I4.0/blob/main/Assets/Contributors_Helpers/AlcoftTAO.jpeg?raw=true)](https://github.com/alcoftTAO)
Main programmer of I4.0.

## Coderarduinopython
[![Coderarduinopython](https://github.com/TAO71-AI/I4.0/blob/main/Assets/Contributors_Helpers/Coderarduinopython.png?raw=true)](https://github.com/coderarduinopython)
Gave Alcoft some scripts that made the first version of I4.0 possible.

## JLMR08
[![JLMR08](https://github.com/TAO71-AI/I4.0/blob/main/Assets/Contributors_Helpers/JLMR08.png?raw=true)](https://github.com/Jlmr08)
Worked in an older dataset for I4.0.
This dataset is still under creation.

## Dinolt
[![DINOLT](https://github.com/TAO71-AI/I4.0/blob/main/Assets/Contributors_Helpers/DINOLT.jpg?raw=true)](https://www.youtube.com/@GoldenClassicsStudios)
I4.0's designer, created all the images of I4.0.