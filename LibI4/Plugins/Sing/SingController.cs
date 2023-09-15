using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using TAO.I4.Plugins.Espeak;

namespace TAO.I4.Plugins.Sing
{
    public static class SingController
    {
        public static List<SongData> Songs = new List<SongData>();
        public static Action<SongData> OnStartSingingAction = null;
        public static Action<(int, string, VoiceData)> OnSayAction = null;
        public static Action<SongData> OnEndSingingAction = null;

        public static void PlaySong(SongData Song, bool SaySongName = true)
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

            if (Songs.Count > SongIndex)
            {
                int lastMs = 0;
                VoiceData currentVoice = SpeakManager.DefaultVoice;
                MusicPlayer player = new MusicPlayer("Sing_Plugin/" + Songs[SongIndex].SongInstrumental);
                string lastDialog = "";

                if (OnStartSingingAction != null)
                {
                    OnStartSingingAction.Invoke(Songs[SongIndex]);
                }

                if (SaySongName)
                {
                    SpeakManager.DefaultVoice = SpeakManager.DefaultEnglish;
                    SpeakManager.SpeakNoAsync("Singing " + Songs[SongIndex].Name + ".");
                    SpeakManager.DefaultVoice = currentVoice;
                }

                if (Songs[SongIndex].DefaultVoice != null)
                {
                    SpeakManager.DefaultVoice = Songs[SongIndex].DefaultVoice;
                }

                player.Play();

                foreach ((int, string, VoiceData) index in Songs[SongIndex].SongLyrics)
                {
                    Thread.Sleep(index.Item1 - lastMs);

                    lastMs = index.Item1;
                    lastDialog = index.Item2;

                    if (Songs[SongIndex].UseVoice)
                    {
                        if (index.Item3 != null)
                        {
                            SpeakManager.DefaultVoice = index.Item3;
                        }
                        else
                        {
                            SpeakManager.DefaultVoice = Songs[SongIndex].DefaultVoice;
                        }

                        SpeakManager.Speak(index.Item2);
                    }

                    if (OnSayAction != null)
                    {
                        OnSayAction.Invoke(index);
                    }
                }

                SpeakManager.DefaultVoice = currentVoice;
                player.Stop();

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

        public static SongData SearchByName(string SongName)
        {
            foreach (SongData song in Songs)
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
    }

    public class SongData
    {
        public string Name = "";
        public string SongInstrumental = "";
        public VoiceData DefaultVoice = null;
        public bool UseVoice = true;
        public List<(int, string, VoiceData)> SongLyrics = new List<(int, string, VoiceData)>();

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