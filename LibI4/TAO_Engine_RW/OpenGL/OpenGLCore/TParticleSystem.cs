using System;
using System.Collections.Generic;

namespace TAO.Engine.OpenGL.OpenGLCore
{
    public class TParticleSystem
    {
        public TObject Particle;
        public int MaxParticles = 50;
        public TVector3 ParticleSpeed = TVector3.Zero();
        public (TVector3, TVector3) ParticleNoisePos = (-TVector3.One(), TVector3.One());
        public (TVector3, TVector3) ParticleNoiseScl = (-TVector3.One(), TVector3.One());
        public TVector3 ParticleNoiseAxis = TVector3.Zero();
        public readonly List<TObject> Particles = new List<TObject>();

        public TParticleSystem(TObject Particle)
        {
            this.Particle = Particle;
        }

        public void CreateParticles()
        {
            while (Particles.Count < MaxParticles)
            {
                Particles.Add(Particle.Clone());
            }
        }

        public void Reset()
        {
            for (int i = 0; i < Particles.Count; i++)
            {
                Particles[i].Delete();
            }

            Particles.Clear();
            CreateParticles();
        }

        public void ResetPos()
        {
            for (int i = 0; i < Particles.Count; i++)
            {
                Particles[i].Position = Particle.Position;
                Particles[i].Rotation = Particle.Rotation;
                Particles[i].Scale = Particle.Scale;
            }
        }

        private (TVector3, TVector3) CalculateNoise()
        {
            TVector3 noisePos = new TVector3(
                new Random().Next(-500, 500),
                new Random().Next(-500, 500),
                new Random().Next(-500, 500)
            );
            TVector3 noiseScl = new TVector3(
                new Random().Next(-500, 500),
                new Random().Next(-500, 500),
                new Random().Next(-500, 500)
            );

            //Pos
            if (ParticleNoisePos.Item1 == ParticleNoisePos.Item2)
            {
                noisePos = ParticleNoisePos.Item1;
            }
            else
            {
                if (noisePos.X <= 0)
                {
                    noisePos.X = ParticleNoisePos.Item1.X;
                }
                else
                {
                    noisePos.X = ParticleNoisePos.Item2.X;
                }

                if (noisePos.Y <= 0)
                {
                    noisePos.Y = ParticleNoisePos.Item1.Y;
                }
                else
                {
                    noisePos.Y = ParticleNoisePos.Item2.Y;
                }

                if (noisePos.Z <= 0)
                {
                    noisePos.Z = ParticleNoisePos.Item1.Z;
                }
                else
                {
                    noisePos.Z = ParticleNoisePos.Item2.Z;
                }
            }

            //Scl
            if (ParticleNoiseScl.Item1 == ParticleNoiseScl.Item2)
            {
                noiseScl = ParticleNoiseScl.Item1;
            }
            else
            {
                if (noiseScl.X <= 0)
                {
                    noiseScl.X = ParticleNoiseScl.Item1.X;
                }
                else
                {
                    noiseScl.X = ParticleNoiseScl.Item2.X;
                }

                if (noiseScl.Y <= 0)
                {
                    noiseScl.Y = ParticleNoiseScl.Item1.Y;
                }
                else
                {
                    noiseScl.Y = ParticleNoiseScl.Item2.Y;
                }

                if (noiseScl.Z <= 0)
                {
                    noiseScl.Z = ParticleNoiseScl.Item1.Z;
                }
                else
                {
                    noiseScl.Z = ParticleNoiseScl.Item2.Z;
                }
            }

            return (noisePos, noiseScl);
        }

        public void UpdateParticles()
        {
            for (int i = 0; i < Particles.Count; i++)
            {
                (TVector3, TVector3) noise = CalculateNoise();

                Particles[i].Position += ParticleSpeed + ParticleNoiseAxis * noise.Item1;
                Particles[i].Scale += ParticleNoiseAxis * noise.Item2;
            }
        }
    }
}