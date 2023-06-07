using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using TAO.NeuroN.PythonManager;

namespace TAO.NeuroN.ControlPanel
{
    public static class Server
    {
        private static Socket ServerSocket = null;
        private static byte[] ReceiveBuffer = new byte[4096];
        private static Socket ClientSocket = null;
        public static Action<string> OnErrorAction = null;
        public static Action<string> OnReceiveAction = null;
        public static int MaxAIAsk = 2;
        private static int AIAsk = 0;

        public static void Start()
        {
            Stop();

            try
            {
                ServerSocket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
                ServerSocket.Bind(new IPEndPoint(IPAddress.Any, 5342));
                ServerSocket.Listen(1);

                ServerSocket.BeginAccept(OnConnect, null);
            }
            catch (Exception ex)
            {
                if (OnErrorAction != null)
                {
                    OnErrorAction.Invoke(ex.Message);
                }
            }
        }

        public static void Stop()
        {
            if (ServerSocket != null)
            {
                ServerSocket.Close();
                ServerSocket = null;
            }
        }

        private static void OnConnect(IAsyncResult ar)
        {
            try
            {
                ClientSocket = ServerSocket.EndAccept(ar);
                
                ClientSocket.BeginReceive(ReceiveBuffer, 0, ReceiveBuffer.Length, SocketFlags.None, OnReceive, ClientSocket);
            }
            catch (Exception ex)
            {
                if (OnErrorAction != null)
                {
                    OnErrorAction.Invoke(ex.Message);
                }
            }

            try
            {
                ServerSocket.BeginAccept(OnConnect, null);
            }
            catch (Exception ex)
            {
                if (OnErrorAction != null)
                {
                    OnErrorAction.Invoke(ex.Message);
                }
            }
        }

        private static void OnReceive(IAsyncResult ar)
        {
            try
            {
                ClientSocket = (Socket)ar.AsyncState;
                int receivedBytes = ClientSocket.EndReceive(ar);
                byte[] tmpBuffer = new byte[receivedBytes];

                Array.Copy(ReceiveBuffer, tmpBuffer, receivedBytes);
                ReceiveBuffer = new byte[ReceiveBuffer.Length];

                string Message = Encoding.ASCII.GetString(tmpBuffer).TrimStart().TrimEnd();

                if (OnReceiveAction != null)
                {
                    try
                    {
                        OnReceiveAction.Invoke(Message);
                    }
                    catch (Exception ex)
                    {
                        if (OnErrorAction != null)
                        {
                            OnErrorAction.Invoke(ex.Message);
                        }
                    }
                }

                if (Message.ToLower().StartsWith("st"))
                {
                    SpeakManager.Kill();
                }
                else if (Message.ToLower().StartsWith("rsay "))
                {
                    SpeakManager.Speak(Message.Substring(5));
                }
                else if (Message.ToLower().StartsWith("rask "))
                {
                    if (AIAsk > MaxAIAsk)
                    {
                        return;
                    }

                    SpeakManager.Speak(PyAIResponse.ExecuteCommandOnServer("ai_response " + Message.Substring(5)));
                    AIAsk += 1;
                }

                try
                {
                    ClientSocket.BeginReceive(ReceiveBuffer, 0, ReceiveBuffer.Length, SocketFlags.None, OnReceive, ClientSocket);
                }
                catch (Exception ex)
                {
                    if (OnErrorAction != null)
                    {
                        OnErrorAction.Invoke(ex.Message);
                    }
                }
            }
            catch (Exception ex)
            {
                if (OnErrorAction != null)
                {
                    OnErrorAction.Invoke(ex.Message);
                }
            }
        }

        public static void SendMessage(string Message)
        {
            try
            {
                ClientSocket.Send(Encoding.ASCII.GetBytes(Message));
            }
            catch (Exception ex)
            {
                if (OnErrorAction != null)
                {
                    OnErrorAction.Invoke(ex.Message);
                }
            }
        }
    }
}
