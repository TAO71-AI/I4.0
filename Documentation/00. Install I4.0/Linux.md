-----
DOCUMENTATION VERSION: v6.5.0
-----

> [!WARNING]
> If you are receiving errors when using the command `python`, try using `python3`.
> Recommended version for I4.0 is the latest available python version.

# Clone repository
> [!NOTE]
> If you don't have Git installed, install it [here](https://git-scm.com/).

To clone the repository, run this command:
```bash
git clone https://github.com/TAO71-AI/I4.0.git
```

# Create Python VENV
> [!NOTE]
> You need to enter first the `I4.0/LibI4/Python_AI/` directory.
> If you don't have Python installed, install it [here](https://www.python.org/downloads/) (recommended version: 3.11.8).
> You need to also install PIP.

To create a Python VENV, run this command:
```bash
python -m venv .env
```

## Start the environment
To start the environment, run this command:
```bash
source .env/bin/activate
```

# Install requirements
## Main method or "manual" method
To install the requirements, run this command:
```bash
# Install requirements
pip install --upgrade -r requirements.txt

# Install optional requirements
pip install --upgrade -r requirements_optional.txt
```

## Alternative method or "automatic" method
To install the requirements automatically, run this command:
```bash
# Make the file executable
chmod +x install_requirements_auto.sh

# Start the file
./install_requirements_auto.sh
```

# I4.0 installed!
Now you have I4.0 installed on your machine.