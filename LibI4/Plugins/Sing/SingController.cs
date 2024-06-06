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
        private static MusicPlayer Player = null;

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

            string snm = SongNameMessage;
            snm = snm.Replace("[$SONG]", Songs[SongIndex].Name).Replace("[$VERSION]", Songs[SongIndex].Version).Replace("[$AUTHOR]", Songs[SongIndex].Author);

            if (snm.Trim().Length > 0)
            {
                Console.WriteLine(snm);
            }

            if (OnStartSingingAction != null)
            {
                OnStartSingingAction.Invoke(Songs[SongIndex]);
            }

            Player = new MusicPlayer(Songs[SongIndex].SongPath);
            Player.PlayUntilEndMiliseconds(Songs[SongIndex].Duration);

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
                SongData[] datas = SongData.GetAllSongsFromFile(file.FullName);

                foreach (SongData data in datas)
                {
                    if (songs.Contains(data))
                    {
                        continue;
                    }

                    songs.Add(data);
                }
            }

            return songs.ToArray();
        }

        public static void StopSinging(int SongIndex, bool ExecuteAction = true)
        {
            Player.Stop();

            if (OnEndSingingAction != null && ExecuteAction)
            {
                OnEndSingingAction.Invoke(Songs[SongIndex]);
            }
        }
    }

    public class SongData
    {
        public string Name = ""; // Optional
        public string Author = ""; // Optional
        public string SongPath = "";
        public int Duration = 0;
        public string Version = "Unknown"; // Optional

        public static SongData[] GetAllSongsFromFile(string FilePath)
        {
            if (!File.Exists(FilePath))
            {
                throw new Exception("File doesn't exists.");
            }

            string text = File.ReadAllText(FilePath);
            string[] songs = text.Split('~');
            List<SongData> datas = new List<SongData>();

            foreach (string s in songs)
            {
                List<string> lines = new List<string>();

                foreach (string data in s.Split('\n'))
                {
                    if (data.TrimStart().TrimEnd().Length == 0)
                    {
                        continue;
                    }

                    lines.Add(data.TrimStart().TrimEnd());
                }

                if (lines.Count == 0)
                {
                    continue;
                }

                datas.Add(FromLines(lines.ToArray()));
                lines.Clear();
            }

            return datas.ToArray();
        }

        public static SongData FromSongFile(string FilePath)
        {
            if (!File.Exists(FilePath))
            {
                throw new Exception("File doesn't exists.");
            }

            string[] lines = File.ReadAllLines(FilePath);
            SongData data = FromLines(lines);

            return data;
        }

        private static SongData FromLines(string[] Lines)
        {
            SongData data = new SongData();

            foreach (string line in Lines)
            {
                string ll = line.ToLower();

                if (ll.StartsWith("name="))
                {
                    data.Name = line.Substring(5);
                }
                else if (ll.StartsWith("author="))
                {
                    data.Author = line.Substring(7);
                }
                else if (ll.StartsWith("path="))
                {
                    data.SongPath = line.Substring(5);
                }
                else if (ll.StartsWith("version="))
                {
                    data.Version = line.Substring(8);
                }
            }

            if (!File.Exists(data.SongPath))
            {
                throw new Exception("Song audio file doesn't exists.");
            }

            WaveFileReader reader = new WaveFileReader(data.SongPath);
            data.Duration = (int)reader.TotalTime.TotalMilliseconds;

            return data;
        }
    }
}