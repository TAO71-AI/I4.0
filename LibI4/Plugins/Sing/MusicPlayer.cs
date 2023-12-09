using System;
using System.IO;
using System.Media;

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
    }
}