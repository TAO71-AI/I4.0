using System;
using System.Collections.Generic;
using OpenTK;
using OpenTK.Graphics;
using OpenTK.Graphics.OpenGL;

namespace TAO.Engine.OpenGL.OpenGLCore
{
    public class TObject
    {
        protected static readonly List<TObject> Objects = new List<TObject>();
        public readonly int ID = GetID();
        public TVector3 Position = TVector3.Zero();
        public TVector3 Rotation = TVector3.Zero();
        public TVector3 Scale = TVector3.One();
        public TVector3[] Vertices = new TVector3[0];
        public TVector3[] Normals = new TVector3[0];
        public Color4[] Colors = new Color4[0];
        public string Texture = "";
        public TVector2[] TextureCoords = new TVector2[0];
        public PrimitiveType RenderMode = PrimitiveType.Polygon;
        public bool AllowTransparency = true;
        public TCollider Collider = new TCollider();
        public List<string> Tags = new List<string>();
        public bool EnableLOD = false;
        public (float, TModelData) LOD1 = (0, null);
        public (float, TModelData) LOD2 = (0, null);
        public (float, TModelData) LOD3 = (0, null);
        public (float, TModelData) LOD4 = (0, null);
        public bool IgnoreByEngine = false;

        public TObject()
        {
            Objects.Add(this);
        }

        ~TObject()
        {
            Delete();
        }

        public static TObject Triangle2D()
        {
            return new TObject()
            {
                Vertices = new TVector3[]
                {
                    new TVector3(-0.5f, -0.5f),
                    new TVector3(0.5f, -0.5f),
                    new TVector3(0, 0.5f)
                },
                TextureCoords = new TVector2[]
                {
                    new TVector2(0, 0),
                    new TVector2(1, 0),
                    new TVector2(0.5f, 1)
                },
                Collider = new TCollider()
                {
                    Enabled = true,
                    Offset = TVector3.Zero(),
                    Size = TVector3.One()
                },
                RenderMode = PrimitiveType.Triangles
            };
        }

        public static TObject Cube2D()
        {
            return new TObject()
            {
                Vertices = new TVector3[]
                {
                    new TVector3(-0.5f, -0.5f),
                    new TVector3(-0.5f, 0.5f),
                    new TVector3(0.5f, 0.5f),
                    new TVector3(0.5f, -0.5f)
                },
                TextureCoords = new TVector2[]
                {
                    new TVector2(0, 0),
                    new TVector2(0, 1),
                    new TVector2(1, 1),
                    new TVector2(1, 0)
                },
                Collider = new TCollider()
                {
                    Enabled = true,
                    Offset = TVector3.Zero(),
                    Size = TVector3.One()
                },
                RenderMode = PrimitiveType.Quads
            };
        }

        public static TObject Circle2D(float Radius = 0.5f)
        {
            List<TVector3> Vertices = new List<TVector3>();
            List<TVector2> TexCoords = new List<TVector2>();

            for (int i = 0; i < 360; i++)
            {
                Vertices.Add(new TVector3(Radius * (float)Math.Cos(i), Radius * (float)Math.Sin(i), 0));
                TexCoords.Add(new TVector2((float)Math.Cos(i) / 2 + 1, (float)Math.Sin(i) / 2) + 0.5f);
            }

            return new TObject()
            {
                Vertices = Vertices.ToArray(),
                Collider = new TCollider()
                {
                    Enabled = true,
                    Offset = TVector3.Zero(),
                    Size = TVector3.One()
                },
                TextureCoords = TexCoords.ToArray(),
                RenderMode = PrimitiveType.Polygon
            };
        }

        private static int GetID()
        {
            int ID = new Random().Next(0, 99999);

            while (Exists(ID))
            {
                ID = GetID();
            }

            return ID;
        }

        public static TObject GetByID(int ID)
        {
            for (int i = 0; i < Objects.Count; i++)
            {
                if (Objects[i].ID == ID)
                {
                    return Objects[i];
                }
            }

            return null;
        }

        public static bool Exists(int ID)
        {
            for (int i = 0; i < Objects.Count; i++)
            {
                if (Objects[i].ID == ID)
                {
                    return true;
                }
            }

            return false;
        }

        public static TObject FromModel(TModelData Data)
        {
            TObject obj = new TObject();

            obj.Vertices = Data.Vertices;
            obj.Colors = OpenGLMath.VectorToColor(Data.Colors);
            obj.TextureCoords = Data.TextureCoords;
            obj.Texture = Data.TextureName;
            obj.AllowTransparency = Data.AllowTransparency;
            obj.Position = Data.Position;
            obj.Scale = Data.Scale;
            obj.Rotation = Data.Rotation;
            obj.Normals = Data.Normals;
            obj.RenderMode = TWindow.GetRenderModeFromString(Data.RenderMode);

            return obj;
        }

        public static TObject[] FromModels(TModelData[] Datas, bool FromMods = false)
        {
            List<TObject> objs = new List<TObject>();

            foreach (TModelData data in Datas)
            {
                objs.Add(FromModel(data));
            }

            return objs.ToArray();
        }

        public static TObject FromModel(string Name, bool FromMods = false)
        {
            return FromModel(ModelImportation.GetModelData(Name, FromMods));
        }

        public static TObject[] FromTextModel(string Name, bool FromMods = false)
        {
            return FromModels(ModelImportation.GetTextModel(Name, FromMods));
        }

        public static TObject[] FromModelAuto(string Name, bool FromMods = false)
        {
            return FromModels(ModelImportation.GetAutoModelData(Name, FromMods));
        }

        public static void MoveArray(TObject[] Objs, TVector3 Direction, bool CalculateColision = true)
        {
            foreach (TObject obj in Objs)
            {
                if (CalculateColision)
                {
                    obj.Move(Direction);
                }
                else
                {
                    obj.Position += Direction;
                }
            }
        }

        public static void RotateArray(TObject[] Objs, TVector3 Direction, bool CalculateColision = true)
        {
            foreach (TObject obj in Objs)
            {
                if (CalculateColision)
                {
                    obj.RotateObj(Direction);
                }
                else
                {
                    obj.Rotation += Direction;
                }
            }
        }

        public static void ScaleArray(TObject[] Objs, TVector3 Direction, bool CalculateColision = true)
        {
            foreach (TObject obj in Objs)
            {
                if (CalculateColision)
                {
                    obj.ScaleObj(Direction);
                }
                else
                {
                    obj.Scale += Direction;
                }
            }
        }

        public static TObject[] GetObjectsWithTag(string Tag)
        {
            List<TObject> objs = new List<TObject>();

            foreach (TObject obj in Objects)
            {
                if (obj.Tags.Contains(Tag))
                {
                    objs.Add(Objects[Objects.IndexOf(obj)]);
                }
            }

            return objs.ToArray();
        }

        public static TObject GetFirstObjectWithTag(string Tag)
        {
            return GetObjectsWithTag(Tag)[0];
        }

        public TObject Clone()
        {
            return new TObject()
            {
                AllowTransparency = AllowTransparency,
                Collider = Collider,
                Colors = Colors,
                Position = Position,
                RenderMode = RenderMode,
                Rotation = Rotation,
                Scale = Scale,
                Texture = Texture,
                TextureCoords = TextureCoords,
                Vertices = Vertices,
                Tags = Tags
            };
        }

        public void Delete()
        {
            Objects.Remove(this);
        }

        public void ChangeColor(Color4 ColorToChange)
        {
            Colors = new Color4[Vertices.Length];

            for (int i = 0; i < Colors.Length; i++)
            {
                Colors[i] = ColorToChange;
            }
        }

        public bool IsMouseOver(TVector2 MousePosition, float MaxDistance = float.MaxValue)
        {
            return false;
        }

        public bool CollidingWith(TObject Obj)
        {
            return TCollider.Between(
                new TCollider(Position + Collider.Offset, Scale * Collider.Size, Collider.Enabled),
                new TCollider(Obj.Position + Obj.Collider.Offset, Obj.Scale * Obj.Collider.Size, Obj.Collider.Enabled),
                false
            );
        }

        public bool CollidingWithAny()
        {
            foreach (TObject obj in Objects)
            {
                if (obj != this)
                {
                    if (CollidingWith(obj))
                    {
                        return true;
                    }
                }
            }

            return false;
        }

        public void Move(TVector3 Direction)
        {
            Position += Direction;

            if (CollidingWithAny())
            {
                Position -= Direction;
            }
        }

        public void RotateObj(TVector3 Direction)
        {
            Rotation += Direction;

            if (CollidingWithAny())
            {
                Rotation -= Direction;
            }
        }

        public void ScaleObj(TVector3 Direction)
        {
            Scale += Direction;

            if (CollidingWithAny())
            {
                Scale -= Direction;
            }
        }

        public TModelData ToTMD()
        {
            return new TModelData()
            {
                AllowTransparency = AllowTransparency,
                Colors = OpenGLMath.ColorToTVector(Colors),
                Normals = Normals,
                Position = Position,
                RenderMode = RenderMode.ToString(),
                Rotation = Rotation,
                Scale = Scale,
                TextureCoords = TextureCoords,
                TextureName = Texture,
                Vertices = Vertices
            };
        }

        public void SetLOD(float Distance)
        {
            if (!EnableLOD || LOD1.Item2 == null || LOD2.Item2 == null || LOD3.Item2 == null || LOD4.Item2 == null)
            {
                return;
            }

            TModelData lod;

            if (Distance >= LOD1.Item1 && Distance < LOD2.Item1)
            {
                lod = LOD1.Item2;
            }
            else if (Distance >= LOD2.Item1 && Distance < LOD3.Item1)
            {
                lod = LOD2.Item2;
            }
            else if (Distance >= LOD3.Item1 && Distance < LOD4.Item1)
            {
                lod = LOD3.Item2;
            }
            else
            {
                lod = LOD4.Item2;
            }

            AllowTransparency = lod.AllowTransparency;
            Colors = OpenGLMath.VectorToColor(lod.Colors);
            Normals = lod.Normals;
            RenderMode = TWindow.GetRenderModeFromString(lod.RenderMode);
            Texture = lod.TextureName;
            TextureCoords = lod.TextureCoords;
            Vertices = lod.Vertices;
        }

        public void SetLOD(TVector3 CameraPosition)
        {
            SetLOD(TVector3.Distance(CameraPosition, Position));
        }
    }
}