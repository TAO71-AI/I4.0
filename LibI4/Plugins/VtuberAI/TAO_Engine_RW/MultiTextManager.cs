using System;
using System.Collections.Generic;
using System.IO;

namespace TAO.Engine
{
    public static class MultiTextManager
    {
        public static TModelData[] ToModels(string Message, bool FromMods = false, TVector3 Offset = null, float Size = 9)
        {
            if (Offset == null)
            {
                Offset = TVector3.Zero();
            }

            List<TModelData> objs = new List<TModelData>();

            for (int i = 0; i < Message.Length; i++)
            {
                TModelData obj = new TModelData();

                obj.Vertices = new TVector3[]
                {
                    new TVector3(-0.5f, -0.5f, 0),
                    new TVector3(-0.5f, 0.5f, 0),
                    new TVector3(0.5f, 0.5f, 0),
                    new TVector3(0.5f, -0.5f, 0)
                };
                obj.TextureCoords = new TVector2[]
                {
                    new TVector2(0, 0),
                    new TVector2(0, 1),
                    new TVector2(1, 1),
                    new TVector2(1, 0)
                };
                obj.RenderMode = "quads";
                obj.Scale = TVector3.One() * (Size / 100);
                obj.Position.X = Size / 100 * i;
                obj.Position += Offset;
                obj.TextureName = MultiTextManager.GetTextureOfAChar(Message[i], FromMods);

                objs.Add(obj);
            }

            return objs.ToArray();
        }

        public static string GetTextureOfAChar(char C, bool FromMods = false)
        {
            string texFolder;
            string charName;
            Dictionary<char, string> otherChars = new Dictionary<char, string>()
            {
                {' ', "Space"},
                {'@', "At"},
                {'/', "Sl"},
                {@"\"[0], "Bsl"},
                {'º', "Dg"},
                {'ª', "Foi"},
                {'|', "Vb"},
                {'!', "Em"},
                {'"', "Qm"}, //
                {'·', "Ip"},
                {'$', "Ds"},
                {'~', "Td"},
                {'%', "Pc"},
                {'&', "Apsd"},
                {'¬', "Ntn"},
                {'{', "Lbc"},
                {'[', "Lbk"},
                {']', "Rbk"},
                {'}', "Rbc"},
                {'?', "Qmk"},
                {'¿', "Iqmk"},
                {'¡', "Iem"},
                {'^', "Crt"},
                {'+', "Psn"},
                {'*', "Atk"},
                {'\'', "Aptp"},
                {';', "Scl"},
                {':', "Cl"},
                {'-', "Dsh"},
                {'_', "Uscr"},
                {',', "Cmm"},
                {'.', "Dot"},
                {'=', "Eql"},
                {'(', "Lp"},
                {')', "Rp"},
                {'<', "Lt"},
                {'>', "Gt"},
                {'#', "Htg"},
                {'`', "Btck"},
                {'∞', "Inft"}
            };

            if (Char.IsUpper(C))
            {
                texFolder = "UChars/";
            }
            else
            {
                texFolder = "LChars/";
            }

            if ((Char.IsSurrogate(C) || Char.IsSymbol(C) || Char.IsPunctuation(C) || Char.IsWhiteSpace(C)) && C != '∞')
            {
                texFolder = "SChars/";
            }
            else if (Char.IsNumber(C) || C == '∞')
            {
                texFolder = "NChars/";
            }

            if (!otherChars.ContainsKey(C))
            {
                charName = C.ToString();
            }
            else
            {
                otherChars.TryGetValue(C, out charName);
            }

            DirectoryInfo dinfo = new DirectoryInfo((FromMods ? "Mods/" : "Assets/") + "Textures/" + texFolder);
            FileInfo[] finfos = dinfo.GetFiles();

            foreach (FileInfo finfo in finfos)
            {
                if (finfo.Name.Substring(0, finfo.Name.LastIndexOf('.')) == charName)
                {
                    charName = finfo.Name;
                    break;
                }
            }

            return texFolder + charName;
        }
    }
}