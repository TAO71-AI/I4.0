using System;
using System.Collections.Generic;
using OpenTK;
using OpenTK.Graphics;
using OpenTK.Graphics.OpenGL;

namespace TAO71.I4.Plugins.VTuber.VirtualWebcam
{
    public class VTuberObject
    {
        public Vector3[] GlobalVerts = new Vector3[0];
        public PrimitiveType RenderMode = PrimitiveType.Polygon;
        public Color4 Color = Color4.White;
        public Vector3 Position = Vector3.Zero;
        public Vector3 Rotation = Vector3.Zero;
        public Vector3 Scale = Vector3.Zero;
        public Action OnStart = null;
        public Action<float> OnLoop = null;
        public Action<string> OnMessage = null;                     // Managed externally
        public Action OnClose = null;

        /*public static VTuberObject FromOBJ(string Path)
        {
            
        }

        public void FromOBJ(string Path)
        {
            
        }
        */

        public class VTuberFaceObject : VTuberObject
        {
            private Vector3[] InitMouthVerts = new Vector3[0];
            private Vector3[] InitLEyeVerts = new Vector3[0];
            private Vector3[] InitREyeVerts = new Vector3[0];
            private Vector3[] InitTongueVerts = new Vector3[0];
            public Vector3[] MouthVerts = new Vector3[0];
            public Vector3[] LEyeVerts = new Vector3[0];
            public Vector3[] REyeVerts = new Vector3[0];
            public Vector3[] TongueVerts = new Vector3[0];
            public float OpenMouthDistance = 0.5f;
            public float CloseEyesDistance = 0.25f;
            public float MoveTongueDistance = 0.25f;
            public float OpenMouthSpeed = 1;
            public float CloseEyesSpeed = 1;
            public float MoveTongueSpeed = 1;
            public bool MouthOpen = false;
            public (bool, bool) EyesClosed = (false, false);        // L, R
            public bool TongueOut = false;

            public VTuberFaceObject(string FilePath)
            {
                //this.FromOBJ(FilePath);
                InitMouthVerts = MouthVerts;
                InitLEyeVerts = LEyeVerts;
                InitREyeVerts = REyeVerts;
                InitTongueVerts = TongueVerts;

                List<Vector3> verts = new List<Vector3>();

                foreach (Vector3 vert in InitMouthVerts)
                {
                    verts.Add(vert);
                }

                foreach (Vector3 vert in InitLEyeVerts)
                {
                    verts.Add(vert);
                }

                foreach (Vector3 vert in InitREyeVerts)
                {
                    verts.Add(vert);
                }

                foreach (Vector3 vert in InitTongueVerts)
                {
                    verts.Add(vert);
                }

                GlobalVerts = verts.ToArray();
                OnLoop = (float DeltaTime) =>
                {
                    for (int i = 0; i < MouthVerts.Length; i++)
                    {
                        Vector3 v;

                        if (MouthOpen)
                        {
                            v = InitMouthVerts[i] - new Vector3(0, OpenMouthDistance, 0);
                        }
                        else
                        {
                            v = InitMouthVerts[i];
                        }

                        if (MouthVerts[i] != InitMouthVerts[i])
                        {
                            MouthVerts[i] = Vector3.Lerp(MouthVerts[i], v, OpenMouthSpeed * DeltaTime);
                        }
                    }

                    for (int i = 0; i < LEyeVerts.Length; i++)
                    {
                        Vector3 v;

                        if (EyesClosed.Item1)
                        {
                            v = InitLEyeVerts[i] - new Vector3(0, CloseEyesDistance, 0);
                        }
                        else
                        {
                            v = InitLEyeVerts[i];
                        }

                        if (LEyeVerts[i] != InitLEyeVerts[i])
                        {
                            LEyeVerts[i] = Vector3.Lerp(LEyeVerts[i], v, CloseEyesSpeed * DeltaTime);
                        }
                    }

                    for (int i = 0; i < REyeVerts.Length; i++)
                    {
                        Vector3 v;

                        if (EyesClosed.Item2)
                        {
                            v = InitREyeVerts[i] - new Vector3(0, CloseEyesDistance, 0);
                        }
                        else
                        {
                            v = InitREyeVerts[i];
                        }

                        if (REyeVerts[i] != InitREyeVerts[i])
                        {
                            REyeVerts[i] = Vector3.Lerp(REyeVerts[i], v, CloseEyesSpeed * DeltaTime);
                        }
                    }

                    for (int i = 0; i < TongueVerts.Length; i++)
                    {
                        Vector3 v;

                        if (TongueOut)
                        {
                            v = InitTongueVerts[i] - new Vector3(0, 0, MoveTongueDistance);
                        }
                        else
                        {
                            v = InitTongueVerts[i];
                        }

                        if (TongueVerts[i] != InitTongueVerts[i])
                        {
                            TongueVerts[i] = Vector3.Lerp(TongueVerts[i], v, MoveTongueSpeed * DeltaTime);
                        }
                    }
                };
            }
        }
    }

    public class VTuberWindow : GameWindow
    {
        public List<VTuberObject> Objects = new List<VTuberObject>();
        public Action<Exception> OnError = null;
        public float DeltaTime = 0;
        public Color4 BackgroundColor = Color4.CornflowerBlue;

        public VTuberWindow()
        {
            Title = "I4.0 VTuber Virtual Camera";
        }

        private void ExecuteAction(Action Act)
        {
            if (Act != null)
            {
                try
                {
                    Act.Invoke();
                }
                catch (Exception ex)
                {
                    ExecuteAction(OnError, ex);
                }
            }
        }

        private void ExecuteAction<T>(Action<T> Act, T Arg)
        {
            if (Act != null)
            {
                try
                {
                    Act.Invoke(Arg);
                }
                catch (Exception ex)
                {
                    ExecuteAction(OnError, ex);
                }
            }
        }

        protected override void OnLoad(EventArgs e)
        {
            base.OnLoad(e);
            GL.Enable(EnableCap.DepthTest);

            foreach (VTuberObject obj in Objects)
            {
                ExecuteAction(obj.OnStart);
            }
        }

        protected override void OnClosed(EventArgs e)
        {
            base.OnUnload(e);

            foreach (VTuberObject obj in Objects)
            {
                ExecuteAction(obj.OnClose);
            }

            GL.Disable(EnableCap.DepthTest);
        }

        protected override void OnResize(EventArgs e)
        {
            base.OnResize(e);
            GL.Viewport(0, 0, Width, Height);
        }

        protected override void OnRenderFrame(FrameEventArgs e)
        {
            base.OnRenderFrame(e);
            DeltaTime = (float)e.Time;

            GL.Clear(ClearBufferMask.ColorBufferBit | ClearBufferMask.DepthBufferBit);
            GL.ClearColor(BackgroundColor);

            foreach (VTuberObject obj in Objects)
            {
                GL.PushMatrix();

                GL.Translate(obj.Position);
                GL.Scale(obj.Scale);
                GL.Rotate(1, obj.Rotation);
                GL.Begin(obj.RenderMode);

                foreach (Vector3 vert in obj.GlobalVerts)
                {
                    Vector3 v = vert;
                    v.Z = -v.Z;

                    GL.Color4(obj.Color);
                    GL.Vertex3(v);
                }

                GL.End();

                ExecuteAction(obj.OnLoop, DeltaTime);
                GL.PopMatrix();
            }

            SwapBuffers();
            GL.Flush();
        }
    }
}