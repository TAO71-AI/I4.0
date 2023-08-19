using System;
using System.Net;
using System.Net.Sockets;
using System.Text;

namespace TAO.I4.Plugins.AIChat
{
    public static class ChatClient
    {
        private static Socket ClientSocket = null;
        private static byte[] ReceiveBuffer = new byte[8192];
        public static Action<byte[]> OnReceiveAction = null;

        public static void Connect(string ServerAddress)
        {
            Disconnect();

            ClientSocket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
            ClientSocket.Connect(new IPEndPoint(IPAddress.Parse(ServerAddress), 2950));

            try
            {
                ClientSocket.BeginReceive(ReceiveBuffer, 0, ReceiveBuffer.Length, SocketFlags.None, OnReceive, null);
            }
            catch
            {

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

        private static void OnReceive(IAsyncResult ar)
        {
            try
            {
                int receivedBytes = ClientSocket.EndReceive(ar);
                byte[] tmpBuffer = new byte[ReceiveBuffer.Length];

                Array.Copy(ReceiveBuffer, tmpBuffer, receivedBytes);
                ReceiveBuffer = new byte[ReceiveBuffer.Length];

                if (OnReceiveAction != null)
                {
                    OnReceiveAction.Invoke(tmpBuffer);
                }

                ClientSocket.BeginReceive(ReceiveBuffer, 0, ReceiveBuffer.Length, SocketFlags.None, OnReceive, null);
            }
            catch
            {

            }
        }

        public static void SendData(string Data)
        {
            ClientSocket.Send(Encoding.ASCII.GetBytes(Data));
        }

        public static void SendData(byte[] Data)
        {
            ClientSocket.Send(Data);
        }
    }
}