﻿using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Net.WebSockets;
using System.Threading;
using System.Threading.Tasks;
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
        private static ClientWebSocket ClientSocket = null;
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

            try
            {
                ClientSocket = new ClientWebSocket();
                ClientSocket.ConnectAsync(new Uri("ws://" + Server + ":8060"), CancellationToken.None);

                int currentTime = 0;

                while (ClientSocket.State != WebSocketState.Open)
                {
                    if (currentTime >= 50)
                    {
                        throw new Exception("Error connecting to the server. Make sure it is started.");
                    }

                    Thread.Sleep(100);
                    currentTime += 1;
                }
            }
            catch (Exception ex)
            {
                throw ex;
            }

            if (OnConnectToServerAction != null)
            {
                OnConnectToServerAction.Invoke(Server);
            }

            try
            {
                ArraySegment<byte> receiveBuffer = new ArraySegment<byte>();
                WebSocketReceiveResult result = ClientSocket.ReceiveAsync(receiveBuffer, CancellationToken.None).Result;

                if (OnReceiveWelcomeMessageAction != null)
                {
                    OnReceiveWelcomeMessageAction.Invoke(Encoding.UTF8.GetString(receiveBuffer.Array));
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
                if (ClientSocket.State != WebSocketState.Closed)
                {
                    ClientSocket.CloseAsync(WebSocketCloseStatus.Empty, "", CancellationToken.None);
                }

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
                switch (ServiceData)
                {
                    case Service.Chatbot:
                        sd += "0";
                        break;
                    case Service.Translation:
                        sd += "1";
                        break;
                    case Service.CustomCommand:
                        sd += "2";
                        break;
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

            return SendAndWaitForReceive(Encoding.UTF8.GetBytes(jsonData), true).Result;
        }

        public static byte[] TryShowImage(string Data, bool OpenFile = true, bool DeleteOnClose = true)
        {
            byte[] buffer = Convert.FromBase64String(Data);

            if (!File.Exists("temp_img.png"))
            {
                File.Create("temp_img.png").Close();
            }

            File.WriteAllBytes("temp_img.png", buffer);

            if (OpenFile)
            {
                System.Diagnostics.Process p = new System.Diagnostics.Process();
                p.StartInfo.FileName = "temp_img.png";

                p.Start();
                p.WaitForExit();

                if (DeleteOnClose)
                {
                    File.Delete("temp_img.png");
                }
            }

            return buffer;
        }

        public static async Task<byte[]> SendAndWaitForReceive(byte[] SendData, bool Connect = true)
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
            await ClientSocket.SendAsync(new ArraySegment<byte>(SendData), WebSocketMessageType.Text, true,
                CancellationToken.None);

            WebSocketReceiveResult result;
            MemoryStream stream = new MemoryStream();
            byte[] streamBytes = new byte[0];

            do
            {
                ArraySegment<byte> buffer = new ArraySegment<byte>(SendData);

                result = await ClientSocket.ReceiveAsync(buffer, CancellationToken.None);
                stream.Write(buffer.Array, buffer.Offset, result.Count);
            }
            while (!result.EndOfMessage);

            streamBytes = stream.ToArray();
            stream.Close();
            stream.Dispose();

            if (OnReceiveDataAction != null)
            {
                OnReceiveDataAction.Invoke(SendData);
            }

            if (Connect)
            {
                DisconnectFromServer();
            }

            return streamBytes;
        }

        public static string ExecuteCommandOnServer(string Command, int Server = -1)
        {
            ConnectToServer(Server);
            string jsonData = "";

            jsonData += "{";
            jsonData += "\"api_key\": \"" + ReadKeyFromFile() + "\", \"cmd\": \"" + Command + "\"";
            jsonData += "}";

            byte[] response_data = SendAndWaitForReceive(Encoding.UTF8.GetBytes(jsonData), false).Result;
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
            CustomCommand = 2,
            Image = 4
        }
    }
}