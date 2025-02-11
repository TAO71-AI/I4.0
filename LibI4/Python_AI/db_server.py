# Import libraries
import pymysql as mysql
import pymysql.cursors as mysql_c
import time
import asyncio
import os
import websockets
import json
import traceback

# Import I4.0 utilities
import encryption as enc
import ai_config as cfg

# Create variables
DBConnection: mysql.Connection | None = None
State: bool = False
ServerPrivateKey: bytes | None = None
ServerPublicKey: bytes | None = None

def WaitUntilReady() -> None:
    while (State):
        # It's reading or writting in the DB, wait
        time.sleep(0.05)

def ConnectToDB(ForceReconnect: bool = False) -> None:
    """
    Connects to the DB.
    """
    # Define global variables
    global DBConnection

    # Check if you're connected alredy and the force reconnect is false
    if (DBConnection is not None and not ForceReconnect):
        # Connected and force reconnect is false, return
        return
    
    # Connect to the DB
    DBConnection = mysql.connect(
        host = "127.0.0.1",         # DATABASE MUST BE HOSTED ON THE SAME SERVER
        user = cfg.current_data["db"]["user"],
        password = cfg.current_data["db"]["password"],
        database = cfg.current_data["db"]["db"],
        cursorclass = mysql_c.DictCursor
    )

def DisconnectFromDB() -> None:
    """
    Disconnects from the DB.
    """
    # Define globals
    global DBConnection

    # Check if the DB is connected
    if (DBConnection is not None):
        # Close the connection
        DBConnection.close()
        
        # Set the connection to None
        DBConnection = None

async def OnConnect(Client: websockets.WebSocketClientProtocol) -> None:
    # Define globals
    global State

    if (Client.remote_address[0] in banned["ip"]):
        try:
            # Print
            print("Banned user. Closing connection.")

            # Close the connection
            await Client.close()
            return
        except:
            # Error closing the connection, print
            print("Error closing the connection. Ignoring...")
            return

    try:
        # Receive
        receivedData = await Client.recv()

        # Convert data to bytes
        if (isinstance(receivedData, str)):
            receivedData = receivedData.encode("utf-8")
        elif (not isinstance(receivedData, bytes)):
            # Invalid data received, close the connection
            await Client.close()
            return
        
        # Print received data
        print(f"Received {len(receivedData)} bytes from client.")
        
        # Decrypt the data
        hash = enc.__parse_hash__(cfg.current_data["db"]["hash"])
        receivedData = enc.DecryptMessage(receivedData, ServerPrivateKey, hash)

        # Parse JSON and get values
        receivedData = cfg.JSONDeserializer(receivedData)
        command = receivedData["Command"]
        objects = tuple(receivedData["Objects"]) if (receivedData["Objects"] is not None) else None

        # Wait until the database is ready
        WaitUntilReady()

        # Connect to the DB
        ConnectToDB(False)

        # Set state to true
        State = True

        # Create cursor
        cursor: mysql_c.Cursor = DBConnection.cursor()

        # Check if the key already exists
        cursor.execute(command, objects)
        results: list[any] | None = cursor.fetchall()

        # Confirm the action
        DBConnection.commit()

        # Close the cursor
        cursor.close()

        # Set state to false
        State = False

        # Convert the results to a list
        if (isinstance(results, tuple)):
            results = list(results)
        elif (results is None):
            results = []
        elif (not isinstance(results, list)):
            results = [results]
        
        # Dump the results
        results = json.dumps(results)

        # Encrypt the results
        response = enc.EncryptMessage(results, ServerPublicKey, hash)

        # Send the response
        await Client.send(response)
    except:
        # If there's an error, print the error
        print(f"Error executing command: {traceback.format_exc()}")

        # Try to send the response
        try:
            await Client.send("ERROR".encode("utf-8"))
        except:
            # Error sending the response, print
            print("Error sending the response. Ignoring...")

        # Set state to false
        State = False
    
    # Close the connection
    await Client.close()

async def StartServer() -> None:
    # Set the IP
    ip = "127.0.0.1" if (cfg.current_data["use_local_ip"]) else "0.0.0.0"

    try:
        # Try to parse the port
        port = int(cfg.current_data["server_port"]) + 1
    except:
        # Error parsing the port, print and use default
        port = 8061
        print(f"Error parsing the server port, make sure it's an integer. Using default ({port}).")

    # Start the server
    serverWS = await websockets.serve(OnConnect, ip, port, max_size = None, ping_interval = 60, ping_timeout = 30)
    await serverWS.wait_closed()

# Start the server
serverLoop = asyncio.new_event_loop()

try:
    # Get the keys
    if (os.path.exists("db_pub.pem") and os.path.exists("db_pri.pem")):
        with open("db_pub.pem", "rb") as f:
            ServerPublicKey = f.read()
        
        with open("db_pri.pem", "rb") as f:
            ServerPrivateKey = f.read()
    else:
        print("Public or private keys not found. Creating new keys.")
        ServerPrivateKey, ServerPublicKey = enc.CreateKeys()

        with open("db_pub.pem", "wb") as f:
            f.write(ServerPublicKey)
        
        with open("db_pri.pem", "wb") as f:
            f.write(ServerPrivateKey)

    # Try to set the banned IPs
    if (os.path.exists("BannedIPs.json")):
        with open("BannedIPs.json", "r") as f:
            banned = cfg.JSONDeserializer(f.read())

    # Try to start the server
    print("Server started!")
    started = True

    serverLoop.run_until_complete(StartServer())
    serverLoop.close()
except KeyboardInterrupt:
    print("\nClosing server...")

    # Close
    started = False
    os._exit(0)
except Exception as ex:
    print("ERROR! Running traceback.\n\n")
    traceback.print_exc()