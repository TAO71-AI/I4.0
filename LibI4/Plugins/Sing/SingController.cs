using System;
using System.Collections.Generic;
using System.IO;
using NAudio.Wave;

namespace TAO.I4.Plugins.Sing
{
    public static class SingController
    {
        public static List<SongData> Songs = new List<SongData>();
        public static Action<SongData> OnStartSingingAction = null;
        public static Action<SongData> OnEndSingingAction = null;
        public static string SongNameMessage = "Singing [$SONG].";

        public static void PlaySong(SongData Song)
        {
            if (!Songs.Contains(Song))
            {
                Songs.Add(Song);
            }

            PlaySong(Songs.IndexOf(Song));
        }

        public static void PlaySong(int SongIndex)
        {
            if (!Directory.Exists("Sing_Plugin/"))
            {
                Directory.CreateDirectory("Sing_Plugin/");
            }

            if (SongIndex >= Songs.Count || SongIndex < 0)
            {
                throw new Exception("Song index must be between 0 and " + (Songs.Count - 1).ToString());
            }

            if (SongNameMessage.Trim().Length > 0)
            {
                Console.WriteLine(SongNameMessage.Replace("[$SONG]", Songs[SongIndex].Name));
            }

            if (OnStartSingingAction != null)
            {
                OnStartSingingAction.Invoke(Songs[SongIndex]);
            }

            MusicPlayer player = new MusicPlayer(Songs[SongIndex].SongPath);
            player.PlayUntilEndMiliseconds(Songs[SongIndex].Duration);

            if (OnEndSingingAction != null)
            {
                OnEndSingingAction.Invoke(Songs[SongIndex]);
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

        public static SongData[] GetSongsAuto()
        {
            if (!Directory.Exists("Sing_Plugin/"))
            {
                Directory.CreateDirectory("Sing_Plugin/");
            }

            List<SongData> songs = new List<SongData>();
            FileInfo[] files = new DirectoryInfo("Sing_Plugin/").GetFiles();

            foreach (FileInfo file in files)
            {
                WaveFileReader wf = new WaveFileReader(file.FullName);
                SongData data = new SongData()
                {
                    Name = file.Name.Substring(0, file.Name.LastIndexOf(".")),
                    SongPath = file.FullName,
                    Duration = (int)wf.TotalTime.TotalMilliseconds
                };

                songs.Add(data);
            }

            return songs.ToArray();
        }
    }

    public class SongData
    {
        public string Name = "";
        public string SongPath = "";
        public int Duration = 0;
    }
}