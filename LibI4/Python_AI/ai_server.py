from collections.abc import Iterator
from websockets.asyncio.server import serve, ServerConnection
from websockets.exceptions import ConnectionClosed, ConnectionClosedError, ConnectionClosedOK
import asyncio
import threading
import os
import json
import datetime
import time
import traceback
import gc
import base64
import ssl

try:
    # Try to import I4.0 utilities
    import server_basics as sb
    import encryption as enc
    import chatbot_all as cb
    import ai_config as cfg
    import conversation_multimodal as conv
    import ai_memory as memories
    import queue_system as qs
    import temporal_files as temp
    import data_save as ds
    import documents as docs
except ImportError:
    # Error importing utilities
    traceback.print_exc()
    print("Error importing I4.0 utilities, please make sure that your workdir is '/path/to/I4.0/LibI4/Python_AI/'.")

    os._exit(1)

# Variables
banned: dict[str, list[str]] = {
    "ip": [],
    "key": []
}
started: bool = False
modelsUsed: dict[str, list[int]] = {}
ServerVersion: int = 150100

# Server sockets
serverWS: serve | None = None

# Keys
ServerPublicKey: bytes | None = None
ServerPrivateKey: bytes | None = None

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
        qs.Clear()

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
        cb.OffloadAll(modelsUsed, False)
        modelsUsed.clear()

        # IMPORTANT!!! Make sure that the offload_time is greater than the time that takes the model to generate a token.
        # Otherwise, the server may freeze and crash.

        # Run the garbage collector
        gc.collect()

def __clear_temporal_conversations_loop__() -> None:
    # Check if clear temporal conversations time is less or equal to 0
    if (cfg.current_data["clear_temporal_conversations_time"] <= 0):
        # Do not clear the temporal conversations
        return
    
    # While the server is running
    while (started):
        # Wait the specified time
        time.sleep(cfg.current_data["clear_temporal_conversations_time"])

        # Clear all the temporal conversations
        conv.ClearTemporalConversations()

def SaveOldData() -> None:
    # Print
    if (os.path.exists("API/") or os.path.exists("Conversations/") or os.path.exists("memories.json")):
        print("Saving old data into the DB.")

    # Check if the API directory exists
    if (os.path.exists("API/")):
        # Create API errors variable
        aerrs = 0

        # For each key file
        for file in os.listdir("API/"):
            # Open stream
            f = open(f"API/{file}", "r")

            try:
                # Parse the JSON
                key = cfg.JSONDeserializer(f.read())

                # Try to save the key
                sb.SaveKey(key)
            except Exception as ex:
                # Error parsing the JSON, continue with the next file
                print(f"Error parsing key file '{file}'. Ignoring. Error: {ex}")

                # Add API error
                aerrs += 1

                # Continue
                continue
            
            # Close the stream
            f.close()

            # Remove the file
            os.remove(f"API/{file}")
        
        # Check if any API errors occurred
        if (aerrs == 0):
            # No API errors occurred, delete directory
            os.rmdir("API/")
    
    # Check if the conversations directory exists
    if (os.path.exists("Conversations/")):
        # Create conversation errors variable
        cerrs = 0

        # For each key file
        for file in os.listdir("Conversations/"):
            # Open stream
            f = open(f"Conversations/{file}", "r")

            try:
                # Parse the JSON
                convers = cfg.JSONDeserializer(f.read())

                # Try to save the conversations
                conv.SaveConversation(convers["User"], convers["Conv"], None)
            except Exception as ex:
                # Error parsing the JSON, continue with the next file
                print(f"Error parsing conversation file '{file}'. Ignoring. Error: {ex}")
                
                # Add conversation error
                cerrs += 1

                # Continue
                continue
            
            # Close the stream
            f.close()

            # Remove the file
            os.remove(f"Conversations/{file}")
        
        # Check if any conversation errors occurred
        if (cerrs == 0):
            # No conversation errors occurred, delete directory
            os.rmdir("Conversations/")
    
    # Check if the memories file exists
    if (os.path.exists("memories.json")):
        # Create memory errors variable
        merrs = 0

        # Open stream
        f = open("memories.json", "r")

        try:
            # Parse the JSON
            mems = cfg.JSONDeserializer(f.read())

            # Try to save the memories
            memories.SaveMemory("", mems)
        except Exception as ex:
            # Error parsing the JSON, continue with the next file
            print(f"Error parsing memories file. Ignoring. Error: {ex}")

            # Add memory error
            merrs += 1
        
        f.close()

        # Check if any memory errors occurred
        if (merrs == 0):
            # No memory errors occurred, delete file
            os.remove("memories.json")

def CheckFiles() -> None:
    # Check if some files exists
    if (not os.path.exists("Logs/")):
        os.mkdir("Logs/")
    
    if (not os.path.exists("TOS.txt")):
        with open("TOS.txt", "w") as f:
            f.write("")

def GetQueueForService(Service: str, Index: int) -> tuple[int, int]:
    # Get the users for the queue
    users = qs.GetUsersFromQueue(Service, Index)
    
    # Calculate the predicted time
    t = qs.GetAllTimes(Service, Index, True)
    
    return (users, t)

def __infer__(
        Service: str,
        Index: int,
        Prompt: str,
        Files: list[dict[str, str]],
        AIArgs: str | None,
        SystemPrompts: str | list[str],
        Key: dict[str, any],
        Conversation: str,
        UseDefaultSystemPrompts: bool | tuple[bool, bool] | list[bool] | None,
        AllowedTools: str | list[str] | None,
        ExtraTools: list[dict[str, str | dict[str, any]]],
        MaxLength: int | None,
        Temperature: float | None,
        TopP: float | None,
        TopK: int | None,
        MinP: float | None,
        TypicalP: float | None,
        SeeTools: bool,
        DataSave: bool
    ) -> Iterator[dict[str, any]]:
    # Check service and files length
    if (Service != "chatbot" and len(Files) > 1):
        raise ValueError("Please, upload only a file per request unless you're using a chatbot.")

    # Copy the key
    Key = Key.copy()

    # Check if the key is None
    if (Key["key"] is None):
        # Replace with an empty string
        Key["key"] = ""

    # Wait for the queue to be valid
    while (GetQueueForService(Service, Index)[0] >= 1):
        # Sleep 1s
        time.sleep(1)

    # Add to the queue
    qs.AddUserToQueue(Service, Index)

    # Create copy of the files
    fs = []
    
    for f in Files:
        fs.append(f.copy())
    
    # Remove tokens
    Key["tokens"] -= cfg.GetInfoOfTask(Service, Index)["price"]
    
    # Save the key if the key is not None
    if (len(Key["key"]) > 0):
        sb.SaveKey(Key)

    # Add the index to the models used
    try:
        modelsUsed[Service].append(Index)
    except:
        modelsUsed[Service] = [Index]
    
    # Print processing message
    print(f"Processing prompt at {Service}:{Index}", flush = True)

    # Process the prompt and get a response
    response = cb.MakePrompt(
        Index,
        Prompt,
        fs,
        Service,
        AIArgs,
        SystemPrompts,
        [Key["key"], Conversation],
        UseDefaultSystemPrompts,
        AllowedTools,
        ExtraTools,
        MaxLength,
        Temperature,
        TopP,
        TopK,
        MinP,
        TypicalP
    )
    fullResponse = ""
    responseFiles = []
    tools = []
    tempTool = ""
    firstToken = True

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

        # Set token variables
        fullResponse += token["response"]
        responseFiles += token["files"]
        token["ended"] = False
        token["errors"] = []

        # Add the timer to the service if it's not the first token
        if (not firstToken or Service != "chatbot"):
            # Set the timer and transform to milliseconds
            timerMs = int((time.time() - timer) * 1000)

            # Add the timer to the service
            qs.AddNewTime(Service, Index, timerMs)
        
        # Restart the timer
        timer = time.time()
        firstToken = False

        # Check if the chatbot is using a tool
        if (token["response"].strip() == "<tool_call>" or len(tempTool) > 0):
            tempTool += token["response"]

            if (token["response"] == "</tool_call>"):
                tools.append(tempTool)
                tempTool = ""
            
            if (SeeTools):
                yield token
            
            continue

        # Yield the token
        yield token
    
    # Delete the timer
    timer = None

    # Strip the full response
    fullResponse = fullResponse.strip()
    convAssistantFiles = []

    # For each tool used
    for toolStr in tools:
        # Remove special tokens
        toolStrCut = toolStr.strip()

        while (toolStrCut.startswith("<tool_call>")):
            toolStrCut = toolStrCut[11:]
        
        while (toolStrCut.endswith("</tool_call>")):
            toolStrCut = toolStrCut[:-12]

        # Parse the JSON
        try:
            tool = cfg.JSONDeserializer(toolStrCut)
        except:
            continue

        if (tool["name"] == "image_generation"):
            # Generate image tool
            # Get the index
            index = GetAutoIndex("text2img", -2)

            # Check if the user has enough tokens
            enoughTokens = CheckIfHasEnoughTokens("text2img", index, Key["tokens"])

            if (not enoughTokens):
                yield {"response": "", "files": [], "ended": False, "errors": [f"Not enough tokens. You need {cfg.GetInfoOfTask('text2img', Index)['price']} tokens, you have {Key['tokens']}. This tool will not be executed."]}
                continue

            # Get the prompt
            pr = tool["arguments"]["prompt"]
            npr = tool["arguments"]["negative_prompt"]

            # Generate the image and append it to the files
            toolResponse = __infer__(
                "text2img",
                index,
                json.dumps({
                    "prompt": pr,
                    "negative_prompt": npr
                }),
                [],
                AIArgs,
                SystemPrompts,
                Key,
                Conversation,
                UseDefaultSystemPrompts,
                AllowedTools,
                ExtraTools,
                MaxLength,
                Temperature,
                TopP,
                TopK,
                MinP,
                TypicalP,
                SeeTools,
                DataSave
            )

            # Append all the files
            for token in toolResponse:
                # Append the image to the convAssistantFiles
                convAssistantFiles += token["files"]
                
                yield {"response": "", "files": token["files"], "ended": False, "errors": []}
        elif (tool["name"] == "audio_generation"):
            # Generate audio tool
            # Get the index
            index = GetAutoIndex("text2audio", -2)

            # Check if the user has enough tokens
            enoughTokens = CheckIfHasEnoughTokens("text2audio", index, Key["tokens"])

            if (not enoughTokens):
                yield {"response": "", "files": [], "ended": False, "errors": [f"Not enough tokens. You need {cfg.GetInfoOfTask('text2audio', Index)['price']} tokens, you have {Key['tokens']}. This tool will not be executed."]}
                continue

            # Get the prompt
            pr = tool["arguments"]["prompt"]

            # Generate the audio and append it to the files
            toolResponse = __infer__(
                "text2audio",
                index,
                pr,
                [],
                AIArgs,
                SystemPrompts,
                Key,
                Conversation,
                UseDefaultSystemPrompts,
                AllowedTools,
                ExtraTools,
                MaxLength,
                Temperature,
                TopP,
                TopK,
                MinP,
                TypicalP,
                SeeTools,
                DataSave
            )

            # Append all the files
            for token in toolResponse:
                # Append the audio to the convAssistantFiles
                convAssistantFiles += token["files"]

                yield {"response": "", "files": token["files"], "ended": False, "errors": []}
        elif (tool["name"] == "internet_search"):
            # Internet search tool
            # Check if the user has enough tokens
            enoughTokens = CheckIfHasEnoughTokens("chatbot", Index, Key["tokens"])

            if (not enoughTokens):
                yield {"response": "", "files": [], "ended": False, "errors": [f"Not enough tokens. You need {cfg.GetInfoOfTask('chatbot', Index)['price']} tokens, you have {Key['tokens']}. This tool will not be executed."]}
                continue

            # Remove the tokens from the key
            Key["tokens"] -= cfg.GetInfoOfTask("chatbot", Index)["price"]

            # Save the key if the key is not None
            if (len(Key["key"]) > 0):
                sb.SaveKey(Key)

            # Get the variables
            keywords = tool["arguments"]["keywords"]
            internetPrompt = tool["arguments"]["prompt"] if ("prompt" in tool["arguments"]) else Prompt
            searchCount = tool["arguments"]["count"] if ("count" in tool["arguments"]) else -1
            
            # Check if the search count is valid
            if (searchCount > cfg.current_data["internet"]["max_results"]):
                searchCount = cfg.current_data["internet"]["max_results"]
            elif (searchCount < cfg.current_data["internet"]["min_results"]):
                searchCount = cfg.current_data["internet"]["min_results"]

            # Get the response from internet
            toolResponse = cb.GetResponseFromInternet(
                Index,
                keywords,
                internetPrompt,
                searchCount,
                AIArgs,
                SystemPrompts,
                UseDefaultSystemPrompts,
                [Key["key"], Conversation],
                MaxLength,
                Temperature,
                TopP,
                TopK,
                MinP,
                TypicalP
            )
            text = ""

            # Yield another line
            yield {"response": "\n", "files": [], "ended": False, "errors": []}

            # Save and yield the tokens
            for token in toolResponse:
                text += token["response"]
                yield {"response": token["response"], "files": token["files"], "ended": False, "errors": []}
            
            # Remove CoT from the response
            while (text.count("<think>") > 0 and text.count("</think>") > 0):
                text = text[text.index("</think>") + 8:].strip()
            
            # Add a response to the tool
            fullResponse = fullResponse.replace(toolStr, f"{toolStr}\n<tool_response>\n{text}\n</tool_response>")
        elif (tool["name"] == "internet_url"):
            # Internet search tool (using URLs)
            # Check if the user has enough tokens
            enoughTokens = CheckIfHasEnoughTokens("chatbot", Index, Key["tokens"])

            if (not enoughTokens):
                yield {"response": "", "files": [], "ended": False, "errors": [f"Not enough tokens. You need {cfg.GetInfoOfTask('chatbot', Index)['price']} tokens, you have {Key['tokens']}. This tool will not be executed."]}
                continue

            # Remove the tokens from the key
            Key["tokens"] -= cfg.GetInfoOfTask("chatbot", Index)["price"]

            # Save the key if the key is not None
            if (len(Key["key"]) > 0):
                sb.SaveKey(Key)

            # Get the variables
            urls = tool["arguments"]["urls"]
            internetPrompt = tool["arguments"]["prompt"] if ("prompt" in tool["arguments"]) else Prompt

            # Convert URL to a string if it's only one
            if (len(urls) == 1):
                urls = urls[0]

            # Get the response from internet
            toolResponse = cb.GetResponseFromInternet_URL(
                Index,
                urls,
                internetPrompt,
                AIArgs,
                SystemPrompts,
                UseDefaultSystemPrompts,
                [Key["key"], Conversation],
                MaxLength,
                Temperature,
                TopP,
                TopK,
                MinP,
                TypicalP
            )
            text = ""

            # Yield another line
            yield {"response": "\n", "files": [], "ended": False, "errors": []}

            # Save and yield the tokens
            for token in toolResponse:
                text += token["response"]
                yield {"response": token["response"], "files": token["files"], "ended": False, "errors": []}
            
            # Remove CoT from the response
            while (text.count("<think>") > 0 and text.count("</think>") > 0):
                text = text[text.index("</think>") + 8:].strip()
            
            # Add a response to the tool
            fullResponse = fullResponse.replace(toolStr, f"{toolStr}\n<tool_response>\n{text}\n</tool_response>")
        elif (tool["name"] == "internet_research"):
            # Internet research tool
            # Check if the user has enough tokens
            price = cfg.GetInfoOfTask("chatbot", Index)["price"] * (cfg.current_data["internet"]["max_results"] + 1) + cfg.current_data["internet"]["research"]["price"]
            enoughTokens = Key["tokens"] >= price

            if (not enoughTokens):
                yield {"response": "", "files": [], "ended": False, "errors": [f"Not enough tokens. You need {price} tokens, you have {Key['tokens']}. This tool will not be executed."]}
                continue

            # Remove the tokens from the key
            Key["tokens"] -= price

            # Save the key if the key is not None
            if (len(Key["key"]) > 0):
                sb.SaveKey(Key)

            # Get the variables
            keywords = tool["arguments"]["keywords"]
            internetPrompt = tool["arguments"]["prompt"] if ("prompt" in tool["arguments"]) else Prompt

            # Yield another line
            yield {"response": "\n", "files": [], "ended": False, "errors": []}

            # Get the response from internet
            toolResponse = cb.InternetResearch(
                Index,
                keywords,
                internetPrompt,
                AIArgs,
                SystemPrompts,
                UseDefaultSystemPrompts,
                [Key["key"], Conversation],
                MaxLength,
                Temperature,
                TopP,
                TopK,
                MinP,
                TypicalP
            )
            text = ""

            # Yield another line
            yield {"response": "\n", "files": [], "ended": False, "errors": []}

            # Save and yield the tokens
            for token in toolResponse:
                text += token["response"]
                yield {"response": token["response"], "files": token["files"], "ended": False, "errors": []}
            
            # Remove CoT from the response
            while (text.count("<think>") > 0 and text.count("</think>") > 0):
                text = text[text.index("</think>") + 8:].strip()
            
            # Add a response to the tool
            fullResponse = fullResponse.replace(toolStr, f"{toolStr}\n<tool_response>\n{text}\n</tool_response>")
        elif (tool["name"] == "save_memory"):
            # Save memory tool
            # Get the prompt
            mem = tool["arguments"]["content"]

            # Save the memory
            memories.SaveMemory(Key["key"], mem)
        elif (tool["name"] == "edit_memory"):
            # Edit memory tool
            # Get the ID and new memory
            memID = tool["arguments"]["memory_id"]
            newMem = tool["arguments"]["new_content"]

            # Delete the previous memory
            memories.DeleteMemory(Key["key"], memories.GetMemory(Key["key"], memID))

            # Create a new memory
            memories.SaveMemory(Key["key"], newMem)
        elif (tool["name"] == "delete_memory"):
            # Delete memory tool
            # Get the memory ID
            memID = tool["arguments"]["memory_id"]

            # Delete the memory
            memories.DeleteMemory(Key["key"], memories.GetMemory(Key["key"], memID))
        elif (tool["name"] == "document_creator"):
            # Create a document tool
            # Get the content of the document and document type
            fileCode = tool["arguments"]["content"]
            documentType = tool["arguments"]["document_type"].lower().strip()

            # Check the document type and create the document
            try:
                if (documentType == "html2pdf"):
                    document = docs.HTML2PDF(fileCode)
                    documentType = "pdf"
                elif (documentType == "html2docx"):
                    document = docs.HTML2DOCX(fileCode)
                    documentType = "docx"
                elif (documentType == "csv2xlsx"):
                    document = docs.CSV2XLSX(fileCode)
                    documentType = "xlsx"
                else:
                    raise ValueError("Invalid document type.")
            except Exception as ex:
                yield {"response": "", "files": [], "ended": False, "errors": [f"Error using tool. Details: {ex}"]}
            
            # Convert to base64
            document = base64.b64encode(document).decode("utf-8")

            # Send message
            yield {"response": "", "files": [{"type": documentType, "data": document}], "ended": False, "errors": []}
        else:
            # Unknown tool. Send to the client
            yield {"response": json.dumps(tool), "files": [], "ended": False, "errors": ["unknown tool"]}
    
    # Save messages in the conversation if the service is a chatbot
    if (Service == "chatbot"):
        conversation = conv.GetConversation(Key["key"], Conversation)
        uFiles = []
        aFiles = []

        if (cfg.current_data["save_conversation_files"]):
            for f in Files:
                uFiles.append({"type": f["type"], f["type"]: f["data"]})
            
            for f in convAssistantFiles:
                aFiles.append({"type": f["type"], f["type"]: f["data"]})

        conversation.append({
            "role": "user",
            "content": uFiles + [
                {"type": "text", "text": Prompt}
            ]
        })
        conversation.append({
            "role": "assistant",
            "content": aFiles + [
                {"type": "text", "text": fullResponse}
            ]
        })

        conv.SaveConversation(Key["key"], (Conversation, conversation), Key["temporal_conversations"])
    
    # Save the data into the DB if allowed by the user
    if (DataSave and cfg.current_data["allow_data_save"]):
        uFiles = []
        aFiles = []

        if (len("".join(f["data"] for f in Files)) + len("".join(f["data"] for f in convAssistantFiles)) <= cfg.current_data["data_save_max_fs"] * 1024 * 1024):
            for f in Files:
                uFiles.append({"type": f["type"], f["type"]: f["data"]})
                
            for f in convAssistantFiles:
                aFiles.append({"type": f["type"], f["type"]: f["data"]})

        ds.SaveData(
            uFiles + [{"type": "text", "text": Prompt}],
            aFiles + [{"type": "text", "text": fullResponse}]
        )

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

def GetAutoIndex(Service: str, IndexMode: int) -> int:
    try:
        # Get the length of the service
        length = cb.GetServicesAndIndexes()[Service]

        # Check the length
        if (length == 0):
            raise Exception("Length of the services is 0.")
        
        # Add all the indexes
        for idx in range(length):
            qs.__add_to_queue__(Service, idx)

        # Check index mode
        if (IndexMode == -1):
            # Return the index with the smallest queue
            return qs.GetIndexFromQueue_Filter(Service, 1)
        elif (IndexMode == -2):
            # Create the prices list
            prices = []

            # For each index
            for idx in range(length):
                # Get the price of that idx
                idxPrice = cfg.GetInfoOfTask(Service, idx)["price"]

                # Append the price into the list
                prices.append(idxPrice)

            # Return the cheapest index
            return prices.index(min(prices))
        
        # Return the cheapest model by default
        return GetAutoIndex(Service, -2)
    except Exception as ex:
        # Return an error saying the service is not available
        traceback.print_exception(ex)
        raise Exception("Service not available.")

def ExecuteService(Prompt: dict[str, any], IPAddress: str) -> Iterator[dict[str, any]]:
    # Get some required variables
    service = str(Prompt["Service"])

    try:
        # Try to get the key
        key = sb.GetKey(Prompt["APIKey"])

        try:
            # Check if the API key is daily-updated
            if (str(key["daily"]).lower() == "true" or str(key["daily"]) == "1"):
                # If it is, calculate the time that has passed (minute-precise)
                date = datetime.datetime.now()
                key_date = datetime.datetime(
                    int(key["date"]["year"]),
                    int(key["date"]["month"]),
                    int(key["date"]["day"]),
                    int(key["date"]["hour"]),
                    int(key["date"]["minute"]))
                date_diff = date - key_date

                # If a day or more has passed since the last use of the key, reset the tokens and the day
                if (date_diff.total_seconds() >= 86400 and key["tokens"] < key["default"]["tokens"]):
                    key["tokens"] = key["default"]["tokens"]
                    key["date"] = sb.__get_current_datetime__()

                # Save the key
                sb.SaveKey(key)
        except Exception as ex:
            # Print the exception if something went wrong
            print("Error on API Key '" + str(key["key"]) + "': " + str(ex))
    except Exception as ex:
        # Could not get the key, create empty key
        print(f"Could not get client key. Reason: {ex}")
        key = {"tokens": 0, "key": None, "admin": False, "temporal_conversations": cfg.current_data["nokey_temporal_conversations"]}
    
    # Get other variables
    try:
        # Try to get the client's public key
        clientPublicKey = str(Prompt["PublicKey"])
    except:
        # If an error occurs, set to default
        clientPublicKey = None

    try:
        # Try to get conversation
        conversation = str(Prompt["Conversation"])
    except:
        # If an error occurs, set to default
        conversation = "default"
    
    try:
        # Try to get the prompt and files
        prompt = str(Prompt["Prompt"])
        files = list(Prompt["Files"])
    except Exception as ex:
        # If any of this variables is missing, return an error
        yield {"response": f"", "files": [], "ended": True, "errors": [f"missing variables. Details: {ex}"], "pubKey": clientPublicKey}
        
    try:
        # Try to get AI args
        aiArgs = Prompt["AIArgs"]
    except:
        # If an error occurs, set to default
        aiArgs = None
    
    try:
        # Try to get extra system prompts
        if (isinstance(Prompt["SystemPrompts"], list)):
            systemPrompts = Prompt["SystemPrompts"]
        else:
            systemPrompts = [str(Prompt["SystemPrompts"])]
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
        # Try to get the index of the model to use
        index = int(Prompt["Index"])
    except:
        # If an error occurs, set to default
        index = -2
    
    try:
        # Try to get the allowed tools
        aTools = Prompt["AllowedTools"]
    except:
        # If an error occurs, set to default
        aTools = None
    
    try:
        # Try to get the extra tools
        eTools = Prompt["ExtraTools"]
    except:
        # If an error occurs, set to default
        eTools = []
    
    try:
        # Try to get the max length
        maxLength = int(Prompt["MaxLength"])
    except:
        # If an error occurs, set to default
        maxLength = None
    
    try:
        # Try to get the temperature
        temperature = float(Prompt["Temperature"])
    except:
        # If an error occurs, set to default
        temperature = None
    
    try:
        # Try to get the see tools
        seeTools = Prompt["SeeTools"]
    except:
        # If an error occurs, set to default
        seeTools = False
    
    try:
        # Try to get the data save
        dataSave = Prompt["AllowDataSave"]
    except:
        # If an error occurs, set to default
        dataSave = True
    
    try:
        # Try to get top_p
        top_p = float(Prompt["TopP"])
    except:
        # If an error occurs, set to default
        top_p = None
    
    try:
        # Try to get top_k
        top_k = int(Prompt["TopK"])
    except:
        # If an error occurs, set to default
        top_k = None
    
    try:
        # Try to get min_p
        min_p = float(Prompt["MinP"])
    except:
        # If an error occurs, set to default
        min_p = None
    
    try:
        # Try to get typical_p
        typical_p = float(Prompt["TypicalP"])
    except:
        # If an error occurs, set to default
        typical_p = None
    
    # Check if the API key is banned
    if (key["key"] in banned["key"]):
        yield {"response": "", "files": [], "ended": True, "errors": ["API key banned"], "pubKey": clientPublicKey}
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
            yield {"response": "", "files": [], "ended": False, "errors": ["WARNING! Processing delayed 2s for security reasons. To avoid this warning, please use a valid API key or set it to empty."], "pubKey": clientPublicKey}

        # Check index
        if (index < 0):
            # Get index
            index = GetAutoIndex(service, index)
            Prompt["Index"] = index

        # Check the if the index is valid
        try:
            enoughTokens = CheckIfHasEnoughTokens(service, index, key["tokens"])
        except ValueError:
            print(f"Invalid index for service, returning exception. From 0 to {len(cfg.GetAllInfosOfATask(service)) - 1} expected; got {index}.")
            yield {"response": "", "files": [], "ended": True, "errors": [f"Invalid index. Expected index to be from 0 to {len(cfg.GetAllInfosOfATask(service)) - 1}; got {index}."], "pubKey": clientPublicKey}
            return
        except Exception as ex:
            print(f"[Check enough tokens: ai_server.py] Unknown error: {ex}")
            yield {"response": "", "files": [], "ended": True, "errors": [f"Unknown error while checking if you had enough tokens."], "pubKey": clientPublicKey}

        # Check the price and it's a valid key
        if (not enoughTokens and key["key"] != None and cfg.current_data["force_api_key"]):
            # Doesn't have enough tokens or the API key is invalid, return an error
            yield {"response": "", "files": [], "ended": True, "errors": [f"Not enough tokens. You need {cfg.GetInfoOfTask(service, index)['price']} tokens, you have {key['tokens']}."], "pubKey": clientPublicKey}
            return
        elif (not enoughTokens and key["key"] == None):
            # Invalid API key
            yield {"response": "", "files": [], "ended": True, "errors": ["Invalid API key."], "pubKey": clientPublicKey}
            return
        
        # Check if the key is an admin
        if (key["admin"]):
            # It is, apply admin system prompts to the extra messages
            systemPrompts.append(cfg.current_data["custom_api_admin_system_messages"])
        else:
            # It isn't, apply not admin system prompts to the extra messages
            systemPrompts.append(cfg.current_data["custom_api_nadmin_system_messages"])
        
        # Set done in the prompt
        Prompt["Done"] = False
        
        try:
            # Execute the service with all the files
            inf = __infer__(
                service,
                index,
                prompt,
                files,
                aiArgs,
                systemPrompts,
                key,
                conversation,
                useDefSystemPrompts,
                aTools,
                eTools,
                maxLength,
                temperature,
                top_p,
                top_k,
                min_p,
                typical_p,
                seeTools,
                dataSave
            )

            # For each token
            for inf_t in inf:
                inf_t["pubKey"] = clientPublicKey
                yield inf_t
            
            # Clear
            inf = None

            # Remove the user from the queue
            qs.RemoveUserFromQueue(service, index)

            # Return empty response
            yield {"response": "", "files": [], "ended": True, "errors": [], "pubKey": clientPublicKey}
        except Exception as ex:
            if (str(ex).lower() == "nsfw detected!"):
                # NSFW detected, check if the server should ban the API key
                if (cfg.current_data["ban_if_nsfw"] and cfg.current_data["force_api_key"] and key["key"] is not None):
                    # Ban the API key
                    banned["key"].append(key["key"])
                
                # Check if the server should ban the IP address
                if (cfg.current_data["ban_if_nsfw_ip"] and IPAddress != "127.0.0.1"):
                    # Ban the IP address
                    banned["ip"].append(IPAddress)
            elif (key["key"] is None):
                # Check if the server should ban the IP address
                if (cfg.current_data["ban_if_nsfw_ip"] and IPAddress != "127.0.0.1"):
                    # Ban the IP address
                    banned["ip"].append(IPAddress)
            
            # Remove the user from the queue
            qs.RemoveUserFromQueue(service, index)
            
            # Return the exception
            print("Unknown exception found in a service.")
            traceback.print_exception(ex)

            yield {"response": "", "files": [], "ended": True, "errors": [f"Unknown error: {ex}"], "pubKey": clientPublicKey}
        
        # Set done in the prompt
        Prompt["Done"] = True

        # Save the banned IP addresses and keys
        with open("BannedIPs.json", "w+") as f:
            f.write(json.dumps(banned))
    elif (service == "clear_my_history" or service == "clear_conversation"):
        # Clear the conversation
        # Check the key
        if (key["key"] == None and len(Prompt["APIKey"]) > 0):
            # Key it's not valid nor empty
            # Wait 2s before processing
            time.sleep(2)

            # Return a warning
            yield {"response": "", "files": [], "ended": False, "errors": ["WARNING! Processing delayed 2s for security reasons. To avoid this warning, please use a valid API key or set it to empty."], "pubKey": clientPublicKey}

        # Check if the API key is valid
        if (key["key"] != None and len(key["key"].strip()) > 0):
            # The key is valid, delete the conversation
            conv.DeleteConversation(key["key"], conversation)
        elif (not cfg.current_data["force_api_key"] or MinPriceForService("chatbot") <= 0):
            # The key is not valid, but the server says it's optional, so delete the conversation
            conv.DeleteConversation("", conversation)
        else:
            # The key is invalid and it's required by the server, return an error
            yield {"response": "", "files": [], "ended": True, "errors": ["Invalid API key."], "pubKey": clientPublicKey}
        
        # Return a message
        yield {"response": "Conversation deleted.", "files": [], "ended": True, "errors": [], "pubKey": clientPublicKey}
    elif (service == "get_all_services"):
        # Get all the available services
        # Return all the services
        yield {"response": json.dumps(cb.GetServicesAndIndexes()), "files": [], "ended": True, "errors": [], "pubKey": clientPublicKey}
    elif (service == "get_conversation"):
        # Get the conversation of the user
        # Check the key
        if (key["key"] == None and len(Prompt["APIKey"]) > 0):
            # Key it's not valid nor empty
            # Wait 2s before processing
            time.sleep(2)

            # Return a warning
            yield {"response": "", "files": [], "ended": False, "errors": ["WARNING! Processing delayed 2s for security reasons. To avoid this warning, please use a valid API key or set it to empty."], "pubKey": clientPublicKey}
        
        # Check if the key is valid
        if (key["key"] != None and len(key["key"].strip()) > 0):
            # Get the conversation of the key
            cnv = conv.GetConversation(key["key"], conversation)
        else:
            # Get the conversation from the empty key
            cnv = conv.GetConversation("", conversation)

        # Return the conversation
        yield {"response": json.dumps(cnv), "files": [], "ended": True, "errors": [], "pubKey": clientPublicKey}
    elif (service == "get_conversations"):
        # Get all the conversations of the user
        # Check the key
        if (key["key"] == None and len(Prompt["APIKey"]) > 0):
            # Key it's not valid nor empty
            # Wait 2s before processing
            time.sleep(2)

            # Return a warning
            yield {"response": "", "files": [], "ended": False, "errors": ["WARNING! Processing delayed 2s for security reasons. To avoid this warning, please use a valid API key or set it to empty."], "pubKey": clientPublicKey}
        
        # Check if the key is valid
        if (key["key"] != None and len(key["key"].strip()) > 0):
            # Get the conversations of the key
            cnv = list(conv.GetConversations(key["key"]).keys())
        else:
            # Get the conversations from the empty key
            cnv = list(conv.GetConversations("").keys())

        # Return all the conversations
        yield {"response": json.dumps([cn for cn in cnv]), "files": [], "ended": True, "errors": [], "pubKey": clientPublicKey}
    elif (service == "clear_memories"):
        # Delete all the memories of the user
        # Check the key
        if (key["key"] == None and len(Prompt["APIKey"]) > 0):
            # Key it's not valid nor empty
            # Wait 2s before processing
            time.sleep(2)

            # Return a warning
            yield {"response": "", "files": [], "ended": False, "errors": ["WARNING! Processing delayed 2s for security reasons. To avoid this warning, please use a valid API key or set it to empty."], "pubKey": clientPublicKey}
        
        # Check if the API key is valid
        if (key["key"] != None and len(key["key"].strip()) > 0):
            # The key is valid, delete the memories
            memories.DeleteMemories(key["key"])
        elif (not cfg.current_data["force_api_key"] or MinPriceForService("chatbot") <= 0):
            # The key is not valid, but the server says it's optional, so delete the memories
            memories.DeleteMemories("")
        else:
            # The key is invalid and it's required by the server, return an error
            yield {"response": "", "files": [], "ended": True, "errors": ["Invalid API key."], "pubKey": clientPublicKey}
        
        # Return a message
        yield {"response": "Memories deleted.", "files": [], "ended": True, "errors": [], "pubKey": clientPublicKey}
    elif (service == "clear_memory"):
        # Delete a memory of the user
        # Check the key
        if (key["key"] == None and len(Prompt["APIKey"]) > 0):
            # Key it's not valid nor empty
            # Wait 2s before processing
            time.sleep(2)

            # Return a warning
            yield {"response": "", "files": [], "ended": False, "errors": ["WARNING! Processing delayed 2s for security reasons. To avoid this warning, please use a valid API key or set it to empty."], "pubKey": clientPublicKey}
            
        # Check if the API key is valid
        if (key["key"] != None and len(key["key"].strip()) > 0):
            # The key is valid, delete the memory
            memories.DeleteMemory(key["key"], int(prompt))
        elif (not cfg.current_data["force_api_key"] or MinPriceForService("chatbot") <= 0):
            # The key is not valid, but the server says it's optional, so delete the memory
            memories.DeleteMemory("", int(prompt))
        else:
            # The key is invalid and it's required by the server, return an error
            yield {"response": "", "files": [], "ended": True, "errors": ["Invalid API key."], "pubKey": clientPublicKey}
        
        # Return a message
        yield {"response": "Memory deleted.", "files": [], "ended": True, "errors": [], "pubKey": clientPublicKey}
    elif (service == "get_memories"):
        # Get all the memories of the user
        # Check the key
        if (key["key"] == None and len(Prompt["APIKey"]) > 0):
            # Key it's not valid nor empty
            # Wait 2s before processing
            time.sleep(2)

            # Return a warning
            yield {"response": "", "files": [], "ended": False, "errors": ["WARNING! Processing delayed 2s for security reasons. To avoid this warning, please use a valid API key or set it to empty."], "pubKey": clientPublicKey}
        
        # Check if the key is valid
        if (key["key"] != None and len(key["key"].strip()) > 0):
            # Get the memories of the key
            mms = memories.GetMemories(key["key"])
        else:
            # Get the memories from the empty key
            mms = memories.GetMemories("")

        # Return all the memories
        yield {"response": json.dumps(mms), "files": [], "ended": True, "errors": [], "pubKey": clientPublicKey}
    elif (service == "get_queue"):
        # Check index
        if (index < 0):
            # Set index
            index = GetAutoIndex(prompt, index)

        # Get a queue for a service
        if (len(prompt) > 0):
            queueUsers, queueTime = GetQueueForService(prompt, index)

            print(f"Queue for service '{prompt}:{index}' ==> {queueUsers} users, ~{queueTime}ms/token.")
            yield {"response": json.dumps({"users": queueUsers, "time": queueTime}), "files": [], "ended": True, "errors": [], "pubKey": clientPublicKey}
    elif (service == "get_tos"):
        # Get the Terms of Service of the server
        with open("TOS.txt", "r") as f:
            tos = f.read()
        
        yield {"response": tos, "files": [], "ended": True, "errors": [], "pubKey": clientPublicKey}
    elif (service == "create_key" and key["admin"]):
        # Create a new API key
        keyData = cfg.JSONDeserializer(prompt)
        keyData = sb.CreateKey(keyData["tokens"], keyData["daily"])

        yield {"response": keyData["key"], "files": [], "ended": True, "errors": [], "pubKey": clientPublicKey}
    elif (service == "get_key"):
        # Get information about the key
        keyData = key.copy()
        keyData["key"] = "[PRIVATE]"

        yield {"response": json.dumps(keyData), "files": [], "ended": True, "errors": [], "pubKey": clientPublicKey}
    elif (service == "get_service_description"):
        # Get the description of a specific service
        # Get the info from the service
        info = cfg.GetInfoOfTask(prompt, index)

        # Check if contains a description
        if ("description" in list(info.keys())):
            # Contains a description, send it
            yield {"response": info["description"], "files": [], "ended": True, "errors": [], "pubKey": clientPublicKey}
        else:
            # Does not contain a description, send an empty message
            yield {"response": "", "files": [], "ended": True, "errors": [], "pubKey": clientPublicKey}
    elif (service == "is_chatbot_multimodal"):
        # Check if the chatbot is multimodal
        try:
            # Check index
            if (index < 0):
                # Set index
                index = GetAutoIndex("chatbot")

            yield {"response": cfg.GetInfoOfTask("chatbot", index)["multimodal"], "files": [], "ended": True, "errors": [], "pubKey": clientPublicKey}
        except Exception as ex:
            yield {"response": "", "files": [], "ended": True, "errors": [str(ex)], "pubKey": clientPublicKey}
    elif (service == "get_price"):
        # Get the price of a service and index
        try:
            # Check if the index is valid
            if (index < 0):
                # Set index by default
                index = GetAutoIndex(prompt, index)
            
            if (index >= len(cfg.GetAllInfosOfATask(prompt))):
                # Index is out of range, return error
                yield {"response": "", "files": [], "ended": True, "errors": ["Invalid index."], "pubKey": clientPublicKey}
            else:
                yield {"response": str(cfg.GetInfoOfTask(prompt, index)["price"]), "files": [], "ended": True, "errors": [], "pubKey": clientPublicKey}
        except Exception as ex:
            yield {"response": "", "files": [], "ended": True, "errors": [f"COULD NOT GET THE PRICE DUE TO THIS ERROR: {ex}"], "pubKey": clientPublicKey}
    else:
        yield {"response": "", "files": [], "ended": True, "errors": ["Invalid command."], "pubKey": clientPublicKey}

async def ExecuteServiceAndSendToClient(
        Client: ServerConnection,
        Prompt: dict[str, any],
        HashAlgorithm: enc.hashes.HashAlgorithm | None,
        ClientVersion: int,
    ) -> None:
    clPubKey = None
    
    try:
        # Try to execute the service
        for response in ExecuteService(Prompt, Client.remote_address[0]):
            # Get the public key from the response
            clPubKey = response["pubKey"]
            response.pop("pubKey")

            # Send the response
            await __send_to_client__(Client, json.dumps(response).encode("utf-8"), clPubKey, HashAlgorithm, ClientVersion)
    except ConnectionClosed as ex:
        # Print error
        print("Connection closed while processing!")

        # Check if the processing was done
        if ("Done" not in list(Prompt.keys()) or ("Done" in list(Prompt.keys()) and not Prompt["Done"])):
            # Check if the service is valid
            if (len(cfg.GetAllInfosOfATask(Prompt["Service"])) == 0):
                # Not valid, return
                return

            try:
                # Try to get the index of the model to use
                index = int(Prompt["Index"])

                # Check if the index is less than 0
                if (index < 0):
                    index = GetAutoIndex(Prompt["Service"], index)

                # Throw an error if the index is invalid
                if (index >= len(cfg.GetAllInfosOfATask(Prompt["Service"]))):
                    raise Exception()
            except:
                # If an error occurs, auto get index
                index = GetAutoIndex(Prompt["Service"], -2)

            # Remove from the queue
            qs.RemoveUserFromQueue(Prompt["Service"], index)

        # Raise the exception
        raise ex
    except Exception as ex:
        # Print error
        print(f"Error processing! Could not send data to client. Error: {ex}")

        # Print error info
        traceback.print_exception(ex)

        # Check if the service is valid
        if (len(cfg.GetAllInfosOfATask(Prompt["Service"])) == 0):
            # Not valid, return
            return

        try:
            # Try to get the index of the model to use
            index = int(Prompt["Index"])

            # Check if the index is less than 0
            if (index < 0):
                index = GetAutoIndex(Prompt["Service"], index)

            # Throw an error if the index is invalid
            if (index >= len(cfg.GetAllInfosOfATask(Prompt["Service"]))):
                raise Exception()
        except:
            # If an error occurs, auto get index
            index = GetAutoIndex(Prompt["Service"], -2)
        
        # Remove from the queue
        qs.RemoveUserFromQueue(Prompt["Service"], index)

        try:
            # Try to send the closed message
            await __send_to_client__(Client, json.dumps({
                "response": "",
                "files": [],
                "ended": True,
                "errors": []
            }).encode("utf-8"), clPubKey, HashAlgorithm, ClientVersion)
        except:
            # Error, ignore
            pass

async def ProcessMessage(Client: ServerConnection, Message: bytes | str | None) -> None:
    # Print received length
    print(f"Received {len(Message)} bytes from '{Client.remote_address[0]}'")

    # Convert message to string
    if (isinstance(Message, bytes)):
        Message = Message.decode("utf-8")

    # Check for some services
    if (Message == "get_public_key"):
        # Send the public key to the client
        await __send_to_client__(Client, ServerPublicKey.decode("utf-8"), None, None, -1)
        return
    elif (Message == "get_server_version"):
        # Send the server version to the client
        await __send_to_client__(Client, str(ServerVersion), None, None, -1)
        return

    try:
        clientHashType = None
        clientVersion = -1

        # Get the message and hash algorithm of the client
        try:
            Message = cfg.JSONDeserializer(Message)
            clientHashType = Message["Hash"]
            clientVersion = int(Message["Version"]) if ("Version" in list(Message.keys())) else -1
            Message = enc.DecryptMessage(Message["Message"], ServerPrivateKey, enc.__parse_hash__(clientHashType))

            print(f"Client is using the hash '{clientHashType}' (specified by client).")
            clientHashType = enc.__parse_hash__(clientHashType)
        except json.JSONDecodeError:
            # Oldest decryption, VERY slow, deprecated
            for encType in cfg.current_data["allowed_hashes"]:
                try:
                    Message = enc.DecryptMessage(Message, ServerPrivateKey, enc.__parse_hash__(encType))
                    clientHashType = enc.__parse_hash__(encType)

                    print(f"Client is using the hash '{encType}' (automatically detected).")
                    break
                except:
                    continue
        except:
            raise ValueError(f"Invalid client hash. The valid hashes are: {cfg.current_data['allowed_hashes']}.")
        
        # Try to deserialize the message
        prompt = cfg.JSONDeserializer(Message)
        
        # Execute service and send data
        await ExecuteServiceAndSendToClient(Client, prompt, clientHashType, clientVersion)
    except ConnectionClosed as ex:
        raise ex
    except Exception as ex:
        # If there's an error, send the response
        await __send_to_client__(Client, json.dumps({
            "response": "",
            "files": [],
            "ended": True,
            "errors": [f"Error. Details: {ex}"]
        }).encode("utf-8"), None, None, -1)

async def __send_to_client__(
        Client: ServerConnection,
        Message: str | bytes,
        EncryptKey: bytes | None,
        HashAlgorithm: enc.hashes.HashAlgorithm | None,
        ClientVersion: int
    ) -> None:
    # Encrypt the message
    if (EncryptKey is None or HashAlgorithm is None):
        msg = Message
    else:
        msg = enc.EncryptMessage(Message, EncryptKey, HashAlgorithm, ClientVersion >= 140100)

    # Send the message
    try:
        await Client.send(msg)
    except ConnectionClosed as ex:
        raise ex
    except Exception as ex:
        print(f"Error sending message. Details:")
        traceback.print_exception(ex)

async def __receive_loop__(Client: ServerConnection) -> None:
    # Receive every message from the client
    async for msg in Client:
        try:
            await ProcessMessage(Client, msg)
        except ConnectionClosed:
            # Close the client
            break
        except Exception as ex:
            # Error returned
            print(f"Error executing a prompt of the client. Error: {ex}")

            try:
                # Try to send to the client
                await __send_to_client__(Client, json.dumps({
                    "response": "",
                    "files": [],
                    "ended": True,
                    "errors": [f"Error executing service. Details: {ex}"]
                }), None, None, -1)

                # Print the error
                print("Error executing service. Traceback:")
                traceback.print_exception(ex)
            except:
                # Print an error
                print("Could not send response to a client.")
    
    # Close the connection
    await Client.close()
    print("Client closed!")

async def OnConnect(Client: ServerConnection) -> None:
    try:
        # Print connection message
        print(f"'{Client.remote_address[0]}' has connected.")

        # Check if the IP is in the banned IPs list
        if (Client.remote_address[0] in banned["ip"]):
            try:
                # Print message
                print("Banned user. Closing connection.")

                # Send banned message
                await __send_to_client__(Client, json.dumps({
                    "response": "",
                    "files": [],
                    "ended": True,
                    "errors": ["Your IP address has been banned. Please contact support if this was a mistake."]
                }), None, None, -1)

                # Close the connection
                await Client.close()
                return
            except:
                # Error closing the connection, print
                print("Error closing the connection. Ignoring...")
                return
            
        # Receive
        await __receive_loop__(Client)
    except Exception as ex:
        print(f"Error while the client was connecting.")
        traceback.print_exception(ex)

async def __start_server__() -> tuple[str, int]:
    # Create thread for the queue cleanup
    queueThread = threading.Thread(target = __clear_queue_loop__)
    queueThread.start()

    # Create thread for the model offloading
    offloadThread = threading.Thread(target = __offload_loop__)
    offloadThread.start()

    # Create thread for the temporal conversations
    tempConvsThread = threading.Thread(target = __clear_temporal_conversations_loop__)
    tempConvsThread.start()

    # Set the IP
    ip = "127.0.0.1" if (cfg.current_data["use_local_ip"]) else "0.0.0.0"

    try:
        # Try to parse the port
        port = int(cfg.current_data["server_port"])
    except:
        # Error parsing the port, print and use default
        port = 8060
        print(f"Error parsing the server port, make sure it's an integer. Using default ({port}).")
    
    # Return variables
    return (ip, port)

async def StartWebSocketsServer(IP: str, Port: int) -> None:
    # Define global variables
    global serverWS

    # Set SSL variables
    sslContext = None

    if (
        "ssl" in cfg.current_data and
        len(cfg.current_data["ssl"]["cert"]) > 0 and
        len(cfg.current_data["ssl"]["key"]) > 0
    ):
        # Create SSL context
        sslContext = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        sslContext.load_cert_chain(
            certfile = cfg.current_data["ssl"]["cert"],
            keyfile = cfg.current_data["ssl"]["key"]
        )

        print("SSL enabled for WebSockets server.")

    # Start WebSockets server
    async with serve(
        OnConnect,
        IP,
        Port,
        max_size = None,
        ping_interval = None,
        ping_timeout = None,
        close_timeout = None,
        ssl = sslContext
    ):
        print(f"Started WebSockets at {IP}:{Port}")
        await asyncio.Future()

async def StartServer() -> None:
    # Get IP and port
    serverIP, serverPort = await __start_server__()

    # Start servers
    await asyncio.gather(
        StartWebSocketsServer(serverIP, serverPort),
        return_exceptions = True
    )

if (__name__ == "__main__"):
    # Save old data
    SaveOldData()

    # Start the server
    serverLoop = asyncio.new_event_loop()

    try:
        # Generate public and private keys
        ServerPrivateKey, ServerPublicKey = enc.CreateKeys()

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
        # Print
        print("\nClosing server...")
        
        # Close loop
        serverLoop.close()

        # Close
        started = False
        os._exit(0)
    except Exception as ex:
        print("ERROR! Running traceback.\n\n")
        traceback.print_exception(ex)