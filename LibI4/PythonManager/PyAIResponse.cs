using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;

namespace TAO.I4.PythonManager
{
    public static class PyAIResponse
    {
        public static List<string> Servers = new List<string>()
        {
            "127.0.0.1", // Localhost
            "147.78.87.113", //TAO Server
        };
        public static int DefaultServer = 0;
        private static Socket ClientSocket = null;
        public static Action<string> OnConnectingToServerAction = null;
        public static Action<string> OnConnectToServerAction = null;
        public static Action OnDisconnectFromServerAction = null;
        public static Action<byte[]> OnSendDataAction = null;
        public static Action<byte[]> OnReceiveDataAction = null;
        public static Action<string> OnReceiveWelcomeMessageAction = null;

        public static string ReadKeyFromFile()
        {
            if (!File.Exists("Python_Server_API_Key.txt"))
            {
                File.Create("Python_Server_API_Key.txt").Close();
            }

            return File.ReadAllText("Python_Server_API_Key.txt").Trim();
        }

        public static void ConnectToServer(string Server)
        {
            ReadKeyFromFile();
            DisconnectFromServer();

            if (OnConnectingToServerAction != null)
            {
                OnConnectingToServerAction.Invoke(Server);
            }

            ClientSocket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
            ClientSocket.Connect(new IPEndPoint(IPAddress.Parse(Server), 8071));

            if (OnConnectToServerAction != null)
            {
                OnConnectToServerAction.Invoke(Server);
            }

            try
            {
                byte[] rec_wm_buffer = new byte[4096];
                ClientSocket.Receive(rec_wm_buffer);

                if (OnReceiveWelcomeMessageAction != null)
                {
                    OnReceiveWelcomeMessageAction.Invoke(Server);
                }
            }
            catch
            {

            }
        }

        public static void ConnectToServer(int Server)
        {
            if (Server < 0 || Server >= Servers.Count)
            {
                if (DefaultServer < 0 || DefaultServer >= Servers.Count)
                {
                    return;
                }

                Server = DefaultServer;
            }

            ConnectToServer(Servers[Server]);
        }

        public static void DisconnectFromServer()
        {
            if (ClientSocket != null)
            {
                if (ClientSocket.Connected)
                {
                    ClientSocket.Disconnect(true);
                }

                ClientSocket.Close();
                ClientSocket = null;

                if (OnDisconnectFromServerAction != null)
                {
                    OnDisconnectFromServerAction.Invoke();
                }
            }
        }

        public static byte[] ExecuteService(string Message, Service ServiceData = Service.CustomCommand,
            string[] ExtraSystemMessages = null, string Translator = "")
        {
            string sd = "service_";
            string jsonData = "";

            if (ExtraSystemMessages == null)
            {
                ExtraSystemMessages = new string[0];
            }

            if (ServiceData < 0)
            {
                if (ServiceData == Service.Chatbot)
                {
                    sd += "0";
                }
                else if (ServiceData == Service.Translation)
                {
                    sd += "1";
                }
                else if (ServiceData == Service.CustomCommand)
                {
                    sd += "2";
                }
            }
            else
            {
                sd += ((int)ServiceData).ToString();
            }

            sd += " ";

            jsonData += "{";
            jsonData += "\"api_key\": \"" + ReadKeyFromFile() + "\", \"cmd\": \"" + sd + Message + "\", " +
                "\"extra_data\": {\"system_msgs\": " + Config.ArrayToJson(ExtraSystemMessages) + ", " +
                "\"translator\": \"" + Translator + "\"}";
            jsonData += "}";

            return SendAndWaitForReceive(Encoding.UTF8.GetBytes(jsonData), true);
        }

        public static byte[] SendAndWaitForReceive(byte[] SendData, bool Connect = true)
        {
            if (Connect)
            {
                ConnectToServer(DefaultServer);
            }

            if (OnSendDataAction != null)
            {
                OnSendDataAction.Invoke(SendData);
            }

            ReadKeyFromFile();
            ClientSocket.Send(SendData);

            byte[] rec_buffer = new byte[10240];
            int bytes = ClientSocket.Receive(rec_buffer);
            byte[] response = new byte[bytes];

            Array.Copy(rec_buffer, response, bytes);

            if (OnReceiveDataAction != null)
            {
                OnReceiveDataAction.Invoke(SendData);
            }

            if (Connect)
            {
                DisconnectFromServer();
            }

            return response;
        }

        public static string ExecuteCommandOnServer(string Command, int Server = -1)
        {
            ConnectToServer(Server);
            string jsonData = "";

            jsonData += "{";
            jsonData += "\"api_key\": \"" + ReadKeyFromFile() + "\", \"cmd\": \"" + Command + "\"";
            jsonData += "}";

            byte[] response_data = SendAndWaitForReceive(Encoding.UTF8.GetBytes(jsonData), false);
            string response;

            try
            {
                response = Encoding.UTF8.GetString(response_data);
            }
            catch
            {
                response = Encoding.ASCII.GetString(response_data);
            }

            DisconnectFromServer();
            return response;
        }

        public static int TryAllServer(bool SetFirstAsDefault = true)
        {
            foreach (string server in Servers)
            {
                try
                {
                    ConnectToServer(server);
                    DisconnectFromServer();
                    int id = Servers.IndexOf(server);

                    if (SetFirstAsDefault)
                    {
                        DefaultServer = id;
                    }

                    return id;
                }
                catch
                {
                    
                }
            }

            return -1;
        }

        public enum Service
        {
            Chatbot = 0,
            Translation = 1,
            CustomCommand = 2
        }
    }
}