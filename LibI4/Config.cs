using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
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
                        "1. Python3 (or Python)\n" +
                        "2. Python pip\n"
                    );
                }
            }

            public static class Dependencies
            {
                public static string ForApt = "python3 python3-pip";
                public static string ForPacman = "python python-pip";
                public static string ForDnf = "python3 python3-pip";
                public static string ForPkg = "python3 py38-pip";
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