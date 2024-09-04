import { InternetSearchOptions } from "./Service";

export class Config
{
    // General
    Servers: string[] = [
        "127.0.0.1",            // Localhost
        "tao71.sytes.net"       // TAO71 Server
    ];
    DefaultImagesProgram: string = "";         // Leave empty to use the system's default
    DefaultAudiosProgram: string = "";         // Leave empty to use the system's default
    InternetOptions: InternetSearchOptions = InternetSearchOptions.QuestionAnswering;
    ServerAPIKey: string = "";

    // Chatbot
    Chatbot_ExtraSystemPrompts: string = "";
    Chatbot_AllowServerSystemPrompts: boolean | null = null;
    Chatbot_Conversation: string = "Client";
    Chatbot_AIArgs: string | null = null;

    // Text2Image
    Text2Image_Width: number = -1;
    Text2Image_Height: number = -1;
    Text2Image_GuidanceScale: number = -1;
    Text2Image_Steps: number = -1;

    // RVC
    RVC_FilterRadius: number = 3;
    RVC_Protect: number = 0.33;
    RVC_F0: number = 0;
    RVC_Model: string = "";

    // TTS
    TTS_Voice: string = "espeak-f1";
    TTS_Language: string = "en-us";
    TTS_Pitch: number = 1;
    TTS_Speed: number = 1;

    // UVR
    UVR_Agg: number = 10;

    // Image2Image
    Image2Image_Steps: number = 10;
}