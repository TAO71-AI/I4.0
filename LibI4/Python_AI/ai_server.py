from typing import Iterator
import websockets.server
import asyncio
import threading
import os
import json
import datetime
import time
import traceback
import server_basics as sb
import chatbot_all as cb
import ai_config as cfg
import ai_conversation as conv
import data_share as ds
import rec_files as rfs

# Variables
max_buffer_length: int = 4096
max_users: int = 1000
queue: dict[str, int] = {}
args: list[str] = []
times: dict[str, list[float]] = {}
banned: dict[str, list[str]] = {
    "ip": [],
    "key": []
}
started: bool = False
serverWS: websockets.WebSocketServerProtocol = None
__version__: str = "v6.5.0"

def CheckFiles() -> None:
    # Check if some files exists
    if (not os.path.exists("API/")):
        os.mkdir("API/")
    
    if (not os.path.exists("Logs/")):
        os.mkdir("Logs/")

def UpdateServer() -> None:
    # Check the files
    CheckFiles()

    if (cfg.current_data["force_api_key"]):
        # Get all the API keys from the server
        api_keys = sb.GetAllKeys()

        for api_key in api_keys:
            try:
                # Check if the API key is daily-updated
                if (str(api_key["daily"]).lower() == "true" or str(api_key["daily"]) == "1"):
                    # If it is, calculate the time that has passed (minute-precise)
                    date = datetime.datetime.now()
                    key_date = datetime.datetime(
                        int(api_key["date"]["year"]),
                        int(api_key["date"]["month"]),
                        int(api_key["date"]["day"]),
                        int(api_key["date"]["hour"]),
                        int(api_key["date"]["minute"]))
                    date_diff = date - key_date

                    # If a day or more has passed since the last use of the key, reset the tokens and the day
                    if (date_diff.total_seconds() >= 86400):
                        api_key["tokens"] = api_key["default"]["tokens"]
                        api_key["date"] = sb.GetCurrentDateDict()
            except Exception as ex:
                # Print the exception if something went wrong
                print("Error on API Key '" + str(api_key["key"]) + "': " + str(ex))
            
            # Save the API key
            sb.SaveKey(api_key)
    
    # Save all the conversations
    conv.SaveConversations()

    # Update the banned IPs in other services
    rfs.banned_ips = banned["ip"]

def GetQueueForService(Service: str) -> tuple[int, float]:
    # Get the users for the queue
    try:
        users = queue[Service]
    except:
        users = 0
    
    # Calculate the predicted time
    try:
        t = 0

        for ti in times[Service]:
            t += ti
        
        t = t * (users + 1)
    except:
        t = -1
    
    return (users, t)

def __send_share_data__(Data: str | bytes) -> list[tuple[bool, str, websockets.WebSocketClientProtocol]]:
    # Set the servers
    ds.Servers = cfg.current_data["data_share_servers"]
    
    # Create a loop and send
    loop = asyncio.new_event_loop()
    results = loop.run_until_complete(ds.SendToAllServers(Data))

    # Return the results
    return results

def __share_data__(UserPrompt: str, UserFiles: dict[str, list[str | bytes]], Response: str, ResponseFiles: dict[str, list[str | bytes]]) -> None:
    # Check if the sharing of data is enabled
    if (not cfg.current_data["allow_data_share"]):
        # Stop if it's not
        return
    
    # Set some variables
    userFiles = []
    responseFiles = []
    
    # Add all the user files
    for ft in UserFiles:
        for f in UserFiles[ft]:
            t = "unknown"

            if (ft == "images" or ft == "image"):
                t = "image"
            elif (ft == "audios" or ft == "audio"):
                t = "audio"
            elif (ft == "videos" or ft == "video"):
                t = "video"
            elif (ft == "documents" or ft == "document"):
                t = "document"
            
            userFiles.append({"Type": t, "Data": f})
    
    # Add all the response files
    for ft in ResponseFiles:
        for f in ResponseFiles[ft]:
            t = "unknown"

            if (ft == "images" or ft == "image"):
                t = "image"
            elif (ft == "audios" or ft == "audio"):
                t = "audio"
            elif (ft == "videos" or ft == "video"):
                t = "video"
            elif (ft == "documents" or ft == "document"):
                t = "document"
            
            responseFiles.append({"Type": t, "Data": f})

    # Set the data to send
    data = {
        "UserText": UserPrompt,
        "ResponseText": Response,
        "UserFiles": userFiles,
        "ResponseFiles": responseFiles
    }
    
    try:
        # Try to share the data
        results = []
        dataThread = threading.Thread(target = lambda: results.extend(__send_share_data__(json.dumps(data))))
        dataThread.start()
        dataThread.join()

        # Print the results
        for result in results:
            if (result[0]):
                print("[DATA SHARE] Sent without errors to the server '" + ds.Servers[results.index(result)] + "'.")
            else:
                print("[DATA SHARE] Error sending to the server '" + ds.Servers[results.index(result)] + "'.")
    except Exception as ex:
        print("[DATA SHARE] Error sending to ALL servers. Please check logs for more info.")

def CheckIfHasEnoughTokens(Service: str, KeyTokens: float) -> bool:
    # Calculate price for each service
    return KeyTokens >= cfg.current_data["price"][Service]

def ExecuteService(Prompt: dict[str, any], IPAddress: str) -> Iterator[dict[str, any]]:
    # Get some required variables
    service = Prompt["Service"]

    try:
        # Try to get the key
        key = sb.GetKey(Prompt["APIKey"])
    except:
        # Could not get the key, create empty key
        key = {"tokens": 0, "key": (None if (cfg.current_data["force_api_key"]) else "")}
    
    # Get some "optional" variables
    try:
        # Try to get conversation
        conversation = Prompt["Conversation"]
    except:
        # If an error occurs, set to default
        conversation = "default"
    
    try:
        # Try to get the prompt and files
        prompt = Prompt["Prompt"]
        files = Prompt["Files"]
    except:
        # If any of this variables is missing, return an error
        raise Exception("Missing variables.")
        
    try:
        # Try to get conversation
        conversation = Prompt["Conversation"]
    except:
        # If an error occurs, set to default
        conversation = "default"
        
    try:
        # Try to get AI args
        aiArgs = Prompt["AIArgs"]
    except:
        # If an error occurs, set to default
        aiArgs = None
        
    try:
        # Try to get extra system prompts
        systemPrompts = Prompt["SystemPrompts"]
    except:
        # If an error occurs, set to default
        systemPrompts = []
        
    try:
        # Try to get use default system prompts
        useDefSystemPrompts = Prompt["UseDefaultSystemPrompts"]
    except:
        # If an error occurs, set to default
        useDefSystemPrompts = None
        
    try:
        # Try to get the internet method
        internetMethod = Prompt["Internet"]
    except:
        # If an error occurs, set to default
        internetMethod = "qa"
    
    # Check if the API key is banned
    if (key["key"] in banned["key"]):
        raise Exception("Your API key is banned.")
    
    # Check if the user wants to execute a service
    if (cfg.current_data["models"].split(" ").count(service) > 0):
        # It's a service to execute
        # Check the price and it's a valid key
        if (not CheckIfHasEnoughTokens(service, key["tokens"]) and key["key"] != None and cfg.current_data["force_api_key"]):
            # Doesn't have enough tokens or the API key is invalid, return an error
            raise Exception("Not enough tokens or invalid API key. You need " + str(cfg.current_data["price"][service]) + " tokens, you have " + str(key["tokens"]) + ".")
        elif (key["key"] == None):
            # Invalid API key
            raise Exception("Invalid API key.")
        
        try:
            # Start timer
            timer = time.time()

            # Get queue
            queueUsers, _ = GetQueueForService(service)

            # Wait for the queue to be valid
            while (queueUsers > cfg.current_data["max_prompts"]):
                pass

            try:
                # Try to add to the queue
                queue[service] += 1
            except:
                # The queue doesn't exists, create
                queue[service] = 1

            # Process the prompt and get a response
            response = cb.MakePrompt(prompt, files, service, aiArgs, systemPrompts, [key["key"], conversation], useDefSystemPrompts)
            fullResponse = ""
            responseFiles = []
            am = False

            # For every token, return it to the client
            for token in response:
                # Make sure the response is a string
                token["response"] = str(token["response"])

                # Remove some words from the response if the service is chatbot
                if (service == "chatbot" and (token["response"].strip().lower() == "assistant" or token["response"].strip().lower() == "assistant" or (token["response"].strip().lower() == ":" and am))):
                    am = True
                    continue
                else:
                    am = False

                # Set the files, ending and full response
                fullResponse += str(token["response"])
                responseFiles += token["files"]
                token["ended"] = False

                # Yield the token
                yield token

            # Set the timer
            timer = time.time() - timer

            # Add the timer to the service
            try:
                times[service].append(timer)
            except:
                times[service] = [timer]

            # Remove the user from the queue
            queue[service] -= 1

            if (queue[service] < 0):
                queue[service] = 0

            # Set the data share files
            sdFilesTemplate = {
                "images": [],
                "audios": [],
                "documents": [],
                "other": []
            }

            sdUFiles = sdFilesTemplate.copy()
            sdRFiles = sdFilesTemplate.copy()

            # For every response file
            for file in responseFiles:
                if (file["type"] == "image"):
                    sdRFiles["images"].append(file["data"])
                elif (file["type"] == "audio"):
                    sdRFiles["audios"].append(file["data"])
                elif (file["type"] == "document"):
                    sdRFiles["documents"].append(file["data"])
                else:
                    sdRFiles["other"].append(file["data"])
            
            # For every client file
            for file in files:
                try:
                    # Read the file
                    with open("ReceivedFiles/" + file["name"] + ".enc_file", "r") as f:
                        if (file["type"] == "image"):
                            sdUFiles["images"].append(f.read())
                        elif (file["type"] == "audio"):
                            sdUFiles["audios"].append(f.read())
                        elif (file["type"] == "document"):
                            sdUFiles["documents"].append(f.read())
                        else:
                            sdUFiles["other"].append(f.read())
                except:
                    print("Error appending user file. Might not exist.")

            # Share the data (if allowed by the server)
            __share_data__(prompt, sdUFiles, fullResponse, sdRFiles)

            # Strip the full response
            fullResponse = fullResponse.strip()

            # Search for commands for every line
            for line in fullResponse.split("\n"):
                # Check if the line starts and/or ends with quotes, then remove them
                while (line.startswith("\"") or line.startswith("\'") or line.startswith("`")):
                    line = line[1:]
            
                while (line.endswith("\"") or line.endswith("\'") or line.endswith("`")):
                    line = line[:-1]
                
                # Strip the line
                line = line.strip()

                if (line.startswith("(agi) ")):
                    # Generate image command
                    # Get the prompt
                    cmd = line[6:].strip()

                    # Generate the image and append it to the files
                    cmdResponse = cb.MakePrompt(cmd, [], "text2img")

                    # Append all the files
                    for token in cmdResponse:
                        yield {"response": "\n[IMAGES]\n", "files": token["files"], "ended": False}

                    # Remove the command from the response
                    fullResponse.replace(line, "")
                elif (line.startswith("(aga) ")):
                    # Generate audio command
                    # Get the prompt
                    cmd = line[6:].strip()

                    # Generate the audio and append it to the files
                    cmdResponse = cb.MakePrompt(cmd, [], "text2audio")

                    # Append all the files
                    for token in cmdResponse:
                        yield {"response": "\n[AUDIOS]\n", "files": token["files"], "ended": False}

                    # Remove the command from the response
                    fullResponse.replace(line, "")
                elif (line.startswith("(int) ")):
                    # Internet search command
                    # Get the prompt
                    cmd = line[6:].strip()
                    
                    # Deserialize the prompt
                    try:
                        cmd = cfg.JSONDeserializer(cmd)
                        cmdQ = cmd["question"].strip()
                        cmd = cmd["prompt"].strip()
                    except:
                        # Could not deserialize the prompt, ignoring
                        continue

                    # Generate the image and append it to the files
                    cmdResponse = cb.GetResponseFromInternet(cmd, cmdQ, internetMethod)
                    text = ""

                    # Yield another line
                    yield {"response": "\n", "files": [], "ended": False}

                    for token in cmdResponse:
                        text += token
                        yield {"response": token, "files": [], "ended": False}

                    # Remove the command from the response
                    fullResponse.replace(line, text)

                    # Add internet result to the conversation
                    conv.conversations[key["key"]][conversation][len(conv.conversations[key["key"]][conversation]) - 1]["content"] += "\n" + text
            
            # Return empty response
            yield {"response": "", "files": [], "ended": True}
        except Exception as ex:
            if (str(ex).lower() == "nsfw detected!"):
                # NSFW detected, check if the server should ban the API key
                if (cfg.current_data["ban_if_nsfw"] and cfg.current_data["force_api_key"] and key["key"] != None):
                    # Ban the API key
                    banned["key"].append(key["key"])
                
                # Check if the server should ban the IP address
                if (cfg.current_data["ban_if_nsfw_ip"] and IPAddress != "127.0.0.1"):
                    # Ban the IP address
                    banned["ip"].append(IPAddress)
            
            # Remove the user from the queue
            queue[service] -= 1
            
            # Return the exception
            raise ex
    elif (service == "clear_my_history" or service == "clear_conversation"):
        # Clear the conversation
        # Check if the API key is valid
        if (key["key"] != None and len(key["key"].strip()) > 0):
            # The key is valid, delete the conversation
            conv.ClearConversation(key["key"], conversation)
        elif (not cfg.current_data["force_api_key"]):
            # The key is not valid, but the server says it's optional, so delete the conversation
            conv.ClearConversation("", conversation)
        else:
            # The key is invalid and it's required by the server, return an error
            raise Exception("Invalid API key.")
        
        # Return a message
        yield {"response": "Conversation deleted.", "files": [], "ended": True}
    elif (service == "get_all_services"):
        # Get all the available services
        # Return all the services
        yield {"response": json.dumps(cb.GetAllModels()), "files": [], "ended": True}
    elif (service == "get_conversation"):
        # Get the conversation of the user
        # Return the conversation
        yield {"response": json.dumps(conv.GetConversation(key["key"], conversation)), "files": [], "ended": True}
    elif (service == "get_queue"):
        # Get a queue for a service
        if (len(prompt) > 0):
            queueUsers, queueTime = GetQueueForService(prompt)
            yield {"response": json.dumps({"users": queueUsers, "time": queueTime}), "files": [], "ended": True}
    else:
        raise Exception("Invalid command.")

async def WaitForReceive(Client: websockets.WebSocketClientProtocol) -> None:
    # Wait for receive
    received = await Client.recv()

    # Print received length
    print(f"Received {len(received)} bytes from '{Client.remote_address[0]}'")

    try:
        # Check the type of the received message
        if (type(received) == str):
            # Received a string, try to deserialize it
            prompt = cfg.JSONDeserializer(received)
        elif (type(received) == bytes):
            # Received bytes, try to decode it to string and deserialize it
            prompt = cfg.JSONDeserializer(received.decode("utf-8"))
        else:
            # Received something else, return an error
            raise Exception("Invalid received type.")
    except Exception as ex:
        # If there's an error, send the response
        await Client.send(json.dumps({
            "response": "Error. Details: " + str(ex),
            "files": [],
            "ended": True
        }))

    # Execute the service
    for response in ExecuteService(prompt, Client.remote_address[0]):
        # Send the response
        await Client.send(json.dumps(response))
    
    # Update the server
    UpdateServer()

async def __receive_loop__(Client: websockets.WebSocketClientProtocol) -> None:
    while (not Client.closed and started):
        try:
            # Wait for receive in a bucle
            await WaitForReceive(Client)
        except Exception as ex:
            # Error returned
            try:
                # Try to send to the client
                await Client.send(json.dumps({
                    "response": "Error executing service. Details: " + str(ex),
                    "files": [],
                    "ended": True
                }))

                # Print the error
                print("Error executing service. Traceback:")
                traceback.print_exc()
            except:
                # Print an error, then ignore
                print("Could not send any response to a client. Closing...")

                try:
                    # Try to close the connection
                    await Client.close()
                except:
                    # Error closing the connection, print
                    print("Error closing the connection. Ignoring.")
                    break
        
        # Save the banned IP addresses and keys
        with open("BannedIPs.json", "w+") as f:
            f.write(json.dumps(banned))
            f.close()

async def OnConnect(Client: websockets.WebSocketClientProtocol) -> None:
    print(f"'{Client.remote_address[0]}' has connected.")

    if (Client.remote_address[0] in banned["ip"]):
        try:
            # Send banned message
            await Client.send(json.dumps({
                "response": "Your IP address has been banned. Please contact support if this was a mistake.",
                "files": [],
                "ended": True
            }))

            # Close the connection
            await Client.close()
            return
        except:
            # Error closing the connection, print
            print("Error closing the connection. Ignoring...")
            return

    await __receive_loop__(Client)

def StartServer() -> None:
    global serverWS

    # Set the IP
    ip = "127.0.0.1" if (cfg.current_data["use_local_ip"]) else "0.0.0.0"

    # Set the websocket and listen
    eventLoop = asyncio.new_event_loop()
    asyncio.set_event_loop(eventLoop)

    serverWS = websockets.serve(OnConnect, ip, 8060)

    # Start the server
    eventLoop.run_until_complete(serverWS)
    eventLoop.run_forever()

# Start the server
try:
    # Try to set the banned IPs
    if (os.path.exists("BannedIPs.json")):
        with open("BannedIPs.json", "r") as f:
            banned = cfg.JSONDeserializer(f.read())
            f.close()
    
    # Load all the models
    cb.LoadAllModels()

    # Try to start the server
    print("Server started!")
    started = True

    StartServer()
except KeyboardInterrupt:
    print("\nClosing server...")

    # Save the configuration
    cfg.SaveConfig(cfg.current_data)

    # Close
    started = False
    os._exit(0)
except Exception as ex:
    print("ERROR! Running traceback.\n\n")
    traceback.print_exc()