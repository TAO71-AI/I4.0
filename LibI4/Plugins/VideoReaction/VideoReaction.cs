using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Threading;
using TAO71.I4.PythonManager;

namespace TAO71.I4.Plugins.VideoReaction
{
    public static class VideoReaction
    {
        public static Action<string> OnInitReactingAction = null;
        public static Action<string> OnStartReactingAction = null;
        public static Action<string, Response> OnGetFrameResponseAction = null;
        public static Action<string> OnEndReactingAction = null;
        public static Action<Exception> OnErrorAction = null;
        public static bool IgnoreErrors = false;
        private static bool IsReacting = false;

        public static void Init()
        {
            if (!Directory.Exists("Videos/"))
            {
                Directory.CreateDirectory("Videos/");
            }
        }

        public static Response RecognizeFromVideoFrame(int Monitor = -1, float TimeBetweenFrames = 5, string Translator = "", string AIArgs = "", string Conversation = "")
        {
            Recorder.GetScreenshot(Monitor);
            Recorder.GetSystemSoundData(TimeBetweenFrames);

            string imageID = PyAIResponse.SendFileToServer("tmp_pil_image.png", -1).Result.ToString();
            string whisperID = PyAIResponse.SendFileToServer("tmp_whisper_audio.wav", -1).Result.ToString();

            Response imageDescription = PyAIResponse.GetFullResponse(imageID, Service.ImageToText, null, "", false, "", "", true);
            Response whisperRecognition = PyAIResponse.GetFullResponse(whisperID, Service.WhisperSTT, null, "", false, "", "", true);
            string prompt = "What you see on the video: " + imageDescription.TextResponse + "\nWhat you hear on the video: " + whisperRecognition.TextResponse;

            if (imageDescription.Errors.Length > 0 || whisperRecognition.Errors.Length > 0)
            {
                List<string> Errors = new List<string>();
                Exception ex;

                foreach (string error in imageDescription.Errors)
                {
                    Errors.Add("(IMAGE TO TEXT) " + error);
                }

                foreach (string error in whisperRecognition.Errors)
                {
                    Errors.Add("(WHISPER RECOGNITION) " + error);
                }

                ex = new Exception("Errors: " + Extra.ArrayToJson(Errors.ToArray()));

                if (OnErrorAction != null)
                {
                    OnErrorAction.Invoke(ex);
                }

                if (!IgnoreErrors)
                {
                    throw ex;
                }
            }

            return PyAIResponse.GetFullResponse(prompt, Service.Chatbot, new string[]
            {
                "You're reacting to a video."
            }, Translator, true, AIArgs, Conversation, true);
        }

        public static string GetRandomVideoName()
        {
            string[] videosNames = Directory.GetFiles("Videos/");
            return videosNames[new Random().Next(0, videosNames.Length)];
        }

        public static void ReactToVideo(string VideoName, int Monitor = -1, float FrameTime = 5, string Translator = "", string AIArgs = "", string Conversation = "")
        {
            Init();
            IsReacting = true;

            string videoPath = "Videos/" + VideoName;
            Thread videoThread = new Thread(() =>
            {
                ProcessStartInfo videoProcessInfo = new ProcessStartInfo()
                {
                    FileName = videoPath
                };
                Process videoProcess = new Process();

                videoProcess.StartInfo = videoProcessInfo;
                videoProcess.Start();

                Thread.Sleep(250);

                while (IsReacting)
                {
                    try
                    {
                        Response frameResponse = RecognizeFromVideoFrame(Monitor, FrameTime, Translator, AIArgs, Conversation);

                        if (OnGetFrameResponseAction != null)
                        {
                            OnGetFrameResponseAction.Invoke(VideoName, frameResponse);
                        }

                        Thread.Sleep((int)(FrameTime * 1000));
                    }
                    catch (Exception ex)
                    {
                        if (OnErrorAction != null)
                        {
                            OnErrorAction.Invoke(ex);
                        }

                        if (!IgnoreErrors)
                        {
                            throw ex;
                        }
                    }
                }
            })
            {
                Priority = ThreadPriority.BelowNormal
            };

            try
            {
                videoThread.Start();
            }
            catch (Exception ex)
            {
                if (OnErrorAction != null)
                {
                    OnErrorAction.Invoke(ex);
                }

                if (!IgnoreErrors)
                {
                    videoThread.Abort();
                    throw ex;
                }
            }
        }

        public static void StopReacting()
        {
            IsReacting = false;
        }
    }
}