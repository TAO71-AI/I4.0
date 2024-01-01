using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;

namespace TAO.I4
{
    public static class Recorder
    {
        private static readonly string PythonCode = "import speech_recognition as sr\n" +
            "recognizer = sr.Recognizer()\nwith sr.Microphone() as source:\n    data = recognizer.listen(source)\n" +
            "with open(\"[$PATH]tmp_whisper_audio.wav\", \"wb\") as f:\n    f.write(data.get_wav_data())\n    f.close()";
        public static List<string> Commands = new List<string>()
        {
            "py",
            "python",
            "python3"
        };
        public static string Path = "";

        private static int RunCommand(string Args = "")
        {
            foreach (string cmd in Commands)
            {
                ProcessStartInfo info = new ProcessStartInfo()
                {
                    FileName = cmd,
                    Arguments = Args,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                };
                Process p = new Process();

                try
                {
                    p.StartInfo = info;
                    p.Start();
                    p.WaitForExit();

                    if (p.ExitCode == 0)
                    {
                        return 0;
                    }
                }
                catch
                {
                    continue;
                }
            }

            return -1;
        }

        public static void InstallDependencies()
        {
            RunCommand("-m ensurepip");
            RunCommand("-m pip install --break-system-packages --upgrade SpeechRecognition");
        }

        public static byte[] GetMicData()
        {
            string path = Path;
            byte[] dataB = new byte[0];

            if (!path.EndsWith("/") && path.Trim().Length > 0)
            {
                path += "/";
            }

            string code = PythonCode;
            code = code.Replace("[$PATH]", path);

            if (!File.Exists(path + "tmp_whisper_audio.py"))
            {
                File.Create(path + "tmp_whisper_audio.py").Close();
            }

            File.WriteAllText(path + "tmp_whisper_audio.py", code);
            int data = RunCommand(path + "tmp_whisper_audio.py");

            if (data == 0)
            {
                dataB = File.ReadAllBytes(path + "tmp_whisper_audio.wav");
            }

            return dataB;
        }
    }
}