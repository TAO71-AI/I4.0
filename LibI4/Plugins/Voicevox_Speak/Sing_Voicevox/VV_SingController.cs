﻿using System;
using System.Collections.Generic;
using System.IO;
using System.Media;
using System.Threading;
using NAudio.Wave;

namespace TAO.I4.Plugins.Voicevox.Sing
{
    public static class VV_SingController
    {
        public static List<VV_SongData> Songs = new List<VV_SongData>();
        public static VV_VoiceData DefaultVoice = new VV_VoiceData(1, 1);
        public static bool ForceTemporal = false;
        public static Action<VV_SongData> OnStartSingingAction = null;
        public static Action<(int, string, VV_VoiceData)> OnSayAction = null;
        public static Action<VV_SongData> OnEndSingingAction = null;
        public static string SongNameMessage = "Singing [$SONG]";

        public static void PlaySong(VV_SongData Song, bool SaySongName = true)
        {
            if (!Songs.Contains(Song))
            {
                Songs.Add(Song);
            }

            PlaySong(Songs.IndexOf(Song), SaySongName);
        }

        public static void PlaySong(int SongIndex, bool SaySongName = true)
        {
            if (!Directory.Exists("Sing_Plugin/"))
            {
                Directory.CreateDirectory("Sing_Plugin/");
            }

            if (!Directory.Exists("VV_SingPlugin/"))
            {
                Directory.CreateDirectory("VV_SingPlugin/");
            }

            if (!Directory.Exists("VV_SingPlugin/" + Songs[SongIndex].Name))
            {
                Directory.CreateDirectory("VV_SingPlugin/" + Songs[SongIndex].Name);
            }

            if (Songs.Count > SongIndex)
            {
                int lastMs = 0;
                MusicPlayer player = new MusicPlayer("Sing_Plugin/" + Songs[SongIndex].SongInstrumental);
                string lastDialog = "";

                Console.WriteLine("1");

                foreach ((int, string, VV_VoiceData) data in Songs[SongIndex].SongLyrics)
                {
                    if (data.Item2.Trim().Length <= 0)
                    {
                        continue;
                    }

                    if (File.Exists("VV_SingPlugin/" + Songs[SongIndex].Name + "/" + data.Item1 + ".wav"))
                    {
                        continue;
                    }

                    VV_VoiceData vdata = new VV_VoiceData(1, 1);

                    if (data.Item3 == null)
                    {
                        if (Songs[SongIndex].VoiceData == null)
                        {
                            vdata = DefaultVoice;
                        }
                        else
                        {
                            vdata = Songs[SongIndex].VoiceData;
                        }
                    }
                    else
                    {
                        vdata = data.Item3;
                    }

                    File.Create("VV_SingPlugin/" + Songs[SongIndex].Name + "/" + data.Item1 + ".wav").Close();
                    File.WriteAllBytes("VV_SingPlugin/" + Songs[SongIndex].Name + "/" + data.Item1 + ".wav",
                        Voicevox_ServerConnection.SendToServer(new TParameter[]
                        {
                            new TParameter("text", data.Item2),
                            new TParameter("speaker", vdata.Speaker.ToString(), TParamType.GET),
                            new TParameter("key", "[$API]"),
                            new TParameter("speed", vdata.Velocity.ToString().Replace(",", "."), TParamType.GET),
                            new TParameter("velocity", vdata.Velocity.ToString().Replace(",", "."), TParamType.GET)
                        }, -1).Result);
                }

                Console.WriteLine("2");

                if (OnStartSingingAction != null)
                {
                    OnStartSingingAction.Invoke(Songs[SongIndex]);
                }

                if (SaySongName)
                {
                    Voicevox_SpeakManager.Speak(
                        SongNameMessage.Replace("[$SONG]", Songs[SongIndex].Name),
                        new TParameter[]
                        {
                            new TParameter("speaker", Voicevox_SpeakManager.DefaultVoice.Speaker.ToString()),
                            new TParameter("speed", Voicevox_SpeakManager.DefaultVoice.Velocity.ToString()),
                            new TParameter("velocity", Voicevox_SpeakManager.DefaultVoice.Velocity.ToString())
                        }
                    );
                }

                player.Play();
                Console.WriteLine("3");

                foreach ((int, string, VV_VoiceData) index in Songs[SongIndex].SongLyrics)
                {
                    Console.WriteLine("Time to sleep: " + (index.Item1 - lastMs).ToString());
                    Thread.Sleep(index.Item1 - lastMs);

                    lastMs = index.Item1;
                    lastDialog = index.Item2;

                    if (index.Item2.Trim().Length > 0)
                    {
                        SoundPlayer vp = new SoundPlayer("VV_SingPlugin/" + Songs[SongIndex].Name + "/" + index.Item1 + ".wav");
                        vp.Load();
                        vp.Play();
                    }

                    if (OnSayAction != null)
                    {
                        OnSayAction.Invoke(index);
                    }
                }

                Console.WriteLine("4");
                player.Stop();

                if (Songs[SongIndex].Temporal || ForceTemporal)
                {
                    foreach ((int, string, VV_VoiceData) data in Songs[SongIndex].SongLyrics)
                    {
                        if (File.Exists("VV_SingPlugin/" + Songs[SongIndex].Name + "/" + data.Item1 + ".wav"))
                        {
                            File.Delete("VV_SingPlugin/" + Songs[SongIndex].Name + "/" + data.Item1 + ".wav");
                        }
                    }
                }

                if (OnEndSingingAction != null)
                {
                    OnEndSingingAction.Invoke(Songs[SongIndex]);
                }
            }
        }

        public static void PlayRandomSong()
        {
            if (Songs.Count < 0)
            {
                return;
            }
            else if (Songs.Count == 0)
            {
                PlaySong(0);
                return;
            }

            PlaySong(new Random().Next(0, Songs.Count));
        }

        public static VV_SongData SearchByName(string SongName)
        {
            foreach (VV_SongData song in Songs)
            {
                if (song.Name.ToLower() == SongName.ToLower())
                {
                    return song;
                }
            }

            return null;
        }

        public static bool ContainsByName(string SongName)
        {
            return SearchByName(SongName) != null;
        }

        public static VV_SongData[] GetSongsAuto()
        {
            if (!Directory.Exists("Sing_Plugin/"))
            {
                Directory.CreateDirectory("Sing_Plugin/");
            }

            List<VV_SongData> songs = new List<VV_SongData>();
            FileInfo[] files = new DirectoryInfo("Sing_Plugin/").GetFiles();

            foreach (FileInfo file in files)
            {
                WaveFileReader wf = new WaveFileReader(file.FullName);
                VV_SongData data = new VV_SongData()
                {
                    Name = file.Name.Substring(0, file.Name.LastIndexOf(".")),
                    SongInstrumental = file.Name,
                    IgnoreLyrics = true,
                    SongLyrics = new List<(int, string, VV_VoiceData)>()
                    {
                        ((int)wf.TotalTime.TotalMilliseconds, "", new VV_VoiceData(1, 1))
                    }
                };

                songs.Add(data);
            }

            return songs.ToArray();
        }
    }

    public class VV_SongData
    {
        public string Name = "";
        public string SongInstrumental = "";
        public VV_VoiceData VoiceData = new VV_VoiceData(1, 1);
        public bool Temporal = false;
        public bool IgnoreLyrics = false;
        public List<(int, string, VV_VoiceData)> SongLyrics = new List<(int, string, VV_VoiceData)>();

        public override string ToString()
        {
            return "Song name: " + Name + "\n   Instrumental: " + SongInstrumental + "\n   " + SongLyrics.Count.ToString() + " lyrics";
        }

        public bool TryGetMS(int Ms, out int Index, List<int> ExceptIndex = null)
        {
            for (int i = 0; i < SongLyrics.Count; i++)
            {
                if (ExceptIndex != null && ExceptIndex.Contains(i))
                {
                    continue;
                }

                if (SongLyrics[i].Item1 == Ms)
                {
                    Index = i;
                    return true;
                }
            }

            Index = -1;
            return false;
        }
    }
}