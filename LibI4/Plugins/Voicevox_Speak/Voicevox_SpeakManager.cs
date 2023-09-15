using System;
using System.Collections.Generic;
using System.IO;
using System.Media;
using System.Threading;

namespace TAO.I4.Plugins.Voicevox
{
    public static class Voicevox_SpeakManager
    {
        private static SoundPlayer Player = new SoundPlayer();
        public static VV_VoiceData DefaultVoice = new VV_VoiceData(1, 1);
        public static string APIKey = "";
        public static Action<string> OnStartTalking = null;
        public static Action<string> OnEndTalking = null;

        public static void Init()
        {
            if (!File.Exists("Temp/Voicevox_Plugin.wav"))
            {
                File.Create("Temp/Voicevox_Plugin.wav").Close();
                return;
            }

            if (!Directory.Exists("Voicevox_Plugin"))
            {
                Directory.CreateDirectory("Voicevox_Plugin");
            }

            if (!File.Exists("Voicevox_Plugin/APIKey.txt"))
            {
                File.Create("Voicevox_Plugin/APIKey.txt").Close();
            }

            File.Delete("Temp/Voicevox_Plugin.wav");
            Init();
        }

        public static TParameter[] FilterParameters(TParameter[] Parameters, TParameter[] ExtraData = null)
        {
            List<TParameter> prs = new List<TParameter>();

            foreach (TParameter p in Parameters)
            {
                TParameter pa = new TParameter(p.Name, p.Value
                    .Replace("[$SPEED]", DefaultVoice.Velocity.ToString())
                    .Replace("[$VOICE_ID]", DefaultVoice.Speaker.ToString())
                    .Replace("[$API]", APIKey), p.Type
                );

                if (ExtraData != null && ExtraData.Length > 0)
                {
                    foreach (TParameter ea in ExtraData)
                    {
                        pa = new TParameter(pa.Name, pa.Value.Replace(ea.Name, ea.Value), pa.Type);
                    }
                }

                prs.Add(pa);
            }

            return prs.ToArray();
        }

        public static void Speak(string Message, TParameter[] Parameters, int Server = -1, bool AudioFile = false, bool Speak = true)
        {
            //Stop current and check files
            Player.Stop();
            Init();

            //Get audio data from server (internet connection required)
            TParameter[] prs = FilterParameters(Parameters, new TParameter[]
            {
                new TParameter("[$TEXT]", Message),
                new TParameter("[$MESSAGE]", Message)
            });

            if (!AudioFile)
            {
                byte[] data = Voicevox_ServerConnection.SendToServer(prs, Server).Result;
                File.WriteAllBytes("Temp/Voicevox_Plugin.wav", data);
            }
            else
            {
                byte[] data = File.ReadAllBytes(Message);
                File.WriteAllBytes("Temp/Voicevox_Plugin.wav", data);
            }

            //Play the audio
            if (Speak)
            {
                Thread t = new Thread(() =>
                {
                    if (OnStartTalking != null)
                    {
                        try
                        {
                            OnStartTalking.Invoke(Message);
                        }
                        catch
                        {

                        }
                    }
                    
                    Player = new SoundPlayer("Temp/Voicevox_Plugin.wav");
                    Player.Load();
                    Player.PlaySync();

                    Thread.Sleep(500);

                    if (OnEndTalking != null)
                    {
                        try
                        {
                        OnEndTalking.Invoke(Message);
                        }
                        catch
                        {

                        }
                    }
                })
                {
                    Priority = ThreadPriority.Lowest
                };
                t.Start();
            }

            //File.Delete("Temp/Voicevox_Plugin.wav");
        }

        public static void StopSpeaking()
        {
            Player.Stop();
        }
    }

    public class VV_VoiceData
    {
        public int Speaker = 1;
        public float Velocity = 1;

        public VV_VoiceData(int Speaker = 1, float Velocity = 1)
        {
            this.Speaker = Speaker;
            this.Velocity = Velocity;
        }
    }
}