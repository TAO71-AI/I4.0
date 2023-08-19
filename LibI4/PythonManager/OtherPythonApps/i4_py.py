import socket
import json

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
api_key = "YOUR API KEY HERE"
server_ip = "127.0.0.1"

def Connect():
    global server_ip, client
    
    Disconnect()
    client.connect((server_ip, 8071))

def Disconnect():
    global client
    
    client.close()
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def SendAndWaitForResponse(send_data: bytes) -> bytes:
    global client
    
    try:
        Connect()
        
        client.send(send_data)
        data = client.recv(4096)
    except Exception as ex:
        print("ERROR #1: " + str(ex))
        data = b""
    
    Disconnect()
    return data

def ExecuteCommandWithAPIKey(send_data: str) -> bytes:
    global api_key
    
    command_dict = {
        "api_key": api_key,
        "cmd": send_data
    }
    return SendAndWaitForResponse(str(command_dict).encode("utf-8"))

def ExecuteCommandWithoutAPIKey(send_data: str) -> bytes:
    command_dict = {
        "api_key": "",
        "cmd": send_data
    }
    return SendAndWaitForResponse(str(command_dict).encode("utf-8"))

def GetQueue() -> int:
    cmd = ExecuteCommandWithoutAPIKey("get_queue").decode("utf-8")
    print("DATA: " + str(cmd))
    
    try:
        response = cmd
        response = int(json.loads(response)["response"])
        
        return response
    except Exception as ex:
        print("ERROR #2: " + str(ex))
        return -1
    
def DoPromptFull(prompt: str, translation: bool = True) -> dict:
    if (translation):
        service = "2"
    else:
        service = "1"
    
    try:
        response = ExecuteCommandWithAPIKey("service_" + service + "_f " + prompt).decode("utf-8")
        response = dict(json.loads(response))
        
        return response
    except Exception as ex:
        print("ERROR #3: " + str(ex))
        return {
            "response": "",
            "api_key": {
                "tokens": 0,
                "connections": 0
            }
        }

while True:
    print("\n\nPlease select a option: \n1 - Prompt with translation.\n2 - Prompt without translation.\n" +
        "3 - Change server IP.\n4 - Exit.\n")
    option = input("Option: ")
    
    if (option == "1"):
        prompt = input("Prompt: ")
        queue = GetQueue()
        
        print("Server queue: " + str(queue))
        response = DoPromptFull(prompt, True)
        
        print("AI: " + response["response"])
    elif (option == "2"):
        prompt = input("Prompt: ")
        queue = GetQueue()
        
        print("Server queue: " + str(queue))
        response = DoPromptFull(prompt, False)
        
        print("AI: " + response["response"])
    elif (option == "3"):
        server_ip = input("Server IP: ")
        print("Testing connection...")
        queue = GetQueue()
        
        if (queue < 0):
            print("Error on the IP, please try again.")
        else:
            print("Connection established.")
    elif (option == "4"):
        break
    
print("Closing I4.0 Python Server Connection.")