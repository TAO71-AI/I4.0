using System;
using System.IO;
using OpenTK;
using OpenTK.Graphics;
using OpenTK.Graphics.OpenGL;

namespace TAO.Engine.OpenGL.OpenGLCore
{
    public class TCustomShader
    {
        public string ShaderCode = "";
        private int ShaderID = -1;
        public ShaderType SType = ShaderType.VertexShader;

        public void Create()
        {
            if (ShaderCode.Trim().Length > 0)
            {
                ShaderID = GL.CreateShader(SType);
                GL.ShaderSource(ShaderID, ShaderCode);
            }
        }

        public void CompileShader()
        {
            if (ShaderCode.Trim().Length > 0)
            {
                GL.CompileShader(ShaderID);
            }
        }

        public void Attach(int Program)
        {
            if (ShaderCode.Trim().Length > 0)
            {
                GL.AttachShader(Program, ShaderID);
            }
        }

        public void Detach(int Program)
        {
            if (ShaderCode.Trim().Length > 0)
            {
                GL.DetachShader(Program, ShaderID);
            }
        }

        public void Delete()
        {
            if (ShaderCode.Trim().Length > 0)
            {
                GL.DeleteShader(ShaderID);
            }
        }
    }

    public class TShader
    {
        public TCustomShader VertexShader = new TCustomShader()
        {
            ShaderCode = "",
            SType = ShaderType.VertexShader
        };
        public TCustomShader FragmentShader = new TCustomShader()
        {
            ShaderCode = "",
            SType = ShaderType.FragmentShader
        };

        public static TShader FromCode(string Code)
        {
            string[] lines = Code.Split('\n', ';');
            string vertexCode = "";
            string fragmentCode = "";
            TShader shader = new TShader();
            bool vertex = false;
            bool fragment = false;

            foreach (string line in lines)
            {
                if (vertex && fragment)
                {
                    throw new Exception("You can't code the vertex and fragment shaders at the same time.");
                }

                if (line.ToLower().Trim() == "[vertex]")
                {
                    vertex = true;
                }
                else if (line.ToLower().Trim() == "[end_vertex]")
                {
                    vertex = false;
                }
                else if (line.ToLower().Trim() == "[fragment]")
                {
                    fragment = true;
                }
                else if (line.ToLower().Trim() == "[end_fragment]")
                {
                    fragment = false;
                }

                if (vertex)
                {
                    vertexCode += line + "\n";
                }
                else if (fragment)
                {
                    fragmentCode += line + "\n";
                }
            }

            shader.VertexShader.ShaderCode = vertexCode;
            shader.FragmentShader.ShaderCode = fragmentCode;

            return shader;
        }

        public static TShader FromFile(string FileName, bool FromMods = false)
        {
            DiskData.CheckData();
            string filePath = FromMods ? "Mods/Shaders/" : "Assets/Shaders/";

            if (!File.Exists(filePath + FileName + ".tshader"))
            {
                throw new Exception("The file '" + (filePath + FileName + ".tshader") + "' doesn't exists.");
            }

            return FromCode(File.ReadAllText(filePath + FileName + ".tshader"));
        }
    }
}