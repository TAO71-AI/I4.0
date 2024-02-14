using System;
using System.Collections.Generic;
using System.IO;

namespace TAO.Engine
{
    public static class TSceneCreation
    {
        public static TSceneData GetSceneData(string SceneName, bool FromMods = false)
        {
            TSceneData data = new TSceneData();
            string[] sceneData = File.ReadAllLines((FromMods ? "Mods/" : "Assets/") + "Scenes/" + SceneName + ".tsd");

            for (int i = 0; i < sceneData.Length; i++)
            {
                string l = sceneData[i];
                string ll = l.ToLower();

                if (ll.StartsWith("sname "))
                {
                    //Set scene name
                    data.SceneName = l.Substring("sname ".Length);
                }
                else if (ll.StartsWith("bgcolor "))
                {
                    //Set background color (from 0 to 1)
                    data.BGColor = TBasicMath.StringToVector3(ll.Substring("bgcolor ".Length));
                }
                else if (ll.StartsWith("bbgcolor "))
                {
                    //Set background color (from 0 to 255)
                    data.BGColor = TBasicMath.StringToVector3(ll.Substring("bbgcolor ".Length)) / 255;
                }
                else if (ll.StartsWith("obj "))
                {
                    //Add a object from "Assets/Models/"
                    TModelData[] objData;

                    try
                    {
                        objData = ModelImportation.GetAutoModelData(l.Substring("obj ".Length), false);

                        foreach (TModelData mdata in objData)
                        {
                            data.Objects.Add(mdata);
                        }
                    }
                    catch
                    {
                        continue;
                    }
                }
                else if (ll.StartsWith("mobj "))
                {
                    //Add a object from "Mods/Models/"
                    TModelData[] objData;

                    try
                    {
                        objData = ModelImportation.GetAutoModelData(l.Substring("mobj ".Length), true);

                        foreach (TModelData mdata in objData)
                        {
                            data.Objects.Add(mdata);
                        }
                    }
                    catch
                    {
                        continue;
                    }
                }
                else if (ll.StartsWith("iobj "))
                {
                    data.Objects.Add(ModelImportation.ObjToTMD(l.Substring(5), false));
                }
                else if (ll.StartsWith("miobj "))
                {
                    data.Objects.Add(ModelImportation.ObjToTMD(l.Substring(6), true));
                }
                else if (ll.StartsWith("suncol "))
                {
                    //Set the sun light color (from 0 to 1)
                    data.SunColor = TBasicMath.StringToVector4(ll.Substring("suncol ".Length));
                }
                else if (ll.StartsWith("bsuncol "))
                {
                    //Set the sun light color (from 0 to 255)
                    data.SunColor = TBasicMath.StringToVector4(ll.Substring("bsuncol ".Length)) / 255;
                }
                else if (ll.StartsWith("sunint "))
                {
                    //Set the sun light intensity (from 0 to 1)
                    data.SunIntensity = (byte)(TBasicMath.StringToFloat(ll.Substring("sunint ".Length)) * 255);
                }
                else if (ll.StartsWith("bsunint "))
                {
                    //Set the sun light intensity (from 0 to 255)
                    data.SunIntensity = (byte)TBasicMath.StringToFloat(ll.Substring("bsunint ".Length));
                }
                else if (ll == "hidname")
                {
                    //Hide the name
                    data.SceneName = "[HN]";
                }
            }

            if (data.SceneName.Trim() == "")
            {
                data.SceneName = SceneName;
            }

            if (data.SceneName.Trim() == "[HN]")
            {
                data.SceneName = "";
            }

            return data;
        }
    }

    public class TSceneData
    {
        public string SceneName = "";
        public TVector3 BGColor = new TVector3(0.4f, 0.58f, 0.93f);
        public List<TModelData> Objects = new List<TModelData>();
        public TVector4 SunColor = TVector4.One();
        public byte SunIntensity = 255;
    }
}