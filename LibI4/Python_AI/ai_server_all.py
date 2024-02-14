import ai_server
import os

max_buffer_length: int = 4096
max_users: int = 1000
extra_system_messages: list[str] = []
plugins: list[str] = ai_server.cb.basics.Plugins.All()
version: str = "TAO71 I4.0 for Servers"

while (True):
    command = ""

    try:
        command = input(">$ ")
    except:
        command = "exit"

    if (command == "quit" or command == "close" or command == "stop" or command == "exit"):
        ai_server.__print__("Closing server...")

        ai_server.cfg.SaveConfig()
        ai_server.logs.WriteToFile()
        ai_server.UpdateServer()
        os._exit(0)
    elif (len(command.split()) > 0):
        ai_server.__print__(ai_server.run_server_command(command, {"ip": "0.0.0.0"}))