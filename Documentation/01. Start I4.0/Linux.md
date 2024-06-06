-----
DOCUMENTATION VERSION: v6.0.0
-----

> [!WARNING]
> If you are receiving errors when using the command `python`, try using `python3`.
> Python, PIP and I4.0's requirements are required to be installed on your machine.
> You must be in a VENV, otherwise errors are expected.
> You must be inside the directory `I4.0/LibI4/Python_AI/`.

# Creating I4.0 configuration file
The configuration file should be created automatically when running the server for the first time.
You can also create it manually by running:
```sh
touch config.tcfg
```
It's not recommended to create the configuration file manually.

# First time running the server
To start the I4.0 server, run:
```sh
python ai_server_all.py
```

If the configuration file it's not created before running this command, it will be created automatically and the program will exit.
To start the server just run the same command again.