using System;
using OpenTK;
using OpenTK.Graphics;
using OpenTK.Graphics.OpenGL;

namespace TAO.Engine.OpenGL.OpenGLCore
{
    public class TCamera
    {
        public Matrix4 CameraMatrix = Matrix4.Identity;
        public float FOV = 60;
        public float MinDistance = 0.01f;
        public float MaxDistance = 1000;
    }
}