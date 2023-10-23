using System;
using System.Diagnostics;
using System.IO;
using System.Threading;

namespace TAO.I4.Plugins.Espeak
{
    public static class SpeakManager
    {
        public static readonly VoiceData DefaultEnglish = new VoiceData()
        {
            Code = "en",
            Gender = "f1",
            Speed = 1.5f
        };
        public static readonly VoiceData DefaultSpanish = new VoiceData()
        {
            Code = "es",
            Gender = "f1",
            Speed = 1.5f
        };
        public static VoiceData DefaultVoice = new VoiceData();
        public static Action<string> OnStartSpeakAction = null;
        public static Action<string> OnEndSpeakAction = null;
        public static Process CurrentProcess = null;

        public static string Speak(string message)
        {
            string r = "";

            Thread t = new Thread(() =>
            {
                r = SpeakNoAsync(message);
            });
            t.Priority = ThreadPriority.Lowest;
            t.Start();

            return r;
        }

        public static string SpeakNoAsync(string message)
        {
            Kill();

            if (OnStartSpeakAction != null)
            {
                try
                {
                    OnStartSpeakAction.Invoke(message);
                }
                catch
                {

                }
            }

            string error = "";

            try
            {
                CurrentProcess = Process.Start(
                    "espeak",
                    "-v " + DefaultVoice.Code + "+" + DefaultVoice.Gender +
                    " -s " + (int)(DefaultVoice.Speed * 100) + " " +
                    '"' + message + '"'
                );
                CurrentProcess.WaitForExit();
            }
            catch (Exception ex)
            {
                error = ex.Message;
            }

            if (OnEndSpeakAction != null)
            {
                try
                {
                    OnEndSpeakAction.Invoke(message);
                }
                catch
                {

                }
            }

            if (error.Trim().Length > 0)
            {
                throw new Exception(error);
            }

            return message;
        }

        public static void Kill()
        {
            if (CurrentProcess != null && !CurrentProcess.HasExited)
            {
                try
                {
                    CurrentProcess.Kill();
                    CurrentProcess.Close();

                    CurrentProcess = null;
                }
                catch
                {

                }
            }
        }

        public static void SaveConfig()
        {
            if (!File.Exists("ConfigData.tconf"))
            {
                File.Create("ConfigData.tconf").Close();
            }

            if (!Directory.Exists("Temp/"))
            {
                Directory.CreateDirectory("Temp/");
            }

            File.WriteAllText("ConfigData.tconf",
                "[CONFIG(speak_voice_lang)] " + DefaultVoice.Code + "\n" +
                "[CONFIG(speak_voice_gender)] " + DefaultVoice.Gender + "\n" +
                "[CONFIG(speak_voice_speed)] " + DefaultVoice.Speed + "\n"
            );
        }

        public static void LoadConfig()
        {
            if (!File.Exists("ConfigData.tconf"))
            {
                return;
            }

            string[] lines = File.ReadAllLines("ConfigData.tconf");

            foreach (string line in lines)
            {
                if (line.ToUpper().StartsWith("[CONFIG(") && line.Contains(")] "))
                {
                    string config = line.Substring(8, line.IndexOf(")] ") - 8).ToLower();
                    string val = line.Substring(line.IndexOf(")] ") + 3);

                    if (config == "speak_voice_lang")
                    {
                        DefaultVoice.Code = val;
                    }
                    else if (config == "speak_voice_gender")
                    {
                        DefaultVoice.Gender = val;
                    }
                    else if (config == "speak_voice_speed")
                    {
                        DefaultVoice.Speed = float.Parse(val.Replace(".", ","));
                    }
                }
            }
        }
    }

    public class VoiceData
    {
        public string Code = "en";
        public string Gender = "f1";
        public float Speed = 1.5f;

        public VoiceData()
        {

        }

        public VoiceData(string Code, string Gender, float Speed)
        {
            this.Code = Code;
            this.Gender = Gender;
            this.Speed = Speed;
        }
    }
}