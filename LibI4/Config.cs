using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Runtime.InteropServices;

namespace TAO.I4
{
    public static class Config
    {
        public static AI_StateOfHumor CurrentStateOfHumor = AI_StateOfHumor.Neutral;

        public static PlatformID GetOS()
        {
            return Environment.OSVersion.Platform;
        }

        public static Architecture GetArch()
        {
            return RuntimeInformation.OSArchitecture;
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
                "[CONFIG(speak_voice_lang)] " + SpeakManager.DefaultVoice.Code + "\n" +
                "[CONFIG(speak_voice_gender)] " + SpeakManager.DefaultVoice.Gender + "\n" +
                "[CONFIG(speak_voice_speed)] " + SpeakManager.DefaultVoice.Speed + "\n"
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
                        SpeakManager.DefaultVoice.Code = val;
                    }
                    else if (config == "speak_voice_gender")
                    {
                        SpeakManager.DefaultVoice.Gender = val;
                    }
                    else if (config == "speak_voice_speed")
                    {
                        SpeakManager.DefaultVoice.Speed = float.Parse(val.Replace(".", ","));
                    }
                }
            }

            if (File.Exists("Temp/StateOfHumor.aistate"))
            {
                try
                {
                    CurrentStateOfHumor = (AI_StateOfHumor)Convert.ToInt32(File.ReadAllText("Temp/StateOfHumor.aistate"));
                }
                catch
                {
                    CurrentStateOfHumor = AI_StateOfHumor.Neutral;
                }
            }
            else
            {
                CurrentStateOfHumor = AI_StateOfHumor.Neutral;

                File.Create("Temp/StateOfHumor.aistate").Close();
                File.WriteAllText("Temp/StateOfHumor.aistate", ((int)AI_StateOfHumor.Neutral).ToString());
            }
        }

        public static string DictionaryToJson(Dictionary<object, object> Dictionary)
        {
            string jsonDict = "{";

            foreach (object key in Dictionary.Keys)
            {
                jsonDict += "\"" + key + "\": \"" + Dictionary[key] + "\"";
            }

            jsonDict += "}";
            return jsonDict;
        }

        public static string ArrayToJson(params object[] Array)
        {
            string jsonArray = "[";

            foreach (object obj in Array)
            {
                jsonArray += "\"" + obj.ToString() + "\"";
            }

            jsonArray += "]";
            return jsonArray;
        }

        public static class InstallDependencies
        {
            private static void Install(string baseCommand, string updateCommand, string installCommand, string dependencies)
            {
                Process.Start("sudo", baseCommand + " " + updateCommand).WaitForExit();
                Process.Start("sudo", baseCommand + " " + installCommand + " " + dependencies).WaitForExit();
            }

            public static void InstallUsingApt()
            {
                //For Ubuntu, Debian, Etc...
                Install("apt", "update", "install", Dependencies.ForApt);
            }

            public static void InstallUsingPacman()
            {
                //For Arch Linux
                Install("pacman", "-Sy", "-S", Dependencies.ForPacman);
            }

            public static void InstallUsingDnf()
            {
                //For Fedora
                Install("dnf", "update", "install", Dependencies.ForDnf);
            }

            public static void InstallUsingPkg()
            {
                //For FreeBSD
                Install("pkg", "update", "install", Dependencies.ForPkg);
            }

            public static void InstallUsingPip()
            {
                Process.Start("pip", "install " + Dependencies.ForPip).Start();
            }

            public static void WindowsOrMacOSWarning()
            {
                PlatformID os = GetOS();

                if (os != PlatformID.Unix)
                {
                    Console.WriteLine("If you don't have installed the required dependencies for Windows or MacOS, " +
                    "please install them.");
                    Console.WriteLine("Please see DEPENDENCIES.txt file.");

                    if (!File.Exists("DEPENDENCIES.txt"))
                    {
                        File.Create("DEPENDENCIES.txt").Close();
                    }

                    File.WriteAllText("DEPENDENCIES.txt", "Dependencies list:\n" +
                        "1. eSpeak-ng\n" +
                        "2. Python3 (or Python)\n" +
                        "3. Python pip\n"
                    );
                }
            }

            public static class Dependencies
            {
                public static string ForApt = "espeak-ng python3 python3-pip";
                public static string ForPacman = "espeak-ng python python-pip";
                public static string ForDnf = "espeak-ng python3 python3-pip";
                public static string ForPkg = "espeak-ng python3 py38-pip";
                public static string ForPip = "tensorflow torch sockets numpy";
            }
        }

        public enum AI_StateOfHumor
        {
            Neutral = -1,
            Happy = 0,
            Sad = 1,
            Angry = 2,
            Scared = 3
        }
    }
}