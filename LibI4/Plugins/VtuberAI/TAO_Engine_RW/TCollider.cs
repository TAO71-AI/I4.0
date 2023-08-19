using System;
using System.Collections.Generic;

namespace TAO.Engine
{
    public class TCollider
    {
        public TVector3 Offset = TVector3.Zero();
        public TVector3 Size = TVector3.One();
        public bool Enabled = true;
        public List<string> Tags = new List<string>();
        public List<string> IgnoreTags = new List<string>();

        public TCollider()
        {

        }

        public TCollider(TVector3 Offset, TVector3 Size)
        {
            this.Offset = Offset;
            this.Size = Size;
        }

        public TCollider(TVector3 Offset, TVector3 Size, bool Enabled)
        {
            this.Offset = Offset;
            this.Size = Size;
            this.Enabled = Enabled;
        }

        public static bool Between(TCollider A, TCollider B, bool IgnoreColliderEnabled = false)
        {
            bool x = (B.Offset.X + B.Size.X / 2 >= A.Offset.X - A.Size.X / 2) &&
                (B.Offset.X - B.Size.X / 2 <= A.Offset.X + A.Size.X / 2);
            bool y = (B.Offset.Y + B.Size.Y / 2 >= A.Offset.Y - A.Size.Y / 2) &&
                (B.Offset.Y - B.Size.Y / 2 <= A.Offset.Y + A.Size.Y / 2);
            bool z = (B.Offset.Z + B.Size.Z / 2 >= A.Offset.Z - A.Size.Z / 2) &&
                (B.Offset.Z - B.Size.Z / 2 <= A.Offset.Z + A.Size.Z / 2);

            foreach (string tag in B.Tags)
            {
                if (A.IgnoreTags.Contains(tag))
                {
                    return false;
                }
            }

            foreach (string tag in A.Tags)
            {
                if (B.IgnoreTags.Contains(tag))
                {
                    return false;
                }
            }

            return x && y && z && (A != B) && (IgnoreColliderEnabled || (A.Enabled && B.Enabled));
        }

        public bool Between(TCollider B, bool IgnoreColliderEnabled = false)
        {
            return Between(this, B, IgnoreColliderEnabled);
        }

        public override string ToString()
        {
            return "Offset = '" + Offset + "', Size = '" + Size + "', Enabled = '" + Enabled + "'";
        }
    }
}