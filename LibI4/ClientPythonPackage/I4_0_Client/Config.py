class Conf():
    def __init__(self) -> None:
        # General
        self.Servers: list[str] = [
            "127.0.0.1",                # Localhost
            "main.tao71.org",           # TAO71 Main Server
            "tao71.sytes.net"           # TAO71 Main Server (old URL)
        ]
        self.ServerAPIKey: str = ""
        self.AllowedTools: list[str] | str | None = None
        self.ExtraTools: list[dict[str, str | dict[str, any]]] = []
        self.HashAlgorithm: str = "sha512"
        self.MaxLength: int | None = None
        self.Temperature: float | None = None
        self.SeeTools: bool = False
        self.AllowDataSave: bool = True

        # Chatbot
        self.Chatbot_ExtraSystemPrompts: str = ""
        self.Chatbot_AllowServerSystemPrompts: list[bool] | bool = [True, True, True, True]  # Boolean array for prompts [default I4.0 personality, server's extra system prompt (global), server's extra system prompt (for the selected index), server's dynamic system prompts]
        self.Chatbot_Conversation: str = "Client"
        self.Chatbot_AIArgs: str | None = None
        self.Chatbot_TopP: float | None = None
        self.Chatbot_TopK: float | None = None

        # Simulated vision v1
        self.SimulatedVision_v1_Image2Text_Allow: bool = True
        self.SimulatedVision_v1_Image2Text_Index: int = -1
        self.SimulatedVision_v1_ObjectDetection_Allow: bool = True
        self.SimulatedVision_v1_ObjectDetection_Index: int = -1

        # Simulated vision v2
        self.SimulatedVision_v2_Video_Allow: bool = True
        self.SimulatedVision_v2_Video_ProcessFrames: int = 1
        self.SimulatedVision_v2_Video_UseAudition: bool = True

        # Simulated audition v1
        self.SimulatedAudition_v1_SpeechToText_Allow: bool = True
        self.SimulatedAudition_v1_SpeechToText_Index: int = -1

        # Text2Image
        self.Text2Image_Width: int = -1
        self.Text2Image_Height: int = -1
        self.Text2Image_GuidanceScale: float = -1
        self.Text2Image_Steps: int = -1

        # RVC
        self.RVC_FilterRadius: int = 3
        self.RVC_Protect: float = 0.33
        self.RVC_f0: int = 0
        self.RVC_IndexRate: float = 0.75
        self.RVC_MixRate: float = 0.25

        # UVR
        self.UVR_Agg: int = 10

        # Image2Image
        self.Image2Image_Steps: int = 10
    
    @classmethod
    def __from_dict__(cls, Dictionary: dict[str, any]) -> "Conf":
        obj = cls()
        
        for key, value in Dictionary.items():
            if (hasattr(obj, key)):
                setattr(obj, key, value)
        
        return obj
    
    def __to_dict__(self) -> dict[str, any]:
        return self.__dict__