using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Threading;
using OpenTK;
using OpenTK.Graphics;
using OpenTK.Graphics.OpenGL;
using OpenTK.Input;
using StbImageSharp;
using TAO.Engine.UI;

namespace TAO.Engine.OpenGL.OpenGLCore
{
    public class TWindow : GameWindow
    {
        public Action OnRenderFrameAction = null;
        public Action OnLoadAction = null;
        public Action OnUnloadAction = null;
        public Action OnResizeAction = null;
        public Action<KeyboardKeyEventArgs> OnKeyDownAction = null;
        public Action<KeyboardKeyEventArgs> OnKeyUpAction = null;
        public Action BeforeDrawObjectAction = null;
        public Action AfterDrawObjectAction = null;
        public Action<TVector2> OnMouseMoveAction = null;
        public Action<MouseButtonEventArgs> OnMouseDownAction = null;
        public Action<MouseButtonEventArgs> OnMouseUpAction = null;
        public List<EnableCap> EnableOnStart = new List<EnableCap>()
        {
            EnableCap.TextureCubeMap
        };
        public List<TObject> Objs = new List<TObject>();
        public List<UIObject> UIObjs = new List<UIObject>();
        public Dictionary<string, TTexture> Textures = new Dictionary<string, TTexture>();
        public Color4 BackgroundColor = Color4.CornflowerBlue;
        public TCamera Camera = new TCamera();
        public float DeltaTime = 0;
        public bool FullScreen = false;
        public TVector2 MousePosition = TVector2.Zero();
        public TVector2 MousePosition01 = TVector2.Zero();
        public Light SunLight = new Light()
        {
            LightColor = Color4.White,
            LightIntensity = 255
        };
        private int ShaderProgram = -1;
        public List<TCustomShader> CustomShaders = new List<TCustomShader>();
        public List<TShader> Shaders = new List<TShader>();
        public AntialiasingMode Antialiasing = AntialiasingMode.Disabled;

        public static TWindow FromScene(TSceneData Data)
        {
            TWindow window = new TWindow();

            window.Title = Data.SceneName;
            window.BackgroundColor = OpenGLMath.VectorToColor(Data.BGColor);
            window.SunLight.LightColor = OpenGLMath.VectorToColor(Data.SunColor);
            window.SunLight.LightIntensity = Data.SunIntensity;

            for (int i = 0; i < Data.Objects.Count; i++)
            {
                window.Objs.Add(TObject.FromModel(Data.Objects[i]));
            }

            return window;
        }

        public static TWindow FromScene(string SceneName, bool FromMods = false)
        {
            TWindow window = new TWindow();
            TSceneData Data = TSceneCreation.GetSceneData(SceneName, FromMods);

            window.Title = Data.SceneName;
            window.BackgroundColor = OpenGLMath.VectorToColor(Data.BGColor);

            for (int i = 0; i < Data.Objects.Count; i++)
            {
                window.Objs.Add(TObject.FromModel(Data.Objects[i]));
            }

            return window;
        }

        public static Thread CreateAsync(Action<TWindow> OnCreateAction = null)
        {
            return new Thread(() =>
            {
                TWindow window = new TWindow();

                if (OnCreateAction != null)
                {
                    OnCreateAction.Invoke(window);
                }
            });
        }

        public static Thread CreateAsyncFromScene(string SceneName, bool FromMods = false, Action<TWindow> OnCreateAction = null)
        {
            return new Thread(() =>
            {
                TWindow window = FromScene(SceneName, FromMods);

                if (OnCreateAction != null)
                {
                    OnCreateAction.Invoke(window);
                }
            });
        }

        public static PrimitiveType GetRenderModeFromString(string RenderMode)
        {
            if (RenderMode.ToLower() == "quads")
            {
                return PrimitiveType.Quads;
            }
            else if (RenderMode.ToLower() == "triangles")
            {
                return PrimitiveType.Triangles;
            }
            else if (RenderMode.ToLower() == "lines")
            {
                return PrimitiveType.Lines;
            }
            else if (RenderMode.ToLower() == "points")
            {
                return PrimitiveType.Points;
            }
            else if (RenderMode.ToLower() == "patches")
            {
                return PrimitiveType.Patches;
            }

            return PrimitiveType.Polygon;
        }

        public void BasicStart(VSyncMode VSync = VSyncMode.On)
        {
            //Setting the parameters
            OSInfo info = OSInfo.GetClientInfo();

            this.VSync = VSync;

            if (this.Title.Trim() == "OpenTK Game Window" || this.Title.Trim() == "")
            {
                this.Title = "OpenGL Core | " + info.Platform + " | " + info.ProcessArchitecture;
            }

            //Starting the window
            Run();
        }

        protected void LoadTexture(string TextureName)
        {
            TTexture texture;

            if (Textures.TryGetValue(TextureName, out texture))
            {
                GL.BindTexture(TextureTarget.Texture2D, texture.ID);
                StbImage.stbi_set_flip_vertically_on_load(1);

                GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureMinFilter, (int)texture.MinFilter);
                GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureMagFilter, (int)texture.MagFilter);
                GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureWrapS, (int)texture.WrapMode);
                GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureWrapT, (int)texture.WrapMode);
                GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureWrapR, (int)texture.WrapMode);

                GL.TexImage2D(TextureTarget.Texture2D, 0, PixelInternalFormat.Rgba, texture.Result.Width, texture.Result.Height, 0,
                    PixelFormat.Rgba, PixelType.UnsignedByte, texture.Result.Data);
                GL.GenerateMipmap(GenerateMipmapTarget.Texture2D);
            }
            else
            {
                Log.WriteWarning("Texture '" + TextureName + "' doesn't exists.");
            }
        }

        protected void UnloadTexture(string TextureName)
        {
            TTexture texture;

            if (Textures.TryGetValue(TextureName, out texture))
            {
                GL.BindTexture(TextureTarget.Texture2D, texture.ID);
                GL.ClearTexImage(texture.ID, 0, PixelFormat.Rgba, PixelType.UnsignedByte, texture.Result.Data);
            }
        }

        public void ReloadCamera()
        {
            Camera.CameraMatrix = Matrix4.CreatePerspectiveFieldOfView
            (
                MathHelper.DegreesToRadians(Camera.FOV),
                Width / (float)Height,
                Camera.MinDistance,
                Camera.MaxDistance
            );
        }

        public void Translate(TVector3 Axis)
        {
            GL.Translate(OpenGLMath.TVectorToVector(Axis));
        }

        public void Rotate(TVector3 Axis, float Angle)
        {
            Angle = Math.Abs(Angle);
            GL.Rotate(Angle, OpenGLMath.TVectorToVector(Axis));
        }

        public void Rotate(TVector3 Angles)
        {
            if (Angles <= 0)
            {
                Angles = TVector3.One();
            }

            GL.Rotate(Angles.X, Vector3.UnitX);
            GL.Rotate(Angles.Y, Vector3.UnitY);
            GL.Rotate(Angles.Z, Vector3.UnitZ);
        }

        public void Scale(TVector3 Axis)
        {
            GL.Scale(OpenGLMath.TVectorToVector(Axis));
        }

        public void AddObject(TObject Object)
        {
            //Adds an object
            if (!Objs.Contains(Object))
            {
                Objs.Add(Object);
            }
        }

        public void AddObjectArray(params TObject[] Objects)
        {
            //Adds an array of TObjects
            foreach (TObject Object in Objects)
            {
                AddObject(Object);
            }
        }

        public void AddParticles(TParticleSystem Particles)
        {
            //Adds the list of TObjects from the particle system
            AddObjectArray(Particles.Particles.ToArray());
        }

        public void AddUI(UIObject Object)
        {
            //Adds an UI object
            if (!UIObjs.Contains(Object))
            {
                UIObjs.Add(Object);
            }
        }

        public void AddUIArray(params UIObject[] Objects)
        {
            //Adds an array of UI objects
            foreach (UIObject Object in Objects)
            {
                AddUI(Object);
            }
        }

        public void RemoveObject(TObject Object)
        {
            //Removes an object
            if (Objs.Contains(Object))
            {
                Object.Delete();
                Objs.Remove(Object);
            }
        }

        public void RemoveObjectArray(params TObject[] Objects)
        {
            //Removes an array of TObjects
            foreach (TObject Object in Objects)
            {
                RemoveObject(Object);
            }
        }

        public void RemoveParticles(TParticleSystem Particles)
        {
            //Removes the list of TObjects from the particle system
            RemoveObjectArray(Particles.Particles.ToArray());
        }

        public void RemoveUI(UIObject Object)
        {
            //Removes an UI object
            if (UIObjs.Contains(Object))
            {
                UIObjs.Remove(Object);
            }
        }
        public void RemoveUIArray(params UIObject[] Objects)
        {
            //Removes an array of UI objects
            foreach (UIObject Object in Objects)
            {
                RemoveUI(Object);
            }
        }

        protected override void OnLoad(EventArgs e)
        {
            base.OnLoad(e);

            //Flip the textures
            StbImage.stbi_set_flip_vertically_on_load(1);

            //Check data
            DiskData.CheckData();

            //Load textures and other assets on other thread
            Log.WriteMessage("Loading textures...");

            //Assets
            string[] textures = DiskData.GetAssetsFromDirectory("Assets/Textures/");

            for (int i = 0; i < textures.Length; i++)
            {
                if (!Textures.ContainsKey(textures[i]))
                {
                    Textures.Add(textures[i], new TTexture("Assets/Textures/" + textures[i]));
                }
            }

            //Mods (if allowed)
            if (DiskData.AllowMods)
            {
                string[] texturesMods = DiskData.GetAssetsFromDirectory("Mods/Textures/");

                for (int i = 0; i < texturesMods.Length; i++)
                {
                    if (!Textures.ContainsKey(texturesMods[i]))
                    {
                        Textures.Add(texturesMods[i], new TTexture("Mods/Textures/" + texturesMods[i]));
                    }
                }
            }

            //Enabling everything specified
            Log.WriteMessage("Loading OpenGL addons...");

            for (int i = 0; i < EnableOnStart.Count; i++)
            {
                GL.Enable(EnableOnStart[i]);
            }

            if (Antialiasing > 0)
            {
                GL.Enable(EnableCap.Multisample);
            }

            //Shaders
            ShaderProgram = GL.CreateProgram();

            foreach (TShader shader in Shaders)
            {
                shader.VertexShader.Create();
                shader.FragmentShader.Create();

                shader.VertexShader.CompileShader();
                shader.FragmentShader.CompileShader();

                shader.VertexShader.Attach(ShaderProgram);
                shader.FragmentShader.Attach(ShaderProgram);
            }

            foreach (TCustomShader shader in CustomShaders)
            {
                shader.Create();
                shader.CompileShader();
                shader.Attach(ShaderProgram);
            }

            GL.LinkProgram(ShaderProgram);

            foreach (TShader shader in Shaders)
            {
                shader.VertexShader.Detach(ShaderProgram);
                shader.FragmentShader.Detach(ShaderProgram);

                shader.VertexShader.Delete();
                shader.FragmentShader.Delete();
            }

            foreach (TCustomShader shader in CustomShaders)
            {
                shader.Detach(ShaderProgram);
                shader.Delete();
            }

            Shaders.Add(TShader.FromFile("default", false));

            //Loading the camera
            ReloadCamera();

            Log.WriteMessage("Loading camera Matrix4...");
            GL.LoadMatrix(ref Camera.CameraMatrix);

            //Execute the action
            OSInfo.ExecuteAction(OnLoadAction);
            Log.WriteMessage("OpenGL started!");
        }

        protected override void OnUnload(EventArgs e)
        {
            base.OnUnload(e);

            //Shaders
            GL.UseProgram(0);
            GL.DeleteProgram(ShaderProgram);

            //Execute the action
            OSInfo.ExecuteAction(OnUnloadAction);
        }

        protected override void OnClosing(CancelEventArgs e)
        {
            base.OnClosing(e);

            Log.WriteMessage("Closing window...");
        }

        protected override void OnClosed(EventArgs e)
        {
            base.OnClosed(e);

            Log.WriteMessage("Window closed!");
        }

        protected override void OnResize(EventArgs e)
        {
            base.OnResize(e);

            //Changing the viewport size on resizing
            GL.Viewport(0, 0, Width, Height);

            //Execute the action
            OSInfo.ExecuteAction(OnResizeAction);
        }

        protected override void OnRenderFrame(FrameEventArgs e)
        {
            base.OnRenderFrame(e);

            //Delta time
            DeltaTime = (float)e.Time;

            //Shaders
            GL.UseProgram(ShaderProgram);

            //Check full screen
            if (FullScreen)
            {
                this.WindowState = WindowState.Fullscreen;
                this.WindowBorder = WindowBorder.Hidden;
            }
            else
            {
                this.WindowState = WindowState.Normal;
                this.WindowBorder = WindowBorder.Resizable;
            }

            //Clear and set background color
            GL.Clear(ClearBufferMask.ColorBufferBit | ClearBufferMask.DepthBufferBit);
            GL.ClearColor(BackgroundColor);

            //Objects drawing
            foreach (TObject obj in Objs)
            {
                if (obj.IgnoreByEngine)
                {
                    continue;
                }

                //Load texture
                if (obj.Texture.Trim() != "")
                {
                    LoadTexture(obj.Texture);
                    GL.Enable(EnableCap.Texture2D);
                }
                else
                {
                    GL.Disable(EnableCap.Texture2D);
                }

                //Push the camera
                GL.PushMatrix();

                //Run before draw object action
                OSInfo.ExecuteAction(BeforeDrawObjectAction, false);

                //Disable Basic Addons
                foreach (EnableCap addon in EnableOnStart)
                {
                    if (addon == EnableCap.Texture2D)
                    {
                        continue;
                    }

                    GL.Disable(addon);
                }

                GL.Disable(EnableCap.DepthTest);
                GL.Enable(EnableCap.Blend);

                //Apply transparency (if allowed)
                if (obj.AllowTransparency)
                {
                    GL.BlendFunc(BlendingFactor.SrcAlpha, BlendingFactor.OneMinusSrcAlpha);
                }
                else
                {
                    GL.BlendFunc(BlendingFactor.One, BlendingFactor.Zero);
                }

                //Calculate position
                TVector3 pos = obj.Position * new TVector3(1, 1, -1);

                //Translate, scale and rotate the object
                Translate(pos + Camera.Position);
                Scale(obj.Scale * Camera.Scale);
                Rotate(TBasicMath.AbsVector(obj.Rotation));
                //Begin drawing
                GL.Begin(obj.RenderMode);

                //Drawing vertices
                for (int vert = 0; vert < obj.Vertices.Length; vert++)
                {
                    //Calculating vert vector and color
                    Vector3 v = OpenGLMath.TVectorToVector(obj.Vertices[vert]);
                    Color4 c;

                    if (obj.Colors.Length > vert)
                    {
                        c = obj.Colors[vert];
                    }
                    else
                    {
                        c = Color4.White;
                    }

                    //Calculate lighting to "c" color
                    c = OpenGLMath.ExtraColorMath.Multiply
                    (
                        c,
                        OpenGLMath.ExtraColorMath.Multiply(SunLight.LightColor, SunLight.LightIntensity)
                    );

                    //Calculate vertex to "v" vector
                    v.Z = -v.Z;

                    //Drawing the vert with the color and texture coords
                    if (obj.Texture.Trim() != "")
                    {
                        TVector2 tc;

                        if (obj.TextureCoords.Length > vert)
                        {
                            tc = obj.TextureCoords[vert];
                        }
                        else
                        {
                            tc = TVector2.Zero();
                        }

                        GL.TexCoord2(OpenGLMath.TVectorToVector(tc));
                    }

                    if (vert < obj.Normals.Length)
                    {
                        GL.Normal3(OpenGLMath.TVectorToVector(obj.Normals[vert]).Normalized());
                    }

                    GL.Color4(c);
                    GL.Vertex3(v);
                }

                //Stop drawing
                GL.End();

                //Enable Basic Addons
                GL.Disable(EnableCap.Blend);
                GL.Enable(EnableCap.Texture2D);
                GL.Enable(EnableCap.DepthTest);

                foreach (EnableCap addon in EnableOnStart)
                {
                    if (addon == EnableCap.Texture2D)
                    {
                        continue;
                    }

                    GL.Enable(addon);
                }

                //Run after draw object action
                OSInfo.ExecuteAction(AfterDrawObjectAction, false);

                //Pop the camera
                GL.PopMatrix();

                //Unload texture
                if (obj.Texture.Trim() != "")
                {
                    UnloadTexture(obj.Texture);
                }
            }

            //UI objects drawing
            for (int uio = 0; uio < UIObjs.Count; uio++)
            {
                //Load texture
                if (UIObjs[uio].Texture.Trim() != "")
                {
                    LoadTexture(UIObjs[uio].Texture);
                    GL.Enable(EnableCap.Texture2D);
                }
                else
                {
                    GL.Disable(EnableCap.Texture2D);
                }

                //Push the camera
                GL.PushMatrix();

                //Run before draw object action
                OSInfo.ExecuteAction(BeforeDrawObjectAction, false);

                //Disable Basic Addons
                foreach (EnableCap addon in EnableOnStart)
                {
                    if (addon == EnableCap.Texture2D)
                    {
                        continue;
                    }

                    GL.Disable(addon);
                }

                GL.Disable(EnableCap.DepthTest);
                GL.Enable(EnableCap.Blend);

                //Apply transparency (if allowed)
                if (UIObjs[uio].AllowTransparency)
                {
                    GL.BlendFunc(BlendingFactor.SrcAlpha, BlendingFactor.OneMinusSrcAlpha);
                }
                else
                {
                    GL.BlendFunc(BlendingFactor.One, BlendingFactor.Zero);
                }

                //Calculate position and scale
                TVector2 pos = UIObjs[uio].Position;
                TVector2 scl = UIObjs[uio].Scale;

                //Translate, scale and rotate the object
                /*Translate(new TVector3(pos.X, pos.Y, 0) - Camera.Position * new TVector3(1, 1, 0));
                Scale(new TVector3(scl.X, scl.Y, 1) * Camera.Scale);*/
                //Begin drawing
                GL.Begin(GetRenderModeFromString(UIObjs[uio].RenderMode));

                //Drawing vertices
                for (int vert = 0; vert < UIObjs[uio].Vertices.Length; vert++)
                {
                    //Calculating vert vector and color
                    Vector2 v = OpenGLMath.TVectorToVector(UIObjs[uio].Vertices[vert]);
                    Color4 c;

                    if (UIObjs[uio].Colors.Length > vert)
                    {
                        c = OpenGLMath.VectorToColor(UIObjs[uio].Colors[vert]);
                    }
                    else
                    {
                        c = Color4.White;
                    }

                    //Calculate lighting to "c" color
                    c = OpenGLMath.ExtraColorMath.Multiply
                    (
                        c,
                        OpenGLMath.ExtraColorMath.Multiply(SunLight.LightColor, SunLight.LightIntensity)
                    );

                    //Drawing the vert with the color and texture coords
                    if (UIObjs[uio].Texture.Trim() != "")
                    {
                        TVector2 tc;

                        if (UIObjs[uio].TextureCoords.Length > vert)
                        {
                            tc = UIObjs[uio].TextureCoords[vert];
                        }
                        else
                        {
                            tc = TVector2.Zero();
                        }

                        GL.TexCoord2(OpenGLMath.TVectorToVector(tc));
                    }

                    Vector2 v2 = v * OpenGLMath.TVectorToVector(scl + pos);

                    GL.Color4(c);
                    GL.Vertex3(new Vector3(v2.X, v2.Y, -0.85f));
                }

                //Stop drawing
                GL.End();

                //Enable Basic Addons
                GL.Disable(EnableCap.Blend);
                GL.Enable(EnableCap.Texture2D);
                GL.Enable(EnableCap.DepthTest);

                foreach (EnableCap addon in EnableOnStart)
                {
                    if (addon == EnableCap.Texture2D)
                    {
                        continue;
                    }

                    GL.Enable(addon);
                }

                //Run after draw object action
                OSInfo.ExecuteAction(AfterDrawObjectAction, false);

                //Pop the camera
                GL.PopMatrix();

                //Unload texture
                if (UIObjs[uio].Texture.Trim() != "")
                {
                    UnloadTexture(UIObjs[uio].Texture);
                }
            }

            //Antialiasing
            if (Antialiasing > 0)
            {
                GL.RenderbufferStorageMultisample(
                    RenderbufferTarget.Renderbuffer,
                    (int)Antialiasing,
                    RenderbufferStorage.Depth24Stencil8,
                    Width,
                    Height
                );
            }

            //Execute the action
            OSInfo.ExecuteAction(OnRenderFrameAction, false);

            //Swap buffers and flush
            SwapBuffers();
            GL.Flush();
        }

        protected override void OnKeyDown(KeyboardKeyEventArgs e)
        {
            base.OnKeyDown(e);

            //Close the program if the combination is ALT+F4
            if (e.Alt && e.Key == Key.F4)
            {
                Close();
            }

            //Execute the action
            OSInfo.ExecuteAction(OnKeyDownAction, e);
        }

        protected override void OnKeyUp(KeyboardKeyEventArgs e)
        {
            base.OnKeyUp(e);

            //Execute the action
            OSInfo.ExecuteAction(OnKeyUpAction, e);
        }

        protected override void OnMouseMove(MouseMoveEventArgs e)
        {
            base.OnMouseMove(e);

            //Calculate and set the mouse position
            /*
             *          |            
             *    -+    |     ++
             *          |
             *  --------|--------
             *          |
             *    --    |     +-
             *          |
            */
            MousePosition = new TVector2(e.X - Width / 2, e.Y - Height / 2);
            MousePosition01 = (MousePosition + new TVector2(Width, Height) / 2) / new TVector2(Width, Height);

            OSInfo.ExecuteAction(OnMouseMoveAction, new TVector2(e.XDelta, e.YDelta));
        }

        protected override void OnMouseDown(MouseButtonEventArgs e)
        {
            base.OnMouseDown(e);
            OSInfo.ExecuteAction(OnMouseDownAction, e);
        }

        protected override void OnMouseUp(MouseButtonEventArgs e)
        {
            base.OnMouseUp(e);
            OSInfo.ExecuteAction(OnMouseUpAction, e);
        }
    }

    public enum AntialiasingMode
    {
        Disabled = 0,
        x2 = 2,
        x4 = 4,
        x6 = 6,
        x8 = 8
    }
}