using System;
using System.Collections.Generic;
using System.IO;

namespace TAO.Engine
{
    public static class ModelImportation
    {
        public static TModelData[] GetAutoModelData(string ModelName, bool FromMods = false)
        {
            string[] modelData = File.ReadAllLines((FromMods ? "Mods/" : "Assets/") + "Models/" + ModelName + ".tmd");

            foreach (string line in modelData)
            {
                if (line.TrimStart().TrimEnd().ToLower().StartsWith("text "))
                {
                    return GetTextModel(ModelName, FromMods);
                }
            }

            return new TModelData[]
            {
                GetModelData(ModelName, FromMods)
            };
        }

        public static TModelData GetModelData(string ModelName, bool FromMods = false)
        {
            //IMPORTANT: the model file extension must be .tmd (TAO Model Data)
            string[] modelData = File.ReadAllLines((FromMods ? "Mods/" : "Assets/") + "Models/" + ModelName + ".tmd");
            List<TVector3> Vertices = new List<TVector3>();
            List<TVector4> Colors = new List<TVector4>();
            List<TVector2> TextureCoords = new List<TVector2>();
            string TextureName = "";
            string RenderMode = "";
            bool AllowTransparency = true;
            TVector3 Position = TVector3.Zero();
            TVector3 Scale = TVector3.One();
            TVector3 Rotation = TVector3.Zero();
            List<TVector3> Normals = new List<TVector3>();
            TModelData data = new TModelData();

            for (int i = 0; i < modelData.Length; i++)
            {
                string l = modelData[i].TrimStart().TrimEnd();
                string ll = l.ToLower();

                if (ll.StartsWith("vert "))
                {
                    //Apply vertices
                    Vertices.Add(TBasicMath.StringToVector3(ll.Substring(5)));
                }
                else if (ll.StartsWith("nor "))
                {
                    //Apply normals
                    Normals.Add(TBasicMath.StringToVector3(ll.Substring(4)));
                }
                else if (ll.StartsWith("texcoord "))
                {
                    //Apply texture coords
                    TextureCoords.Add(TBasicMath.StringToVector2(ll.Substring(9)));
                }
                else if (ll.StartsWith("texname "))
                {
                    //Apply texture
                    TextureName = l.Substring(8);
                }
                else if (ll.StartsWith("color "))
                {
                    //Apply colors (in float, from 0 to 1)
                    Colors.Add(TBasicMath.StringToVector4(ll.Substring(6)));
                }
                else if (ll.StartsWith("bcolor "))
                {
                    //Apply colors (in bytes, from 0 to 255)
                    Colors.Add(TBasicMath.StringToVector4(ll.Substring(7)) / 255);
                }
                else if (ll.StartsWith("renmod "))
                {
                    //Apply render mode
                    RenderMode = ll.Substring(7);
                }
                else if (ll == "distran")
                {
                    //Set transparency to false
                    AllowTransparency = false;
                }
                else if (ll == "enatran")
                {
                    //Set transparency to true
                    AllowTransparency = true;
                }
                else if (ll == "togtran")
                {
                    //Toggle transparency
                    AllowTransparency = !AllowTransparency;
                }
                else if (ll.StartsWith("pos "))
                {
                    //Apply position
                    Position = TBasicMath.StringToVector3(ll.Substring(4));
                }
                else if (ll.StartsWith("scl "))
                {
                    //Apply position
                    Scale = TBasicMath.StringToVector3(ll.Substring(4));
                }
                else if (ll.StartsWith("rtn "))
                {
                    //Apply position
                    Rotation = TBasicMath.StringToVector3(ll.Substring(4));
                }
                else if (ll.StartsWith("import "))
                {
                    //Import a model
                    TModelData md = ModelImportation.ObjToTMD(l.Substring(7));

                    foreach (TVector3 vert in md.Vertices)
                    {
                        Vertices.Add(vert);
                    }

                    foreach (TVector2 tc in md.TextureCoords)
                    {
                        TextureCoords.Add(tc);
                    }
                }
            }

            data.Vertices = Vertices.ToArray();
            data.Colors = Colors.ToArray();
            data.TextureCoords = TextureCoords.ToArray();
            data.TextureName = TextureName;
            data.RenderMode = RenderMode;
            data.AllowTransparency = AllowTransparency;
            data.Position = Position;
            data.Scale = Scale;
            data.Rotation = Rotation;
            data.Normals = Normals.ToArray();

            return data;
        }

        public static TModelData[] GetTextModel(string ModelName, bool FromMods = false)
        {
            string[] modelData = File.ReadAllLines((FromMods ? "Mods/" : "Assets/") + "Models/" + ModelName + ".tmd");
            TModelData data = GetModelData(ModelName, FromMods);
            string text = "";
            TVector3 offset = TVector3.Zero();
            float size = 9;

            foreach (string line in modelData)
            {
                string l = line.TrimStart().TrimEnd();
                string ll = l.ToLower();

                if (ll.StartsWith("text "))
                {
                    text = l.Substring(5);
                }
                else if (ll.StartsWith("text_offset "))
                {
                    offset = TBasicMath.StringToVector3(ll.Substring(12));
                }
                else if (ll.StartsWith("text_size "))
                {
                    size = TBasicMath.StringToFloat(ll.Substring(10));
                }
            }

            TModelData[] datas = MultiTextManager.ToModels(text, FromMods, offset, size);

            if (text.Trim().Length > 0)
            {
                data.Scale -= TVector3.One();

                foreach (TModelData mdata in datas)
                {
                    mdata.AllowTransparency = data.AllowTransparency;
                    mdata.Colors = data.Colors;
                    mdata.Position += data.Position;
                    mdata.Rotation += data.Rotation;
                    mdata.Scale += data.Scale;
                }
            }

            return datas;
        }

        private static (TVector3, TVector2, TVector3) ObjBlockToData(string BlockData, (TVector3[], TVector2[], TVector3[]) Data)
        {
            BlockData = BlockData.Trim();

            string[] blockVerts = BlockData.Split('/');
            TVector3 vert = TVector3.Zero();
            TVector2 texCoord = TVector2.Zero();
            TVector3 vertNormal = TVector3.Zero();

            for (int i = 0; i < 3; i++)
            {
                int index = (int)TBasicMath.StringToFloat(blockVerts[i]) - 1;

                if (i == 0)
                {
                    vert = Data.Item1[index];
                }
                else if (i == 1)
                {
                    if (index >= 0 && index < Data.Item2.Length)
                    {
                        texCoord = Data.Item2[index];
                    }
                }
                else if (i == 2)
                {
                    if (index >= 0 && index < Data.Item3.Length)
                    {
                        vertNormal = Data.Item3[index];
                    }
                }
            }

            return (vert, texCoord, vertNormal);
        }

        public static TModelData ObjToTMD(string[] ObjData)
        {
            List<TVector3> verts = new List<TVector3>();
            List<TVector2> texCoords = new List<TVector2>();
            List<TVector3> normals = new List<TVector3>();
            List<TVector3> rverts = new List<TVector3>();
            List<TVector2> rtexCoords = new List<TVector2>();
            List<TVector3> rnormals = new List<TVector3>();
            List<TVector4> colors = new List<TVector4>();

            foreach (string l in ObjData)
            {
                string ll = l.TrimStart().TrimEnd().ToLower().Replace("  ", " ");

                if (ll.StartsWith("v "))
                {
                    verts.Add(TBasicMath.StringToVector3(ll.Substring(2)));
                }
                else if (ll.StartsWith("vn "))
                {
                    normals.Add(TBasicMath.StringToVector3(ll.Substring(3)));
                }
                else if (ll.StartsWith("vt "))
                {
                    texCoords.Add(TBasicMath.StringToVector2(ll.Substring(3)));
                }
                else if (ll.StartsWith("f "))
                {
                    string[] blocks = ll.Substring(2).Split(' ');

                    foreach (string block in blocks)
                    {
                        (TVector3, TVector2, TVector3) blockData = ObjBlockToData(
                            block,
                            (verts.ToArray(), texCoords.ToArray(), normals.ToArray())
                        );

                        if (block.Contains("//"))
                        {
                            // Format: v//vn
                            string[] blockParts = block.Split('/');
                            int vertIndex = int.Parse(blockParts[0]) - 1;
                            int normalIndex = int.Parse(blockParts[2]) - 1;

                            blockData.Item1 = verts[vertIndex];
                            blockData.Item2 = TVector2.Zero();
                            blockData.Item3 = normals[normalIndex];
                        }
                        else if (block.Contains("/"))
                        {
                            // Format: v/vt/vn
                            blockData = ObjBlockToData(block, (verts.ToArray(), texCoords.ToArray(), normals.ToArray()));
                        }
                        else
                        {
                            // Format: v
                            blockData = ObjBlockToData(block, (verts.ToArray(), texCoords.ToArray(), normals.ToArray()));
                        }

                        rverts.Add(blockData.Item1);
                        rtexCoords.Add(blockData.Item2);
                        rnormals.Add(blockData.Item3);
                        colors.Add(new TVector4(1, 1, 1, 1));
                    }
                }
            }

            return new TModelData()
            {
                AllowTransparency = true,
                Colors = colors.ToArray(),
                Position = TVector3.Zero(),
                RenderMode = "polygon",
                Rotation = TVector3.Zero(),
                Scale = TVector3.One(),
                TextureCoords = rtexCoords.ToArray(),
                TextureName = "",
                Vertices = rverts.ToArray(),
                Normals = rnormals.ToArray()
            };
        }

        public static TModelData ObjToTMD(string ObjFileName, bool FromMods = false)
        {
            return ObjToTMD(File.ReadAllLines((FromMods ? "Mods/" : "Assets/") + "Models/" + ObjFileName + ".obj"));
        }
    }

    public class TModelData
    {
        public TVector3[] Vertices = new TVector3[0];
        public TVector4[] Colors = new TVector4[0];
        public TVector2[] TextureCoords = new TVector2[0];
        public string TextureName = "";
        public string RenderMode = "";
        public bool AllowTransparency = true;
        public TVector3 Position = TVector3.Zero();
        public TVector3 Scale = TVector3.One();
        public TVector3 Rotation = TVector3.Zero();
        public TVector3[] Normals = new TVector3[0];

        public TModelData Clone()
        {
            return new TModelData()
            {
                Vertices = Vertices,
                Colors = Colors,
                TextureCoords = TextureCoords,
                TextureName = TextureName,
                RenderMode = RenderMode,
                AllowTransparency = AllowTransparency,
                Position = Position,
                Scale = Scale,
                Rotation = Rotation,
                Normals = Normals
            };
        }

        public override string ToString()
        {
            string tr = "";

            tr += "Vertices: \n";

            foreach (TVector3 vector in Vertices)
            {
                tr += "    " + vector + "\n";
            }

            tr += "Colors: \n";

            foreach (TVector4 vector in Colors)
            {
                tr += "    " + vector + "\n";
            }

            tr += "Texture Coordenates: \n";

            foreach (TVector2 vector in TextureCoords)
            {
                tr += "    " + vector + "\n";
            }

            tr += "Texture: " + TextureName;

            return tr;
        }
    }
}