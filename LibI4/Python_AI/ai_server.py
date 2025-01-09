from collections.abc import Iterator
import websockets.server
import asyncio
import threading
import os
import json
import datetime
import time
import traceback
import gc

try:
    # Try to import I4.0 utilities
    import server_basics as sb
    import encryption as enc
    import chatbot_all as cb
    import ai_config as cfg
    import conversation_multimodal as conv
    import ai_memory as memories
except ImportError:
    # Error importing utilities
    traceback.print_exc()
    print("Error importing I4.0 utilities, please make sure that your workdir is '/path/to/I4.0/LibI4/Python_AI/'.")

    os._exit(1)

# Variables
queue: dict[str, list[int]] = {}
times: dict[str, list[list[int]]] = {}
banned: dict[str, list[str]] = {
    "ip": [],
    "key": []
}
started: bool = False
modelsUsed: dict[str, list[int]] = {}

def __clear_cache_loop__() -> None:
    # Check if cache clear time is less or equal to 0
    if (cfg.current_data["clear_cache_time"] <= 0):
        # Do not clear the cache
        return

    # While the server in running
    while (started):
        # Wait the specified time
        time.sleep(cfg.current_data["clear_cache_time"])

        # Clear the cache
        cb.EmptyCache()

def __clear_queue_loop__() -> None:
    # Check if queue clear time is less or equal to 0
    if (cfg.current_data["clear_queue_time"] <= 0):
        # Do not clear the queue
        return

    # While the server in running
    while (started):
        # Wait the specified time
        time.sleep(cfg.current_data["clear_queue_time"])

        # Clear the queue
        queue.clear()
        times.clear()

def __offload_loop__() -> None:
    # Check if the offload time is less or equal to 0
    if (cfg.current_data["offload_time"] <= 0):
        # Do not offload the models
        return
    
    # While the server is running
    while (started):
        # Wait the specified time
        time.sleep(cfg.current_data["offload_time"])

        # Offload the models
        cb.OffloadAll(modelsUsed)
        modelsUsed.clear()

        # IMPORTANT!!! Make sure that the offload_time is greater than the time that takes the model to generate a token.
        # Otherwise, the server may freeze and crash.

        # Run the garbage collector
        gc.collect()

def CheckFiles() -> None:
    # Check if some files exists
    if (not os.path.exists("API/")):
        os.mkdir("API/")
    
    if (not os.path.exists("Logs/")):
        os.mkdir("Logs/")
    
    if (not os.path.exists("TOS.txt")):
        with open("TOS.txt", "w") as f:
            f.write("")

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

def GetQueueForService(Service: str, Index: int) -> tuple[int, int]:
    # Get the users for the queue
    try:
        if (queue[Service][Index] < 0):
            queue[Service][Index] = 0

        users = queue[Service][Index]
    except:
        users = 0
    
    # Calculate the predicted time
    try:
        t = 0

        for ti in times[Service][Index]:
            t += ti
        
        t = int(t / len(times[Service][Index]))
    except:
        t = -1
    
    return (users, t)

def __infer__(Service: str, Index: int, Prompt: str, Files: list[dict[str, str]], AIArgs: str, SystemPrompts: str | list[str], Key: dict[str, any], Conversation: str, UseDefaultSystemPrompts: bool, AllowDataShare: bool, AllowedTools: str | list[str] | None) -> Iterator[dict[str, any]]:
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

    # Add the index to the models used
    try:
        modelsUsed[Service].append(Index)
    except:
        modelsUsed[Service] = [Index]

    # Process the prompt and get a response
    response = cb.MakePrompt(Index, Prompt, fs, Service, AIArgs, SystemPrompts, [Key["key"], Conversation], UseDefaultSystemPrompts, AllowedTools)
    fullResponse = ""
    responseFiles = []

    # Start timer
    timer = time.time()

    # For every token, return it to the client
    for token in response:
        # Add the index to the models used (if not there already)
        if (Service not in list(modelsUsed.keys()) or Index not in modelsUsed[Service]):
            try:
                modelsUsed[Service].append(Index)
            except:
                modelsUsed[Service] = [Index]

        # Make sure the response is a string
        token["response"] = str(token["response"])

        # Set the files, ending and full response
        fullResponse += str(token["response"])
        responseFiles += token["files"]
        token["ended"] = False

        # Set the timer and transform to milliseconds
        timer = int((time.time() - timer) * 1000)

        # Add the timer to the service
        try:
            times[Service][Index].append(timer)
        except:
            times[Service][Index] = [timer]
        
        # Restart the timer
        timer = time.time()

        # Yield the token
        yield token

    # Remove the user from the queue
    queue[Service][Index] -= 1

    if (queue[Service][Index] < 0):
        queue[Service][Index] = 0

    # Strip the full response
    fullResponse = fullResponse.strip()
    convAssistantFiles = []

    # Search for commands for every line
    for line in fullResponse.split("\n"):
        # Check if the line starts and/or ends with quotes, then remove them
        while (line.startswith("\"") or line.startswith("\'") or line.startswith("`")):
            line = line[1:]
            
        while (line.endswith("\"") or line.endswith("\'") or line.endswith("`")):
            line = line[:-1]
                
        # Strip the line
        line = line.strip()

        if (line.lower().startswith("/img ")):
            # Generate image command
            # Get the prompt
            cmd = line[5:].strip()

            # Generate the image and append it to the files
            cmdResponse = __infer__("text2img", GetAutoIndex("text2img"), cmd, [], AIArgs, SystemPrompts, Key, Conversation, UseDefaultSystemPrompts, AllowDataShare, AllowedTools)

            # Append all the files
            for token in cmdResponse:
                # Append the image to the convAssistantFiles
                convAssistantFiles += token["files"]
                
                yield {"response": "\n[IMAGES]\n", "files": token["files"], "ended": False}

            # Remove the command from the response
            fullResponse = fullResponse.replace(line, "[IMAGES]")
        elif (line.lower().startswith("/aud ")):
            # Generate audio command
            # Get the prompt
            cmd = line[5:].strip()

            # Generate the audio and append it to the files
            cmdResponse = __infer__("text2audio", GetAutoIndex("text2audio"), cmd, [], AIArgs, SystemPrompts, Key, Conversation, UseDefaultSystemPrompts, AllowDataShare, AllowedTools)

            # Append all the files
            for token in cmdResponse:
                # Append the audio to the convAssistantFiles
                convAssistantFiles += token["files"]

                yield {"response": "\n[AUDIOS]\n", "files": token["files"], "ended": False}

            # Remove the command from the response
            fullResponse = fullResponse.replace(line, "[AUDIOS]")
        elif (line.lower().startswith("/int ")):
            # Internet (websites, answers, news, chat and maps) search command
            # Get the prompt
            cmd = line[5:].strip()
                    
            # Deserialize the prompt
            try:
                cmd = cfg.JSONDeserializer(cmd)
                cmdP = cmd["prompt"].strip()
                cmdQ = cmd["question"].strip()
                cmdS = cmd["type"].strip()
                
                try:
                    cmdC = int(cmd["count"])

                    if (cmdC > 8):
                        cmdC = 8
                    elif (cmdC <= 0):
                        cmdC = 1
                except:
                    cmdC = 5
            except:
                # Could not deserialize the prompt, ignoring
                continue

            # Generate the image and append it to the files
            cmdResponse = cb.GetResponseFromInternet(Index, cmdP, cmdQ, cmdS, cmdC)
            text = ""

            # Yield another line
            yield {"response": "\n", "files": [], "ended": False}

            for token in cmdResponse:
                text += token["response"]
                yield {"response": token["response"], "files": token["files"], "ended": False}
            
            # Replace lines with spaces
            text = text.replace("\n", " ")

            # Create a memory with the information
            memories.AddMemory(Key["key"], f"Internet: {text}")
        elif (line.lower().startswith("/mem ")):
            # Save memory command
            # Get the prompt
            cmd = line[5:].strip()

            # Save the memory
            memories.AddMemory(Key["key"], cmd)
    
    # Save messages in the conversation if the service is a chatbot
    if (Service == "chatbot"):
        conversation = conv.GetConversationFromUser(Key["key"] if (Key["key"] != None) else "", True)

        conversation.AppendMessageToConversation_User(Conversation, Prompt, Files)
        conversation.AppendMessageToConversation_Assistant(Conversation, fullResponse, convAssistantFiles)

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
        # Try to get the data share
        allowDataShare = Prompt["DataShare"]
    except:
        # If an error occurs, set to default
        allowDataShare = True

    try:
        # Try to get the index of the model to use
        index = Prompt["Index"]
    except:
        # If an error occurs, set to default
        index = -1
    
    try:
        # Try to get the client's public key
        clientPublicKey = Prompt["PublicKey"]
    except:
        # If an error occurs, set to default
        clientPublicKey = None
    
    try:
        # Try to get the allowed tools
        aTools = Prompt["AllowedTools"]
    except:
        # If an error occurs, set to default
        aTools = None
    
    # Check if the API key is banned
    if (key["key"] in banned["key"]):
        yield {"response": "ERROR: Your API key is banned.", "files": [], "ended": True, "pubKey": clientPublicKey}
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
            yield {"response": "WARNING! Processing delayed 2s for security reasons. To avoid this warning, please use a valid API key or set it to empty.\n", "files": [], "ended": False, "pubKey": clientPublicKey}

        # Check index
        if (index < 0):
            # Get index
            index = GetAutoIndex(service)

        # Check the if the index is valid
        try:
            enoughTokens = CheckIfHasEnoughTokens(service, index, key["tokens"])
        except ValueError:
            print(f"Invalid index for service, returning exception. From 0 to {len(cfg.GetAllInfosOfATask(service)) - 1} expected; got {index}.")
            yield {"response": f"ERROR: Invalid index. Expected index to be from 0 to {len(cfg.GetAllInfosOfATask(service)) - 1}; got {index}.", "files": [], "ended": True, "pubKey": clientPublicKey}
            return
        except Exception as ex:
            print(f"[Check enouth tokens: ai_server.py] Unknown error: {ex}")
            yield {"response": f"ERROR: Unknown error checking if you have enouth tokens.", "files": [], "ended": True, "pubKey": clientPublicKey}

        # Check the price and it's a valid key
        if (not enoughTokens and key["key"] != None and cfg.current_data["force_api_key"]):
            # Doesn't have enough tokens or the API key is invalid, return an error
            yield {"response": f"ERROR: Not enough tokens or invalid API key. You need {cfg.GetInfoOfTask(service, index)['price']} tokens, you have {key['tokens']}.", "files": [], "ended": True, "pubKey": clientPublicKey}
            return
        elif (not enoughTokens and key["key"] == None):
            # Invalid API key
            yield {"response": "ERROR: Invalid API key.", "files": [], "ended": True, "pubKey": clientPublicKey}
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
                inf = __infer__(service, index, prompt, files, aiArgs, systemPrompts, key, conversation, useDefSystemPrompts, allowDataShare, aTools)

                # For each token
                for inf_t in inf:
                    inf_t["pubKey"] = clientPublicKey
                    yield inf_t
            else:
                # For each file
                for file in files:
                    # Execute the service with the current file
                    inf = __infer__(service, index, prompt, [file], aiArgs, systemPrompts, key, conversation, useDefSystemPrompts, allowDataShare, aTools)

                    # For each token
                    for inf_t in inf:
                        inf_t["pubKey"] = clientPublicKey
                        yield inf_t
            
            # Return empty response
            yield {"response": "", "files": [], "ended": True, "pubKey": clientPublicKey}
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
            print("Unknown exception found in a service.")
            traceback.print_exc()

            yield {"response": f"ERROR: {ex}", "files": [], "ended": True, "pubKey": clientPublicKey}
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
            conv.GetConversationFromUser(key["key"], True).DeleteConversation(conversation)
        elif (not cfg.current_data["force_api_key"] or MinPriceForService("chatbot") <= 0):
            # The key is not valid, but the server says it's optional, so delete the conversation
            conv.GetConversationFromUser("", True).DeleteConversation(conversation)
        else:
            # The key is invalid and it's required by the server, return an error
            yield {"response": "ERROR: Invalid API key.", "files": [], "ended": True, "pubKey": clientPublicKey}
        
        # Return a message
        yield {"response": "Conversation deleted.", "files": [], "ended": True, "pubKey": clientPublicKey}
    elif (service == "get_all_services"):
        # Get all the available services
        # Return all the services
        yield {"response": json.dumps(cb.GetServicesAndIndexes()), "files": [], "ended": True, "pubKey": clientPublicKey}
    elif (service == "get_conversation"):
        # Get the conversation of the user
        # Check the key
        if (key["key"] == None and len(Prompt["APIKey"]) > 0):
            # Key it's not valid nor empty
            # Wait 2s before processing
            time.sleep(2)

            # Return a warning
            yield {"response": "WARNING! Processing delayed 2s for security reasons. To avoid this warning, please use a valid API key or set it to empty.\n", "files": [], "ended": False, "pubKey": clientPublicKey}
        
        # Check if the key is valid
        if (key["key"] != None and len(key["key"].strip()) > 0):
            # Get the conversation of the key
            cnv = conv.GetConversationFromUser(key["key"], True).Conv[conversation]
        else:
            # Get the conversation from the empty key
            cnv = conv.GetConversationFromUser("", True).Conv[conversation]

        # Return the conversation
        yield {"response": json.dumps(cnv), "files": [], "ended": True, "pubKey": clientPublicKey}
    elif (service == "get_conversations"):
        # Get all the conversations of the user
        # Check the key
        if (key["key"] == None and len(Prompt["APIKey"]) > 0):
            # Key it's not valid nor empty
            # Wait 2s before processing
            time.sleep(2)

            # Return a warning
            yield {"response": "WARNING! Processing delayed 2s for security reasons. To avoid this warning, please use a valid API key or set it to empty.\n", "files": [], "ended": False, "pubKey": clientPublicKey}
        
        # Check if the key is valid
        if (key["key"] != None and len(key["key"].strip()) > 0):
            # Get the conversations of the key
            cnv = list(conv.GetConversationFromUser(key["key"], True).Conv.keys())
        else:
            # Get the conversations from the empty key
            cnv = list(conv.GetConversationFromUser("", True).Conv.keys())

        # Return all the conversations
        yield {"response": json.dumps([cn for cn in cnv]), "files": [], "ended": True, "pubKey": clientPublicKey}
    elif (service == "clear_memories"):
        # Delete all the memories of the user
        # Check the key
        if (key["key"] == None and len(Prompt["APIKey"]) > 0):
            # Key it's not valid nor empty
            # Wait 2s before processing
            time.sleep(2)

            # Return a warning
            yield {"response": "WARNING! Processing delayed 2s for security reasons. To avoid this warning, please use a valid API key or set it to empty.\n", "files": [], "ended": False, "pubKey": clientPublicKey}
        
        # Check if the API key is valid
        if (key["key"] != None and len(key["key"].strip()) > 0):
            # The key is valid, delete the memories
            memories.RemoveMemories(key["key"])
        elif (not cfg.current_data["force_api_key"] or MinPriceForService("chatbot") <= 0):
            # The key is not valid, but the server says it's optional, so delete the memories
            memories.RemoveMemories("")
        else:
            # The key is invalid and it's required by the server, return an error
            yield {"response": "ERROR: Invalid API key.", "files": [], "ended": True, "pubKey": clientPublicKey}
        
        # Return a message
        yield {"response": "Memories deleted.", "files": [], "ended": True, "pubKey": clientPublicKey}
    elif (service == "clear_memory"):
        # Delete a memory of the user
        # Check the key
        if (key["key"] == None and len(Prompt["APIKey"]) > 0):
            # Key it's not valid nor empty
            # Wait 2s before processing
            time.sleep(2)

            # Return a warning
            yield {"response": "WARNING! Processing delayed 2s for security reasons. To avoid this warning, please use a valid API key or set it to empty.\n", "files": [], "ended": False, "pubKey": clientPublicKey}
            
        # Check if the API key is valid
        if (key["key"] != None and len(key["key"].strip()) > 0):
            # The key is valid, delete the memory
            memories.RemoveMemory(key["key"], int(prompt))
        elif (not cfg.current_data["force_api_key"] or MinPriceForService("chatbot") <= 0):
            # The key is not valid, but the server says it's optional, so delete the memory
            memories.RemoveMemory("", int(prompt))
        else:
            # The key is invalid and it's required by the server, return an error
            yield {"response": "ERROR: Invalid API key.", "files": [], "ended": True, "pubKey": clientPublicKey}
        
        # Return a message
        yield {"response": "Memory deleted.", "files": [], "ended": True, "pubKey": clientPublicKey}
    elif (service == "get_memories"):
        # Get all the memories of the user
        # Check the key
        if (key["key"] == None and len(Prompt["APIKey"]) > 0):
            # Key it's not valid nor empty
            # Wait 2s before processing
            time.sleep(2)

            # Return a warning
            yield {"response": "WARNING! Processing delayed 2s for security reasons. To avoid this warning, please use a valid API key or set it to empty.\n", "files": [], "ended": False, "pubKey": clientPublicKey}
        
        # Check if the key is valid
        if (key["key"] != None and len(key["key"].strip()) > 0):
            # Get the memories of the key
            mms = memories.GetMemories(key["key"])
        else:
            # Get the memories from the empty key
            mms = memories.GetMemories("")

        # Return all the memories
        yield {"response": json.dumps(mms), "files": [], "ended": True, "pubKey": clientPublicKey}
    elif (service == "get_queue"):
        # Check index
        if (index < 0):
            # Set index
            index = GetAutoIndex(prompt)

        # Get a queue for a service
        if (len(prompt) > 0):
            queueUsers, queueTime = GetQueueForService(prompt, index)

            print(f"Queue for service '{prompt}:{index}' ==> {queueUsers} users, ~{queueTime}ms/token.")
            yield {"response": json.dumps({"users": queueUsers, "time": queueTime}), "files": [], "ended": True, "pubKey": clientPublicKey}
    elif (service == "get_tos"):
        # Get the Terms of Service of the server
        with open("TOS.txt", "r") as f:
            tos = f.read()
        
        yield {"response": tos, "files": [], "ended": True, "pubKey": clientPublicKey}
    elif (service == "create_key" and key["admin"]):
        # Create a new API key
        keyData = cfg.JSONDeserializer(Prompt)
        keyData = sb.GenerateKey(keyData["tokens"], keyData["daily"])["key"]

        yield {"response": keyData, "files": [], "ended": True, "pubKey": clientPublicKey}
    elif (service == "get_key"):
        # Get information about the key
        keyData = key
        keyData["key"] = "[PRIVATE]"

        yield {"response": json.dumps(keyData), "files": [], "ended": True, "pubKey": clientPublicKey}
    elif (service == "get_service_description"):
        # Get the description of a specific service
        # Get the info from the service
        info = cfg.GetInfoOfTask(prompt, index)

        # Check if contains a description
        if ("description" in list(info.keys())):
            # Contains a description, send it
            yield {"response": info["description"], "files": [], "ended": True, "pubKey": clientPublicKey}
        else:
            # Does not contain a description, send an empty message
            yield {"response": "", "files": [], "ended": True, "pubKey": clientPublicKey}
    elif (service == "is_chatbot_multimodal"):
        # Check if the chatbot is multimodal
        try:
            # Check index
            if (index < 0):
                # Set index
                index = GetAutoIndex("chatbot")

            yield {"response": str(cfg.GetInfoOfTask("chatbot", index)["allows_files"]), "files": [], "ended": True, "pubKey": clientPublicKey}
        except Exception as ex:
            {"response": f"ERROR: {ex}", "files": [], "ended": True, "pubKey": clientPublicKey}
    else:
        yield {"response": "ERROR: Invalid command.", "files": [], "ended": True, "pubKey": clientPublicKey}

async def ExecuteServiceAndSendToClient(Client: websockets.WebSocketClientProtocol, Prompt: dict[str, any], HashAlgorithm: enc.hashes.HashAlgorithm) -> None:
    clPubKey = None
    
    try:
        # Try to execute the service
        for response in ExecuteService(Prompt, Client.remote_address[0]):
            # Get the public key from the response
            clPubKey = response["pubKey"]
            response.pop("pubKey")

            # Send the response
            await __send_to_client__(Client, json.dumps(response).encode("utf-8"), clPubKey, HashAlgorithm)
    except websockets.ConnectionClosedError:
        # Print error
        print("Connection closed while processing!")

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
        try:
            queue[Prompt["Service"]][index] -= 1
        except:
            pass
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
        try:
            queue[Prompt["Service"]][index] -= 1
        except:
            pass

        try:
            # Try to send the closed message
            await __send_to_client__(Client, json.dumps({
                "response": "",
                "files": [],
                "ended": True
            }).encode("utf-8"), clPubKey, HashAlgorithm)
        except:
            # Error, ignore
            pass
    
    # Update the server
    UpdateServer()

async def WaitForReceive(Client: websockets.WebSocketClientProtocol, Message: bytes | str) -> None:
    # Wait for receive
    clientHashType = None

    # Check the length of the received data
    if (len(Message) == 0):
        # Received nothing, close the connection
        Client.close()
        raise websockets.ConnectionClosed(None, None)

    # Print received length
    print(f"Received {len(Message)} bytes from '{Client.remote_address[0]}'")

    # Check for some services
    if ((Message == "get_public_key" and type(Message) is str) or (Message.decode("utf-8") == "get_public_key" and type(Message) is bytes)):
        # Send the public key to the client
        await __send_to_client__(Client, enc.PublicKey.decode("utf-8"), None, None)
        return

    try:
        # Decrypt the message
        for encType in cfg.current_data["allowed_hashes"]:
            try:
                Message = enc.DecryptMessage(Message, enc.__parse_hash__(encType))
                clientHashType = enc.__parse_hash__(encType)

                print(f"Client is using the hash '{encType}'.")

                break
            except:
                continue
        
        # Check if the client hash is valid
        if (clientHashType == None):
            # Invalid hash
            raise ValueError(f"Invalid client hash. The valid hashes are: {cfg.current_data['allowed_hashes']}.")
        
        # Try to deserialize the message
        prompt = cfg.JSONDeserializer(Message)
        
        # Execute service and send data
        await ExecuteServiceAndSendToClient(Client, prompt, clientHashType)
    except Exception as ex:
        # If there's an error, send the response
        try:
            await __send_to_client__(Client, json.dumps({
                "response": "Error. Details: " + str(ex),
                "files": [],
                "ended": True
            }).encode("utf-8"), None, None)
        except:
            pass

async def __send_to_client__(Client: websockets.WebSocketClientProtocol, Message: str | bytes, EncryptKey: bytes | None, HashAlgorithm: enc.hashes.HashAlgorithm | None) -> None:
    # Encrypt the message
    if (EncryptKey is None or HashAlgorithm is None):
        msg = Message
    else:
        msg = enc.EncryptMessage(Message, EncryptKey, HashAlgorithm)

    # Send the message
    await Client.send(msg)

def __receive_thread__(Client: websockets.WebSocketClientProtocol, Message: str | bytes) -> None:
    # Create new event loop
    clientLoop = asyncio.new_event_loop()

    # Run the receive function
    clientLoop.run_until_complete(WaitForReceive(Client, Message))

    # Close the event loop
    clientLoop.close()

async def __receive_loop__(Client: websockets.WebSocketClientProtocol) -> None:
    async for message in Client:
        # Check if the connection ended or if the server is closed
        if (Client.closed or not started):
            # Break the loop
            break

        try:
            # Create and start a new thread
            clientThread = threading.Thread(target = __receive_thread__, args = (Client, message), daemon = True)
            clientThread.start()
        except websockets.ConnectionClosed:
            # Connection closed
            break
        except Exception as ex:
            # Error returned
            print(f"Error executing a prompt of the client. Error: {ex}")

            try:
                # Try to send to the client
                await __send_to_client__(Client, json.dumps({
                    "response": "Error executing service. Details: " + str(ex),
                    "files": [],
                    "ended": True
                }), None, None)

                # Print the error
                print("Error executing service. Traceback:")
                traceback.print_exc()
            except:
                # Print an error
                print("Could not send response to a client.")
        
        # Save the banned IP addresses and keys
        with open("BannedIPs.json", "w+") as f:
            f.write(json.dumps(banned))

async def OnConnect(Client: websockets.WebSocketClientProtocol) -> None:
    print(f"'{Client.remote_address[0]}' has connected.")

    if (Client.remote_address[0] in banned["ip"]):
        try:
            # Print
            print("Banned user. Closing connection.")

            # Send banned message
            await __send_to_client__(Client, json.dumps({
                "response": "Your IP address has been banned. Please contact support if this was a mistake.",
                "files": [],
                "ended": True
            }), None, None)

            # Close the connection
            await Client.close()
            return
        except:
            # Error closing the connection, print
            print("Error closing the connection. Ignoring...")
            return

    # Receive
    await __receive_loop__(Client)

async def StartServer() -> None:
    # Create thread for the cache cleanup
    cacheThread = threading.Thread(target = __clear_cache_loop__)
    cacheThread.start()

    # Create thread for the queue cleanup
    queueThread = threading.Thread(target = __clear_queue_loop__)
    queueThread.start()

    # Create thread for the model offloading
    offloadThread = threading.Thread(target = __offload_loop__)
    offloadThread.start()

    # Set the IP
    ip = "127.0.0.1" if (cfg.current_data["use_local_ip"]) else "0.0.0.0"

    # Start the server
    serverWS = await websockets.serve(OnConnect, ip, 8060, max_size = None, ping_interval = 60, ping_timeout = 30)
    await serverWS.wait_closed()

# Start the server
serverLoop = asyncio.new_event_loop()

try:
    # Generate public and private keys
    enc.__create_keys__()

    # Try to set the banned IPs
    if (os.path.exists("BannedIPs.json")):
        with open("BannedIPs.json", "r") as f:
            banned = cfg.JSONDeserializer(f.read())

    # Load all the models
    cb.LoadAllModels()

    # Try to start the server
    print("Server started!")
    started = True

    serverLoop.run_until_complete(StartServer())
    serverLoop.close()
except KeyboardInterrupt:
    print("\nClosing server...")

    # Save the configuration
    cfg.SaveConfig(cfg.current_data)

    # Save the conversations
    conv.SaveConversations()

    # Stop the DB
    sb.StopDB()

    # Delete the cache
    cb.EmptyCache()

    # Close
    started = False
    os._exit(0)
except Exception as ex:
    print("ERROR! Running traceback.\n\n")
    traceback.print_exc()