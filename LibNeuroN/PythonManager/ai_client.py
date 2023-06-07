import socket

api_key = "YOUR_API_KEY_HERE"
use_api_key = True
server_connection = ("147.78.87.113", 8071)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client_socket.connect(server_connection)
except:
    print("Error connecting to the server.")

print("WARNING: Server connection can take a while.")

while True:
    msg = input("You: ")

    if (msg.lower() == "exit" or msg.lower() == "stop"):
        break

    msg_complete = (api_key if use_api_key else "") + msg

    client_socket.send(msg_complete.encode("utf-8"))
    response = client_socket.recv(4096).decode("utf-8")

    print("AI: " + response)

client_socket.close()