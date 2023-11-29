import ai_server
import os
import time
import requests
import socket
from sys import argv

def GetIPs() -> list[tuple[str, int]]:
    local = ""
    public = ""

    try:
        host_name = socket.gethostname()
        local = socket.gethostbyname(host_name)
    except:
        print("Error getting local IP.")
    
    try:
        response = requests.get("https://api64.ipify.org?format=json")
        data = response.json()
        public = data["ip"]
    except:
        print("Error getting public IP.")
    
    return [(local, 8060), (public, 8060)]

max_buffer_length: int = 4096
max_users: int = 1000
extra_system_messages: list[str] = []
plugins: list[str] = ai_server.cb.basics.Plugins.All()
version: str = "TAO71 I4.0 for Servers"
ips: list[tuple[str, int]] = GetIPs()

if (len(argv) > 1):
    if (argv[1].lower() == "-l"):
        max_users = 1
    elif (argv[1].lower() == "-he"):
        max_users = 7500
        max_buffer_length = 8192

print("Local IP: " + ips[0][0] + ":" + str(ips[0][1]))
print("Public IP: " + ips[1][0] + ":" + str(ips[1][1]))
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