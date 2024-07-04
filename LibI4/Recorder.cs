using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Media;

namespace TAO71.I4
{
    public static class Recorder
    {
        private static readonly string MicrophonePythonCode = "import speech_recognition as sr\n" +
            "recognizer = sr.Recognizer()\nwith sr.Microphone() as source:\n    data = recognizer.listen(source)\n" +
            "with open(\"[$PATH]tmp_whisper_audio.wav\", \"wb\") as f:\n    f.write(data.get_wav_data())\n    f.close()";
        private static readonly string SystemSoundPythonCode = "import soundcard as sc\nimport soundfile as sf\nimport sys\n" +
            "sample = 48000\nrecord_time = 5\nfor arg in sys.argv:\n    if (arg.startswith(\"sample=\")):\n        sample = int(arg[7:].strip())\n" +
            "    elif (arg.startswith(\"time=\")):\n        record_time = float(arg[5:].strip())\n" +
        	"with sc.get_microphone(id = str(sc.default_speaker().name), include_loopback = True) as mic:\n" +
        	"    data = mic.record(numframes = sample * record_time)\n    sf.write(file = \"[$PATH]tmp_sc_audio.wav\", data = data[:, 0], samplerate = sample)";
        private static readonly string ScreenshotPythonCode = "from PIL import ImageGrab, Image\nimport sys\nfrom screeninfo import get_monitors\nimport numpy as np\n" +
        	"screen = -1\nmonitors = get_monitors()\nfor arg in sys.argv:\n    if (arg.startswith(\"mon=\")):\n        screen = int(arg[4:])\n" +
        	"if (screen >= len(monitors)):\n    print(\"Selected monitor was greater than the active monitors. Using default.\")\n    screen = -1\n" +
            "screenshot = ImageGrab.grab()\nif (screen >= 0):\n    (x, y, w, h) = (monitors[screen].x, monitors[screen].y, monitors[screen].width, monitors[screen].height)\n" +
            "    print(\"Using monitor \" + str(screen) + \": (\" + str(x) + \", \" + str(y) + \"), (\" + str(w) + \", \" + str(h) + \")\")\n" +
        	"    screenshot = np.array(screenshot)\n    screenshot = screenshot[y:y + h, x:x + w]\n    screenshot = Image.fromarray(screenshot)\n" +
        	"else:\n    print(\"Using ALL monitors.\")\nscreenshot.save(\"[$PATH]tmp_pil_image.png\")";
        public static List<string> Commands = new List<string>()
        {
            "py",
            "python",
            "python3"
        };
        public static string Path = "";

        private static (int, string) RunCommand(string Args = "")
        {
            (int, string) lcmd = (-1, "");

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

                    string output = p.StandardOutput.ReadToEnd().TrimStart().TrimEnd();

                    if (output.Length == 0)
                    {
                        output = p.StandardError.ReadToEnd().TrimStart().TrimEnd();
                    }

                    lcmd = (p.ExitCode, output);

                    if (p.ExitCode == 0)
                    {
                        break;
                    }
                }
                catch
                {
                    continue;
                }
            }

            return lcmd;
        }

        public static void InstallDependencies()
        {
            RunCommand("-m ensurepip");
            RunCommand("-m pip install --break-system-packages --upgrade pyaudio SpeechRecognition soundcard soundfile Pillow screeninfo numpy");
        }

        public static byte[] GetMicData()
        {
            string path = Path;
            byte[] dataB = new byte[0];

            if (!path.EndsWith("/") && path.Trim().Length > 0)
            {
                path += "/";
            }

            string code = MicrophonePythonCode;
            code = code.Replace("[$PATH]", path);

            if (!File.Exists(path + "tmp_whisper_audio.py"))
            {
                File.Create(path + "tmp_whisper_audio.py").Close();
            }

            File.WriteAllText(path + "tmp_whisper_audio.py", code);
            (int, string) data = RunCommand(path + "tmp_whisper_audio.py");

            if (data.Item1 == 0)
            {
                dataB = File.ReadAllBytes(path + "tmp_whisper_audio.wav");
            }
            else
            {
                throw new Exception("Error! Process did not end at exit code 0: " + data.Item2);
            }

            return dataB;
        }

        public static byte[] GetSystemSoundData(float SecondsToRecord = 5)
        {
            string path = Path;
            byte[] dataB = new byte[0];

            if (!path.EndsWith("/") && path.Trim().Length > 0)
            {
                path += "/";
            }

            string code = SystemSoundPythonCode;
            code = code.Replace("[$PATH]", path);

            if (!File.Exists(path + "tmp_ss_audio.py"))
            {
                File.Create(path + "tmp_ss_audio.py").Close();
            }

            File.WriteAllText(path + "tmp_ss_audio.py", code);
            (int, string) data = RunCommand(path + "tmp_ss_audio.py time=" + SecondsToRecord);

            if (data.Item1 == 0)
            {
                dataB = File.ReadAllBytes(path + "tmp_sc_audio.wav");
            }

            return dataB;
        }

        public static byte[] GetScreenshot(int Monitor = -1)
        {
            string path = Path;
            byte[] dataB = new byte[0];

            if (!path.EndsWith("/") && path.Trim().Length > 0)
            {
                path += "/";
            }

            string code = ScreenshotPythonCode;
            code = code.Replace("[$PATH]", path);

            if (!File.Exists(path + "tmp_screenchot.py"))
            {
                File.Create(path + "tmp_screenchot.py").Close();
            }

            File.WriteAllText(path + "tmp_screenchot.py", code);
            (int, string) data = RunCommand(path + "tmp_screenchot.py mon=" + Monitor.ToString());

            if (data.Item1 == 0)
            {
                dataB = File.ReadAllBytes(path + "tmp_pil_image.png");
            }

            return dataB;
        }
    }
}