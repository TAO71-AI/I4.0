using System;
using TAO.I4.PythonManager;

namespace TAO.I4.Plugins.Gaming
{
    public static class I4Games
    {
        public static int GameMonitor = -1;

        public static void FNF(string ArrowsDir = "PythonCode/opencv_fnf_arrows", int ScreenSize = 3, int Scale = 1)
        {
            if (ArrowsDir.Trim().Length <= 0)
            {
                ArrowsDir = "PythonCode/opencv_fnf_arrows";
            }

            PythonDownloader.ExecutePythonCode("opencv_games_fnf.py", GameMonitor + " " + ArrowsDir +
                " 0.74 " + ScreenSize + " " + Scale);
        }
    }
}