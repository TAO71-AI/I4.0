using System;
using System.IO;
using OpenTK;
using OpenTK.Graphics;
using OpenTK.Graphics.OpenGL;
using StbImageSharp;

namespace TAO.Engine.OpenGL.OpenGLCore
{
    public class TTexture
    {
        public readonly int ID = GL.GenTexture();
        public readonly string ImagePath = "";
        public readonly ImageResult Result;
        public TextureMinFilter MinFilter = TextureMinFilter.Linear;
        public TextureMagFilter MagFilter = TextureMagFilter.Linear;
        public TextureWrapMode WrapMode = TextureWrapMode.Repeat;

        public TTexture(string TextureData)
        {
            this.ImagePath = TextureData;
            this.Result = ImageResult.FromMemory(File.ReadAllBytes(TextureData), ColorComponents.RedGreenBlueAlpha);
        }
    }
}