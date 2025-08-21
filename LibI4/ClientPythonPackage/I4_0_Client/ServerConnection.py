# Import libraries
from collections.abc import AsyncIterator
from websockets.asyncio.client import connect, ClientConnection
from websockets.protocol import State
import asyncio
import json

# Import I4.0 utilities
from .Config import Conf as Config
from .Service import Service
from . import Encryption

# Servers variables
ServersTasks: dict[int, list[Service]] = {}
Connected: tuple[str, str, int] | None = None
Conf: Config = Config()
ClientVersion: int = 160000

# WebSocket variables
ClientSocket: ClientConnection | None = None

# Keys
PublicKey: bytes | None = None
PrivateKey: bytes | None = None
ServerPublicKey: bytes | None = None

def GetTasks() -> dict[int, list[Service]]:
    # Return a copy of the tasks
    return ServersTasks.copy()

async def __connect_str__(Server: str, Port: int = 8060) -> None:
    global ClientSocket, Connected, PublicKey, PrivateKey, ServerPublicKey

    # Check if the keys have been generated
    if (PublicKey is None or PrivateKey is None):
        # Generate keys
        PrivateKey, PublicKey = Encryption.CreateKeys()

    # Disconnect from any other server
    await Disconnect()

    # Get the extension
    if (Server.startswith("ws://")):
        ext = "ws://"
        Server = Server[5:]
    elif (Server.startswith("wss://")):
        ext = "wss://"
        Server = Server[6:]
    else:
        ext = "ws://"
    
    # Get port
    if (":" in Server):
        Server = Server.split(":")
        Port = int(Server[1])
        Server = Server[0]

    # Create socket and connect
    ClientSocket = await connect(f"{ext}{Server}:{Port}", max_size = None, ping_interval = None, ping_timeout = None, close_timeout = None)

    # Wait until it's connected
    waited = 0

    while (ClientSocket.state == State.CONNECTING):
        if (waited > 50):
            raise TimeoutError("Server not responding.")

        await asyncio.sleep(0.1)
        waited += 1
    
    # Check client state
    if (ClientSocket.state != State.OPEN):
        raise RuntimeError(f"Error connecting. WebSocket state: {ClientSocket.state}")

    # Set connected server
    Connected = (Server, f"{ext}{Server}:{Port}", -1)

    # Get the public key from the server
    if (ServerPublicKey is None):
        ServerPublicKey = await SendAndReceive("get_public_key".encode("utf-8"), False)
    
    # Get the server version from the server
    serverVersion = await SendAndReceive("get_server_version".encode("utf-8"), False)
    serverVersion = serverVersion.decode("utf-8")

    try:
        Connected = (Connected[0], Connected[1], int(serverVersion))
    except:
        pass

async def __connect_int__(Server: int, Port: int = 8060) -> None:
    if (Server < 0 or Server >= len(Conf.Servers)):
        # The server ID is invalid
        raise Exception("Invalid server ID.")

    # Connect to the server
    await __connect_str__(Conf.Servers[Server], Port)

async def Connect(Server: str | int, Port: int = 8060) -> None:
    """
    This will connect the user to a server.
    If the user is alredy connected to a server, this will disconnect it first.
    """

    if (type(Server) == str):
        # Connect to a server by string
        await __connect_str__(Server, Port)
    elif (type(Server) == int):
        # Connect to a server by ID
        await __connect_int__(Server, Port)
    else:
        # Invalid server type
        raise Exception("Invalid server type.")

async def Disconnect() -> None:
    """
    This will disconnect the user from the server.
    If the user is not connected to any server this will not do anything.
    """
    global ClientSocket, Connected, ServerPublicKey

    if (ClientSocket != None):
        try:
            # Try to close the connection to the server
            await ClientSocket.close()
        except:
            # Ignore any errors during the disconnection
            pass

        # Delete the socket
        ClientSocket = None

    # Delete the connected server
    Connected = None

    # Delete the server public key
    ServerPublicKey = None

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

async def SendAndReceive(Data: bytes | str, Encrypt: bool = True) -> bytes:
    """
    This will send a message to the server and wait for it's response.
    The user must be connected to a server before using this.
    """

    # Check if you're connected
    if (not IsConnected()):
        await Disconnect()
        raise Exception("Connect to a server first.")
    
    # Convert the data to bytes
    if (isinstance(Data, str)):
        Data = Data.encode("utf-8")

    # Encrypt the data
    if (Encrypt):
        Data = Encryption.EncryptMessage(Data, ServerPublicKey, Encryption.__parse_hash__(Conf.HashAlgorithm), Connected[2] >= 140100)
        Data = json.dumps({"Hash": Conf.HashAlgorithm, "Message": Data, "Version": str(ClientVersion)})
    else:
        Data = Data.decode("utf-8") if (isinstance(Data, bytes)) else Data

    # Send the data
    await ClientSocket.send(Data)

    received = await __receive_from_server__()

    # Decrypt the data
    if (Encrypt):
        received = Encryption.DecryptMessage(received, PrivateKey, Encryption.__parse_hash__(Conf.HashAlgorithm)).encode("utf-8")

    # Return the response
    return received

async def GetServicesFromServer() -> list[Service]:
    """
    This will get all the available services from the current connected server.
    The user must be connected to a server before using this.
    """
    # Ask the server for the models, then deserialize the response into a dictionary and create a services list
    received = await SendAndReceive(json.dumps({
        "Service": "get_all_services",
        "Prompt": "",
        "Files": {},
        "PublicKey": PublicKey.decode("utf-8")
    }).encode("utf-8"), True)
    receivedData = received.decode("utf-8")
    jsonData = json.loads(receivedData)
    services = []

    # Set jsonData
    jsonData = json.loads(jsonData["response"])

    for service in list(jsonData.keys()):
        # Ignore if it alredy exists on the list
        if (Service.FromString(service) not in services):
            # Add the service to the list if don't exists
            services.append(Service.FromString(service))

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
    # Define globals
    global Connected, ClientSocket

    # Check if the user is connected to a server
    return Connected is not None and ClientSocket != None and ClientSocket.state == State.OPEN

async def SendAndWaitForStreaming(Data: str | bytes) -> AsyncIterator[dict[str, any]]:
    """
    This will send a prompt to the connected server and will wait for the full response.
    Also, this will yield the response of the server when received even if they're not complete.
    """

    # Send to the server and get a response
    responseBytes = await SendAndReceive(Data.encode("utf-8"), True)
    responseStr = responseBytes.decode("utf-8")
    response = json.loads(responseStr)

    # Check if it's streaming
    while (not response["ended"]):
        # Hasn't ended stream, returning dictionary
        yield response

        # Wait for receive
        responseBytes = await __receive_from_server__()
        responseStr = Encryption.DecryptMessage(responseBytes, PrivateKey, Encryption.__parse_hash__(Conf.HashAlgorithm))
        response = json.loads(responseStr)

    yield response