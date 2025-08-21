# Import libraries
from collections.abc import AsyncIterator
from io import BytesIO
from PIL import Image as PILImage
import av
import cv2
import json
import base64
import os
import math

# Import I4.0 utilities
from .. import ServerConnection as ServerCon
from ..Config import Conf as Config
from ..Service import Service, KokoroVoice

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
    def GetImageInfo(Image: str | bytes) -> dict[str, any]:
        """
        Gets information of an image.
        """
        # Create image buffer
        if (isinstance(Image, str)):
            buffer = BytesIO(base64.b64decode(Image))
        elif (isinstance(Image, bytes)):
            buffer = BytesIO(Image)
        else:
            raise ValueError("Invalid image type.")
        
        # Convert image to Pillow
        image = PILImage.open(buffer)

        # Extract properties
        metdata = {
            "width": image.width,
            "height": image.height
        }

        # Close the buffers
        image.close()
        buffer.close()

        # Return the metadata
        return metdata

    @staticmethod
    async def __execute_simulated_vision__(
        Template: str,
        Files: list[dict[str, str]],
        VisionService: Service,
        Index: int,
        Server: str | int | None
    ) -> str:
        """
        Executes the simulated vision service and gets a response.
        """
        # Get only the images files
        files = SimulatedVisionV1.SeparateFiles(Files)

        # Check files
        if (len(files) == 0):
            return ""
        
        # Connect to the server
        if (Server is not None):
            await ServerCon.Connect(Server)
        
        # For each file
        img = 1
        response = ""

        for file in files:
            # Send the message
            res = ExecuteService("", [file], VisionService, Index, False)

            # For each token
            async for token in res:
                # Check if the response ended
                if (token["ended"]):
                    # Break the loop
                    break

                # Get the response from the service and apply to the template
                response += Template.replace("[IMAGE_ID]", str(img)).replace("[RESPONSE]", str(token["response"])) + "\n"
                img += 1
        
        # Strip the response
        response = response.strip()
        
        # Return the response
        return response
    
    @staticmethod
    async def ExecuteImageToText(Files: list[dict[str, str]]) -> str:
        """
        Executes the ImageToText simulated vision.
        """
        # Return the response
        response = await SimulatedVisionV1.__execute_simulated_vision__(
            "Image [IMAGE_ID] description:\n```plaintext\n[RESPONSE]\n```\n",
            Files,
            Service.ImageToText,
            Conf.SimulatedVision_v1_Image2Text_Index,
            Conf.SimulatedVision_v1_Image2Text_Server
        )
        return response
    
    @staticmethod
    async def ExecuteObjectDetection(Files: list[dict[str, str]]) -> str:
        """
        Executes the ObjectDetection simulated vision.
        """
        # Return the response
        response = await SimulatedVisionV1.__execute_simulated_vision__(
            "Image [IMAGE_ID] list of objects detected and their position:\n```json\n[RESPONSE]\n```\n",
            Files,
            Service.ObjectDetection,
            Conf.SimulatedVision_v1_ObjectDetection_Index,
            Conf.SimulatedVision_v1_ObjectDetection_Server
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
        if (isinstance(VideoData, str)):
            VideoData = base64.b64decode(VideoData)
        elif (not isinstance(VideoData, bytes)):
            raise ValueError("VideoData must be bytes or str.")
        
        # Create buffer and variables
        videoBuffer = BytesIO(VideoData)

        try:
            # Open video metadata
            reader = av.open(videoBuffer)
            stream = next(s for s in reader.streams if (s.type == "video"))

            # Extract properties
            fps = float(stream.average_rate) if (stream.average_rate) else 0
            size = [stream.codec_context.width, stream.codec_context.height]
            numberOfFrames = stream.frames
            duration = float(reader.duration / av.time_base) if (reader.duration) else (numberOfFrames / fps if (fps) else 0)

            # Save into the dictionary
            metdata = {
                "fps": math.floor(fps),
                "width": size[0],
                "height": size[1],
                "frame_count": numberOfFrames,
                "duration": math.floor(duration)
            }

            # Close the buffers
            reader.close()
            videoBuffer.close()

            # Return the metadata
            return metdata
        except Exception as ex:
            # Close the buffer
            videoBuffer.close()

            # Raise exception
            raise Exception("Unable to get video info.") from ex

    @staticmethod
    def GetVideoFrames(VideoData: bytes | str, GetFrameEvery: int = 1) -> list[str]:
        """
        Gets the frames of the video.
        """
        # Check if the video data is valid
        if (isinstance(VideoData, str)):
            VideoData = base64.b64decode(VideoData)
        elif (not isinstance(VideoData, bytes)):
            raise ValueError("VideoData must be bytes or str.")
        
        # Create buffer
        videoBuffer = BytesIO(VideoData)

        try:
            # Open video
            reader = av.open(videoBuffer)
            frames = []
            frameCount = 0

            # For each frame
            for frame in reader.decode(video = 0):
                # Check if the frame should be extracted
                if (frameCount % GetFrameEvery == 0):
                    # Encode to JPG buffer
                    buffer = frame.to_ndarray(format = "bgr24")
                    success, buffer = cv2.imencode(".jpg", buffer)

                    # Check there are no errors
                    if (not success):
                        continue

                    # Encode the buffer and save it
                    buffer = base64.b64encode(buffer).decode("utf-8")
                    frames.append(buffer)
                
                # Increment frame count
                frameCount += 1
            
            # Close the buffers
            reader.close()
            videoBuffer.close()

            # Return the frames
            return frames
        except Exception as ex:
            # Close the buffer
            videoBuffer.close()

            # Raise exception
            raise Exception("Unable to open video.") from ex
    
    @staticmethod
    async def ExecuteSimulatedVision(Files: list[dict[str, str]]) -> str:
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
            
            # Create result string variable
            simulatedVisionResult = ""

            # For each frame
            for frameIdx, frame in enumerate(frames):
                # Use img2text from simulated vision 1
                if (Conf.SimulatedVision_v1_Image2Text_Allow):
                    try:
                        # Connect to the server
                        if (Conf.SimulatedVision_v1_Image2Text_Server is not None):
                            await ServerCon.Connect(Conf.SimulatedVision_v1_Image2Text_Server)

                        # Execute the service
                        res = ExecuteService("", [{"type": "image", "data": frame}], Service.ImageToText, Conf.SimulatedVision_v1_Image2Text_Index, False)
                        strRes = ""

                        # Receive all tokens and save into the string
                        async for token in res:
                            if (len(token["errors"]) > 0):
                                continue
                            
                            strRes += token["response"]
                        
                        # Save into the result variable
                        if (len(strRes.strip()) > 0):
                            simulatedVisionResult += f"Frame {frameIdx * Conf.SimulatedVision_v2_Video_ProcessFrames} description: {strRes}\n"
                    except:
                        pass
            
                if (Conf.SimulatedVision_v1_ObjectDetection_Allow):
                    try:
                        # Connect to the server
                        if (Conf.SimulatedVision_v1_ObjectDetection_Server is not None):
                            await ServerCon.Connect(Conf.SimulatedVision_v1_ObjectDetection_Server)

                        # Execute the service
                        res = ExecuteService("", [{"type": "image", "data": frame}], Service.ObjectDetection, Conf.SimulatedVision_v1_ObjectDetection_Index, False)
                        strRes = ""

                        # Receive all tokens and save into the string
                        async for token in res:
                            if (len(token["errors"]) > 0):
                                continue
                            
                            strRes += token["response"]
                        
                        # Save into the result variable
                        if (len(strRes.strip()) > 0):
                            simulatedVisionResult += f"Frame {frameIdx * Conf.SimulatedVision_v2_Video_ProcessFrames} objects detected: {strRes}\n"
                    except:
                        pass
            
            # Append the simulated vision of the video
            simulatedVision += f"Video {files.index(video) + 1} frames:\n```plaintext\n{simulatedVisionResult.strip()}\n```\n"

            # Use simulated audition if the user allows it
            if (Conf.SimulatedVision_v2_Video_UseAudition):
                # Get the data of the video
                if (isinstance(videoData, str)):
                    videoBData = base64.b64decode(videoData)
                elif (isinstance(videoData, bytes)):
                    videoBData = videoData
                else:
                    raise ValueError("Video data is neither bytes or a base64-encoded string.")
                
                # Create the video buffers
                videoBuffer = BytesIO(videoBData)
                audioOutputBuffer = BytesIO()

                try:
                    # Try to open the video
                    reader = av.open(videoBuffer)

                    # Search the audio track
                    audioStream = next((s for s in reader.streams if (s.type == "audio")), None)

                    # Make sure the audio stream is not null
                    if (audioStream is not None):
                        # Open the writer and the stream
                        writer = av.open(audioOutputBuffer, mode = "w", format = "wav")
                        outStream = writer.add_stream("pcm_u8", 22000)
                        resampler = av.audio.resampler.AudioResampler("u8p", "mono", 22000)

                        for frame in reader.decode(audio = 0):
                            outFrames = resampler.resample(frame)

                            for outFrame in outFrames:
                                for packet in outStream.encode(outFrame):
                                    writer.mux(packet)
                        
                        # Close the writer
                        writer.close()

                        # Get the audio transcription using speech2text if available
                        if (Conf.SimulatedAudition_v1_SpeechToText_Allow):
                            try:
                                # Connect to the server
                                if (Conf.SimulatedAudition_v1_SpeechToText_Server is not None):
                                    await ServerCon.Connect(Conf.SimulatedAudition_v1_SpeechToText_Server)

                                # Execute the service
                                res = ExecuteService("", [{"type": "audio", "data": base64.b64encode(audioOutputBuffer.getvalue()).decode("utf-8")}], Service.SpeechToText, Conf.SimulatedAudition_v1_SpeechToText_Index, False)
                                strRes = ""

                                # Receive all tokens and save into the string
                                async for token in res:
                                    if (len(token["errors"]) > 0):
                                        continue
                                    
                                    strRes += token["response"]
                                
                                # Try to convert to JSON
                                try:
                                    strRes = json.loads(strRes.strip())
                                    transcriptionText = strRes["text"].strip()
                                    transcriptionLanguage = strRes["lang"].strip().lower()

                                    # Make sure the language is not unknown
                                    if (transcriptionLanguage == "unknown"):
                                        transcriptionLanguage = "unable to determine"
                                except:
                                    transcriptionText = strRes
                                    transcriptionLanguage = "unable to determine"
                                
                                # Create dictionary variable
                                transcriptionJson = {"text": transcriptionText, "language": transcriptionLanguage}
                                transcriptionJson = json.dumps(transcriptionJson, indent = 4)
                                
                                # Save into the result variable
                                if (len(strRes.strip()) > 0):
                                    simulatedVision += f"Video {files.index(video) + 1} transcription:\n```json\n{transcriptionJson}\n```\n"
                            except:
                                pass
                    
                    # Close the reader
                    reader.close()

                    # Close the buffers
                    audioOutputBuffer.close()
                    videoBuffer.close()
                except Exception as ex:
                    # Close the buffers
                    audioOutputBuffer.close()
                    videoBuffer.close()

                    # Raise the exception
                    raise Exception("Unable to open video.") from ex
        
        # Return the response
        return simulatedVision.strip()

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
    async def __execute_simulated_audition__(
        Template: str,
        Files: list[dict[str, str]],
        AuditionService: Service,
        Index: int,
        Server: str | int | None
    ) -> str:
        """
        Executes the simulated audition service and gets a response.
        """
        # Get only the audio files
        files = SimulatedAuditionV1.SeparateFiles(Files)

        # Check files
        if (len(files) == 0):
            return ""
        
        # Connect to the server
        if (Server is not None):
            await ServerCon.Connect(Server)
        
        # For each file
        aud = 1
        response = ""

        for file in files:
            # Send the message
            res = ExecuteService("", [file], AuditionService, Index, False)

            # For each token
            async for token in res:
                # Check if the response ended
                if (token["ended"]):
                    # Break the loop
                    break

                # Get the response from the service and apply to the template
                response += Template.replace("[AUDIO_ID]", str(aud)).replace("[RESPONSE]", str(token["response"])) + "\n"
                aud += 1
        
        # Strip the response
        response = response.strip()
        
        # Return the response
        return response
    
    @staticmethod
    async def ExecuteSpeechToText(Files: list[dict[str, str]]) -> str:
        """
        Executes the SpeechToText simulated audition.
        """
        # Get the text response
        response = await SimulatedAuditionV1.__execute_simulated_audition__(
            "> Audio [AUDIO_ID] dialogue: [RESPONSE]\n",
            Files,
            Service.SpeechToText,
            Conf.SimulatedAudition_v1_SpeechToText_Index,
            Conf.SimulatedAudition_v1_SpeechToText_Server
        )

        # Try to deserialize
        try:
            response = json.loads(response)
            response = response["text"]
        except:
            pass

        # Return the text response
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
        "AllowDataSave": Conf.AllowDataSave,
        "SeeTools": Conf.SeeTools
    })

    # Return the response (probably serialized)
    async for token in ServerCon.SendAndWaitForStreaming(jsonData):
        yield token

async def ExecuteService(
        Prompt: str,
        Files: list[dict[str, str]],
        ServerService: Service,
        Index: int | None = None,
        FilesPath: bool = True
    ) -> AsyncIterator[dict[str, any]]:
    """
    This will automatically get a response a server.
    If the service requires it, this will serialize your prompt.
    This will also do other things before and after I4.0's response to your prompt.

    If FilesPath is False, the Files list must have the bytes of the files, in base64.
    """
    # Update config
    __update_config__()

    # Set index
    if (Index is None):
        Index = Conf.DefaultIndex

    # Make sure the user is connected to a server
    if (not ServerCon.IsConnected()):
        # Raise exception
        raise RuntimeError("Not connected to any server. Connect to a server first.")

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
    
    # Set variables
    maxLength = None
    temperature = None
    topP = None
    topK = None
    minP = None
    typicalP = None

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
    elif (ServerService == Service.UVR):
        # Template: UVR
        Prompt = json.dumps({
            "agg": Conf.UVR_Agg
        })
    elif (ServerService == Service.Audio):
        # Check if the model type is kokoro
        modelType = await GetTextToAudioType(Index)

        if (modelType == "kokoro"):
            # Model type is kokoro, set the template
            # Template: Text2Audio Kokoro
            Prompt = json.dumps({
                "prompt": Prompt,
                "voice": KokoroVoice.ToString(KokoroVoice.FromInt(Conf.Text2Audio_TTS_Voice)) if (isinstance(Conf.Text2Audio_TTS_Voice, int)) else Conf.Text2Audio_TTS_Voice,
                "speed": Conf.Text2Audio_TTS_Speed
            })
    elif (ServerService == Service.Chatbot):
        # Set variables
        maxLength = Conf.Chatbot_MaxLength
        temperature = Conf.Chatbot_Temperature
        topP = Conf.Chatbot_TopP
        topK = Conf.Chatbot_TopK
        minP = Conf.Chatbot_MinP
        typicalP = Conf.Chatbot_TypicalP

        # Check if the chatbot is multimodal
        chatbotMultimodal = ""
        simulatedPrompt = ""
        currentServer = ServerCon.Connected[1]

        async for token in ExecuteCommand("is_chatbot_multimodal", "", Index):
            # Check if the response is an error
            if (token["response"].lower().startswith("error") or len(token["errors"]) > 0):
                # Error, break the loop
                break

            # Not an error, set string
            chatbotMultimodal += token["response"].lower()

        if ("image" not in chatbotMultimodal and len(SimulatedVisionV1.SeparateFiles(files)) > 0):
            # Model doesn't support images. Use Simulated Vision V1

            # Use the `img2text` service if allowed in the configuration
            if (Conf.SimulatedVision_v1_Image2Text_Allow):
                try:
                    res = await SimulatedVisionV1.ExecuteImageToText(files)
                    
                    if (len(res) > 0):
                        simulatedPrompt += res
                except:
                    pass  # Error. Ignore
            
            # Use the `od` service if allowed in the configuration
            if (Conf.SimulatedVision_v1_ObjectDetection_Allow):
                try:
                    res = await SimulatedVisionV1.ExecuteObjectDetection(files)
                    
                    if (len(res) > 0):
                        simulatedPrompt += res
                except:
                    pass  # Error. Ignore
            
            # Separate the images
            imgs = SimulatedVisionV1.SeparateFiles(files)

            # Get the metadata of each image and save into the simulated prompt
            for imgIdx, img in enumerate(imgs):
                imgMetadata = SimulatedVisionV1.GetImageInfo(img["data"])
                simulatedPrompt += f"Image {imgIdx + 1} metadata:\n```json\n{json.dumps(imgMetadata, indent = 4)}\n```\n"

            # Remove all the images from the files
            for file in files:
                if (file["type"] == "image"):
                    files.remove(file)
        
        if ("video" not in chatbotMultimodal and len(SimulatedVisionV2.SeparateFiles(files)) > 0):
            # Model doesn't support videos. Use Simulated Vision V2

            if (Conf.SimulatedVision_v2_Video_Allow):
                try:
                    res = await SimulatedVisionV2.ExecuteSimulatedVision(files)
                    
                    if (len(res) > 0):
                        simulatedPrompt += res
                except Exception as ex:
                    pass  # Error. Ignore
            
            # Separate the videos
            vids = SimulatedVisionV2.SeparateFiles(files)

            # Get the metadata of each video and save into the simulated prompt
            for vidIdx, vid in enumerate(vids):
                vidMetadata = SimulatedVisionV2.GetVideoInfo(vid["data"])
                simulatedPrompt += f"\nVideo {vidIdx + 1} metadata:\n```json\n{json.dumps(vidMetadata, indent = 4)}\n```\n"
            
            # Remove all the videos from the files
            for file in files:
                if (file["type"] == "video"):
                    files.remove(file)
        
        if ("audio" not in chatbotMultimodal and len(SimulatedAuditionV1.SeparateFiles(files)) > 0):
            # Model doesn't support audios. Use Simulated Audition V1

            # Use the `speech2text` service if allowed in the configuration
            if (Conf.SimulatedAudition_v1_SpeechToText_Allow):
                try:
                    res = await SimulatedAuditionV1.ExecuteSpeechToText(files)
                    
                    if (len(res) > 0):
                        simulatedPrompt += res
                except:
                    pass  # Error. Ignore
            
            # Remove all the audios from the files
            for file in files:
                if (file["type"] == "audio"):
                    files.remove(file)

        # Add into the system prompts
        if (len(simulatedPrompt.strip()) > 0):
            if (Conf.SimulatedSensesInUserPrompt):
                Prompt = f"{simulatedPrompt.strip()}\n\n{Prompt}"
            else:
                systemPrompt += f"\n{simulatedPrompt.strip()}"
        
        # Reconnect to the server if disconnected
        if (ServerCon.Connected[1] != currentServer):
            await ServerCon.Connect(currentServer)
    elif (ServerService == Service.ImageToText):
        # Set variables
        maxLength = Conf.Image2Text_MaxLength

    # Set prompt
    Prompt = json.dumps({
        "Service": Service.ToString(ServerService),
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
        "MaxLength": maxLength,
        "Temperature": temperature,
        "SeeTools": Conf.SeeTools,
        "AllowDataSave": Conf.AllowDataSave,
        "TopP": topP,
        "TopK": topK,
        "MinP": minP,
        "TypicalP": typicalP,
        "UseReasoning": Conf.Chatbot_UseReasoning,
        "AllowMemoriesUsage": Conf.Chatbot_AllowMemoriesUsage,
        "ToolsInSystemPrompt": Conf.Chatbot_ToolsInSystemPrompt
    })

    # Return the response
    async for token in ServerCon.SendAndWaitForStreaming(Prompt):
        yield token

async def GetQueueForService(QueueService: Service, Index: int | None = None) -> tuple[int, int]:
    """
    This will send a prompt to the connected server asking for the queue size and time.
    Once received, it will return it.

    Index == -1 automatically gets the model with the smallest queue size.
    """
    # Update config
    __update_config__()

    # Set index
    if (Index is None):
        Index = Conf.DefaultIndex

    # Get response from the queue command
    res = ExecuteCommand("get_queue", Service.ToString(QueueService), Index)

    async for response in res:
        if (not response["ended"]):
            # Continue, ignoring this message
            continue

        # Deserialize the received JSON response to a dictionary and return the users and the time
        queue = json.loads(response["response"])
        return (queue["users"], queue["time"])

    # Throw an error
    raise RuntimeError("Queue error: Error getting queue.")

async def DeleteConversation(Conversation: str | None) -> None:
    """
    This will delete your current conversation ONLY on the connected server.
    If `Conversation` is null this will use the conversation of the configuration.
    """
    # Update config
    __update_config__()

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
            raise RuntimeError(f"Error deleting the conversation. Got `{result}`; `conversation deleted.` expected. Errors: {response['errors']}")

        # It's a valid response, return
        return

    # Throw an error
    raise RuntimeError("Delete conversation error.")

async def DeleteMemory(Memory: int = -1) -> None:
    """
    This will delete your current memory/memories ONLY on the connected server.
    If `Memory` is -1 this will delete all the memories.
    """
    # Update config
    __update_config__()

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
            raise RuntimeError(f"Error deleting the memories/memory. Got `{result}`; `memories deleted.` or `memory deleted.` expected. Errors: {response['errors']}")

        # It's a valid response, return
        return

    # Throw an error
    raise RuntimeError("Delete memory/memories error.")

async def GetTOS() -> str:
    """
    Gets the server's Terms Of Service.
    """
    # Update config
    __update_config__()

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

    raise RuntimeError("Error getting TOS: No response from server.")

async def GetTextToAudioType(Index: int | None = None) -> str:
    """
    Gets the server's Terms Of Service.
    """
    # Update config
    __update_config__()

    # Set index
    if (Index is None):
        Index = Conf.DefaultIndex

    # Send command to the server and wait for response
    res = ExecuteCommand("get_text2audio_type")

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

        # Return the text response
        return tResponse

    raise RuntimeError("Error getting TextToAudio model type: No response from server.")