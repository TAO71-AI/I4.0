export enum InternetSearchOptions
{
    QuestionAnswering = 0,
    Chatbot = 1,
    QuestionAnswering_Chatbot = 2,
    Chatbot_QuestionAnswering = 3
}

export enum Service
{
    Chatbot = 0,
    CustomCommand = 1,
    ImageGeneration = 2,
    ImageToText = 3,
    SpeechToText = 4,
    Audio = 5,
    DepthEstimation = 6,
    ObjectDetection = 7,
    RVC = 8,
    Translator = 9,
    TextClassification = 10,
    NSFWFilterText = 11,
    NSFWFilterImage = 12,
    TTS = 13,
    UVR = 14,
    ImageToImage = 15,
    QuestionAnswering = 16,
    None = -1
}

export class ServiceManager
{
    static FromString(ServiceName: string): Service
    {
        switch (ServiceName.toLowerCase())
        {
            case "chatbot":
                return Service.Chatbot;
            case "text2img":
                return Service.ImageGeneration;
            case "img2text":
                return Service.ImageToText;
            case "de":
                return Service.DepthEstimation;
            case "text2audio":
                return Service.Audio;
            case "speech2text":
                return Service.SpeechToText;
            case "od":
                return Service.ObjectDetection;
            case "rvc":
                return Service.RVC;
            case "tr":
                return Service.Translator;
            case "sc":
                return Service.TextClassification;
            case "nsfw_filter-text":
                return Service.NSFWFilterText;
            case "nsfw_filter-image":
                return Service.NSFWFilterImage;
            case "tts":
                return Service.TTS;
            case "uvr":
                return Service.UVR;
            case "img2img":
                return Service.ImageToImage;
            case "qa":
                return Service.QuestionAnswering;
            default:
                throw new Error("Could not parse service.");
        }
    }

    static ToString(ServiceName: Service): string
    {
        switch (ServiceName)
        {
            case Service.Chatbot:
                return "chatbot";
            case Service.ImageGeneration:
                return "text2img";
            case Service.ImageToText:
                return "img2text";
            case Service.DepthEstimation:
                return "de";
            case Service.Audio:
                return "text2audio";
            case Service.SpeechToText:
                return "speech2text";
            case Service.ObjectDetection:
                return "od";
            case Service.RVC:
                return "rvc";
            case Service.Translator:
                return "tr";
            case Service.TextClassification:
                return "sc";
            case Service.NSFWFilterText:
                return "nsfw_filter-text";
            case Service.NSFWFilterImage:
                return "nsfw_filter-image";
            case Service.TTS:
                return "tts";
            case Service.UVR:
                return "uvr";
            case Service.ImageToImage:
                return "img2img";
            case Service.QuestionAnswering:
                return "qa";
            default:
                throw new Error("Could not parse service.");
        }
    }

    static FromInt(ServiceID: number): Service
    {
        return ServiceID as Service;
    }

    static ToInt(ServiceName: Service): number
    {
        return ServiceName;
    }

    static AutoConvert(ServiceName: string | number): Service
    {
        if (typeof ServiceName == "string")
        {
            return isNaN(Number(ServiceName)) ? this.FromString(ServiceName) : this.FromInt(Number(ServiceName));
        }

        return this.FromInt(ServiceName);
    }
}

export class InternetSearchManager
{
    static FromString(TypeName: string): InternetSearchOptions
    {
        switch (TypeName.toLowerCase())
        {
            case "qa":
                return InternetSearchOptions.QuestionAnswering;
            case "chatbot":
                return InternetSearchOptions.Chatbot;
            case "qa-chatbot":
                return InternetSearchOptions.QuestionAnswering_Chatbot;
            case "chatbot-qa":
                return InternetSearchOptions.Chatbot_QuestionAnswering;
            default:
                throw new Error("Could not parse internet search options.");
        }
    }

    static ToString(TypeName: InternetSearchOptions): string
    {
        switch (TypeName)
        {
            case InternetSearchOptions.QuestionAnswering:
                return "qa";
            case InternetSearchOptions.Chatbot:
                return "chatbot";
            case InternetSearchOptions.QuestionAnswering_Chatbot:
                return "qa-chatbot";
            case InternetSearchOptions.Chatbot_QuestionAnswering:
                return "chatbot-qa";
            default:
                throw new Error("Could not parse internet search options.");
        }
    }

    static FromInt(ServiceID: number): InternetSearchOptions
    {
        return ServiceID as InternetSearchOptions;
    }

    static ToInt(ServiceName: InternetSearchOptions): number
    {
        return ServiceName;
    }

    static AutoConvert(ServiceName: string | number): InternetSearchOptions
    {
        if (typeof ServiceName == "string")
        {
            return isNaN(Number(ServiceName)) ? this.FromString(ServiceName) : this.FromInt(Number(ServiceName));
        }

        return this.FromInt(ServiceName);
    }
}