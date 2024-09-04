# This script is created to test I4.0's server
# This SHOULD NOT be used as a client, it's a very basic implementation

from collections.abc import AsyncIterator
import asyncio
import websockets
import json
import sys
import traceback
import random
import base64
import requests
import os

Servers: list[str] = ["127.0.0.1"]
Client: websockets.WebSocketClientProtocol | None = None
Conversation: str = "Test"
Key: str = ""
TestImage: str = ""
TestAudio: str = ""

def DownloadFile(URL: str, FileName: str) -> None:
    # Get the response
    response = requests.get(URL)
    response.raise_for_status()

    # Write the file
    with open(FileName, "wb") as f:
        f.write(response.content)
        f.close()

def GetServiceInputType(Service: str, Simplify: bool) -> str:
    # Check the service type
    if (Service == "chatbot" or Service == "text2img" or Service == "qa" or Service == "sc" or Service == "tr" or Service == "nsfw_filter-text" or Service == "tts" or Service == "text2audio"):
        # It's a text2any service
        return "text"
    elif (Service == "img2img" or Service == "od" or Service == "img2text" or Service == "de" or Service == "nsfw_filter-image"):
        # It's a img2any service
        if (Simplify):
            return "file"
        
        return "image"
    elif (Service == "speech2text" or Service == "rvc" or Service == "uvr"):
        # It's a audio2any service
        if (Simplify):
            return "file"
        
        return "audio"
    
    raise Exception("Unknown service.")

def SaveFile(FileData: dict[str, str]) -> str:
    # Create chars to use for random name
    chars = "abcdefghijklmnopqrstuvwxyz"
    chars += chars.upper() + "0123456789"

    # Generate a random name for the file
    name = "".join([chars[random.randint(0, len(chars) - 1)] for _ in range(5)])

    # Decode the data in bytes using base64
    data = base64.b64decode(FileData["data"])

    # Check the type of the file
    if (FileData["type"] == "audio"):
        # It's an audio, apply the extension to the name
        name += ".wav"
    elif (FileData["type"] == "image"):
        # It's an image, apply the extension to the name
        name += ".png"
    else:
        # Not a recognized type. Do not add any extension
        print("Invalid file type. No extension will be set.")
    
    # Write the file
    with open(name, "wb") as f:
        f.write(data)
        f.close()
    
    # Return the name of the file
    return name

async def UploadFileToServer(Ip: str | int, FileName: str) -> int:
    # Check the ip type
    if (type(Ip) == int):
        # It's an index, replace IP
        Ip = Servers[Ip]
    elif (type(Ip) != str):
        # Invalid IP type
        raise Exception("Invalid IP type.")
    
    # Connect to the server
    filesClient = await websockets.connect(f"ws://{Ip}:8061")

    # Set other variables
    chunkSize = 4096

    # Get file size
    fileSize = os.path.getsize(FileName)
    totalChunks = (fileSize + chunkSize - 1) // chunkSize

    # Read the file
    with open(FileName, "rb") as f:
        for i in range(totalChunks):
            # Set the offset
            offset = i * chunkSize
            f.seek(offset)

            # Get the current chunk
            chunk = f.read(chunkSize)

            # Send to the server
            await filesClient.send(chunk)

            # Check if it's completed
            if (i == totalChunks - 1):
                break
        
        # Send an end message
        await filesClient.send("<end>".encode("utf-8"))
        
        # Close the file
    
    # Wait for server's response
    response = await filesClient.recv()

    # Convert to int
    response = int(response)

    # Close the connection
    await filesClient.close()

    # Return the file's ID/name in the server
    return response

async def SendAndReceiveOnce(DataToSend: bytes) -> dict[str, any]:
    # Send to the server
    await Client.send(DataToSend)

    # Receive from the server
    return await ReceiveOnce()

async def ReceiveOnce() -> dict[str, any]:
    # Receive from the server
    received = await Client.recv()

    # Check the type of data
    if (type(received) == bytes):
        # It's a string, replace with encoded data
        received = received.decode("utf-8")
    elif (type(received) != str):
        # Invalid type
        raise Exception("Invalid received type.")
        
    # Load the JSON data
    received = json.loads(received)
    
    # Return the encoded data
    return received

async def SendToServer(DataToSend: bytes) -> AsyncIterator[dict[str, any]]:
    # Send to the server
    await Client.send(DataToSend)

    # Set ended
    ended = False

    # While the response didn't ended
    while (not ended):
        # Receive from the server
        received = await ReceiveOnce()

        # Check if the response ended
        ended = received["ended"]

        # Yield the received data
        yield received

async def ConnectToServer(Ip: str | int) -> None:
    global Client
    await DisconnectFromServer()

    # Check the ip type
    if (type(Ip) == int):
        # It's an index, replace IP
        Ip = Servers[Ip]
    elif (type(Ip) != str):
        # Invalid IP type
        raise Exception("Invalid IP type.")
    
    # Connect to the server
    Client = await websockets.connect(f"ws://{Ip}:8060", max_size = None)

async def DisconnectFromServer() -> None:
    global Client

    try:
        # Try to disconenct from the server first
        if (Client != None):
            await Client.close()
    finally:
        # Set to null
        Client = None

async def DeleteConversation() -> None:
    print("Deleting the conversation...")

    # Send data
    received = await SendAndReceiveOnce(json.dumps({
        "Service": "clear_my_history",
        "Prompt": "",
        "Files": [],
        "Conversation": Conversation,
        "APIKey": Key
    }).encode("utf-8"))

    # Check the response
    if (received["response"].lower() != "conversation deleted."):
        raise Exception("Error deleting conversation.")

async def TestInstance(Service: str, Index: int, Prompt: str, Files: list[dict[str, str]]) -> None:
    # Delete the conversation if the service has a text input
    await DeleteConversation()

    print(f"Testing the service '{Service}' at index '{Index}'...")

    # Send the request to the server
    data = json.dumps({
        "APIKey": Key,
        "Conversation": Conversation,
        "Prompt": Prompt,
        "Files": Files,
        "AIArgs": None,
        "SystemPrompts": [],
        "UseDefaultSystemPrompts": None,
        "Internet": "chatbot",
        "Index": Index,
        "Service": Service
    })
    response = SendToServer(data.encode("utf-8"))

    # Create a files list
    files = []

    # Print a template
    print(f"Response from service '{Service}' (index '{Index}'):\n\n- Text: ")

    # For each response
    async for res in response:
        # For each file
        for file in res["files"]:
            # Save the file and add the name to the list
            files.append(SaveFile(file))
        
        # Print the text output
        print(res["response"], end = "", flush = True)

        # Check if ended
        if (res["ended"]):
            # Break
            break
    
    print("")
    
    # Print the files names
    for file in files:
        print(f"\n\n- Files: {files}")
    
    print("---------------------------")

async def TestServer(Server: str | int) -> None:
    # Connect to the server
    await ConnectToServer(Server)

    # Get all the services from the server
    services = await SendAndReceiveOnce(json.dumps({
        "Service": "get_all_services",
        "Prompt": "",
        "Files": []
    }).encode("utf-8"))
    services = json.loads(services["response"])

    print(f"Got services:\n{"".join([f"- {serv} ({services[serv]} instances)" for serv in list(services.keys())])}")

    # For each service
    for service in list(services.keys()):
        # Get the number or instances
        instances = services[service]

        # Get type of input for the service
        serviceInput = GetServiceInputType(service, False)

        # Check the service's input
        if (serviceInput == "text"):
            # It's a text service
            # Set variables
            prompt = "This is a test. Please respond with a \"OK\" and a brief description about you."
            files = []
        elif (serviceInput == "image"):
            # It's an image service
            # Download a test image
            DownloadFile(TestImage, "test_image.png")

            # Upload the file to the server and get the name in the server
            fileName = await UploadFileToServer(Server, "test_image.png")

            # Set variables
            prompt = ""
            files = [{"type": "image", "name": str(fileName)}]
        elif (serviceInput == "audio"):
            # It's an audio service
            # Download a audio image
            DownloadFile(TestAudio, "test_audio.wav")

            # Upload the file to the server and get the name in the server
            fileName = await UploadFileToServer(Server, "test_audio.wav")

            # Set variables
            prompt = ""
            files = [{"type": "audio", "name": str(fileName)}]

        print(f"Initializing test of instances for service '{service}'.")

        # For each instance
        for i in range(-1, instances):
            # Test the instance
            await TestInstance(service, i, prompt, files)
        
        print(f"Test of instances completed successfully for the service '{service}'.")

# For each arg
for arg in sys.argv:
    if (arg.startswith("key=")):
        # Set the key
        Key = arg[4:]

# Create asyncio loop
loop = asyncio.new_event_loop()

# For each server
for server in Servers:
    try:
        # Test the server
        loop.run_until_complete(TestServer(server))
    except:
        # Error on the server, print traceback
        traceback.print_exc()

# Close the connection with the server
loop.run_until_complete(DisconnectFromServer())

# Test completed
print("Test completed.")
loop.close()