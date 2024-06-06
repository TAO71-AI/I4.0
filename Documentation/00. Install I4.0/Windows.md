-----
DOCUMENTATION VERSION: v6.0.0
-----

> [!WARNING]
> This guide is not verified.
> If you're receiving errors using the `python` command, use `py` or `python3`.
> Recommended version for I4.0 is the latest available python version.

# Clone repository
> [!NOTE]
> If you don't have Git installed, install it [here](https://git-scm.com/).
> Or you can also use `winget` (recommended):
> ```sh
> winget install git
> ```

To clone the repository, run this command:
```sh
git clone https://github.com/TAO71-AI/I4.0.git
```

# Create Python VENV
> [!NOTE]
> You need to enter first the `I4.0/LibI4/Python_AI/` directory.
> If you don't have Python installed, install it [here](https://www.python.org/downloads/) (recommended version: 3.11.8).

To create a Python VENV, run this command:
```sh
python -m venv .env
```

## Start the environment
To start the environment, run this command:
```sh
.env\Scripts\activate
```

# Install requirements
Before installing requirements, you need to install PIP. To do so, run:
```sh
python -m ensurepip
```

To install the requirements, run this command:
```sh
# Install requirements
python -m pip install --upgrade -r requirements.txt

# Install optional requirements
python -m pip install --upgrade -r requirements_optional.txt
```

If this gives you an error, try:
```sh
# Install requirements
python -m pip install --upgrade -r requirements.txt

# Install optional requirements
python -m pip install --upgrade -r requirements_optional.txt
```

# I4.0 installed!
Now you have I4.0 installed on your machine.