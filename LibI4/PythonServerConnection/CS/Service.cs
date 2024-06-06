using System;

namespace TAO.I4.PythonManager
{
    public enum Service
    {
        Chatbot = 0,
        CustomCommand = 1,
        ImageGeneration = 2,
        ImageToText = 3,
        WhisperSTT = 4,
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
        None = -1
    }

    public static class ServiceManager
    {
        public static Service FromString(string ServiceName)
        {
            ServiceName = ServiceName.ToLower();

            switch (ServiceName)
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
                case "whisper":
                    return Service.WhisperSTT;
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
            }

            throw new Exception("Could not parse service.");
        }

        public static string ToString(Service ServiceName)
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
                case Service.WhisperSTT:
                    return "whisper";
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
            }

            throw new Exception("Could not parse service.");
        }

        public static Service FromInt(int ServiceID)
        {
            try
            {
                return (Service)ServiceID;
            }
            catch
            {
                throw new Exception("Could not fing service with the ID '" + ServiceID.ToString() + "'.");
            }
        }

        public static int ToInt(Service ServiceName)
        {
            return (int)ServiceName;
        }

        public static Service AutoConvert(string ServiceName)
        {
            return FromString(ServiceName);
        }

        public static Service AutoConvert(int ServiceID)
        {
            return FromInt(ServiceID);
        }

        public static string AutoConvert(Service ServiceName)
        {
            return ToString(ServiceName);
        }
    }
}