using System;

namespace TAO.Engine
{
    public static class Raycast
    {
        //IN DEVELOPMENT
        /*public static RaycastHitData Ray(TVector3 Start, TVector3 Dir, float Dist = 1)
        {

        }*/
    }

    public class RaycastHitData
    {
        public readonly TVector3 Position;
        public readonly TCollider Collider;

        public RaycastHitData(TVector3 Position, TCollider Collider)
        {
            this.Position = Position;
            this.Collider = Collider;
        }
    }
}