from collections.abc import Iterator
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
import ai_memory as memories
import data_share as ds

# Variables
max_buffer_length: int = 4096
max_users: int = 1000
queue: dict[str, list[int]] = {}
args: list[str] = []
times: dict[str, list[list[float]]] = {}
banned: dict[str, list[str]] = {
    "ip": [],
    "key": []
}
started: bool = False
serverWS: websockets.WebSocketServerProtocol = None
__version__: str = "v8.1.0"
filesCreated: list[str] = []

def CheckFiles() -> None:
    # Check if some files exists
    if (not os.path.exists("API/")):
        os.mkdir("API/")
    
    if (not os.path.exists("Logs/")):
        os.mkdir("Logs/")
    
    if (not os.path.exists("TOS.txt")):
        with open("TOS.txt", "w") as f:
            f.write("")
            f.close()

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
    
    # Save all the conversations and memories
    conv.SaveConversations()
    memories.SaveMemories()

def GetQueueForService(Service: str, Index: int) -> tuple[int, float]:
    # Get the users for the queue
    try:
        users = queue[Service][Index]
    except:
        users = 0
    
    # Calculate the predicted time
    try:
        t = 0

        for ti in times[Service][Index]:
            t += ti
        
        t = t / len(times[Service][Index])
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
                print(f"[DATA SHARE] Sent without errors to the server '{ds.Servers[results.index(result)]}'.")
            else:
                print(f"[DATA SHARE] Error sending to the server '{ds.Servers[results.index(result)]}': {result[1]}")
    except Exception as ex:
        print(f"[DATA SHARE] Error sending to ALL servers. Info: {ex}")

def __infer__(Service: str, Index: int, Prompt: str, Files: list[dict[str, str]], AIArgs: str, SystemPrompts: str | list[str], Key: dict[str, any], Conversation: str, UseDefaultSystemPrompts: bool, InternetMethod: str) -> Iterator[dict[str, any]]:
    # Start timer
    timer = time.time()

    # Make sure the key of the service exists
    if (Service not in list(queue.keys())):
        queue[Service] = []
        times[Service] = []

    # Wait for the queue to be valid
    while (GetQueueForService(Service, Index)[0] >= 1):
        # Sleep 1s
        time.sleep(1)

    try:
        # Try to add to the queue
        queue[Service][Index] += 1
    except IndexError:
        # The queue doesn't exists for this index
        # While the length of the list of the queue is less than the index
        while (len(queue[Service]) < Index + 1):
            # Add 0s to the queue and empty list to the times
            queue[Service].append(0)
            times[Service].append([])
                
        # Now, add 1 to the index
        queue[Service][Index] += 1

    # Create copy of the files
    fs = []
    
    for f in Files:
        fs.append(f.copy())
    
    # Remove tokens
    Key["tokens"] -= cfg.GetInfoOfTask(Service, Index)["price"]
    sb.SaveKey(Key, None)

    # Process the prompt and get a response
    response = cb.MakePrompt(Index, Prompt, fs, Service, AIArgs, SystemPrompts, [Key["key"], Conversation], UseDefaultSystemPrompts)
    fullResponse = ""
    responseFiles = []
    am = False

    # Add the files to the filesCreated
    for i in fs:
        filesCreated.append(i)

    # For every token, return it to the client
    for token in response:
        # Make sure the response is a string
        token["response"] = str(token["response"])

        # Remove some words from the response if the service is chatbot
        if (Service == "chatbot" and (token["response"].strip().lower() == "assistant" or token["response"].strip().lower() == "assistant" or (token["response"].strip().lower() == ":" and am))):
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

    # Remove all the generated files
    for i in fs:
        try:
            filesCreated.remove(i)
        except Exception as ex:
            print(f"Could not delete temporal file '{i}': {ex}.")

    # Set the timer
    timer = time.time() - timer

    # Add the timer to the service
    try:
        times[Service][Index].append(timer)
    except:
        times[Service][Index] = [timer]

    # Remove the user from the queue
    queue[Service][Index] -= 1

    if (queue[Service][Index] < 0):
        queue[Service][Index] = 0

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
    for file in Files:
        if (file["type"] == "image"):
            sdUFiles["images"].append(file["data"])
        elif (file["type"] == "audio"):
            sdUFiles["audios"].append(file["data"])
        elif (file["type"] == "document"):
            sdUFiles["documents"].append(file["data"])
        else:
            sdUFiles["other"].append(file["data"])

    # Share the data (if allowed by the server)
    __share_data__(Prompt, sdUFiles, fullResponse, sdRFiles)

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

        if (line.lower().startswith("(agi) ")):
            # Generate image command
            # Get the prompt
            cmd = line[6:].strip()

            # Generate the image and append it to the files
            cmdResponse = __infer__("text2img", GetAutoIndex("text2img"), cmd, Files, AIArgs, SystemPrompts, Key, Conversation, UseDefaultSystemPrompts, InternetMethod)

            # Append all the files
            for token in cmdResponse:
                yield {"response": "\n[IMAGES]\n", "files": token["files"], "ended": False}

            # Remove the command from the response
            fullResponse.replace(line, "")
        elif (line.lower().startswith("(aga) ")):
            # Generate audio command
            # Get the prompt
            cmd = line[6:].strip()

            # Generate the audio and append it to the files
            cmdResponse = __infer__("text2audio", GetAutoIndex("text2audio"), cmd, Files, AIArgs, SystemPrompts, Key, Conversation, UseDefaultSystemPrompts, InternetMethod)

            # Append all the files
            for token in cmdResponse:
                yield {"response": "\n[AUDIOS]\n", "files": token["files"], "ended": False}

            # Remove the command from the response
            fullResponse.replace(line, "")
        elif (line.lower().startswith("(int) ")):
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
            cmdResponse = cb.GetResponseFromInternet(Index, cmd, cmdQ, InternetMethod)
            text = ""

            # Yield another line
            yield {"response": "\n", "files": [], "ended": False}

            for token in cmdResponse:
                text += token
                yield {"response": token, "files": [], "ended": False}

            # Remove the command from the response
            fullResponse.replace(line, text)

            # Add internet result to the conversation
            conv.conversations[Key["key"]][Conversation][:-1]["content"] += "\n" + text
        elif (line.lower().startswith("(mem) ")):
            # Save memory command
            # Get the prompt
            cmd = line[6:].strip()

            # Save the memory
            memories.AddMemory(Key["key"], cmd)

            # Remove the command from the response
            fullResponse.replace(line, "")

def CheckIfHasEnoughTokens(Service: str, Index: int, KeyTokens: float) -> bool:
    # Get price
    price = cfg.GetInfoOfTask(Service, Index)["price"]

    # Check if price is less or equal to 0
    if (price <= 0):
        return True

    # Check if the tokens from the key are more or equal than the price
    return KeyTokens >= price

def MinPriceForService(Service: str) -> float:
    # Create prices
    prices = []

    # For each info of the service
    for info in cfg.GetAllInfosOfATask(Service):
        # Get the price and add it to prices
        prices.append(info["price"])
    
    # Check if the length of the prices is greater than 0
    if (len(prices) > 0):
        # It is, return the minimum price
        return min(prices)

    # If no prices are found, return -1
    return -1

def GetAutoIndex(Service: str) -> int:
    try:
        # Get the length of the service
        length = cb.GetServicesAndIndexes()[Service]

        # Check the length
        if (length == 0):
            raise Exception("Length of the services is 0.")
        
        # Check if the service exists in the queue
        if (Service not in list(queue.keys())):
            # It isn't, return 0 (the first index)
            return 0
        
        # It is, return the index with the smallest queue
        return min(queue[Service])
    except:
        # Return an error saying the service is not available
        raise Exception("Service not available.")

def ExecuteService(Prompt: dict[str, any], IPAddress: str) -> Iterator[dict[str, any]]:
    # Get some required variables
    service = Prompt["Service"]

    try:
        # Try to get the key
        key = sb.GetKey(Prompt["APIKey"])
    except:
        # Could not get the key, create empty key
        key = {"tokens": 0, "key": None, "admin": False}
    
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
        yield {"response": "ERROR: Missing variables.", "files": [], "ended": True}
        
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

        # Check the type
        if (type(systemPrompts) != list[str] and type(systemPrompts) != list):
            systemPrompts = [str(systemPrompts)]
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
    
    try:
        # Try to get the index of the model to use
        index = Prompt["Index"]
    except:
        # If an error occurs, set to default
        index = -1
    
    # Check if the API key is banned
    if (key["key"] in banned["key"]):
        yield {"response": "ERROR: Your API key is banned.", "files": [], "ended": True}
        return
    
    # Check if the user wants to execute a service
    if (len(cfg.GetAllInfosOfATask(service)) > 0):
        # It's a service to execute
        # Check the key
        if (key["key"] == None and len(Prompt["APIKey"]) > 0):
            # Key it's not valid nor empty
            # Wait 2s before processing
            time.sleep(2)

            # Return a warning
            yield {"response": "WARNING! Processing delayed 2s for security reasons. To avoid this warning, please use a valid API key or set it to empty.\n", "files": [], "ended": False}

        # Check index
        if (index < 0):
            # Get index
            index = GetAutoIndex(service)

        # Check the if the index is valid
        try:
            enoughTokens = CheckIfHasEnoughTokens(service, index, key["tokens"])
        except ValueError:
            print(f"Invalid index for service, returning exception. From 0 to {len(cfg.GetAllInfosOfATask(service)) - 1} expected; got {index}.")
            yield {"response": f"ERROR: Invalid index. Expected index to be from 0 to {len(cfg.GetAllInfosOfATask(service)) - 1}; got {index}.", "files": [], "ended": True}
            return
        except Exception as ex:
            print(f"[Check enouth tokens: ai_server.py] Unknown error: {ex}")
            yield {"response": f"ERROR: Unknown error checking if you have enouth tokens.", "files": [], "ended": True}

        # Check the price and it's a valid key
        if (not enoughTokens and key["key"] != None and cfg.current_data["force_api_key"]):
            # Doesn't have enough tokens or the API key is invalid, return an error
            yield {"response": f"ERROR: Not enough tokens or invalid API key. You need {cfg.GetInfoOfTask(service, index)['price']} tokens, you have {key['tokens']}.", "files": [], "ended": True}
            return
        elif (not enoughTokens and key["key"] == None):
            # Invalid API key
            yield {"response": "ERROR: Invalid API key.", "files": [], "ended": True}
            return
        
        # Check if the key is an admin
        if (key["admin"]):
            # It is, apply admin system prompts to the extra messages
            systemPrompts.append(cfg.current_data["custom_api_admin_system_messages"])
        else:
            # It isn't, apply not admin system prompts to the extra messages
            systemPrompts.append(cfg.current_data["custom_api_nadmin_system_messages"])
        
        try:
            # Check files length and service
            if (len(files) == 0 or service == "chatbot"):
                # Execute the service with all the files
                inf = __infer__(service, index, prompt, files, aiArgs, systemPrompts, key, conversation, useDefSystemPrompts, internetMethod)

                # For each token
                for inf_t in inf:
                    yield inf_t
            else:
                # For each file
                for file in files:
                    # Execute the service with the current file
                    inf = __infer__(service, index, prompt, [file], aiArgs, systemPrompts, key, conversation, useDefSystemPrompts, internetMethod)

                    # For each token
                    for inf_t in inf:
                        yield inf_t
            
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
            else:
                # Return half of the tokens spent
                key["tokens"] += cfg.GetInfoOfTask(service, index)["price"] / 2
                sb.SaveKey(key, None)
            
            # Remove the user from the queue
            queue[service][index] -= 1

            # Check the list is not < 0
            if (queue[service][index] < 0):
                # It is, set to 0
                queue[service][index] = 0
            
            # Return the exception
            yield {"response": f"ERROR: {ex}", "files": [], "ended": True}
    elif (service == "clear_my_history" or service == "clear_conversation"):
        # Clear the conversation
        # Check the key
        if (key["key"] == None and len(Prompt["APIKey"]) > 0):
            # Key it's not valid nor empty
            # Wait 2s before processing
            time.sleep(2)

            # Return a warning
            yield {"response": "WARNING! Processing delayed 2s for security reasons. To avoid this warning, please use a valid API key or set it to empty.\n", "files": [], "ended": False}

        # Check if the API key is valid
        if (key["key"] != None and len(key["key"].strip()) > 0):
            # The key is valid, delete the conversation
            conv.ClearConversation(key["key"], conversation)
        elif (not cfg.current_data["force_api_key"] or MinPriceForService("chatbot") <= 0):
            # The key is not valid, but the server says it's optional, so delete the conversation
            conv.ClearConversation("", conversation)
        else:
            # The key is invalid and it's required by the server, return an error
            yield {"response": "ERROR: Invalid API key.", "files": [], "ended": True}
        
        # Return a message
        yield {"response": "Conversation deleted.", "files": [], "ended": True}
    elif (service == "get_all_services"):
        # Get all the available services
        # Return all the services
        yield {"response": json.dumps(cb.GetServicesAndIndexes()), "files": [], "ended": True}
    elif (service == "get_conversation"):
        # Get the conversation of the user
        # Check the key
        if (key["key"] == None and len(Prompt["APIKey"]) > 0):
            # Key it's not valid nor empty
            # Wait 2s before processing
            time.sleep(2)

            # Return a warning
            yield {"response": "WARNING! Processing delayed 2s for security reasons. To avoid this warning, please use a valid API key or set it to empty.\n", "files": [], "ended": False}
        
        # Check if the key is valid
        if (key["key"] != None and len(key["key"].strip()) > 0):
            # Get the conversation of the key
            cnv = conv.GetConversation(key["key"], conversation)
        else:
            # Get the conversation from the empty key
            cnv = conv.GetConversation("", conversation)

        # Return the conversation
        yield {"response": json.dumps(cnv), "files": [], "ended": True}
    elif (service == "get_conversations"):
        # Get all the conversations of the user
        # Check the key
        if (key["key"] == None and len(Prompt["APIKey"]) > 0):
            # Key it's not valid nor empty
            # Wait 2s before processing
            time.sleep(2)

            # Return a warning
            yield {"response": "WARNING! Processing delayed 2s for security reasons. To avoid this warning, please use a valid API key or set it to empty.\n", "files": [], "ended": False}
        
        # Check if the key is valid
        if (key["key"] != None and len(key["key"].strip()) > 0):
            # Get the conversations of the key
            cnv = list(conv.conversations[key["key"]].keys())
        else:
            # Get the conversations from the empty key
            cnv = list(conv.conversations[""].keys())

        # Return all the conversations
        yield {"response": json.dumps([cn for cn in cnv]), "files": [], "ended": True}
    elif (service == "clear_memories"):
        # Delete all the memories of the user
        # Check the key
        if (key["key"] == None and len(Prompt["APIKey"]) > 0):
            # Key it's not valid nor empty
            # Wait 2s before processing
            time.sleep(2)

            # Return a warning
            yield {"response": "WARNING! Processing delayed 2s for security reasons. To avoid this warning, please use a valid API key or set it to empty.\n", "files": [], "ended": False}
        
        # Check if the API key is valid
        if (key["key"] != None and len(key["key"].strip()) > 0):
            # The key is valid, delete the memories
            memories.RemoveMemories(key["key"])
        elif (not cfg.current_data["force_api_key"] or MinPriceForService("chatbot") <= 0):
            # The key is not valid, but the server says it's optional, so delete the memories
            memories.RemoveMemories("")
        else:
            # The key is invalid and it's required by the server, return an error
            yield {"response": "ERROR: Invalid API key.", "files": [], "ended": True}
        
        # Return a message
        yield {"response": "Memories deleted.", "files": [], "ended": True}
    elif (service == "clear_memory"):
        # Delete a memory of the user
        # Check the key
        if (key["key"] == None and len(Prompt["APIKey"]) > 0):
            # Key it's not valid nor empty
            # Wait 2s before processing
            time.sleep(2)

            # Return a warning
            yield {"response": "WARNING! Processing delayed 2s for security reasons. To avoid this warning, please use a valid API key or set it to empty.\n", "files": [], "ended": False}
            
        # Check if the API key is valid
        if (key["key"] != None and len(key["key"].strip()) > 0):
            # The key is valid, delete the memory
            memories.RemoveMemory(key["key"], int(prompt))
        elif (not cfg.current_data["force_api_key"] or MinPriceForService("chatbot") <= 0):
            # The key is not valid, but the server says it's optional, so delete the memory
            memories.RemoveMemory("", int(prompt))
        else:
            # The key is invalid and it's required by the server, return an error
            yield {"response": "ERROR: Invalid API key.", "files": [], "ended": True}
        
        # Return a message
        yield {"response": "Memory deleted.", "files": [], "ended": True}
    elif (service == "get_memories"):
        # Get all the memories of the user
        # Check the key
        if (key["key"] == None and len(Prompt["APIKey"]) > 0):
            # Key it's not valid nor empty
            # Wait 2s before processing
            time.sleep(2)

            # Return a warning
            yield {"response": "WARNING! Processing delayed 2s for security reasons. To avoid this warning, please use a valid API key or set it to empty.\n", "files": [], "ended": False}
        
        # Check if the key is valid
        if (key["key"] != None and len(key["key"].strip()) > 0):
            # Get the memories of the key
            mms = memories.GetMemories(key["key"])
        else:
            # Get the memories from the empty key
            mms = memories.GetMemories("")

        # Return all the memories
        yield {"response": json.dumps(mms), "files": [], "ended": True}
    elif (service == "get_queue"):
        # Check index
        if (index < 0):
            # Set index
            index = GetAutoIndex(prompt)

        # Get a queue for a service
        if (len(prompt) > 0):
            queueUsers, queueTime = GetQueueForService(prompt, index)

            print(f"Queue for service '{prompt}' and index '{index}': {queueUsers} users, ~{queueTime}s for full response.")
            yield {"response": json.dumps({"users": queueUsers, "time": queueTime}), "files": [], "ended": True}
    elif (service == "get_tos"):
        # Get the Terms of Service of the server
        with open("TOS.txt", "r") as f:
            yield {"response": f.read(), "files": [], "ended": True}
            f.close()
    elif (service == "create_key" and key["admin"]):
        # Create a new API key
        keyData = cfg.JSONDeserializer(Prompt)
        keyData = sb.GenerateKey(keyData["tokens"], keyData["daily"])["key"]

        yield {"response": keyData, "files": [], "ended": True}
    elif (service == "get_key"):
        # Get information about the key
        keyData = key
        keyData["key"] = "[PRIVATE]"

        yield {"response": json.dumps(keyData), "files": [], "ended": True}
    elif (service == "get_service_description"):
        # Get the description of a specific service
        # Get the info from the service
        info = cfg.GetInfoOfTask(prompt, index)

        # Check if contains a description
        if ("description" in list(info.keys())):
            # Contains a description, send it
            yield {"response": info["description"], "files": [], "ended": True}
        else:
            # Does not contain a description, send an empty message
            yield {"response": "", "files": [], "ended": True}
    else:
        yield {"response": "ERROR: Invalid command.", "files": [], "ended": True}

async def ExecuteServiceAndSendToClient(Client: websockets.WebSocketClientProtocol, Prompt: dict[str, any]) -> None:
    try:
        # Try to execute the service
        for response in ExecuteService(Prompt, Client.remote_address[0]):
            # Send the response
            await Client.send(json.dumps(response).encode("utf-8"))
    except:
        # Print error
        print("Error processing! Could not send data to client.")

        # Print error info
        traceback.print_exc()

        # Check if the service is valid
        if (len(cfg.GetAllInfosOfATask(Prompt["Service"])) == 0):
            # Not valid, return
            return

        try:
            # Try to get the index of the model to use
            index = Prompt["Index"]
        except:
            # If an error occurs, auto get index
            index = GetAutoIndex(Prompt["Service"])
            
        # Substract 1 to the queue
        queue[Prompt["Service"]][index] -= 1
    
    # Update the server
    UpdateServer()

async def WaitForReceive(Client: websockets.WebSocketClientProtocol) -> None:
    async def _run_task_():
        task = asyncio.create_task(ExecuteServiceAndSendToClient(Client, prompt))
        await task

    # Wait for receive
    received = await Client.recv()

    # Check the length of the received data
    if (len(received) == 0):
        # Received nothing, close the connection
        Client.close()
        raise websockets.ConnectionClosed

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
        }).encode("utf-8"))

    # Execute service and send data
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    thread = threading.Thread(target = lambda: asyncio.run(_run_task_()))
    thread.start()

async def __receive_loop__(Client: websockets.WebSocketClientProtocol) -> None:
    while (not Client.closed and started):
        try:
            # Wait for receive in a bucle
            await WaitForReceive(Client)
        except websockets.ConnectionClosed:
            # Connection closed
            break
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
                # Print an error
                print("Could not send response to a client.")
        
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

    # Receive
    await __receive_loop__(Client)

def StartServer() -> None:
    global serverWS

    # Set the IP
    ip = "127.0.0.1" if (cfg.current_data["use_local_ip"]) else "0.0.0.0"

    # Set the websocket and listen
    eventLoop = asyncio.new_event_loop()
    asyncio.set_event_loop(eventLoop)

    serverWS = websockets.serve(OnConnect, ip, 8060, max_size = None)

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

    # Stop the DB
    sb.StopDB()

    # Delete all the saved files
    for f in filesCreated:
        try:
            os.remove(f)
        except:
            print(f"   Error deleting file '{f}'. Ignoring.")

    # Close
    started = False
    os._exit(0)
except Exception as ex:
    print("ERROR! Running traceback.\n\n")
    traceback.print_exc()