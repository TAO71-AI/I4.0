from setuptools import setup, find_packages

setup(
    name = "I4_0-Client-PY",
    version = "14.0.0",
    description = "Client Python bindings for I4.0.",
    author = "TAO71-AI",
    url = "https://github.com/TAO71-AI/I4.0",
    packages = find_packages(include = ["I4_0_Client", "I4_0_Client.*"]),
    include_package_data = True,
    license = "TAO71 I4.0 License (v1)",
    install_requires = [
        "websockets>=15.0.0,<16.0.0",
        "asyncio",
        "pyaudio",
        "cryptography>=44.0.0,<45.0.0",
        "numpy",
        "pydub",
        "ffmpeg-python",
        "opencv-python"
    ],
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent"
    ],
    python_requires = ">=3.8",
    project_urls = {
        "Source": "https://github.com/TAO71-AI/I4.0/tree/development/LibI4/ClientPythonPackage",
        "License": "https://github.com/TAO71-AI/I4.0/blob/main/LICENSE.md"
    }
)