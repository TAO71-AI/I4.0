using System;

namespace TAO.Engine.UI
{
    public class UIObject
    {
        public TVector2[] Vertices = new TVector2[0];
        public TVector4[] Colors = new TVector4[0];
        public TVector2[] TextureCoords = new TVector2[0];
        public TVector2 Position = TVector2.Zero();
        public TVector2 Scale = TVector2.One();
        public TCollider Collider = new TCollider();
        public string RenderMode = "polygon";
        public string Texture = "";
        public bool AllowTransparency = true;

        public static UIObject CreateCube()
        {
            return new UIObject()
            {
                Vertices = new TVector2[]
                {
                    new TVector2(-0.5f, -0.5f),
                    new TVector2(-0.5f, 0.5f),
                    new TVector2(0.5f, 0.5f),
                    new TVector2(0.5f, -0.5f)
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
                    Offset = new TVector3(0.5f, 0.5f, 0),
                    Size = new TVector3(0.515f, 0.75f, 1),
                    Enabled = true
                },
                RenderMode = "quads"
            };
        }

        public bool IsCollidingWithMouse(TVector2 MousePosition01, float MouseSize = 0.25f)
        {
            TCollider mouseCollider = new TCollider(
                new TVector3(MousePosition01.X, MousePosition01.Y, 0),
                TVector3.One() * MouseSize
            );

            return Collider.Between(mouseCollider);
        }
    }
}