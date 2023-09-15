using System;
using TAO.I4.PythonManager;

namespace TAO.I4
{
    public static class SpeechRecognition
    {
        public static string Model = "tiny";

        public static string Recognize(string Language, int MaxTime = 5)
        {
            string data = PythonDownloader.ExecutePythonCode("whisper_recognition.py",
                "127.0.0.1 " + PyAIResponse.ReadKeyFromFile() + " " + Language + " " + MaxTime + " " + Model
            ).Item1;

            return data;
        }
    }
}