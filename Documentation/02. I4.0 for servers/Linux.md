-----
DOCUMENTATION VERSION: v6.5.0
-----

> [!WARNING]
> This was only tested with `Arch Linux` based servers, some commands may be different depending on your servers distribution.

# Start I4.0 automatically on startup
To automatically start I4.0 on startup, you need to create a systemd service.

## Create systemd service
Create this file: `/etc/systemd/system/I4.0.service`.
Then, write this on the file:
```ini
[Unit]
Description=I4.0 Server
After=network-online.target ufw.service # Replace ufw.service with your firewall service.

[Service]
Type=simple
WorkingDirectory=# I4.0/LibI4/Python_AI/ directory here.
ExecStart=.env/bin/python ai_server.py
KillSignal=SIGINT

[Install]
WantedBy=multi-user.target
```

## Starting I4.0 systemd service
To enable the service (to automatically start I4.0) execute:
```sh
sudo systemctl enable I4.0.service
```

Now, to start the service, execute:
```sh
sudo systemctl start I4.0.service
```

# Watch status of I4.0
To watch the status of the I4.0 service, execute:
```sh
sudo systemctl status I4.0.service
```

And to see the I4.0 output execute:
```sh
sudo journalctl -u I4.0.service -f
```

# Remove the I4.0 systemd service
## Stop the service
To stop the service, execute:
```sh
sudo systemctl stop I4.0.service
```

## Disable the service
To disable the service, execute:
```sh
sudo systemctl disable I4.0.service
```

# Done!
The I4.0 service is now running.
Please remember to stop the service if you're going to change some settings or if you're going to update I4.0 or it's dependencies.