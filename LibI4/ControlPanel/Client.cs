using System;
using System.Net;
using System.Net.Sockets;
using System.Text;

namespace TAO.I4.ControlPanel
{
    public static class Client
    {
        private static Socket ClientSocket = null;
        private static byte[] ReceiveBuffer = new byte[4096];
        public static Action<string> OnErrorAction = null;
        public static Action<string> OnReceiveAction = null;

        public static void Connect()
        {
            try
            {
                Disconnect();

                ClientSocket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
                ClientSocket.Connect(new IPEndPoint(IPAddress.Loopback, 5342));

                try
                {
                    ClientSocket.BeginReceive(ReceiveBuffer, 0, ReceiveBuffer.Length, SocketFlags.None, OnReceive, null);
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

        public static void Disconnect()
        {
            if (ClientSocket != null)
            {
                if (ClientSocket.Connected)
                {
                    ClientSocket.Disconnect(false);
                }

                ClientSocket.Close();
                ClientSocket = null;
            }
        }

        private static void SendData(string Message)
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

        public static void SendStopTalking()
        {
            SendData("st");
        }

        public static void SendSayMessage(string Message)
        {
            SendData("rsay " + Message);
        }

        public static void SendAsk(string Question)
        {
            SendData("rask " + Question);
        }

        public static void SendCustom(string Message)
        {
            SendData(Message);
        }

        private static void OnReceive(IAsyncResult ar)
        {
            string Message = Encoding.ASCII.GetString(ReceiveBuffer);
            ReceiveBuffer = new byte[ReceiveBuffer.Length];

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

            try
            {
                ClientSocket.BeginReceive(ReceiveBuffer, 0, ReceiveBuffer.Length, SocketFlags.None, OnReceive, null);
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