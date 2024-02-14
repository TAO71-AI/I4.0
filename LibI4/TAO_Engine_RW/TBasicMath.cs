using System;

namespace TAO.Engine
{
    public static class TBasicMath
    {
        public static TVector2 AbsVector(TVector2 Vector)
        {
            return new TVector2
            (
                Math.Abs(Vector.X),
                Math.Abs(Vector.Y)
            );
        }

        public static TVector3 AbsVector(TVector3 Vector)
        {
            return new TVector3
            (
                Math.Abs(Vector.X),
                Math.Abs(Vector.Y),
                Math.Abs(Vector.Z)
            );
        }

        public static TVector4 AbsVector(TVector4 Vector)
        {
            return new TVector4
            (
                Math.Abs(Vector.X),
                Math.Abs(Vector.Y),
                Math.Abs(Vector.Z),
                Math.Abs(Vector.W)
            );
        }

        public static float Distance(TVector2 A, TVector2 B)
        {
            return Math.Abs(
                (A.X - B.X) +
                (A.Y - B.Y)
            );
        }

        public static float Distance(TVector3 A, TVector3 B)
        {
            return Math.Abs(
                (A.X - B.X) +
                (A.Y - B.Y) +
                (A.Z - B.Z)
            );
        }

        public static float Distance(TVector4 A, TVector4 B)
        {
            return Math.Abs(
                (A.X - B.X) +
                (A.Y - B.Y) +
                (A.Z - B.Z) +
                (A.W - B.W)
            );
        }

        public static float StringToFloat(string Float)
        {
            string tstringdata = Float.Replace(".", ",");

            return float.Parse(tstringdata);
        }

        public static TVector2 StringToVector2(string Vector, char Separator = ' ')
        {
            string[] tstringdata = Vector.Replace(".", ",").Split(Separator);

            return new TVector2
            (
                float.Parse(tstringdata[0]),
                float.Parse(tstringdata[1])
            );
        }

        public static TVector3 StringToVector3(string Vector, char Separator = ' ')
        {
            string[] tstringdata = Vector.Replace(".", ",").Split(Separator);

            return new TVector3
            (
                float.Parse(tstringdata[0]),
                float.Parse(tstringdata[1]),
                float.Parse(tstringdata[2])
            );
        }

        public static TVector4 StringToVector4(string Vector, char Separator = ' ')
        {
            string[] tstringdata = Vector.Replace(".", ",").Split(Separator);

            return new TVector4
            (
                float.Parse(tstringdata[0]),
                float.Parse(tstringdata[1]),
                float.Parse(tstringdata[2]),
                float.Parse(tstringdata[3])
            );
        }

        public static bool Between(float Value, float Min, float Max)
        {
            return Value >= Min && Value <= Max;
        }

        public static bool Between(TVector2 Value, TVector2 Min, TVector2 Max)
        {
            return Value >= Min && Value <= Max;
        }

        public static bool Between(TVector3 Value, TVector3 Min, TVector3 Max)
        {
            return Value >= Min && Value <= Max;
        }

        public static bool Between(TVector4 Value, TVector4 Min, TVector4 Max)
        {
            return Value >= Min && Value <= Max;
        }

    }
}