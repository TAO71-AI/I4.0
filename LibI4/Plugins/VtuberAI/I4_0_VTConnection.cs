using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;

namespace TAO71.I4.Plugins.VTuber
{
    public static class I4_0_VTConnection
    {
        private static Socket ConnectionSocket = null;
        public static Action<string> OnError = null;
        private static Socket Client = null;
        private static byte[] ReceivedBytes = new byte[16];

        public static bool IsConnected()
        {
            if (ConnectionSocket == null || Client == null)
            {
                return false;
            }

            return Client.Connected;
        }

        public static void StartServer(string IP = "0.0.0.0", int Port = 2052)
        {
            StartServer(new IPEndPoint(IPAddress.Parse(IP), Port));
        }

        public static void StartServer(IPEndPoint EndPoint)
        {
            StopServer();
            ConnectionSocket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);

            try
            {
                ConnectionSocket.Bind(EndPoint);
                ConnectionSocket.Listen(32);
                ConnectionSocket.BeginAccept(AcceptClient, null);
            }
            catch (Exception ex)
            {
                if (OnError != null)
                {
                    try
                    {
                        OnError.Invoke(ex.Message);
                    }
                    catch
                    {

                    }
                }
            }
        }

        public static void StopServer()
        {
            if (ConnectionSocket != null)
            {
                ConnectionSocket.Close();

                Client = null;
                ConnectionSocket = null;
            }
        }

        public static void SendData(byte[] Data)
        {
            if (Client != null)
            {
                Client.Send(Data);
            }
            else if (OnError != null)
            {
                try
                {
                    OnError.Invoke("Client is null.");
                }
                catch
                {

                }
            }
        }

        public static byte[] SendData(string Message)
        {
            byte[] rbuffer = new byte[8];

            SendData(Encoding.UTF8.GetBytes(Message));
            Client.Receive(rbuffer);

            Thread.Sleep(100);
            return rbuffer;
        }

        private static void AcceptClient(IAsyncResult Result)
        {
            Client = ConnectionSocket.EndAccept(Result);
        }
    }
}