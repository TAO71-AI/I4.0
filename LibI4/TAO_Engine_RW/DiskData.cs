using System;
using System.Collections.Generic;
using System.IO;

namespace TAO.Engine
{
    public static class DiskData
    {
        public static bool AllowMods = true;

        public static bool CreateFile(string FileName)
        {
            if (!File.Exists(FileName))
            {
                File.Create(FileName).Close();
                return false;
            }

            return true;
        }

        public static bool CreateDirectory(string DirectoryName)
        {
            if (!Directory.Exists(DirectoryName))
            {
                Directory.CreateDirectory(DirectoryName);
                return false;
            }

            return true;
        }

        public static void CheckData()
        {
            if (AllowMods)
            {
                //Mods directories
                CreateDirectory("Mods/");
                CreateDirectory("Mods/Textures/");
                CreateDirectory("Mods/Textures/UChars/");
                CreateDirectory("Mods/Textures/LChars/");
                CreateDirectory("Mods/Textures/NChars/");
                CreateDirectory("Mods/Textures/SChars/");
                CreateDirectory("Mods/Audios/");
                CreateDirectory("Mods/Models/");
                CreateDirectory("Mods/Scenes/");
                CreateDirectory("Mods/Shaders/");
                CreateDirectory("Mods/OtherData/");
            }

            //Assets directories
            CreateDirectory("Assets/");
            CreateDirectory("Assets/Textures/");
            CreateDirectory("Assets/Textures/UChars/");
            CreateDirectory("Assets/Textures/LChars/");
            CreateDirectory("Assets/Textures/NChars/");
            CreateDirectory("Assets/Textures/SChars/");
            CreateDirectory("Assets/Audios/");
            CreateDirectory("Assets/Models/");
            CreateDirectory("Assets/Scenes/");
            CreateDirectory("Assets/Shaders/");
            CreateDirectory("Assets/OtherData/");

            //Log directories
            CreateDirectory("Logs/");
            CreateFile("Logs/latest.txt");

            //Shaders
            string[] dshaderl = new string[]
            {
                "[VERTEX]",
                "#version 330 core",
                "",
                "layout (location = 0) in vec3 position;",
                "layout (location = 1) in vec3 normal;",
                "layout (location = 2) in vec4 fragColorIn;",
                "uniform mat4 model;",
                "uniform mat4 view;",
                "uniform mat4 projection;",
                "out vec3 fragNormal;",
                "out vec3 fragPos;",
                "out vec4 fragColor;",
                "",
                "void main()",
                "{",
                "    fragNormal = mat3(transpose(inverse(model))) * normal;",
                "    fragPos = vec3(model * vec4(position, 1.0));",
                "    fragColor = fragColorIn;",
                "    ",
                "    gl_Position = projection * view * vec4(fragPos, 1.0);",
                "}",
                "[END_VERTEX]",
                "[FRAGMENT]",
                "#version 330 core",
                "",
                "in vec3 fragNormal;",
                "in vec3 fragPos;",
                "in vec4 fragColor;",
                "uniform vec3 lightPos;",
                "uniform vec3 lightColor;",
                "//out vec4 color;",
                "",
                "void main()",
                "{",
                "    //vec3 lightDir = normalize(lightPos - fragPos);",
                "    //float ambientStrength = 0.1;",
                "    //float diffuseStrength = max(dot(fragNormal, lightDir), 0.0);",
                "    //float specularStrength = pow(max(dot(reflect(-lightDir, fragNormal), normalize(-fragPos)), 0.0), 32);",
                "    //vec3 ambient = ambientStrength * lightColor;",
                "    //vec3 diffuse = diffuseStrength * lightColor;",
                "    //vec3 specular = specularStrength * lightColor;",
                "    //vec4 finalColor = fragColor * vec4(ambient + diffuse + specular, 1.0);",
                "    ",
                "    gl_FragColor = vec4(0, 0, 0, 1);",
                "}",
                "[END_FRAGMENT]"
            };
            string dshader = "";

            foreach (string dshaderln in dshaderl)
            {
                dshader += dshaderln + "\n";
            }

            //Models importation data documentation
            CreateFile("Assets/Models/TMD_Documentation.txt");
            File.WriteAllText("Assets/Models/TMD_Documentation.txt", "" +
                "----------------------------\n" +
                "TAO Model Data Documentation\n" +
                "----------------------------\n" +
                "\n" +
                "vert [Vector3] - Add a vertex.\n" +
                "nor [Vector3] - Add a normal.\n" +
                "texcoord [Vector2] - Add a texture coordenate.\n" +
                "texname [String] - Set the texture.\n" +
                "color [Vector4] - Add a color (from 0 to 1).\n" +
                "bcolor [Vector4] - Add a color (from 0 to 255).\n" +
                "renmod [String] - Set the render mode.\n" +
                "distran - Disable transparency.\n" +
                "enatran - Enable transparency.\n" +
                "togtran - Toggle transparency.\n" +
                "pos [Vector3] - Set the position.\n" +
                "rtn [Vector3] - Set the rotation.\n" +
                "scl [Vector3] - Set the scale.\n" +
                "text [String] - Create a text object.\n" +
                "text_offset [Vector3] - Sets the offset of the text object.\n" +
                "text_size [Float] - Sets the font size of the text object.\n" +
                "\n" +
                "Everything else in the code will be ignored.\n" +
                "For more information, visit https://github.com/alcoftTAO/TAO-Engine-Rewrite."
            );
            File.WriteAllText("Assets/Shaders/default.tshader", dshader);
        }

        public static string[] GetAssetsFromDirectory(string Directory)
        {
            List<string> assets = new List<string>();
            DirectoryInfo dirInfo = new DirectoryInfo(Directory);
            FileInfo[] files = dirInfo.GetFiles();
            DirectoryInfo[] dirs = dirInfo.GetDirectories();

            for (int i = 0; i < files.Length; i++)
            {
                assets.Add(files[i].Name);
            }

            for (int i = 0; i < dirs.Length; i++)
            {
                string[] dirFiles = GetAssetsFromDirectory(Directory + dirs[i].Name);
                string dirName = dirs[i].Name;

                if (!dirName.EndsWith("/"))
                {
                    dirName += "/";
                }

                for (int a = 0; a < dirFiles.Length; a++)
                {
                    assets.Add(dirName + dirFiles[a]);
                }
            }

            return assets.ToArray();
        }
    }
}