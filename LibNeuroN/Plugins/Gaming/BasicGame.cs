using System;
using System.Collections.Generic;
using System.Diagnostics;
using OpenCvSharp;

namespace TAO.NeuroN.Plugins.Gaming
{
    public class BasicGame
    {
        protected string GameWindowName = "";
        private VideoCapture VidCapture;

        public BasicGame()
        {
            VidCapture = new VideoCapture(0);

            if (!VidCapture.IsOpened())
            {
                throw new Exception("Error capturing screen.");
            }

            Cv2.NamedWindow(GameWindowName);
        }

        public Mat CaptureScreen()
        {
            Mat frame = new Mat();
            VidCapture.Read(frame);

            if (frame.Empty())
            {
                return null;
            }

            return frame;
        }

        public void PressKey(ConsoleKey Key)
        {

        }
    }
}