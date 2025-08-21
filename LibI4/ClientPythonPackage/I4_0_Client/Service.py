from enum import Enum

class KokoroVoice(Enum):
    # American
    American_Female_Heart = 0
    American_Female_Alloy = 1
    American_Female_Aoede = 2
    American_Female_Bella = 3
    American_Female_Jessica = 4
    American_Female_Kore = 5
    American_Female_Nicole = 6
    American_Female_Nova = 7
    American_Female_River = 8
    American_Female_Sarah = 9
    American_Female_Sky = 10
    American_Male_Adam = 11
    American_Male_Echo = 12
    American_Male_Eric = 13
    American_Male_Fenrir = 14
    American_Male_Liam = 15
    American_Male_Michael = 16
    American_Male_Onyx = 17
    American_Male_Puck = 18
    American_Male_Santa = 19

    # British
    British_Female_Alice = 20
    British_Female_Emma = 21
    British_Female_Isabella = 22
    British_Female_Lily = 23
    British_Male_Daniel = 24
    British_Male_Fable = 25
    British_Male_George = 26
    British_Male_Lewis = 27

    # Japanese
    Japanese_Female_Alpha = 28
    Japanese_Female_Gongitsune = 29
    Japanese_Female_Nezumi = 30
    Japanese_Female_Tebukuro = 31
    Japanese_Male_Kumo = 32

    # Mandarin Chinese
    MandarinChinese_Female_Xiaobei = 33
    MandarinChinese_Female_Xiaoni = 34
    MandarinChinese_Female_Xiaoxiao = 35
    MandarinChinese_Female_Xiaoyi = 36
    MandarinChinese_Male_Yunjian = 37
    MandarinChinese_Male_Yunxi = 38
    MandarinChinese_Male_Yunxia = 39
    MandarinChinese_Male_Yunyang = 40

    # Spanish
    Spanish_Female_Dora = 41
    Spanish_Male_Alex = 42
    Spanish_Male_Santa = 43

    # French
    French_Female_Siwis = 44

    # Hindi
    Hindi_Female_Alpha = 45
    Hindi_Female_Beta = 46
    Hindi_Male_Omega = 47
    Hindi_Male_Psi = 48

    # Italian
    Italian_Female_Sara = 49
    Italian_Male_Nicola = 50

    # Brazilian Portuguese
    BrazilianPortuguese_Female_Dora = 51
    BrazilianPortuguese_Male_Alex = 52
    BrazilianPortuguese_Male_Santa = 53

    # Other
    Custom = 54

    @staticmethod
    def FromString(VoiceName: str) -> "KokoroVoice":
        VoiceName = VoiceName.lower()
        mappings = {
            "af_heart": KokoroVoice.American_Female_Heart,
            "af_alloy": KokoroVoice.American_Female_Alloy,
            "af_aoede": KokoroVoice.American_Female_Aoede,
            "af_bella": KokoroVoice.American_Female_Bella,
            "af_jessica": KokoroVoice.American_Female_Jessica,
            "af_kore": KokoroVoice.American_Female_Kore,
            "af_nicole": KokoroVoice.American_Female_Nicole,
            "af_nova": KokoroVoice.American_Female_Nova,
            "af_river": KokoroVoice.American_Female_River,
            "af_sarah": KokoroVoice.American_Female_Sarah,
            "af_sky": KokoroVoice.American_Female_Sky,
            "am_adam": KokoroVoice.American_Male_Adam,
            "am_echo": KokoroVoice.American_Male_Echo,
            "am_eric": KokoroVoice.American_Male_Eric,
            "am_fenrir": KokoroVoice.American_Male_Fenrir,
            "am_liam": KokoroVoice.American_Male_Liam,
            "am_michael": KokoroVoice.American_Male_Michael,
            "am_onyx": KokoroVoice.American_Male_Onyx,
            "am_puck": KokoroVoice.American_Male_Puck,
            "am_santa": KokoroVoice.American_Male_Santa,
            "bf_allice": KokoroVoice.British_Female_Alice,
            "bf_emma": KokoroVoice.British_Female_Emma,
            "bf_isabella": KokoroVoice.British_Female_Isabella,
            "bf_lily": KokoroVoice.British_Female_Lily,
            "bm_daniel": KokoroVoice.British_Male_Daniel,
            "bm_fable": KokoroVoice.British_Male_Fable,
            "bm_george": KokoroVoice.British_Male_George,
            "bm_lewis": KokoroVoice.British_Male_Lewis,
            "jf_alpha": KokoroVoice.Japanese_Female_Alpha,
            "jf_gongitsune": KokoroVoice.Japanese_Female_Gongitsune,
            "jf_nezumi": KokoroVoice.Japanese_Female_Nezumi,
            "jf_tebukuro": KokoroVoice.Japanese_Female_Tebukuro,
            "jm_kumo": KokoroVoice.Japanese_Male_Kumo,
            "zf_xiaobei": KokoroVoice.MandarinChinese_Female_Xiaobei,
            "zf_xiaoni": KokoroVoice.MandarinChinese_Female_Xiaoni,
            "zf_xiaoxiao": KokoroVoice.MandarinChinese_Female_Xiaoxiao,
            "zf_xiaoyi": KokoroVoice.MandarinChinese_Female_Xiaoyi,
            "zm_yunjian": KokoroVoice.MandarinChinese_Male_Yunjian,
            "zm_yunxi": KokoroVoice.MandarinChinese_Male_Yunxi,
            "zm_yunxia": KokoroVoice.MandarinChinese_Male_Yunxia,
            "zm_yunyang": KokoroVoice.MandarinChinese_Male_Yunyang,
            "ef_dora": KokoroVoice.Spanish_Female_Dora,
            "em_alex": KokoroVoice.Spanish_Male_Alex,
            "em_santa": KokoroVoice.Spanish_Male_Santa,
            "ff_siwis": KokoroVoice.French_Female_Siwis,
            "hf_alpha": KokoroVoice.Hindi_Female_Alpha,
            "hf_beta": KokoroVoice.Hindi_Female_Beta,
            "hm_omega": KokoroVoice.Hindi_Male_Omega,
            "hm_psi": KokoroVoice.Hindi_Male_Psi,
            "if_sara": KokoroVoice.Italian_Female_Sara,
            "im_nicola": KokoroVoice.Italian_Male_Nicola,
            "pf_dora": KokoroVoice.BrazilianPortuguese_Female_Dora,
            "pm_alex": KokoroVoice.BrazilianPortuguese_Male_Alex,
            "pm_santa": KokoroVoice.BrazilianPortuguese_Male_Santa,
            "custom": KokoroVoice.Custom
        }

        if (VoiceName in mappings):
            return mappings[VoiceName]

        raise ValueError("Could not parse the kokoro voice.")
    
    @staticmethod
    def ToString(VoiceName: "KokoroVoice") -> str:
        mappings = {
            KokoroVoice.American_Female_Heart: "af_heart",
            KokoroVoice.American_Female_Alloy: "af_alloy",
            KokoroVoice.American_Female_Aoede: "af_aoede",
            KokoroVoice.American_Female_Bella: "af_bella",
            KokoroVoice.American_Female_Jessica: "af_jessica",
            KokoroVoice.American_Female_Kore: "af_kore",
            KokoroVoice.American_Female_Nicole: "af_nicole",
            KokoroVoice.American_Female_Nova: "af_nova",
            KokoroVoice.American_Female_River: "af_river",
            KokoroVoice.American_Female_Sarah: "af_sarah",
            KokoroVoice.American_Female_Sky: "af_sky",
            KokoroVoice.American_Male_Adam: "am_adam",
            KokoroVoice.American_Male_Echo: "am_echo",
            KokoroVoice.American_Male_Eric: "am_eric",
            KokoroVoice.American_Male_Fenrir: "am_fenrir",
            KokoroVoice.American_Male_Liam: "am_liam",
            KokoroVoice.American_Male_Michael: "am_michael",
            KokoroVoice.American_Male_Onyx: "am_onyx",
            KokoroVoice.American_Male_Puck: "am_puck",
            KokoroVoice.American_Male_Santa: "am_santa",
            KokoroVoice.British_Female_Alice: "bf_allice",
            KokoroVoice.British_Female_Emma: "bf_emma",
            KokoroVoice.British_Female_Isabella: "bf_isabella",
            KokoroVoice.British_Female_Lily: "bf_lily",
            KokoroVoice.British_Male_Daniel: "bm_daniel",
            KokoroVoice.British_Male_Fable: "bm_fable",
            KokoroVoice.British_Male_George: "bm_george",
            KokoroVoice.British_Male_Lewis: "bm_lewis",
            KokoroVoice.Japanese_Female_Alpha: "jf_alpha",
            KokoroVoice.Japanese_Female_Gongitsune: "jf_gongitsune",
            KokoroVoice.Japanese_Female_Nezumi: "jf_nezumi",
            KokoroVoice.Japanese_Female_Tebukuro: "jf_tebukuro",
            KokoroVoice.Japanese_Male_Kumo: "jm_kumo",
            KokoroVoice.MandarinChinese_Female_Xiaobei: "zf_xiaobei",
            KokoroVoice.MandarinChinese_Female_Xiaoni: "zf_xiaoni",
            KokoroVoice.MandarinChinese_Female_Xiaoxiao: "zf_xiaoxiao",
            KokoroVoice.MandarinChinese_Female_Xiaoyi: "zf_xiaoyi",
            KokoroVoice.MandarinChinese_Male_Yunjian: "zm_yunjian",
            KokoroVoice.MandarinChinese_Male_Yunxi: "zm_yunxi",
            KokoroVoice.MandarinChinese_Male_Yunxia: "zm_yunxia",
            KokoroVoice.MandarinChinese_Male_Yunyang: "zm_yunyang",
            KokoroVoice.Spanish_Female_Dora: "ef_dora",
            KokoroVoice.Spanish_Male_Alex: "em_alex",
            KokoroVoice.Spanish_Male_Santa: "em_santa",
            KokoroVoice.French_Female_Siwis: "ff_siwis",
            KokoroVoice.Hindi_Female_Alpha: "hf_alpha",
            KokoroVoice.Hindi_Female_Beta: "hf_beta",
            KokoroVoice.Hindi_Male_Omega: "hm_omega",
            KokoroVoice.Hindi_Male_Psi: "hm_psi",
            KokoroVoice.Italian_Female_Sara: "if_sara",
            KokoroVoice.Italian_Male_Nicola: "im_nicola",
            KokoroVoice.BrazilianPortuguese_Female_Dora: "pf_dora",
            KokoroVoice.BrazilianPortuguese_Male_Alex: "pm_alex",
            KokoroVoice.BrazilianPortuguese_Male_Santa: "pm_santa",
            KokoroVoice.Custom: "custom"
        }

        if (VoiceName in mappings):
            return mappings[VoiceName]

        raise ValueError("Could not parse the kokoro voice.")
    
    @staticmethod
    def FromInt(VoiceID: int) -> "KokoroVoice":
        try:
            return KokoroVoice(VoiceID)
        except ValueError:
            raise ValueError(f"Could not find kokoro voice with the ID '{VoiceID}'.")

    @staticmethod
    def ToInt(Voice: "KokoroVoice") -> int:
        return Voice.value
    
    @staticmethod
    def AutoConvert(Voice: "str | int | KokoroVoice") -> "KokoroVoice | str":
        if (isinstance(Voice, str)):
            return KokoroVoice.FromString(Voice)
        elif (isinstance(Voice, int)):
            return KokoroVoice.FromInt(Voice)
        elif (isinstance(Voice, KokoroVoice)):
            return KokoroVoice.ToString(Voice)
        else:
            raise ValueError("Invalid kokoro voice type.")

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
    UVR = 13
    ImageToImage = 14
    QuestionAnswering = 15
    LanguageDetection = 16
    NONE = -1

    @staticmethod
    def FromString(ServiceName: str) -> "Service":
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
            "uvr": Service.UVR,
            "img2img": Service.ImageToImage,
            "qa": Service.QuestionAnswering
        }

        if (ServiceName in mappings):
            return mappings[ServiceName]

        raise ValueError("Could not parse service.")

    @staticmethod
    def ToString(ServiceName: "Service") -> str:
        mappings = {
            Service.Chatbot: "chatbot",
            Service.ImageGeneration: "text2img",
            Service.ImageToText: "img2text",
            Service.DepthEstimation: "de",
            Service.Audio: "text2audio",
            Service.SpeechToText: "speech2text",
            Service.ObjectDetection: "od",
            Service.RVC: "rvc",
            Service.Translator: "tr",
            Service.LanguageDetection: "ld",
            Service.TextClassification: "sc",
            Service.NSFWFilterText: "nsfw_filter-text",
            Service.NSFWFilterImage: "nsfw_filter-image",
            Service.UVR: "uvr",
            Service.ImageToImage: "img2img",
            Service.QuestionAnswering: "qa"
        }

        if (ServiceName in mappings):
            return mappings[ServiceName]

        raise ValueError("Could not parse service.")

    @staticmethod
    def FromInt(ServiceID: int) -> "Service":
        try:
            return Service(ServiceID)
        except ValueError:
            raise ValueError(f"Could not find service with the ID '{ServiceID}'.")

    @staticmethod
    def ToInt(Serv: "Service") -> int:
        return Serv.value

    @staticmethod
    def AutoConvert(Serv: "str | int | Service") -> "Service | str":
        if (isinstance(Serv, str)):
            return Service.FromString(Serv)
        elif (isinstance(Serv, int)):
            return Service.FromInt(Serv)
        elif (isinstance(Serv, Service)):
            return Service.ToString(Serv)
        else:
            raise ValueError("Invalid service type.")