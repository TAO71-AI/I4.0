using System;
using System.Collections.Generic;
using System.Text;
using System.Threading;
using OpenTK;
using OpenTK.Graphics;
using TAO.Engine;
using TAO.Engine.Animations;
using TAO.Engine.Audio;
using TAO.Engine.OpenGL;
using TAO.Engine.OpenGL.OpenGLCore;
using TAO.Engine.UI;
using TAO.I4.PythonManager;
using Newtonsoft.Json;

namespace TAO.I4.Plugins.VTuber
{
    public static class I4_0_VTWindow
    {
        private static bool Loaded = false;
        public static string HairBackTexture = "";
        public static string HairFrontTexture = "";
        public static string BodyTexture = "";
        public static string NeckTexture = "";
        public static string HeadTexture = "";
        public static string NeutralEyesTexture = "";
        public static string HappyEyesTexture = "";
        public static string SadEyesTexture = "";
        public static string AngryEyesTexture = "";
        public static string LeftPuppilTexture = "";
        public static string RightPuppilTexture = "";
        public static string LoadingTexture = "";
        public static Color4 BGColor = Color4.HotPink;
        public static List<TObject> Accessories = new List<TObject>();
        public static bool Talking = false;
        public static int CurrentExpression = -1;

        public static TWindow StartVTuberWindow(Action<TWindow, TObject[]> ExtraAction = null)
        {
            if (Loaded)
            {
                throw new Exception("Window alredy loaded!");
            }

            Log.AllowLogs = false;
            TWindow vtwindow = null;

            Thread windowThread = new Thread(() =>
            {
                TWindow window = new TWindow();
                TObject[] I4 = new TObject[]
                {
                        //Hair
                        TObject.Cube2D(),
                        //Body
                        TObject.Cube2D(),
                        //Neck
                        TObject.Cube2D(),
                        //Head
                        TObject.Cube2D(),
                        //Eyes
                        TObject.Cube2D(),
                        //Hair 2
                        TObject.Cube2D(),
                        //Left Puppil
                        TObject.Cube2D(),
                        //Right Puppil
                        TObject.Cube2D(),
                        //Extra
                        //Loading
                        TObject.Cube2D(),
                };

                foreach (TObject obj in I4)
                {
                    obj.Position += new TVector3(0, 0, 2.5f);
                    obj.AllowTransparency = true;
                    obj.EnableLOD = false;
                }

                //Hair 1
                I4[0].Scale = new TVector3(1.25f, 1.5f, 1);
                I4[0].Position += new TVector3(0, 0.125f, 0);
                I4[0].Texture = HairBackTexture;

                //Body
                I4[1].Scale = new TVector3(1.25f, 1, 1);
                I4[1].Position += new TVector3(0, -0.95f, 0);
                I4[1].Texture = BodyTexture;

                //Neck
                I4[2].Scale = new TVector3(0.25f, 1, 1);
                I4[2].Position += new TVector3(0.025f, -0.25f, 0);
                I4[2].Texture = NeckTexture;

                //Head
                I4[3].Scale = new TVector3(0.75f, 1, 1);
                I4[3].Position += new TVector3(0, 0.25f, 0);
                I4[3].Texture = HeadTexture;

                //Hair 2
                I4[4].Scale = new TVector3(1.35f, 0.75f, 1);
                I4[4].Position += new TVector3(-0.0675f, 0.675f, 0);
                I4[4].Texture = HairFrontTexture;

                //Eyes
                I4[5].Scale = TVector3.One() * 0.5f + new TVector3(0, -0.15f, 0);
                I4[5].Position += new TVector3(0, 0.35f, 0);
                I4[5].Texture = NeutralEyesTexture;

                //Puppils
                I4[6].Scale = new TVector3(0.075f, 0.15f, 0.075f);
                I4[6].Position += new TVector3(-0.125f, 0.375f, 0);
                I4[6].Texture = LeftPuppilTexture;

                I4[7].Scale = new TVector3(0.075f, 0.15f, 0.075f);
                I4[7].Position += new TVector3(0.125f, 0.375f, 0);
                I4[7].Texture = RightPuppilTexture;

                //Extra
                //Loading
                I4[8].Scale = TVector3.One() * 0.25f;
                I4[8].Position += new TVector3(0, 0, 0);
                I4[8].Texture = LoadingTexture;
                I4[8].IgnoreByEngine = true;

                window.BackgroundColor = BGColor;
                window.Antialiasing = AntialiasingMode.x2;
                window.Title = "I4.0 VTuber Plugin";

                window.OnLoadAction += () =>
                {
                    Loaded = true;
                };
                window.OnRenderFrameAction += () =>
                {
                    I4[8].Rotation += new TVector3(0, 0, 90) * window.DeltaTime;

                    if (Talking)
                    {
                        if (CurrentExpression.ToString() == "4")
                        {
                            I4[5].Texture = HappyEyesTexture;
                            I4[6].Scale = new TVector3(0.075f, 0.15f, 0.075f);
                            I4[7].Scale = new TVector3(0.075f, 0.15f, 0.075f);
                        }
                        else if (CurrentExpression.ToString() == "0")
                        {
                            I4[5].Texture = AngryEyesTexture;
                            I4[6].Scale = new TVector3(0.075f, 0.15f, 0.075f) / 2;
                            I4[7].Scale = new TVector3(0.075f, 0.15f, 0.075f) / 2;
                        }
                        else if (CurrentExpression.ToString() == "1")
                        {
                            I4[5].Texture = SadEyesTexture;
                            I4[6].Scale = new TVector3(0.075f, 0.15f, 0.075f) * 1.25f;
                            I4[7].Scale = new TVector3(0.075f, 0.15f, 0.075f) * 1.25f;
                        }
                        else
                        {
                            I4[5].Texture = NeutralEyesTexture;
                            I4[6].Scale = new TVector3(0.075f, 0.15f, 0.075f);
                            I4[7].Scale = new TVector3(0.075f, 0.15f, 0.075f);
                        }
                    }
                };

                if (ExtraAction != null)
                {
                    try
                    {
                        ExtraAction.Invoke(window, I4);
                    }
                    catch
                    {
                        
                    }
                }

                vtwindow = window;

                window.AddObjectArray(I4);
                window.BasicStart();
            })
            {
                Priority = ThreadPriority.BelowNormal
            };
            windowThread.Start();

            while (vtwindow == null)
            {

            }

            return vtwindow;
        }
    }
}