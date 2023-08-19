using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Text;
using TAO.I4.ControlPanel;

namespace TAO.I4.Plugins.AIChat
{
    public static class ChatServer
    {
        private static Socket ServerSocket = null;
        private static byte[] ReceiveBuffer = new byte[8192];
        public static Action<Socket> OnConnectAction = null;
        public static Action<byte[]> OnReceiveAction = null;
        private static List<Socket> Clients = new List<Socket>();

        public static void StartServer(int MaxUsers = 15)
        {
            StopServer();
            Server.Start();
            Client.Connect();

            MaxUsers = Math.Abs(MaxUsers);

            if (MaxUsers == 0)
            {
                return;
            }

            ServerSocket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
            ServerSocket.Bind(new IPEndPoint(IPAddress.Any, 2950));
            ServerSocket.Listen(MaxUsers);

            ServerSocket.BeginAccept(OnConnect, null);
        }

        public static void StopServer()
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
                Socket client = ServerSocket.EndAccept(ar);

                if (OnConnectAction != null)
                {
                    OnConnectAction.Invoke(client);
                }

                Clients.Add(client);

                client.BeginReceive(ReceiveBuffer, 0, ReceiveBuffer.Length, SocketFlags.None, OnReceive, client);
                ServerSocket.BeginAccept(OnConnect, null);
            }
            catch
            {

            }
        }

        private static void OnReceive(IAsyncResult ar)
        {
            Socket client = (Socket)ar.AsyncState;
            int receivedBytes = client.EndReceive(ar);
            byte[] tmpBuffer = new byte[ReceiveBuffer.Length];

            Array.Copy(ReceiveBuffer, tmpBuffer, receivedBytes);
            ReceiveBuffer = new byte[ReceiveBuffer.Length];

            if (OnReceiveAction != null)
            {
                OnReceiveAction.Invoke(tmpBuffer);
            }

            string strBuffer = Encoding.ASCII.GetString(tmpBuffer).TrimStart().TrimEnd();
            string strBufferLower = strBuffer.ToLower();

            if (strBufferLower.StartsWith("[ai_say] "))
            {
                Client.SendSayMessage(strBuffer.Substring(9));
            }
            else if (strBufferLower == "[ai_st]")
            {
                Client.SendStopTalking();
            }
            else if (strBufferLower.StartsWith("[ai_ask] "))
            {
                Client.SendAsk(strBuffer.Substring(9));
            }
            else if (strBuffer == "")
            {
                Clients.Remove(client);
                client.Close();

                return;
            }
            else
            {
                try
                {
                    client.Send(Encoding.ASCII.GetBytes("'" + Clients.IndexOf(client) + "': " + strBuffer));
                }
                catch
                {

                }
            }

            client.BeginReceive(ReceiveBuffer, 0, ReceiveBuffer.Length, SocketFlags.None, OnReceive, client);
        }
    }
}