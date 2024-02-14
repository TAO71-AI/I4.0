using System;
using System.IO;

namespace TAO.Engine
{
    public static class Log
    {
        public static bool AllowLogs = true;
        public static bool ShowLogsOnTerminal = false;

        public static void WriteCustom(string Message)
        {
            if (AllowLogs)
            {
                string date = DateTime.Now.ToShortDateString();

                if (!File.ReadAllText("Logs/latest.txt").Contains("[" + date + "]"))
                {
                    File.WriteAllText("Logs/latest.txt", File.ReadAllText("Logs/latest.txt") + "[" + date + "]\n");
                }

                File.WriteAllText("Logs/latest.txt", File.ReadAllText("Logs/latest.txt") + Message + "\n");

                if (ShowLogsOnTerminal)
                {
                    Console.WriteLine(Message);
                }
            }
        }

        public static void WriteMessage(string Message)
        {
            WriteCustom("[MESSAGE] " + Message);
        }

        public static void WriteWarning(string Message)
        {
            WriteCustom("[WARNING] " + Message);
        }

        public static void WriteError(string Message)
        {
            WriteCustom("[ERROR] " + Message);
        }
    }
}