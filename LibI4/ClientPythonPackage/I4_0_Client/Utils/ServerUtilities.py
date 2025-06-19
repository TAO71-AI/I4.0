# Import libraries
from collections.abc import AsyncIterator
import json
import base64
import os
import cv2
import numpy as np

# Import I4.0 utilities
from .. import ServerConnection as ServerCon
from ..Config import Conf as Config
from ..Service import Service, ServiceManager

# Create variables
Conf: Config = Config()

class SimulatedVisionV1():
    @staticmethod
    def SeparateFiles(Files: list[dict[str, str]]) -> list[dict[str, str]]:
        """
        Separates the files to only image files.
        """
        # Create list
        files = []

        # For each file
        for file in Files:
            # Check if it's an image
            if (file["type"] == "image"):
                # Append it to the list
                files.append(file)
        
        # Return the files
        return files

    @staticmethod
    async def __execute_simulated_vision__(Template: str, Files: list[dict[str, str]], VisionService: Service, Index: int, ForceNoConnect: bool) -> str:
        """
        Executes the simulated vision service and gets a response.
        """
        # Get only the images files
        files = SimulatedVisionV1.SeparateFiles(Files)

        # Check files
        if (len(files) == 0):
            return ""

        # Try to send the message
        res = ExecuteService("", files, VisionService, Index, ForceNoConnect, False)
        img = 0
        response = ""

        # For each response
        async for token in res:
            # Check if the response ended
            if (token["ended"]):
                # Break the loop
                break

            # Get the response from the service
            img += 1
            response += Template.replace("[IMAGE_ID]", str(img)).replace("[RESPONSE]", str(token["response"]))
        
        return response
    
    @staticmethod
    async def ExecuteImageToText(Files: list[dict[str, str]], ForceNoConnect: bool) -> str:
        """
        Executes the ImageToText simulated vision.
        """
        # Return the response
        response = await SimulatedVisionV1.__execute_simulated_vision__(
            "> Image [IMAGE_ID] description: [RESPONSE]\n",
            Files,
            Service.ImageToText,
            Conf.SimulatedVision_v1_Image2Text_Index,
            ForceNoConnect
        )
        return response
    
    @staticmethod
    async def ExecuteObjectDetection(Files: list[dict[str, str]], ForceNoConnect: bool) -> str:
        """
        Executes the ObjectDetection simulated vision.
        """
        # Return the response
        response = await SimulatedVisionV1.__execute_simulated_vision__(
            "> Image [IMAGE_ID] list of objects detected and their position: [RESPONSE]\n",
            Files,
            Service.ObjectDetection,
            Conf.SimulatedVision_v1_ObjectDetection_Index,
            ForceNoConnect
        )
        return response

class SimulatedVisionV2():
    @staticmethod
    def SeparateFiles(Files: list[dict[str, str]]) -> list[dict[str, str]]:
        """
        Separates the files to only video files.
        """
        # Create list
        files = []

        # For each file
        for file in Files:
            # Check if it's a video
            if (file["type"] == "video"):
                # Append it to the list
                files.append(file)
        
        # Return the files
        return files
    
    @staticmethod
    def GetVideoInfo(VideoData: bytes | str) -> dict[str, any]:
        """
        Gets information of a video.
        """
        # Check if the video data is valid
        if (VideoData is str):
            VideoData = base64.b64decode(VideoData)
        elif (VideoData is not bytes):
            raise ValueError("VideoData must be bytes or str.")
        
        # Create variables
        videoArray = np.frombuffer(VideoData, dtype = np.uint8)
        videoCapture = cv2.VideoCapture()

        # Open the video
        videoCapture.open(cv2.imdecode(videoArray, cv2.IMREAD_COLOR))

        # Check if the video is open
        if (not videoCapture.isOpened()):
            raise Exception("Unable to open video.")
        
        # Get video info
        fps = videoCapture.get(cv2.CAP_PROP_FPS)
        width = int(videoCapture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(videoCapture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        numberOfFrames = int(videoCapture.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = numberOfFrames / fps if (fps > 0) else 0

        # Release the video capture
        videoCapture.release()

        # Return the video info
        return {
            "fps": fps,
            "width": width,
            "height": height,
            "frame_count": numberOfFrames,
            "duration": duration
        }

    @staticmethod
    def GetVideoFrames(VideoData: bytes | str, GetFrameEvery: int = 1) -> list[str]:
        """
        Gets the frames of the video.
        """
        # Check if the video data is valid
        if (VideoData is str):
            VideoData = base64.b64decode(VideoData)
        elif (VideoData is not bytes):
            raise ValueError("VideoData must be bytes or str.")
        
        # Create variables
        videoArray = np.frombuffer(VideoData, dtype = np.uint8)
        videoCapture = cv2.VideoCapture()

        # Open the video
        videoCapture.open(cv2.imdecode(videoArray, cv2.IMREAD_COLOR))

        # Check if the video is open
        if (not videoCapture.isOpened()):
            raise Exception("Unable to open video.")
        
        # Create frames variables
        frameCount = 0
        frames = []

        # Create loop
        while (True):
            # Read frame
            ret, frame = videoCapture.read()

            # Check if the video ended
            if (not ret):
                break

            # Check if the frame should be extracted
            if (frameCount % GetFrameEvery == 0):
                # Encode the frame to base64
                _, buffer = cv2.imencode(".jpg", frame)
                buffer = base64.b64encode(buffer).decode("utf-8")

                # Append it to the frames list
                frames.append(buffer)
            
            # Increment the frame count
            frameCount += 1
        
        # Release the video capture and return the frames
        videoCapture.release()
        return frames
    
    @staticmethod
    async def ExecuteSimulatedVision(Files: list[dict[str, str]], ForceNoConnect: bool) -> str:
        """
        Executes the simulated vision.
        """
        # Create variables
        simulatedVision = ""

        # Get only the video files
        files = SimulatedVisionV2.SeparateFiles(Files)

        # Check files
        if (len(files) == 0):
            return ""

        # For each video
        for video in files:
            # Get the video bytes
            videoData = video["data"]

            # Get the frames of the video
            frames = SimulatedVisionV2.GetVideoFrames(videoData, Conf.SimulatedVision_v2_Video_ProcessFrames)
            framesD = []

            # For each frame
            for frame in frames:
                # Convert to a valid file
                framesD.append({"type": "image", "data": frame})
            
            # Get the simulated vision v1 of the frames
            simulatedVisionFrames = {}

            if (Conf.SimulatedVision_v1_Image2Text_Allow):
                simulatedVisionFrames[f"Frame {len(list(simulatedVisionFrames.keys())) + 1} description"] = await SimulatedVisionV1.__execute_simulated_vision__("[RESPONSE]", framesD, Service.ImageToText, Conf.SimulatedVision_v1_Image2Text_Index, ForceNoConnect)
            
            if (Conf.SimulatedVision_v1_ObjectDetection_Allow):
                simulatedVisionFrames[f"Frame {len(list(simulatedVisionFrames.keys())) + 1} objects detected"] = await SimulatedVisionV1.__execute_simulated_vision__("[RESPONSE]", framesD, Service.ObjectDetection, Conf.SimulatedVision_v1_ObjectDetection_Index, ForceNoConnect)
            
            # Append the simulated vision of the video
            simulatedVision += f"Video {files.index(video) + 1}: {json.dumps(simulatedVisionFrames)}\n"
        
        return simulatedVision
    
    @staticmethod
    async def __execute_simulated_vision_with_audition(Files: dict[str, str], ForceNoConnect: bool) -> str:
        pass  # TODO

class SimulatedAuditionV1():
    @staticmethod
    def SeparateFiles(Files: list[dict[str, str]]) -> list[dict[str, str]]:
        """
        Separates the files to only audio files.
        """
        # Create list
        files = []

        # For each file
        for file in Files:
            # Check if it's an audio
            if (file["type"] == "audio"):
                # Append it to the list
                files.append(file)
        
        # Return the files
        return files

    @staticmethod
    async def __execute_simulated_audition__(Template: str, Files: list[dict[str, str]], AuditionService: Service, Index: int, ForceNoConnect: bool) -> str:
        """
        Executes the simulated audition service and gets a response.
        """
        # Get only the audio files
        files = SimulatedAuditionV1.SeparateFiles(Files)

        # Check files
        if (len(files) == 0):
            return ""

        # Try to send the message
        res = ExecuteService("", files, AuditionService, Index, ForceNoConnect, False)
        aud = 0
        response = ""

        # For each response
        async for token in res:
            # Check if the response ended
            if (token["ended"]):
                # Break the loop
                break

            # Get the response from the service
            aud += 1
            response += Template.replace("[AUDIO_ID]", str(aud)).replace("[RESPONSE]", str(token["response"]))
        
        return response
    
    @staticmethod
    async def ExecuteSpeechToText(Files: list[dict[str, str]], ForceNoConnect: bool) -> str:
        """
        Executes the SpeechToText simulated audition.
        """
        # Return the response
        response = await SimulatedAuditionV1.__execute_simulated_audition__(
            "> Audio [AUDIO_ID] dialogue: [RESPONSE]\n",
            Files,
            Service.SpeechToText,
            Conf.SimulatedAudition_v1_SpeechToText_Index,
            ForceNoConnect
        )
        return response

def __update_config__() -> None:
    """
    Updates the configuration in the server connection.
    """
    ServerCon.Conf = ServerCon.Conf.__from_dict__(Conf.__to_dict__())

async def ExecuteCommand(
        Service: str,
        Prompt: str = "",
        Index: int | None = None
    ) -> AsyncIterator[dict[str, any]]:
    """
    Executes a very-basic command on the server.
    You can use this, for example, to delete your conversation or get the queue for a service.
    """
    # Update config
    __update_config__()

    # Set index
    if (Index is None):
        Index = Conf.DefaultIndex

    # Serialize a very basic, minimum, data to send to the server
    jsonData = json.dumps({
        "APIKey": Conf.ServerAPIKey,
        "Prompt": Prompt,
        "Files": [],
        "Service": Service,
        "Conversation": Conf.Chatbot_Conversation,
        "Index": Index,
        "PublicKey": ServerCon.PublicKey.decode("utf-8"),
        "MaxLength": Conf.MaxLength,
        "Temperature": Conf.Temperature,
        "AllowDataSave": Conf.AllowDataSave,
        "SeeTools": Conf.SeeTools,
        "TopP": Conf.Chatbot_TopP,
        "TopK": Conf.Chatbot_TopK,
        "MinP": Conf.Chatbot_MinP,
        "TypicalP": Conf.Chatbot_TypicalP
    })

    # Return the response (probably serialized)
    async for token in ServerCon.SendAndWaitForStreaming(jsonData):
        yield token

async def ExecuteService(
        Prompt: str,
        Files: list[dict[str, str]],
        ServerService: Service,
        Index: int | None = None,
        ForceNoConnect: bool = False,
        FilesPath: bool = True
    ) -> AsyncIterator[dict[str, any]]:
    """
    This will automatically get a response a server.
    If the service requires it, this will serialize your prompt.
    This will also do other things before and after I4.0's response to your prompt.

    If FilesPath is False, the Files list must have the bytes of the files, in base64.
    If ForceNoConnect is True, this will not connect to any server, so you must be connected to one first.
    """
    # Update config
    __update_config__()

    # Set index
    if (Index is None):
        Index = Conf.DefaultIndex

    # Connect to a server
    currentServer = ServerCon.Connected[1] if (ServerCon.Connected is not None) else None

    if (not ForceNoConnect):
        if (ServerCon.IsConnected()):
            # Get the services from the server
            serverTasks = await ServerCon.GetServicesFromServer()

            if (ServerService not in serverTasks):
                # Connect to the first server to the service
                server = await ServerCon.FindFirstServer(ServerService)
                await ServerCon.Connect(server)
        else:
            # Connect to the first server to the service
            server = await ServerCon.FindFirstServer(ServerService)
            await ServerCon.Connect(server)
    elif (not ServerCon.IsConnected()):
        raise Exception("Please connect to a server first or set `ForceNoConnect` to false.")

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
        chatbotMultimodal = ""
        simulatedPrompt = ""

        async for token in ExecuteCommand("is_chatbot_multimodal", "", Index):
            # Check if the response is an error
            if (token["response"].lower().startswith("error") or len(token["errors"]) > 0):
                # Error, break the loop
                break

            # Not an error, set string
            chatbotMultimodal = token["response"].lower()

        if ("image" not in chatbotMultimodal):
            # Model doesn't support images. Use Simulated Vision V1

            # Use the `img2text` service if allowed in the configuration
            if (Conf.SimulatedVision_v1_Image2Text_Allow):
                try:
                    res = await SimulatedVisionV1.ExecuteImageToText(files, ForceNoConnect)
                    
                    if (len(res) > 0):
                        simulatedPrompt += res
                except:
                    pass  # Error. Ignore
            
            # Use the `od` service if allowed in the configuration
            if (Conf.SimulatedVision_v1_ObjectDetection_Allow):
                try:
                    res = await SimulatedVisionV1.ExecuteObjectDetection(files, ForceNoConnect)
                    
                    if (len(res) > 0):
                        simulatedPrompt += res
                except:
                    pass  # Error. Ignore
        
        if ("video" not in chatbotMultimodal):
            # Model doesn't support videos. Use Simulated Vision V2

            if (Conf.SimulatedVision_v2_Video_Allow):
                try:
                    res = await SimulatedVisionV2.ExecuteSimulatedVision(files, ForceNoConnect)
                    
                    if (len(res) > 0):
                        simulatedPrompt += res
                except:
                    pass  # Error. Ignore
        
        if ("audio" not in chatbotMultimodal):
            # Model doesn't support audios. Use Simulated Audition V1

            # Use the `speech2text` service if allowed in the configuration
            if (Conf.SimulatedAudition_v1_SpeechToText_Allow):
                try:
                    res = await SimulatedAuditionV1.ExecuteSpeechToText(files, ForceNoConnect)
                    
                    if (len(res) > 0):
                        simulatedPrompt += res
                except:
                    pass  # Error. Ignore

        # Add into the system prompts
        if (len(simulatedPrompt.strip()) > 0):
            systemPrompt += f"\n{simulatedPrompt}"
        
        # Reconnect to the server if disconnected
        if (ServerCon.Connected is not None and currentServer is not None and ServerCon.Connected[1] != currentServer and not ForceNoConnect):
            await ServerCon.Connect(currentServer)

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
        "PublicKey": ServerCon.PublicKey.decode("utf-8"),
        "AllowedTools": Conf.AllowedTools,
        "ExtraTools": Conf.ExtraTools,
        "MaxLength": Conf.MaxLength,
        "Temperature": Conf.Temperature,
        "SeeTools": Conf.SeeTools,
        "AllowDataSave": Conf.AllowDataSave,
        "TopP": Conf.Chatbot_TopP,
        "TopK": Conf.Chatbot_TopK,
        "MinP": Conf.Chatbot_MinP,
        "TypicalP": Conf.Chatbot_TypicalP
    })

    # Return the response
    async for token in ServerCon.SendAndWaitForStreaming(Prompt):
        yield token

async def GetQueueForService(QueueService: Service, Index: int = -1) -> tuple[int, int]:
    """
    This will send a prompt to the connected server asking for the queue size and time.
    Once received, it will return it.

    Index == -1 automatically gets the model with the smallest queue size.
    """

    # Get response from the queue command
    res = ExecuteCommand("get_queue", ServiceManager.ToString(QueueService), Index)

    async for response in res:
        if (not response["ended"]):
            # Continue, ignoring this message
            continue

        # Deserialize the received JSON response to a dictionary and return the users and the time
        queue = json.loads(response["response"])
        return (queue["users"], queue["time"])

    # Throw an error
    raise Exception("Queue error: Error getting queue.")

async def DeleteConversation(Conversation: str | None) -> None:
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

    async for response in res:
        if (not response["ended"]):
            # Continue, ignoring this message
            continue

        # Set response variable
        result = response["response"].lower().strip()

        # Check if response it's invalid
        if (result != "conversation deleted." or len(response["errors"]) > 0):
            # It's invalid, throw an error
            raise Exception(f"Error deleting the conversation. Got `{result}`; `conversation deleted.` expected. Errors: {response['errors']}")

        # It's a valid response, return
        return

    # Throw an error
    raise Exception("Delete conversation error.")

async def DeleteMemory(Memory: int = -1) -> None:
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

    async for response in res:
        if (not response["ended"]):
            # Continue, ignoring this message
            continue

        # Set response variable
        result = response["response"].lower().strip()

        # Check if response it's invalid
        if ((result != "memories deleted." and result != "memory deleted.") or len(response["errors"]) > 0):
            # It's invalid, throw an error
            raise Exception(f"Error deleting the memories/memory. Got `{result}`; `memories deleted.` or `memory deleted.` expected. Errors: {response['errors']}")

        # It's a valid response, return
        return

    # Throw an error
    raise Exception("Delete memory/memories error.")

async def GetTOS() -> str:
    """
    Gets the server's Terms Of Service.
    """

    # Send command to the server and wait for response
    res = ExecuteCommand("get_tos")

    # For each response
    async for response in res:
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