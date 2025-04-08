class Conf():
    # General
    Servers: list[str] = [
        "127.0.0.1",                # Localhost
        "tao71.sytes.net"           # TAO71 Server
    ]
    ServerAPIKey: str = ""
    AllowedTools: list[str] | str | None = None
    ExtraTools: list[dict[str, str | dict[str, any]]] = []
    HashAlgorithm: str = "sha512"
    MaxLength: int | None = None
    Temperature: float | None = None

    # Chatbot
    Chatbot_ExtraSystemPrompts: str = ""
    Chatbot_AllowServerSystemPrompts: list[str] = [True, True]  # Boolean array for prompts
    Chatbot_Conversation: str = "Client"
    Chatbot_AIArgs: str | None = None

    # Simulated vision v1
    SimulatedVision_v1_Image2Text_Allow: bool = True
    SimulatedVision_v1_Image2Text_Index: int = -1
    SimulatedVision_v1_ObjectDetection_Allow: bool = True
    SimulatedVision_v1_ObjectDetection_Index: int = -1

    # Simulated vision v2
    SimulatedVision_v2_Video_Allow: bool = True
    SimulatedVision_v2_Video_ProcessFrames: int = 1
    SimulatedVision_v2_Video_UseAudition: bool = True

    # Simulated audition v1
    SimulatedAudition_v1_SpeechToText: bool = True
    SimulatedAudition_v1_SpeechToText_Index: int = -1

    # Text2Image
    Text2Image_Width: int = -1
    Text2Image_Height: int = -1
    Text2Image_GuidanceScale: float = -1
    Text2Image_Steps: int = -1

    # RVC
    RVC_FilterRadius: int = 3
    RVC_Protect: float = 0.33
    RVC_f0: int = 0
    RVC_IndexRate: float = 0.75
    RVC_MixRate: float = 0.25

    # UVR
    UVR_Agg: int = 10

    # Image2Image
    Image2Image_Steps: int = 10