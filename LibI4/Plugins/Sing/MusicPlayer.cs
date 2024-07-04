using System;
using System.Media;
using System.Threading;

namespace TAO71.I4.Plugins.Sing
{
    public class MusicPlayer
    {
        private SoundPlayer Player;

        public MusicPlayer(string AudioFile)
        {
            Player = new SoundPlayer(AudioFile);
            Player.Load();
        }

        public void Play()
        {
            Player.Play();
        }

        public void Stop()
        {
            Player.Stop();
        }

        public void PlayUntilEndSeconds(float Seconds)
        {
            Player.Play();
            Thread.Sleep((int)(Seconds * 1000));
        }

        public void PlayUntilEndMiliseconds(double Miliseconds)
        {
            PlayUntilEndSeconds((float)(Miliseconds / 1000));
        }
    }
}