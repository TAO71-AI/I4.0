using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;

namespace TAO.NeuroN.ServerConnection
{
    public static class Client
    {
        public static List<IPEndPoint> Servers = new List<IPEndPoint>()
        {
            new IPEndPoint(IPAddress.Parse("147.78.87.113"), 7171) //TAO Server
        };
        private static Socket ClientSocket = null;
        private static byte[] ReceiveBuffer = new byte[8192];
        public static Action<IPEndPoint> OnConnectedAction = null;
        public static Action<string> OnReceiveAction = null;

        public static void Connect(IPEndPoint IP)
        {
            Disconnect();

            ClientSocket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
            ClientSocket.Connect(IP);

            if (OnConnectedAction != null)
            {
                try
                {
                    OnConnectedAction.Invoke(IP);
                }
                catch
                {

                }
            }

            ClientSocket.BeginReceive(ReceiveBuffer, 0, ReceiveBuffer.Length, SocketFlags.None, OnReceive, null);
        }

        public static void Connect(int ServerNumber)
        {
            Connect(Servers[ServerNumber]);
        }

        public static void ConnectToAllServers(Action<IPEndPoint> OnEveryServer = null)
        {
            for (int i = 0; i < Servers.Count; i++)
            {
                Connect(i);

                if (OnEveryServer != null)
                {
                    try
                    {
                        OnEveryServer.Invoke(Servers[i]);
                    }
                    catch
                    {

                    }
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

        public static void OnReceive(IAsyncResult ar)
        {
            byte[] tmpBuffer = new byte[ReceiveBuffer.Length];
            int receivedBytes = ClientSocket.EndReceive(ar);

            Array.Copy(ReceiveBuffer, tmpBuffer, receivedBytes);
            ReceiveBuffer = new byte[ReceiveBuffer.Length];

            string receivedMessage = Encoding.ASCII.GetString(tmpBuffer);

            if (OnReceiveAction != null)
            {
                try
                {
                    OnReceiveAction.Invoke(receivedMessage);
                }
                catch
                {

                }
            }
        }

        public static void SendData(string Data)
        {
            ClientSocket.Send(Encoding.ASCII.GetBytes(Data));
        }
    }
}