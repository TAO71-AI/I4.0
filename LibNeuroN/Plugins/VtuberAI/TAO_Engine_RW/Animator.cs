using System;
using System.Collections.Generic;
using System.Threading;

namespace TAO.Engine
{
    public static class Animator
    {
        public static List<Animation> Animations = new List<Animation>();

        public static void PlayAnimation(int Index, bool Async = true)
        {
            if (Index >= Animations.Count)
            {
                return;
            }

            Animations[Index].Play(Async);
        }

        public static void PlayAnimation(Animation Anim, bool Async = true)
        {
            if (!Animations.Contains(Anim))
            {
                Animations.Add(Anim);
            }

            Anim.Play(Async);
        }
    }

    public class Animation
    {
        public string Name = "";
        public List<(int, Action)> Data = new List<(int, Action)>();
        public static Action<Exception> OnErrorAction = null;

        public void Play(bool Async = true)
        {
            if (Async)
            {
                Thread t = new Thread(() =>
                {
                    Play(false);
                });
                t.Priority = ThreadPriority.Normal;
                t.Start();

                return;
            }

            int LastMs = 0;

            foreach ((int, Action) AnimationData in Data)
            {
                Thread.Sleep(AnimationData.Item1 - LastMs);
                LastMs = AnimationData.Item1;

                try
                {
                    if (AnimationData.Item2 != null)
                    {
                        AnimationData.Item2.Invoke();
                    }
                }
                catch (Exception ex)
                {
                    if (OnErrorAction != null)
                    {
                        OnErrorAction.Invoke(ex);
                    }
                }
            }
        }
    }
}