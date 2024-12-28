# General
Servers: list[str] = [
    "127.0.0.1",                # Localhost
    "tao71.sytes.net"           # TAO71 Server
]
DefaultImagesProgram: str = ""  # Leave empty to use the system's default
DefaultAudiosProgram: str = ""  # Leave empty to use the system's default
ServerAPIKey: str = ""
AllowDataShare: bool = True

# Chatbot
Chatbot_ExtraSystemPrompts: str = ""
Chatbot_AllowServerSystemPrompts: list[str] = [True, True]  # Boolean array for prompts
Chatbot_Conversation: str = "Client"
Chatbot_AIArgs: str | None = None
Chatbot_SimulatedVision_Image2Text: bool = True
Chatbot_SimulatedVision_Image2Text_Index: int = -1
Chatbot_SimulatedVision_ObjectDetection: bool = True
Chatbot_SimulatedVision_ObjectDetection_Index: int = -1

# Text2Image
Text2Image_Width: int = -1
Text2Image_Height: int = -1
Text2Image_GuidanceScale: float = -1
Text2Image_Steps: int = -1

# Image2Text
# Nothing to configure

# Voice Recognition
# Nothing to configure

# Text2Audio
# Nothing to configure

# Depth Estimarion
# Nothing to configure

# Object Detection
# Nothing to configure

# RVC
RVC_FilterRadius: int = 3
RVC_Protect: float = 0.33
RVC_f0: int = 0
RVC_IndexRate: float = 0.75
RVC_MixRate: float = 0.25

# Translator
# Nothing to configure

# Text Classification
# Nothing to configure

# NSFW Filter (Text)
# Nothing to configure

# NSFW Filter (Image)
# Nothing to configure

# TTS
TTS_Voice: str = "espeak-f1"
TTS_Language: str = "en-us"
TTS_Pitch: float = 1
TTS_Speed: float = 1

# UVR
UVR_Agg: int = 10

# Image2Image
Image2Image_Steps: int = 10

# Question Answering
# Nothing to configure