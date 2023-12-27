using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Net.WebSockets;
using System.Threading;
using System.Threading.Tasks;
using System.Text;
using Newtonsoft.Json;

namespace TAO.I4.PythonManager
{
    public static class PyAIResponse
    {
        public static List<string> Servers = new List<string>()
        {
            "127.0.0.1", // Localhost
            "147.78.87.113", //TAO71 Server
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

        public static bool ConnectToServer(string Server)
        {
            ReadKeyFromFile();
            DisconnectFromServer();

            bool r = false;

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

                r = true;
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

            return r;
        }

        public static bool ConnectToServer(int Server)
        {
            if (Server < 0 || Server >= Servers.Count)
            {
                if (DefaultServer < 0 || DefaultServer >= Servers.Count)
                {
                    return false;
                }

                Server = DefaultServer;
            }

            return ConnectToServer(Servers[Server]);
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

        public static byte[] ExecuteService(string Message, Service ServiceData = Service.CustomCommand, string[] ExtraSystemMessages = null, string Translator = "", bool UseDefaultSysPrompts = true, string AIArgs = "", string Conversation = "")
        {
            string sd = "service_";
            string jsonData = "";
            string msg = Message;

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
                    case Service.CustomCommand:
                        sd += "1";
                        break;
                    case Service.Image:
                        sd += "2";
                        break;
                    case Service.ImageToText:
                        sd += "3";
                        break;
                    case Service.WhisperSTT:
                        sd += "4";
                        break;
                    case Service.Audio:
                        sd += "5";
                        break;
                    case Service.DepthEstimation:
                        sd += "6";
                        break;
                }
            }
            else
            {
                sd += ((int)ServiceData).ToString();
            }

            sd += " ";

            jsonData += "{";
            jsonData += "\"api_key\": \"" + ReadKeyFromFile() + "\", \"cmd\": \"" + sd + msg + "\", " +
                "\"extra_data\": {\"system_msgs\": " + Extra.ArrayToJson(ExtraSystemMessages) + ", " +
                "\"translator\": \"" + Translator + "\", \"use_default_sys_prompts\": \"" +
                UseDefaultSysPrompts.ToString().ToLower() + "\", \"ai_args\": \"" + AIArgs + "\"}, " +
                "\"conversation\": \"" + Conversation + "\"";
            jsonData += "}";

            return SendAndWaitForReceive(Encoding.UTF8.GetBytes(jsonData), true).Result;
        }

        public static byte[] TryShowImage(byte[] Data, bool OpenFile = true, bool DeleteOnClose = true)
        {
            return TryShowImage(Convert.ToBase64String(Data), OpenFile, DeleteOnClose);
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

        public static byte[] TryOpenAudio(byte[] Data, bool OpenFile = true, bool DeleteOnClose = true)
        {
            return TryOpenAudio(Convert.ToBase64String(Data), OpenFile, DeleteOnClose);
        }

        public static byte[] TryOpenAudio(string Data, bool OpenFile = true, bool DeleteOnClose = true)
        {
            byte[] buffer = Convert.FromBase64String(Data);

            if (!File.Exists("temp_audio.wav"))
            {
                File.Create("temp_audio.wav").Close();
            }

            File.WriteAllBytes("temp_audio.wav", buffer);

            if (OpenFile)
            {
                System.Diagnostics.Process p = new System.Diagnostics.Process();
                p.StartInfo.FileName = "temp_audio.wav";

                p.Start();
                p.WaitForExit();

                if (DeleteOnClose)
                {
                    File.Delete("temp_audio.wav");
                }
            }

            return buffer;
        }

        public static async Task<byte[]> SendAndWaitForReceive(byte[] SendData, bool Connect = true)
        {
            if (Connect)
            {
                if (!ConnectToServer(DefaultServer))
                {
                    throw new Exception("ConnectToServer returned 'false'. Please try to connect to a valid server.");
                }
            }

            if (OnSendDataAction != null)
            {
                OnSendDataAction.Invoke(SendData);
            }

            ReadKeyFromFile();
            await ClientSocket.SendAsync(new ArraySegment<byte>(SendData), WebSocketMessageType.Text, true, CancellationToken.None);

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

        public static string ExecuteCommandOnServer(string Command, bool Connect = true, int Server = -1, string Conversation = "")
        {
            if (Server < 0 || Server >= Servers.Count)
            {
                Server = DefaultServer;
            }

            if (Connect)
            {
                if (!ConnectToServer(Server))
                {
                    throw new Exception("ConnectToServer returned 'false'. Please try to connect to a valid server.");
                }
            }

            string jsonData = "";

            jsonData += "{";
            jsonData += "\"api_key\": \"" + ReadKeyFromFile() + "\", \"cmd\": \"" + Command + "\"," +
                "\"conversation\": \"" + Conversation + "\"";
            jsonData += "}";

            byte[] response_data = SendAndWaitForReceive(Encoding.UTF8.GetBytes(jsonData), false).Result;
            string response;

            if (Connect)
            {
                DisconnectFromServer();
            }

            try
            {
                response = Encoding.UTF8.GetString(response_data);
            }
            catch
            {
                response = Encoding.ASCII.GetString(response_data);
            }

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

        public static async Task<int> SendFileToServer(string FilePath, int Server = -1)
        {
            if (!File.Exists(FilePath))
            {
                throw new Exception("File doesn't exists.");
            }

            if (Server < 0)
            {
                Server = DefaultServer;
            }

            ClientWebSocket client = new ClientWebSocket();
            byte[] FileBytes = File.ReadAllBytes(FilePath);
            int chunksize = 4096;
            int totalChunks = (int)Math.Ceiling((double)FileBytes.Length / chunksize);
            int maxTime = 50;
            int time = 0;

            await client.ConnectAsync(new Uri("ws://" + Servers[Server] + ":8061"), CancellationToken.None);

            while (client.State != WebSocketState.Open)
            {
                if (time > maxTime)
                {
                    throw new Exception("Could not connect to Rec Files server.");
                }

                time++;
                Thread.Sleep(100);
            }

            try
            {
                for (int i = 0; i < totalChunks; i++)
                {
                    int offset = i * chunksize;
                    int length = Math.Min(chunksize, FileBytes.Length - offset);
                    byte[] chunk = new byte[length];

                    Array.Copy(FileBytes, offset, chunk, 0, length);

                    await client.SendAsync(new ArraySegment<byte>(chunk), WebSocketMessageType.Binary, true, CancellationToken.None);

                    if (i == totalChunks - 1)
                    {
                        break;
                    }
                }

                await client.SendAsync(new ArraySegment<byte>(Encoding.UTF8.GetBytes("<end>")), WebSocketMessageType.Binary, true, CancellationToken.None);
            }
            catch
            {
                await client.CloseAsync(WebSocketCloseStatus.Empty, "", CancellationToken.None);
                throw new Exception("Bytes limit error.");
            }

            ArraySegment<byte> rbuffer = new ArraySegment<byte>(new byte[64]);
            await client.ReceiveAsync(rbuffer, CancellationToken.None);

            await client.CloseAsync(WebSocketCloseStatus.Empty, "", CancellationToken.None);
            return Convert.ToInt32(Encoding.UTF8.GetString(rbuffer.Array));
        }

        public static Response GetFullResponse(string Prompt, Service ServerService, string[] SystemPrompts = null, string Translator = "", bool UseDefaultSystemPrompts = true, string AIArgs = "", string Conversation = "", bool Connect = true)
        {
            if (SystemPrompts == null)
            {
                SystemPrompts = new string[0];
            }

            // Send
            byte[] received = ExecuteService(Prompt.Replace("\"", "\'"), ServerService, SystemPrompts, Translator, UseDefaultSystemPrompts, AIArgs, Conversation);

            // Receive
            Response response = new Response();
            List<string> errors = new List<string>();
            dynamic jsonData = null;

            try
            {
                jsonData = JsonConvert.DeserializeObject(Encoding.UTF8.GetString(received).TrimStart().TrimEnd());

                response.JsonData = jsonData;
                response.Command = jsonData["cmd"];

                try
                {
                    dynamic responseData = JsonConvert.DeserializeObject(((string)jsonData["response"]).TrimStart().TrimEnd());
                    List<string> testedModels = new List<string>();

                    response.TextResponse = (string)responseData["response"];
                    response.Model = (string)responseData["model"];
                    response.TextClassification = (string)responseData["text_classification"];
                    response.Title = (string)responseData["title"];

                    foreach (string model in responseData["tested_models"])
                    {
                        testedModels.Add(model);
                    }

                    response.TestedModels = testedModels.ToArray();

                    foreach (string error in responseData["errors"])
                    {
                        errors.Add(error);
                    }

                    try
                    {
                        dynamic filesData = JsonConvert.DeserializeObject(((string)responseData["files"]).TrimStart().TrimEnd());
                        List<Response.ResponseFile> files = new List<Response.ResponseFile>();

                        if (filesData.ContainsKey("image"))
                        {
                            files.Add(new Response.ResponseFile()
                            {
                                FileType = "image",
                                FileBytes = Convert.FromBase64String((string)filesData["image"])
                            });
                        }

                        if (filesData.ContainsKey("audio"))
                        {
                            files.Add(new Response.ResponseFile()
                            {
                                FileType = "audio",
                                FileBytes = Convert.FromBase64String((string)filesData["audio"])
                            });
                        }

                        response.Files = files.ToArray();
                    }
                    catch (Exception ex)
                    {
                        errors.Add("(C#) Could not deserialize file data. Error: " + ex.Message);
                    }
                }
                catch (Exception ex)
                {
                    errors.Add("(C#) Could not deserialize the response, returning full response as string. Error: " + ex.Message);
                    response.TextResponse = (string)jsonData["response"];
                }
            }
            catch (Exception ex)
            {
                errors.Add("(C#) Error in GetFullResponse: " + ex.Message);
            }

            response.Errors = errors.ToArray();
            return response;
        }

        public enum Service
        {
            Chatbot = 0,
            CustomCommand = 1,
            Image = 2,
            ImageToText = 3,
            WhisperSTT = 4,
            Audio = 5,
            DepthEstimation = 6
        }
    }

    public class Response
    {
        public class ResponseFile
        {
            public string FileType = "";
            public byte[] FileBytes = new byte[0];
        }

        public dynamic JsonData = new Dictionary<string, string>();
        public string Title = "";
        public string TextResponse = "";
        public string Model = "";
        public string Command = "";
        public string TextClassification = "";
        public string[] TestedModels = new string[0];
        public string[] Errors = new string[0];
        public ResponseFile[] Files = new ResponseFile[0];
    }
}