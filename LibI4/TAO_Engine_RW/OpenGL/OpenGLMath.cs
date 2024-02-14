using System;
using OpenTK;
using OpenTK.Graphics;

namespace TAO.Engine.OpenGL
{
    public static class OpenGLMath
    {
        //TVector To Vector
        public static Vector2 TVectorToVector(TVector2 vector)
        {
            return new Vector2(vector.X, vector.Y);
        }

        public static Vector3 TVectorToVector(TVector3 vector)
        {
            return new Vector3(vector.X, vector.Y, vector.Z);
        }

        public static Vector4 TVectorToVector(TVector4 vector)
        {
            return new Vector4(vector.X, vector.Y, vector.Z, vector.W);
        }

        //Vector To TVector
        public static TVector2 TVectorToVector(Vector2 vector)
        {
            return new TVector2(vector.X, vector.Y);
        }

        public static TVector3 TVectorToVector(Vector3 vector)
        {
            return new TVector3(vector.X, vector.Y, vector.Z);
        }

        public static TVector4 TVectorToVector(Vector4 vector)
        {
            return new TVector4(vector.X, vector.Y, vector.Z, vector.W);
        }

        //TVector To Color4
        public static Color4 VectorToColor(TVector3 vector)
        {
            return new Color4(vector.X, vector.Y, vector.Z, 1);
        }

        public static Color4 VectorToColor(TVector4 vector)
        {
            return new Color4(vector.X, vector.Y, vector.Z, vector.W);
        }

        public static Color4[] VectorToColor(TVector3[] vectors)
        {
            Color4[] colors = new Color4[vectors.Length];

            for (int i = 0; i < colors.Length; i++)
            {
                colors[i] = VectorToColor(vectors[i]);
            }

            return colors;
        }

        public static Color4[] VectorToColor(TVector4[] vectors)
        {
            Color4[] colors = new Color4[vectors.Length];

            for (int i = 0; i < colors.Length; i++)
            {
                colors[i] = VectorToColor(vectors[i]);
            }

            return colors;
        }

        public static TVector4[] ColorToTVector(Color4[] colors)
        {
            TVector4[] vectors = new TVector4[colors.Length];

            for (int i = 0; i < vectors.Length; i++)
            {
                vectors[i] = new TVector4(colors[i].R, colors[i].G, colors[i].B, colors[i].A);
            }

            return vectors;
        }

        //Vector To Color4
        public static Color4 VectorToColor(Vector3 vector)
        {
            return new Color4(vector.X, vector.Y, vector.Z, 1);
        }

        public static Color4 VectorToColor(Vector4 vector)
        {
            return new Color4(vector.X, vector.Y, vector.Z, vector.W);
        }

        public static Color4[] VectorToColor(Vector3[] vectors)
        {
            Color4[] colors = new Color4[vectors.Length];

            for (int i = 0; i < colors.Length; i++)
            {
                colors[i] = VectorToColor(vectors[i]);
            }

            return colors;
        }

        public static Color4[] VectorToColor(Vector4[] vectors)
        {
            Color4[] colors = new Color4[vectors.Length];

            for (int i = 0; i < colors.Length; i++)
            {
                colors[i] = VectorToColor(vectors[i]);
            }

            return colors;
        }

        //Extra Colors
        public static class ExtraColorMath
        {
            //With bytes
            public static Color4 Add(Color4 a, byte b)
            {
                return new Color4
                (
                    MathHelper.Clamp(a.R + ((float)b / 255), 0, 1),
                    MathHelper.Clamp(a.G + ((float)b / 255), 0, 1),
                    MathHelper.Clamp(a.B + ((float)b / 255), 0, 1),
                    MathHelper.Clamp(a.A + ((float)b / 255), 0, 1)
                );
            }

            public static Color4 Subtract(Color4 a, byte b)
            {
                return new Color4
                (
                    MathHelper.Clamp(a.R - ((float)b / 255), 0, 1),
                    MathHelper.Clamp(a.G - ((float)b / 255), 0, 1),
                    MathHelper.Clamp(a.B - ((float)b / 255), 0, 1),
                    MathHelper.Clamp(a.A - ((float)b / 255), 0, 1)
                );
            }

            public static Color4 Multiply(Color4 a, byte b)
            {
                return new Color4
                (
                    MathHelper.Clamp(a.R * ((float)b / 255), 0, 1),
                    MathHelper.Clamp(a.G * ((float)b / 255), 0, 1),
                    MathHelper.Clamp(a.B * ((float)b / 255), 0, 1),
                    MathHelper.Clamp(a.A * ((float)b / 255), 0, 1)
                );
            }

            public static Color4 Divide(Color4 a, byte b)
            {
                return new Color4
                (
                    MathHelper.Clamp(a.R / ((float)b / 255), 0, 1),
                    MathHelper.Clamp(a.G / ((float)b / 255), 0, 1),
                    MathHelper.Clamp(a.B / ((float)b / 255), 0, 1),
                    MathHelper.Clamp(a.A / ((float)b / 255), 0, 1)
                );
            }

            //With other colors
            public static Color4 Add(Color4 a, Color4 b)
            {
                return new Color4
                (
                    MathHelper.Clamp(a.R + b.R, 0, 1),
                    MathHelper.Clamp(a.G + b.G, 0, 1),
                    MathHelper.Clamp(a.B + b.B, 0, 1),
                    MathHelper.Clamp(a.A + b.A, 0, 1)
                );
            }

            public static Color4 Subtract(Color4 a, Color4 b)
            {
                return new Color4
                (
                    MathHelper.Clamp(a.R - b.R, 0, 1),
                    MathHelper.Clamp(a.G - b.G, 0, 1),
                    MathHelper.Clamp(a.B - b.B, 0, 1),
                    MathHelper.Clamp(a.A - b.A, 0, 1)
                );
            }

            public static Color4 Multiply(Color4 a, Color4 b)
            {
                return new Color4
                (
                    MathHelper.Clamp(a.R * b.R, 0, 1),
                    MathHelper.Clamp(a.G * b.G, 0, 1),
                    MathHelper.Clamp(a.B * b.B, 0, 1),
                    MathHelper.Clamp(a.A * b.A, 0, 1)
                );
            }

            public static Color4 Divide(Color4 a, Color4 b)
            {
                return new Color4
                (
                    MathHelper.Clamp(a.R / b.R, 0, 1),
                    MathHelper.Clamp(a.G / b.G, 0, 1),
                    MathHelper.Clamp(a.B / b.B, 0, 1),
                    MathHelper.Clamp(a.A / b.A, 0, 1)
                );
            }
        }
    }
}