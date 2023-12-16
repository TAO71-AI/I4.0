using System;
using System.Collections.Generic;
using System.IO;
using System.Media;
using NAudio.Wave;
using TAO.I4.Plugins.Espeak;

namespace TAO.I4.Plugins.Sing
{
    public class MusicPlayer
    {
        private SoundPlayer Player = new SoundPlayer();

        public MusicPlayer(string AudioFile)
        {
            Player.SoundLocation = AudioFile;
        }

        public void Play()
        {
            Player.Play();
        }

        public void Stop()
        {
            Player.Stop();
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
                songs.Add(new SongData()
                {
                    Name = file.Name.Substring(0, file.Name.LastIndexOf(".")),
                    SongInstrumental = file.Name,
                    SongLyrics = new List<(int, string, VoiceData)>()
                    {
                        ((int)wf.TotalTime.TotalSeconds, "", new VoiceData("en", "m1", 1))
                    }
                });
            }

            return songs.ToArray();
        }
    }
}