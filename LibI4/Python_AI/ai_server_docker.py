import ai_server
import os
import time
from sys import argv

max_buffer_length: int = 4096
max_users: int = 1000
extra_system_messages: list[str] = []
plugins: list[str] = ai_server.cb.basics.Plugins.All()
version: str = "TAO71 I4.0 for Servers"

if (len(argv) > 1):
    if (argv[1].lower() == "-l"):
        max_users = 1
    elif (argv[1].lower() == "-he"):
        max_users = 7500
        max_buffer_length = 8192

print("Server started. Press Ctrl+C to stop.")

try:
    while True:
        time.sleep(0.1)
except:
    pass

ai_server.__print__("Closing server...")

ai_server.cfg.SaveConfig()
ai_server.sb.StopDB()
ai_server.logs.WriteToFile()
ai_server.UpdateServer()
os._exit(0)