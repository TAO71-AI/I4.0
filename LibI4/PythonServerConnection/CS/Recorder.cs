// NOTE: Some functions are still under creation
// WARNING: C# bindings are deprecated. ^-- These functions will not be completed.

using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;
using NAudio.Wave;
using NAudio.CoreAudioApi;
using Timer = System.Timers.Timer;

namespace TAO71.I4
{
    public static class Recorder
    {
        public static byte[] GetMicData(double TimeToRecord)
        {
            Timer? timer = new Timer(TimeToRecord);
            byte[] bytes = new byte[0];

            if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
            {
                WasapiCapture waveIn = new WasapiCapture();
                WaveFileWriter writer = new WaveFileWriter("taud_mic.wav", waveIn.WaveFormat);

                waveIn.DataAvailable += (s, e) =>
                {
                    writer.Write(e.Buffer, 0, e.BytesRecorded);
                };
                waveIn.RecordingStopped += (s, e) =>
                {
                    writer.Dispose();
                    waveIn.Dispose();
                };
                timer.Elapsed += (s, e) =>
                {
                    waveIn.StopRecording();
                };
                
                waveIn.StartRecording();
            }
            else
            {
                Process process = new Process();

                process.StartInfo.FileName = "ffmpeg";
                process.StartInfo.Arguments = "-f pulse -i default -af apad -ar 48000 -ac 1 taud_mic.wav";
                process.StartInfo.RedirectStandardOutput = true;
                process.StartInfo.RedirectStandardError = true;
                process.StartInfo.UseShellExecute = false;
                process.StartInfo.CreateNoWindow = true;

                process.Start();
                timer.Elapsed += (s, e) =>
                {
                    process.Kill();
                };
            }

            timer.Elapsed += (s, e) =>
            {
                timer.Dispose();
                timer = null;
            };
            timer.Start();

            while (timer != null)
            {
                Thread.Sleep(100);
            }

            bytes = File.ReadAllBytes("taud_mic.wav");
            File.Delete("taud_mic.wav");

            return bytes;
        }

        public static byte[] GetSystemSoundData(double TimeToRecord)
        {
            Timer? timer = new Timer(TimeToRecord);
            byte[] bytes = new byte[0];

            if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
            {
                WasapiLoopbackCapture waveIn = new WasapiLoopbackCapture();
                WaveFileWriter writer = new WaveFileWriter("taud_sys.wav", waveIn.WaveFormat);

                waveIn.DataAvailable += (s, e) =>
                {
                    writer.Write(e.Buffer, 0, e.BytesRecorded);
                };
                waveIn.RecordingStopped += (s, e) =>
                {
                    writer.Dispose();
                    waveIn.Dispose();
                };
                timer.Elapsed += (s, e) =>
                {
                    waveIn.StopRecording();
                };

                waveIn.StartRecording();
            }
            else
            {
                Process process = new Process();

                process.StartInfo.FileName = "ffmpeg";
                process.StartInfo.Arguments = "-f pulse -ar 16000 -af apad -ac 1 -i default.monitor taud_sys.wav";
                process.StartInfo.RedirectStandardOutput = true;
                process.StartInfo.RedirectStandardError = true;
                process.StartInfo.UseShellExecute = false;
                process.StartInfo.CreateNoWindow = true;

                process.Start();
                timer.Elapsed += (s, e) =>
                {
                    process.Kill();
                };
            }

            timer.Elapsed += (s, e) =>
            {
                timer.Dispose();
                timer = null;
            };
            timer.Start();

            while (timer != null)
            {
                Thread.Sleep(100);
            }

            bytes = File.ReadAllBytes("taud_sys.wav");
            File.Delete("taud_sys.wav");

            return bytes;
        }

        public static byte[] GetScreenshot(int Monitor = -1)
        {
            return new byte[0]; // TODO
        }
    }
}