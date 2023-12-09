using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;

namespace TAO.NeuroN.ServerConnection
{
    public static class Server
    {
        private static Socket ServerSocket = null;
        private static byte[] ReceiveBuffer = new byte[4096];
        public static Action<Socket> OnConnectAction = null;
        public static Action<string> OnReceiveAction = null;
        public static string ResponsesFilePath = "Responses.txt";

        public static void StartServer(int Port = 7171, int MaxUsers = 5000)
        {
            StopServer();

            if (!File.Exists(ResponsesFilePath))
            {
                File.Create(ResponsesFilePath).Close();
            }

            ServerSocket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
            ServerSocket.Bind(new IPEndPoint(IPAddress.Any, Port));
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
            Socket clientSocket = ServerSocket.EndAccept(ar);

            if (OnConnectAction != null)
            {
                try
                {
                    OnConnectAction.Invoke(clientSocket);
                }
                catch
                {

                }
            }

            clientSocket.BeginReceive(ReceiveBuffer, 0, ReceiveBuffer.Length, SocketFlags.None, OnReceive, clientSocket);
            ServerSocket.BeginAccept(OnConnect, null);
        }

        private static void OnReceive(IAsyncResult ar)
        {
            Socket clientSocket = (Socket)ar.AsyncState;
            byte[] tmpBuffer = new byte[ReceiveBuffer.Length];
            int receivedBytes = clientSocket.EndReceive(ar);

            Array.Copy(ReceiveBuffer, tmpBuffer, receivedBytes);
            ReceiveBuffer = new byte[ReceiveBuffer.Length];

            string receivedMessage = Encoding.ASCII.GetString(tmpBuffer);
            string lreceiveMessage = receivedMessage.ToLower();

            if (lreceiveMessage.StartsWith("get_response "))
            {
                clientSocket.SendTo(
                Encoding.ASCII.GetBytes(
                    GetResponseFromFile(receivedMessage.Substring(13).TrimStart())
                ),
                clientSocket.RemoteEndPoint);
            }

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

        public static string GetResponseFromFile(string Title)
        {
            string[] lines = File.ReadAllLines(ResponsesFilePath);

            for (int i = 0; i < lines.Length; i++)
            {
                string line = lines[i];

                if (line.StartsWith("[") && line.Contains("]: "))
                {
                    string lineTitle = line.Substring(1, line.IndexOf("]: "));

                    if (lineTitle.ToLower() == Title.ToLower())
                    {
                        return line.Substring(line.IndexOf("]: ") + 3).TrimStart();
                    }
                }
            }

            return "";
        }
    }
}