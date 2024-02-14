using System;
using System.Collections.Generic;
using System.IO;
using System.Media;

namespace TAO.Engine.Audio
{
    public static class AudioManager
    {
        public static List<AudioClip> Audios = new List<AudioClip>();

        public static AudioClip CreateAudio(string AudioName, bool FromMods = false)
        {
            AudioClip clip = new AudioClip(AudioName, FromMods);

            Audios.Add(clip);
            return clip;
        }

        public static AudioClip PlayAudio(int Index)
        {
            if (Index < 0 || Index >= Audios.Count)
            {
                return null;
            }

            Audios[Index].Play();
            return Audios[Index];
        }

        public static AudioClip StopAudio(int Index)
        {
            if (Index < 0 || Index >= Audios.Count)
            {
                return null;
            }

            Audios[Index].Stop();
            return Audios[Index];
        }
    }

    public class AudioClip
    {
        public readonly string AudioName;
        private readonly SoundPlayer Player = new SoundPlayer();

        public AudioClip(string AudioName, bool FromMods = false)
        {
            this.AudioName = AudioName;

            Player.SoundLocation = (FromMods ? "Mods/" : "Assets/") + "Audios/" + AudioName;
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
    }
}