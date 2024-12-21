using System.Collections.Generic;

namespace TAO71.I4.PythonManager
{
    public class Config
    {
        // General
        public List<string> Servers = new List<string>()
        {
            "127.0.0.1",            // Localhost
            "tao71.sytes.net"       // TAO71 Server
        };
        public string DefaultImagesProgram = "";         // Leave empty to use the system's default
        public string DefaultAudiosProgram = "";         // Leave empty to use the system's default
        public string ServerAPIKey = "";
        public bool AllowDataShare = true;

        // Chatbot
        public string Chatbot_ExtraSystemPrompts = "";
        public bool[] Chatbot_AllowServerSystemPrompts = new bool[2]
        {
            // (I4.0 personality and tools, extra system prompts from the server's configuration)
            true, true
        };
        public string Chatbot_Conversation = "Client";
        public string? Chatbot_AIArgs = null;
        public bool Chatbot_SimulatedVision_Image2Text = true;
        public int Chatbot_SimulatedVision_Image2Text_Index = -1;
        public bool Chatbot_SimulatedVision_ObjectDetection = true;
        public int Chatbot_SimulatedVision_ObjectDetection_Index = -1;

        // Text2Image
        public int Text2Image_Width = -1;
        public int Text2Image_Height = -1;
        public float Text2Image_GuidanceScale = -1;
        public int Text2Image_Steps = -1;

        // Image2Text
        // Nothing to configure

        // Voice Recognition
        // Nothing to configure

        // Text2Audio
        // Nothing to configure

        // Depth Estimarion
        // Nothing to configure

        // Object Detection
        // Nothing to configure

        // RVC
        public int RVC_FilterRadius = 3;
        public float RVC_Protect = 0.33f;
        public int RVC_F0 = 0;
        public float RVC_IndexRate = 0.75f;
        public float RVC_MixRate = 0.25f;

        // Translator
        // Nothing to configure

        // Text Classification
        // Nothing to configure

        // NSFW Filter (Text)
        // Nothing to configure

        // NSFW Filter (Image)
        // Nothing to configure

        // TTS
        public string TTS_Voice = "espeak-f1";
        public string TTS_Language = "en-us";
        public float TTS_Pitch = 1;
        public float TTS_Speed = 1;

        // UVR
        public int UVR_Agg = 10;

        // Image2Image
        public int Image2Image_Steps = 10;

        // Question Answering
        // Nothing to configure
    }
}