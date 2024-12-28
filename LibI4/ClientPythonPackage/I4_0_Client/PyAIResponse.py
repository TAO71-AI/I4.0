from collections.abc import Callable, Iterator
import asyncio
import json
import websockets
import os
import subprocess
import base64
from . import Config as Conf
from .Service import Service as Service
from .Service import ServiceManager as ServiceManager
from . import Encryption

# Servers variables
ServersTasks: dict[int, list[Service]] = {}
Connected: str = ""

# WebSocket variables
ClientSocket: websockets.WebSocketClientProtocol | None = None

# Actions
OnConnectingToServerAction: Callable[[str], None] | None = None
OnConnectedToServerAction: Callable[[str], None] | None = None
OnDisconnectFromServerAction: Callable[[], None] | None = None
OnSendDataAction: Callable[[bytes], None] | None = None
OnReceiveDataAction: Callable[[bytes], None] | None = None

def GetTasks() -> dict[int, list[Service]]:
    # Return a copy of the tasks
    return ServersTasks.copy()

async def __connect_str__(Server: str) -> None:
    global ClientSocket, Connected

    # Check if the keys have been generated
    if (len(Encryption.PublicKey) == 0 or len(Encryption.PrivateKey) == 0):
        # Generate keys
        Encryption.__create_keys__()

    # Disconnect from any other server
    await Disconnect()

    # Invoke the action
    if (OnConnectingToServerAction != None):
        OnConnectingToServerAction(Server)
    
    # Create socket and connect
    ClientSocket = await websockets.connect(f"ws://{Server}:8060", max_size = None)

    # Wait until it's connected
    for _ in range(50):
        if (ClientSocket.open):
            break

        await asyncio.sleep(0.1)
    else:
        raise Exception("Server not responding.")

    # Set connected server
    Connected = Server

    # Get the public key from the server
    serverPubKey = await SendAndReceive("get_public_key".encode("utf-8"), False)
    Encryption.ServerPublicKey = serverPubKey

    # Invoke the action
    if (OnConnectedToServerAction != None):
        OnConnectedToServerAction(Server)

async def __connect_int__(Server: int) -> None:
    if (Server < 0 or Server >= len(Conf.Servers)):
        # The server ID is invalid
        raise Exception("Invalid server ID.")
    
    # Connect to the server
    await __connect_str__(Conf.Servers[Server])

async def Connect(Server: str | int) -> None:
    """
    This will connect the user to a server.
    If the user is alredy connected to a server, this will disconnect it first.
    """

    if (type(Server) == str):
        # Connect to a server by string
        await __connect_str__(Server)
    elif (type(Server) == int):
        # Connect to a server by ID
        await __connect_int__(Server)
    else:
        # Invalid server type
        raise Exception("Invalid server type.")

async def Disconnect() -> None:
    """
    This will disconnect the user from the server.
    If the user is not connected to any server this will not do anything.
    """
    global ClientSocket, Connected

    if (ClientSocket != None):
        try:
            # Try to close the connection to the server
            await ClientSocket.close()
        except:
            # Ignore any errors during the disconnection
            pass

        # Delete the socket
        ClientSocket = None

        # Invoke the action
        if (OnDisconnectFromServerAction != None):
            OnDisconnectFromServerAction()
    
    # Delete the connected server
    Connected = ""

async def __receive_from_server__() -> bytes:
    # Receive from the server
    data = await ClientSocket.recv()

    # Check the data type
    if (type(data) == str):
        # It's a string, replace with encoded data
        data = data.encode("utf-8")
    elif (type(data) != bytes):
        # Invalid type
        raise Exception("Invalid received type.")
    
    # Return the bytes
    return data

async def SendAndReceive(Data: bytes, Encrypt: bool = True) -> bytes:
    """
    This will send a message to the server and wait for it's response.
    The user must be connected to a server before using this.
    """

    # Check if you're connected
    if (not IsConnected()):
        raise Exception("Connect to a server first.")
    
    # Encrypt the data
    if (Encrypt):
        OriginalData = Data
        Data = Encryption.EncryptMessage(Data, Encryption.ServerPublicKey).encode("utf-8")
    
    # Send the data
    await ClientSocket.send(Data)

    # Invoke the action
    if (OnSendDataAction != None):
        OnSendDataAction(OriginalData if (Encrypt) else Data)
    
    received = await __receive_from_server__()

    # Decrypt the data
    if (Encrypt):
        received = Encryption.DecryptMessage(received).encode("utf-8")

    # Invoke the action
    if (OnReceiveDataAction != None):
        OnReceiveDataAction(received)
    
    # Return the response
    return received

async def GetServicesFromServer() -> list[Service]:
    """
    This will get all the available services from the current connected server.
    The user must be connected to a server before using this.
    """

    # Check if you're connected
    if (not IsConnected()):
        raise Exception("Connect to a server first.")
    
    # Ask the server for the models, then deserialize the response into a dictionary and create a services list
    received = await SendAndReceive(json.dumps({
        "Service": "get_all_services",
        "Prompt": "",
        "Files": {},
        "PublicKey": Encryption.PublicKey.decode("utf-8")
    }).encode("utf-8"), True)
    receivedData = received.decode("utf-8")
    jsonData = json.loads(receivedData)
    services = []

    # Set jsonData
    jsonData = jsonData["response"]

    for service in list(jsonData.keys()):
        # Ignore if it alredy exists on the list
        if (ServiceManager.FromString(service) not in services):
            # Add the service to the list if don't exists
            services.append(ServiceManager.FromString(service))
    
    # Return all the services
    return services

async def FindFirstServer(ServiceToExecute: Service, DeleteData: bool = False) -> int:
    """
    This will find the first server available with the specified service.
    If there isn't any available server, this will return an error.
    """

    # Check if the user wants to delete the current services list or if the list is empty
    if (DeleteData or len(ServersTasks) == 0):
        # Clear the list and set an invalid server ID
        ServersTasks.clear()
        serverToReturn = -1

        for server in Conf.Servers:
            # For every server
            try:
                # Try to connect to the server
                await Connect(server)

                # Try to get all the services of the server, then add them to the list
                services = await GetServicesFromServer()
                ServersTasks[Conf.Servers.index(server)] = services

                # Check every service available from this server
                for service in services:
                    if (service == ServiceToExecute and serverToReturn < 0):
                        # If the service is the same the user requests, set the server ID to this server's ID
                        serverToReturn = Conf.Servers.index(server)
                
                # Disconnect from the server
                await Disconnect()
            except:
                # If the server doesn't responds or if there's another error, ignore it and continue with the next server
                ServersTasks[Conf.Servers.index(server)] = []
        
        # Check if the server ID is valid
        if (serverToReturn >= 0):
            # Return the ID if it's valid (the requested service has been found)
            return serverToReturn
        
        # Return an error if it's invalid (the requested service could not be found)
        raise Exception("Could not find any server.")

    # If the user doesn't want to delete the data and the service list isn't empty
    for server in Conf.Servers:
        # For every server get it's services
        for service in ServersTasks[Conf.Servers.index(server)]:
            # Check if the service is the same the user is requesting
            if (service == ServiceToExecute):
                # If it is, then return the server ID
                return Conf.Servers.index(server)
        
        # Continue with the next server if the requested service could not be found on this one
    
    # If the requested service has not been found on any server, return an error
    raise Exception("Could not find any server.")

def IsConnected() -> bool:
    # Check if the user is connected to a server
    return len(Connected.strip()) > 0 and ClientSocket != None and ClientSocket.open

def SendAndWaitForStreaming(Data: str) -> Iterator[dict[str, any]]:
    """
    This will send a prompt to the connected server and will wait for the full response.
    Also, this will yield the response of the server when received even if they're not complete.
    """

    # Send to the server and get a response
    responseBytes = asyncio.get_event_loop().run_until_complete(SendAndReceive(Data.encode("utf-8"), True))
    responseStr = responseBytes.decode("utf-8")
    response = json.loads(responseStr)

    # Check if it's streaming
    while (not response["ended"]):
        # Hasn't ended stream, returning dictionary
        yield response

        # Wait for receive
        responseBytes = asyncio.get_event_loop().run_until_complete(__receive_from_server__())
        responseStr = Encryption.DecryptMessage(responseBytes)
        response = json.loads(responseStr)
    
    yield response

def ExecuteCommand(Service: str, Prompt: str = "", Index: int = -1) -> Iterator[dict[str, any]]:
    """
    Executes a very-basic command on the server.
    You can use this, for example, to delete your conversation or get the queue for a service.

    Index == -1 automatically gets the model with the smallest queue size.
    """

    # Serialize a very basic, minimum, data to send to the server
    jsonData = json.dumps({
        "APIKey": Conf.ServerAPIKey,
        "Prompt": Prompt,
        "Files": {},
        "Service": Service,
        "Conversation": Conf.Chatbot_Conversation,
        "Index": Index,
        "DataShare": Conf.AllowDataShare,
        "PublicKey": Encryption.PublicKey.decode("utf-8")
    })

    # Return the response (probably serialized)
    return SendAndWaitForStreaming(jsonData)

def __execute_simulated_vision__(Template: str, Files: list[dict[str, str]], VisionService: Service, Index: int, ForceNoConnect: bool, SVisionPrompts: list[str]) -> None:
    # Try to send the message
    res = AutoGetResponseFromServer("", Files, VisionService, Index, ForceNoConnect, False)
    img = 0

    # For each response
    for token in res:
        # Check if the response ended
        if (token["ended"]):
            # Break the loop
            break

        # Get the response from the service
        SVisionPrompts[img] += Template.replace("[IMAGE_ID]", str(img + 1)).replace("[RESPONSE]", str(token["response"]))
        img += 1

def AutoGetResponseFromServer(Prompt: str, Files: list[dict[str, str]], ServerService: Service, Index: int = -1, ForceNoConnect: bool = False, FilesPath: bool = True) -> Iterator[dict[str, any]]:
    """
    This will automatically get a response a server.
    If the service requires it, this will serialize your prompt.
    This will also do other things before and after I4.0's response to your prompt.

    Index == -1 automatically gets the model with the smallest queue size.
    If FilesPath is false, the Files list MUST have the bytes of the files, in base64.
    If ForceNoConnect is true, this will not connect to any server, so you must be connected to one first.
    """

    # Copy the files list to a new one
    files = []
    systemPrompt = Conf.Chatbot_ExtraSystemPrompts

    for file in Files:
        if (FilesPath):
            # Check if the file exists
            if (not (os.path.exists(file["data"]) and os.path.isfile(file["data"]))):
                # Return an error
                raise Exception("File doesn't exists!")

            # Read the file and convert it to base64
            with open(file["data"], "rb") as f:
                files.append({
                    "type": file["type"],
                    "data": base64.b64encode(f.read()).decode("utf-8")
                })
        else:
            # Add the file as it is
            files.append(file)
    
    # Serialize the data to send to the server (in some services)
    if (ServerService == Service.ImageGeneration):
        # Template: text2img
        # Set variables
        prompt = ""
        nPrompt = ""

        if (Prompt.count(" [NEGATIVE] ") > 0):
            # Contains negative prompt, set prompt and negative prompt
            prompt = Prompt[0:Prompt.index(" [NEGATIVE] ")]
            nPrompt = Prompt[Prompt.index(" [NEGATIVE] ") + 12:]
        else:
            # Doesn't contains negative prompt, set prompt
            prompt = Prompt
        
        # Set prompt to the Text2Image template
        Prompt = json.dumps({
            "prompt": prompt,
            "negative_prompt": nPrompt,
            "width": Conf.Text2Image_Width,
            "height": Conf.Text2Image_Height,
            "guidance": Conf.Text2Image_GuidanceScale,
            "steps": Conf.Text2Image_Steps
        })
    elif (ServerService == Service.RVC):
        # Template: RVC
        Prompt = json.dumps({
            "filter_radius": Conf.RVC_FilterRadius,
            "f0_up_key": Conf.RVC_f0,
            "protect": Conf.RVC_Protect,
            "index_rate": Conf.RVC_IndexRate,
            "mix_rate": Conf.RVC_MixRate
        })
    elif (ServerService == ServerService.UVR):
        # Template: UVR
        Prompt = json.dumps({
            "agg": Conf.UVR_Agg
        })
    elif (ServerService == Service.Chatbot):
        # Check if the chatbot is multimodal
        chatbotMultimodal = None

        for token in ExecuteCommand("is_chatbot_multimodal", "", Index):
            # Check if the response is an error
            if (token["response"].lower().startswith("error")):
                # Error, break the loop
                break

            # Not an error, set boolean
            chatbotMultimodal = token["response"].lower() == "true"
        
        if (chatbotMultimodal != None and not chatbotMultimodal and len(files) > 0):
            # Is not multimodal and files length is > 0, apply simulated vision template
            sVisionPrompts = ["" for _ in range(len(files))]

            # Get response from Img2Text
            if (Conf.Chatbot_SimulatedVision_Image2Text):
                try:
                    # Try to send the message
                    __execute_simulated_vision__("### Image [IMAGE_ID] (description): [RESPONSE]\n", files, Service.ImageToText, Conf.Chatbot_SimulatedVision_Image2Text_Index, ForceNoConnect, sVisionPrompts)
                except:
                    # Ignore error
                    pass
            
            # Get response from ObjectDetection
            if (Conf.Chatbot_SimulatedVision_ObjectDetection):
                try:
                    # Try to send the message
                    __execute_simulated_vision__("### Image [IMAGE_ID] (objects detected with position, in JSON format): [RESPONSE]\n", files, Service.ObjectDetection, Conf.Chatbot_SimulatedVision_ObjectDetection_Index, ForceNoConnect, sVisionPrompts)
                except:
                    # Ignore error
                    pass
        
            # Save the user's prompt
            simulatedVisionPrompt = "".join(sVisionPrompts)

            # Replace the system prompts
            systemPrompt += f"\n{simulatedVisionPrompt}"
    
    if (not ForceNoConnect):
        # Connect to the first server to the service
        server = asyncio.get_event_loop().run_until_complete(FindFirstServer(ServerService))
        asyncio.get_event_loop().run_until_complete(Connect(server))
    elif (not IsConnected()):
        raise Exception("Please connect to a server first or set `ForceNoConnect` to false.")
    
    # Set prompt
    Prompt = json.dumps({
        "Service": ServiceManager.ToString(ServerService),
        "Prompt": Prompt,
        "Files": files,
        "APIKey": Conf.ServerAPIKey,
        "Conversation": Conf.Chatbot_Conversation,
        "AIArgs": Conf.Chatbot_AIArgs,
        "SystemPrompts": systemPrompt.strip(),
        "UseDefaultSystemPrompts": Conf.Chatbot_AllowServerSystemPrompts,
        "Index": Index,
        "DataShare": Conf.AllowDataShare,
        "PublicKey": Encryption.PublicKey.decode("utf-8")
    })

    # Return the response
    return SendAndWaitForStreaming(Prompt)

def GetQueueForService(QueueService: Service, Index: int = -1) -> tuple[int, int]:
    """
    This will send a prompt to the connected server asking for the queue size and time.
    Once received, it will return it.

    Index == -1 automatically gets the model with the smallest queue size.
    """

    # Get response from the queue command
    res = ExecuteCommand("get_command", ServiceManager.ToString(QueueService), Index)

    for response in res:
        if (not response["ended"]):
            # Continue, ignoring this message
            continue

        # Deserialize the received JSON response to a dictionary and return the users and the time
        queue = json.loads(response["response"])
        return (queue["users"], queue["time"])
    
    # Throw an error
    raise Exception("Queue error: Error getting queue.")

def DeleteConversation(Conversation: str | None) -> None:
    """
    This will delete your current conversation ONLY on the connected server.
    If `Conversation` is null this will use the conversation of the configuration.
    """

    CConversation = Conf.Chatbot_Conversation

    if (Conversation != None):
        # Update the conversation in the configuration settings
        Conf.Chatbot_Conversation = Conversation
    
    # Send request to the server and get the result
    res = ExecuteCommand("clear_conversation")

    # Restore the conversation in the configuration settings
    Conf.Chatbot_Conversation = CConversation

    for response in res:
        if (not response["ended"]):
            # Continue, ignoring this message
            continue

        # Set response variable
        result = response["response"].lower().strip()

        # Check if response it's invalid
        if (result != "conversation deleted."):
            # It's invalid, throw an error
            raise Exception(f"Error deleting the conversation. Got `{result}`; `conversation deleted.` expected.")
        
        # It's a valid response, return
        return
    
    # Throw an error
    raise Exception("Delete conversation error.")

def DeleteMemory(Memory: int = -1) -> None:
    """
    This will delete your current memory/memories ONLY on the connected server.
    If `Memory` is -1 this will delete all the memories.
    """

    if (Memory == -1):
        # Set the command to delete all the memories
        cmd = "clear_memories"
    else:
        # Set the command to delete a memory
        cmd = "clear_memory"
    
    # Send request to the server and get the result
    res = ExecuteCommand(cmd, str(Memory))

    for response in res:
        if (not response["ended"]):
            # Continue, ignoring this message
            continue

        # Set response variable
        result = response["response"].lower().strip()

        # Check if response it's invalid
        if (result != "memories deleted." and result != "memory deleted."):
            # It's invalid, throw an error
            raise Exception(f"Error deleting the memories/memory. Got `{result}`; `memories deleted.` or `memory deleted.` expected.")
        
        # It's a valid response, return
        return
    
    # Throw an error
    raise Exception("Delete memory/memories error.")

def GetTOS() -> str:
    """
    Gets the server's Terms Of Service.
    """

    # Send command to the server and wait for response
    res = ExecuteCommand("get_tos")

    # For each response
    for response in res:
        # Check if it ended
        if (not response["ended"]):
            # Continue, ignoring this message
            continue

        # It ended, get the text response
        tResponse = response["response"]

        # Strip the response
        tResponse = tResponse.strip()

        # Check the length of the response
        if (len(tResponse) == 0):
            # There are not TOS
            return "No TOS."
        
        # There are TOS, return the text response
        return tResponse
    
    raise Exception("Error getting TOS: No response from server.")

def OpenFile(Path: str, WaitForExit: bool = False, TemporalFile: bool = False) -> None:
    """
    This will open the file you want, this is meant to be used after the response of any service from the server.
    """

    # Check if the file exists
    if (not (os.path.exists(Path) and os.path.isfile(Path))):
        # Return an error if it doesn't
        raise Exception("File doesn't exists.")
    
    # Check the type of file and adjust the variables to it
    programName = ""
    programArgs = ""

    if (Path.lower().endswith((".png", ".jpeg", ".jpg"))):
        # It's an image
        programName = Conf.DefaultImagesProgram
    elif (Path.lower().endswith((".wav", ".mp3", ".flac"))):
        # It's an audio
        programName = Conf.DefaultAudioProgram
    else:
        # Unknown type, return an error
        raise Exception("Invalid/unknown file type.")
    
    # Check if the program name is empty
    if (len(programName.strip()) == 0):
        # If it is, set it to the path (to use the default system's program)
        programName = Path
    else:
        # If it isn't, set the args (to open the file with the specified program)
        programArgs = Path
    
    # Set the process info and create the process
    info = {
        "args": [programName] + ([programArgs] if (len(programArgs) > 0) else []),
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE
    }

    # Start the process
    p = subprocess.Popen(**info)

    # Wait until the program is closed to continue (if the user requests it)
    if (WaitForExit):
        p.wait()

        # Then closed, delete the file if the user says it's temporal
        if (TemporalFile):
            os.remove(Path)