from enum import Enum

class Service(Enum):
    Chatbot = 0
    CustomCommand = 1
    ImageGeneration = 2
    ImageToText = 3
    SpeechToText = 4
    Audio = 5
    DepthEstimation = 6
    ObjectDetection = 7
    RVC = 8
    Translator = 9
    TextClassification = 10
    NSFWFilterText = 11
    NSFWFilterImage = 12
    TTS = 13
    UVR = 14
    ImageToImage = 15
    QuestionAnswering = 16
    LanguageDetection = 17
    None = -1

class ServiceManager:
    @staticmethod
    def FromString(ServiceName: str) -> Service:
        ServiceName = ServiceName.lower()
        mappings = {
            "chatbot": Service.Chatbot,
            "text2img": Service.ImageGeneration,
            "img2text": Service.ImageToText,
            "de": Service.DepthEstimation,
            "text2audio": Service.Audio,
            "speech2text": Service.SpeechToText,
            "od": Service.ObjectDetection,
            "rvc": Service.RVC,
            "tr": Service.Translator,
            "ld": Service.LanguageDetection,
            "sc": Service.TextClassification,
            "nsfw_filter-text": Service.NSFWFilterText,
            "nsfw_filter-image": Service.NSFWFilterImage,
            "tts": Service.TTS,
            "uvr": Service.UVR,
            "img2img": Service.ImageToImage,
            "qa": Service.QuestionAnswering,
        }

        if (ServiceName in mappings):
            return mappings[ServiceName]

        raise ValueError("Could not parse service.")

    @staticmethod
    def ToString(ServiceName: Service) -> str:
        for key, value in ServiceManager.FromString.__annotations__.items():
            if (value == ServiceName):
                return key
        
        raise ValueError("Could not parse service.")

    @staticmethod
    def FromInt(ServiceID: int) -> Service:
        try:
            return Service(ServiceID)
        except ValueError:
            raise ValueError(f"Could not find service with the ID '{ServiceID}'.")

    @staticmethod
    def ToInt(Serv: Service) -> int:
        return Serv.value

    @staticmethod
    def AutoConvert(Serv: str | int | Service) -> Service | str:
        if (type(Serv) == str):
            return ServiceManager.FromString(Serv)
        elif (type(Serv) == int):
            return ServiceManager.FromInt(Serv)
        elif (type(Serv) == Service):
            return ServiceManager.ToString(Serv)
        else:
            raise ValueError("Invalid service type.")