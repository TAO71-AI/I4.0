using System;
using System.Diagnostics;
using System.Threading;

namespace TAO.I4
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