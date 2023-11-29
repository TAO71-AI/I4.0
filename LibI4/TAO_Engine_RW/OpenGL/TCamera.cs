using System;
using OpenTK;
using OpenTK.Graphics;

namespace TAO.Engine.OpenGL
{
    public class TCamera
    {
        public Matrix4 CameraMatrix = Matrix4.Identity;
        public float FOV = 60;
        public float MinDistance = 0.01f;
        public float MaxDistance = 1000;
        public TVector3 Position = TVector3.Zero();
        public TVector3 Scale = TVector3.One();
    }
}