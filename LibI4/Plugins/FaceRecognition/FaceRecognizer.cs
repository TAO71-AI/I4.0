using System;
using TAO.I4.PythonManager;

namespace TAO.I4.Plugins.FaceRecognition
{
    public static class FaceRecognizer
    {
        public static (int, int, int, int) Recognize(bool DrawRectangle = true)
        {
            string args = "";

            if (!DrawRectangle)
            {
                args = "-nr";
            }

            (string, int) response = PythonDownloader.ExecutePythonCode("opencv_face_recognition.py", args);
            string[] spRes = response.Item1.Split(' ');
            (int, int, int, int) r = (-1, -1, -1, -1);

            try
            {
                r.Item1 = Convert.ToInt32(spRes[0]);
                r.Item2 = Convert.ToInt32(spRes[1]);
                r.Item3 = Convert.ToInt32(spRes[2]);
                r.Item4 = Convert.ToInt32(spRes[3]);
            }
            catch
            {
                r = (-1, -1, -1, -1);
            }

            return r;
        }
    }
}