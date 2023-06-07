using System;
using System.Collections.Generic;
using OpenCvSharp;

namespace TAO.NeuroN.Plugins.Gaming
{
    public class FNF : BasicGame
    {
        private List<Scalar> arrowColors = new List<Scalar>();
        private bool started = false;

        public FNF(string WindowName)
        {
            this.GameWindowName = WindowName;
        }

        public void Start()
        {
            try
            {
                Stop();
            }
            catch
            {

            }

            started = true;

            while (started)
            {
                Mat frame = CaptureScreen();

                Mat gray = new Mat();
                Cv2.CvtColor(frame, gray, ColorConversionCodes.BGR2GRAY);

                Mat edges = new Mat();
                Cv2.Canny(gray, edges, 50, 150);

                var contours = Cv2.FindContoursAsArray(edges, RetrievalModes.External, ContourApproximationModes.ApproxSimple);

                foreach (var contour in contours)
                {
                    var approx = Cv2.ApproxPolyDP(contour, Cv2.ArcLength(contour, true) * 0.02, true);

                    if (approx.Length == 7)
                    {
                        Mat roi = new Mat(frame, Cv2.BoundingRect(approx));
                        var meanColor = Cv2.Mean(roi);

                        if (arrowColors.Count > 0 && !ColorsAreEqual(meanColor, arrowColors[arrowColors.Count - 1]))
                        {
                            Console.WriteLine("COLOR CHANGED!");
                        }

                        arrowColors.Add(meanColor);
                        frame.DrawContours(new[] {approx}, -1, Scalar.Red, 2);
                    }
                }

                Cv2.ImShow("Detección de flechas", frame);

                if (Cv2.WaitKey(1) == 27)
                {
                    break;
                }
            }

            Cv2.DestroyWindow("Detección de flechas");
        }

        public void Stop()
        {
            started = false;
        }

        private static bool ColorsAreEqual(Scalar color1, Scalar color2)
        {
            const double colorThreshold = 10.0;

            for (int i = 0; i < 3; i++)
            {
                if (Math.Abs(color1[i] - color2[i]) > colorThreshold)
                {
                    return false;
                }
            }

            return true;
        }
    }
}