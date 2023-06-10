import socket
import threading
import os
import server_basics as sb
import chatbot_all as cb
import ai_config as cfg

# Variables
max_buffer_length: int = 4096
max_users: int = 1000
requires_api_key: bool = True
processing: bool = False

cb.use_chat_history_if_available = False
cb.system_messages = cb.basics.GetDefault_I4_SystemMessages(cb.basics.Plugins.All(), cb.basics.ExtraSystemMessages.Human())

cb.LoadAllModels()

# Server
def run_server_command(command_data: str) -> str:
    global processing

    if (command_data.lower().startswith("-u ")):
        command = command_data[3:len(command_data)]
        admin = False
    else:
        command = command_data
        admin = True

    if (command.startswith("ai_response ")):
        while processing:
            pass

        processing = True
        ai_response = cb.MakePrompt(command[12:len(command)])["response"]
        processing = False

        return ai_response
    elif (command.startswith("ai_fresponse ")):
        while processing:
            pass

        processing = True
        ai_response = cb.MakePrompt(command[13:len(command)])
        processing = False

        return ai_response
    elif (command.startswith("echo ") and admin):
        return command[5:len(command)]
    elif (command == "createkey" and admin and requires_api_key):
        return sb.GenerateKey()["key"]
    
    return "Invalid command."

def handle_client(client_socket: socket, address: socket):
    while (True):
        data: str = client_socket.recv(max_buffer_length).decode()

        if (len(data) > 0):
            print("Received data from '" + str(address) + "': '" + data + "'")
            server_response = None

            if (requires_api_key and len(data) >= 15):
                try:
                    api_key = data[0:15]
                    key_data = sb.GetKey(api_key)
                    data = data.replace(api_key, "")
                except:
                    pass

                try:
                    if (key_data["tokens"] > 0 and key_data["connections"] > 0):
                        key_data["tokens"] -= (len(data) - 15) / 5
                        key_data["connections"] -= 1

                        try:
                            server_response = run_server_command("-u " + data)
                            sb.SaveKey(key_data)
                        except Exception as ex:
                            client_socket.send("Error on the server: " + str(ex))
                    else:
                        client_socket.send("ERROR ON API KEY: Not enough tokens.".encode())
                        return
                except:
                    client_socket.send("ERROR ON API KEY: Invalid key.".encode())
                    return
            elif (not requires_api_key):
                server_response = run_server_command("-u " + data)
            else:
                client_socket.send("ERROR ON API KEY: Invalid key.".encode())
                return

            print("Command: '-u " + data + "': " + server_response)
            client_socket.send(server_response.encode())
        else:
            break

    client_socket.close()

def accept_client():
    while (True):
        client_socket, address = server_socket.accept()
        print("Incomming connection from '" + str(address) + "'")

        client_handle_thread = threading.Thread(target = handle_client, args = (client_socket, address))
        client_handle_thread.start()

with open("openai_api_key.txt", "w+") as f:
    cb.openai.api_key = f.read()

if (requires_api_key and len(os.listdir("API/")) <= 0):
    run_server_command("createkey")

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("0.0.0.0", 8071))
server_socket.listen(max_users)

print("Server started and listening.\n\n")

try:
    accept_client_thread = threading.Thread(target = accept_client)
    accept_client_thread.start()
except:
    print("Error on accept client.")

while (True):
    command = input(">$ ")

    if (command == "quit" or command == "close" or command == "stop" or command == "exit"):
        print("Closing server...")

        cfg.SaveConfig()
        os._exit(0)
    elif (len(command.split()) > 0):
        print(run_server_command(command))