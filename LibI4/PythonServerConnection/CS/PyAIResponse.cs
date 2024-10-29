/*
 * REMEMBER: Both client-side code and server-side code can be updated and might not work with older versions.
*/

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net.WebSockets;
using System.Threading;
using System.Threading.Tasks;
using System.Text;
using Newtonsoft.Json;

namespace TAO71.I4.PythonManager
{
    public static class PyAIResponse
    {
        // Servers variables
        private static Dictionary<int, Service[]> ServersTasks = new Dictionary<int, Service[]>();
        private static string Connected = "";

        // WebSocket variables
        private static ClientWebSocket? ClientSocket = null;

        // Actions
        public static Action<string>? OnConnectingToServerAction = null;
        public static Action<string>? OnConnectedToServerAction = null;
        public static Action? OnDisconnectFromServerAction = null;
        public static Action<byte[]>? OnSendDataAction = null;
        public static Action<byte[]>? OnReceiveDataAction = null;

        // Other variables
        public static Config Conf = new Config();

        public static Dictionary<int, Service[]> GetTasks()
        {
            // Return a copy of the tasks
            return ServersTasks;
        }

        public static async Task Connect(string Server)
        {
            /*
             * This will connect the user to a server.
             * If the user is alredy connected to a server, this will disconnect it first.            
            */

            // Disconnect from any other server
            await Disconnect();

            // Invoke the action
            if (OnConnectingToServerAction != null)
            {
                OnConnectingToServerAction.Invoke(Server);
            }

            // Create socket and connect
            ClientSocket = new ClientWebSocket();
            await ClientSocket.ConnectAsync(new Uri("ws://" + Server + ":8060"), CancellationToken.None);

            // Wait until it's connected
            int time = 0;

            while (ClientSocket.State != WebSocketState.Open)
            {
                if (time > 50)
                {
                    throw new Exception("Server not responding.");
                }

                Thread.Sleep(100);
                time++;
            }

            // Set connected server
            Connected = Server;

            // Invoke the action
            if (OnConnectedToServerAction != null)
            {
                OnConnectedToServerAction.Invoke(Server);
            }
        }

        public static async Task Connect(int Server)
        {
            /*
             * Alternative connect method using the server ID.           
            */

            if (Server < 0 || Server >= Conf.Servers.Count)
            {
                // The server ID is invalid
                throw new Exception("Invalid server ID.");
            }

            // Connect to the server
            await Connect(Conf.Servers[Server]);
        }

        public static async Task Disconnect()
        {
            /*
             * This will disconnect the user from the server.
             * If the user is not connected to any server this will not do anything.
            */

            if (ClientSocket != null)
            {
                try
                {
                    // Try to close the connection to the server
                    await ClientSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "", CancellationToken.None);
                    ClientSocket.Dispose();
                }
                catch
                {

                }

                // Delete the socket
                ClientSocket = null;

                // Invoke the action
                if (OnDisconnectFromServerAction != null)
                {
                    OnDisconnectFromServerAction.Invoke();
                }
            }

            // Delete the connected server
            Connected = "";
        }

        private static async Task<byte[]> ReceiveFromServer()
        {
            // Result variables
            WebSocketReceiveResult result;
            MemoryStream stream = new MemoryStream();
            byte[] streamBytes = new byte[314572800];  // Max receive size: 314 MB

            do
            {
                // Create a new buffer
                ArraySegment<byte> buffer = new ArraySegment<byte>(streamBytes);

                // Write the result to the buffer, then to the stream
                result = await ClientSocket?.ReceiveAsync(buffer, CancellationToken.None);
                stream.Write(buffer.Array, buffer.Offset, result.Count);

                // Repeat until the end of message
            }
            while (!result.EndOfMessage);

            // Get the bytes from the stream and delete the stream
            streamBytes = stream.ToArray();
            stream.Close();
            stream.Dispose();

            // Return the bytes
            return streamBytes;
        }

        public static async Task<byte[]> SendAndReceive(byte[] Data)
        {
            /*
             * This will send a message to the server and wait for it's response.
             * The user must be connected to a server before using this.            
            */

            // Check if you're connected
            if (!IsConnected())
            {
                throw new Exception("Connect to a server first.");
            }

            // Send the data
            await ClientSocket?.SendAsync(new ArraySegment<byte>(Data), WebSocketMessageType.Binary, true, CancellationToken.None);

            // Invoke the action
            if (OnSendDataAction != null)
            {
                OnSendDataAction.Invoke(Data);
            }

            byte[] received = await ReceiveFromServer();

            // Invoke the action
            if (OnReceiveDataAction != null)
            {
                OnReceiveDataAction.Invoke(received);
            }

            // Return the response
            return received;
        }

        public static async Task<Service[]> GetServicesFromServer()
        {
            /*
             * This will get all the available services from the current connected server.
             * The user must be connected to a server before using this.
            */

            // Check if you're connected
            if (!IsConnected())
            {
                throw new Exception("Connect to a server first.");
            }

            // Ask the server for the models, then deserialize the response into a dictionary and create a services list
            byte[] received = await SendAndReceive(Encoding.UTF8.GetBytes(JsonConvert.SerializeObject(new Dictionary<string, object>()
            {
                {"Service", "get_all_services"},
                {"Prompt", ""},
                {"Files", new Dictionary<string, string>()}
            })));
            string receivedData = Encoding.UTF8.GetString(received);
            Dictionary<string, object> jsonData = JsonConvert.DeserializeObject<Dictionary<string, object>>(receivedData);
            List<Service> services = new List<Service>();

            // Set jsonData
            jsonData = JsonConvert.DeserializeObject<Dictionary<string, object>>((string)jsonData["response"]);

            foreach (string service in jsonData.Keys)
            {
                // Ignore if it alredy exists on the list
                if (!services.Contains(ServiceManager.FromString(service)))
                {
                    // Add the service to the list if don't exists
                    services.Add(ServiceManager.FromString(service));
                }
            }

            // Return all the services
            return services.ToArray();
        }

        public static async Task<int> FindFirstServer(Service ServiceToExecute, bool DeleteData = false)
        {
            /*
             * This will find the first server available with the specified service.
             * If there isn't any available server, this will return an error.
            */

            // Check if the user wants to delete the current services list or if the list is empty
            if (DeleteData || ServersTasks.Count == 0)
            {
                // Clear the list and set an invalid server ID
                ServersTasks.Clear();
                int serverToReturn = -1;

                foreach (string server in Conf.Servers)
                {
                    // For every server
                    try
                    {
                        // Try to connect to the server
                        await Connect(server);

                        // Try to get all the services of the server, then add them to the list
                        Service[] services = await GetServicesFromServer();
                        ServersTasks.Add(Conf.Servers.IndexOf(server), services);

                        // Check every service available from this server
                        foreach (Service service in services)
                        {
                            if (service == ServiceToExecute && serverToReturn < 0)
                            {
                                // If the service is the same the user requests, set the server ID to this server's ID
                                serverToReturn = Conf.Servers.IndexOf(server);
                            }
                        }

                        // Disconnect from the server
                        await Disconnect();
                    }
                    catch
                    {
                        // If the server doesn't responds or if there's another error, ignore it and continue with the next server
                        ServersTasks.Add(Conf.Servers.IndexOf(server), new Service[0]);
                    }
                }

                // Check if the server ID is valid
                if (serverToReturn >= 0)
                {
                    // Return the ID if it's valid (the requested service has been found)
                    return serverToReturn;
                }

                // Return an error if it's invalid (the requested service could not be found)
                throw new Exception("Could not find any server.");
            }

            // If the user doesn't want to delete the data and the services list isn't empty
            foreach (string server in Conf.Servers)
            {
                // For every server get it's services
                foreach (Service service in ServersTasks[Conf.Servers.IndexOf(server)])
                {
                    // Check if the service is the same the user is requesting
                    if (service == ServiceToExecute)
                    {
                        // If it is, then return the server ID
                        return Conf.Servers.IndexOf(server);
                    }
                }

                // Continue with the next server if the requested service could not be found on this one
            }

            // If the requested service has not been found on any server, return an error
            throw new Exception("Could not find any server.");
        }

        public static bool IsConnected()
        {
            // Check if the user is connected to a server
            return Connected.Trim().Length > 0 && ClientSocket?.State == WebSocketState.Open;
        }

        public static IEnumerable<Dictionary<string, object>> SendAndWaitForStreaming(string Data)
        {
            /*
             * This will send a prompt to the connected server and will wait for the full response.
             * Also, this will yield the response of the server when received even if they're not complete.
            */

            // Send to the server and get a response
            byte[] responseBytes = SendAndReceive(Encoding.UTF8.GetBytes(Data)).Result;
            string responseStr = Encoding.UTF8.GetString(responseBytes);
            Dictionary<string, object> response = JsonConvert.DeserializeObject<Dictionary<string, object>>(responseStr);

            // Check if it's streaming
            while (!(bool)response["ended"])
            {
                // Hasn't ended stream, returning dictionary
                yield return response;

                // Wait for receive
                responseBytes = ReceiveFromServer().Result;
                responseStr = Encoding.UTF8.GetString(responseBytes);
                response = JsonConvert.DeserializeObject<Dictionary<string, object>>(responseStr);
            }

            // The stream ended
            yield return response;
            yield break;
        }

        public static IEnumerable<Dictionary<string, object>> ExecuteCommand(string Service, string Prompt = "", int Index = -1)
        {
            /*
             * Executes a very-basic command on the server.
             * You can use this, for example, to delete your conversation or get the queue for a service.
             * 
             * Index == -1 automatically gets the model with the smallest queue size.
            */

            // Serialize a very basic, minimum, data to send to the server
            string jsonData = JsonConvert.SerializeObject(new Dictionary<string, object>()
            {
                {"APIKey", Conf.ServerAPIKey},
                {"Files", new Dictionary<string, string>()},
                {"Service", Service},
                {"Prompt", Prompt},
                {"Conversation", Conf.Chatbot_Conversation},
                {"Index", Index}
            });

            // Return the response (probably serialized)
            return SendAndWaitForStreaming(jsonData);
        }

        public static IEnumerable<Dictionary<string, object>> AutoGetResponseFromServer(string Prompt, Service ServerService, int Index = -1, bool ForceNoConnect = false)
        {
            /*
             * This will automatically get a response a server.
             * If the service requires it, this will serialize your prompt.
             * This will also do other thing before and after I4.0's response to your prompt.
             * 
             * Index == -1 automatically gets the model with the smallest queue size.
            */

            if (!ForceNoConnect)
            {
                // Connect to best server
                int server = FindFirstServer(ServerService).Result;
                Connect(server).Wait();
            }
            else if (!IsConnected())
            {
                throw new Exception("Please connect to a server first or set `ForceNoConnect` to false.");
            }

            // Set the files
            List<Dictionary<string, string>> files = new List<Dictionary<string, string>>();

            // Set prompt template
            if (ServerService == Service.ImageToText || ServerService == Service.DepthEstimation || ServerService == Service.NSFWFilterImage || ServerService == Service.ObjectDetection)
            {
                // Template: img2any
                // For each file
                foreach (string file in Prompt.Split(' '))
                {
                    // Check if file exists
                    if (!File.Exists(file))
                    {
                        // Return an error
                        throw new Exception("File doesn't exists!");
                    }

                    // Read file bytes
                    byte[] fBytes = File.ReadAllBytes(file);

                    // Encode to Base64
                    string fBase64 = Convert.ToBase64String(fBytes);

                    // Add to the list
                    files.Add(new Dictionary<string, string>()
                    {
                        {"type", "image"},
                        {"data", fBase64}
                    });
                }
            }
            else if (ServerService == Service.SpeechToText)
            {
                // Template: audio2text
                // For each file
                foreach (string file in Prompt.Split(' '))
                {
                    // Check if file exists
                    if (!File.Exists(file))
                    {
                        // Return an error
                        throw new Exception("File doesn't exists!");
                    }

                    // Read file bytes
                    byte[] fBytes = File.ReadAllBytes(file);

                    // Encode to Base64
                    string fBase64 = Convert.ToBase64String(fBytes);

                    // Add to the list
                    files.Add(new Dictionary<string, string>()
                    {
                        {"type", "audio"},
                        {"data", fBase64}
                    });
                }
            }
            else if (ServerService == Service.ImageGeneration)
            {
                // Template: text2img
                // Set variables
                string prompt;
                string nPrompt;

                if (Prompt.Contains(" [NEGATIVE] "))
                {
                    // Contains negative prompt, set prompt and negative prompt
                    prompt = Prompt.Substring(0, Prompt.IndexOf(" [NEGATIVE] ", StringComparison.InvariantCulture));
                    nPrompt = Prompt.Substring(Prompt.IndexOf(" [NEGATIVE] ", StringComparison.InvariantCulture) + 12);
                }
                else
                {
                    // Doesn't contains negative prompt, set prompt
                    prompt = Prompt;
                    nPrompt = "";
                }

                // Set prompt to the Text2Image template
                Prompt = JsonConvert.SerializeObject(new Dictionary<string, object>()
                {
                    {"prompt", prompt},
                    {"negative_prompt", nPrompt},
                    {"width", Conf.Text2Image_Width},
                    {"height", Conf.Text2Image_Height},
                    {"guidance", Conf.Text2Image_GuidanceScale},
                    {"steps", Conf.Text2Image_Steps}
                });
            }
            else if (ServerService == Service.TTS)
            {
                // Template: text2audio (for TTS)
                Prompt = JsonConvert.SerializeObject(new Dictionary<string, object>()
                {
                    {"voice", Conf.TTS_Voice},
                    {"language", Conf.TTS_Language},
                    {"pitch", Conf.TTS_Pitch},
                    {"speed", Conf.TTS_Speed},
                    {"text", Prompt}
                });
            }
            else if (ServerService == Service.RVC)
            {
                // Template: audio2audio (RVC)
                foreach (string file in Prompt.Split(' '))
                {
                    // Check if file exists
                    if (!File.Exists(file))
                    {
                        // Return an error
                        throw new Exception("File doesn't exists!");
                    }

                    // Read file bytes
                    byte[] fBytes = File.ReadAllBytes(file);

                    // Encode to Base64
                    string fBase64 = Convert.ToBase64String(fBytes);

                    // Add to the list
                    files.Add(new Dictionary<string, string>()
                    {
                        {"type", "audio"},
                        {"data", fBase64}
                    });
                }

                Prompt = JsonConvert.SerializeObject(new Dictionary<string, object>()
                {
                    {"filter_radius", Conf.RVC_FilterRadius},
                    {"f0_up_key", Conf.RVC_F0},
                    {"protect", Conf.RVC_Protect}
                });
            }
            else if (ServerService == Service.UVR)
            {
                // Template: audio2audio+audio (UVR)
                foreach (string file in Prompt.Split(' '))
                {
                    // Check if file exists
                    if (!File.Exists(file))
                    {
                        // Return an error
                        throw new Exception("File doesn't exists!");
                    }

                    // Read file bytes
                    byte[] fBytes = File.ReadAllBytes(file);

                    // Encode to Base64
                    string fBase64 = Convert.ToBase64String(fBytes);

                    // Add to the list
                    files.Add(new Dictionary<string, string>()
                    {
                        {"type", "audio"},
                        {"data", fBase64}
                    });
                }

                Prompt = JsonConvert.SerializeObject(new Dictionary<string, object>()
                {
                    {"agg", Conf.UVR_Agg}
                });
            }
            else if (ServerService == Service.Chatbot)
            {
                // Template: text2text (vision chatbot)
                try
                {
                    // Try to convert to JSON
                    Dictionary<string, object> jsonPrompt = JsonConvert.DeserializeObject<Dictionary<string, object>>(Prompt);

                    // Check keys
                    if (!jsonPrompt.ContainsKey("prompt") || jsonPrompt.ContainsKey("files"))
                    {
                        // Return error
                        throw new Exception("Invalid keys.");
                    }

                    // Set prompt
                    Prompt = (string)jsonPrompt["prompt"];

                    // Set files
                    files = (List<Dictionary<string, string>>)jsonPrompt["files"];
                }
                catch
                {
                    // Can't deserialize prompt of invalid keys, do not set the template
                }
            }

            // Set prompt
            Prompt = JsonConvert.SerializeObject(new Dictionary<string, object>()
            {
                {"Service", ServiceManager.ToString(ServerService)},
                {"Prompt", Prompt},
                {"Files", files.ToArray()},
                {"APIKey", Conf.ServerAPIKey},
                {"Conversation", Conf.Chatbot_Conversation},
                {"AIArgs", Conf.Chatbot_AIArgs},
                {"SystemPrompts", Conf.Chatbot_ExtraSystemPrompts},
                {"UseDefaultSystemPrompts", Conf.Chatbot_AllowServerSystemPrompts},
                {"Internet", InternetSearchManager.ToString(Conf.InternetOptions)},
                {"Index", Index}
            });

            // Return the response
            return SendAndWaitForStreaming(Prompt);
        }

        public static (int, float) GetQueueForService(Service QueueService, int Index = -1)
        {
            /*
             * This will send a prompt to the connected server asking for the queue size and time.
             * Once received, it will return it.
             * 
             * Index == -1 automatically gets the model with the smallest queue size.
            */

            // Get response from the queue command
            IEnumerable<Dictionary<string, object>> res = ExecuteCommand("get_queue", ServiceManager.ToString(QueueService), Index);

            foreach (Dictionary<string, object> response in res)
            {
                if (!(bool)response["ended"])
                {
                    // Continue ignoring this message
                    continue;
                }

                // Deserialize the received JSON response to a Dictionary and return the users and the time
                Dictionary<string, float> queue = JsonConvert.DeserializeObject<Dictionary<string, float>>((string)response["response"]);
                return ((int)queue["users"], queue["time"]);
            }

            // Throw an error
            throw new Exception("Queue error: Error getting queue.");
        }

        public static void DeleteConversation(string Conversation = null)
        {
            /*
             * This will delete your current conversation ONLY on the connected server.
             * If `Conversation` is null this will use the conversation of the configuration.
            */

            string CConversation = Conf.Chatbot_Conversation.Clone().ToString();

            if (Conversation != null)
            {
                // Update the conversation in the configuration settings
                Conf.Chatbot_Conversation = Conversation;
            }

            // Send request to the server and get the result
            IEnumerable<Dictionary<string, object>> res = ExecuteCommand("clear_conversation");

            // Restore the conversation in the configuration settings
            Conf.Chatbot_Conversation = CConversation;

            foreach (Dictionary<string, object> response in res)
            {
                if (!(bool)response["ended"])
                {
                    // Continue ignoring this message
                    continue;
                }

                // Set response variable
                string result = ((string)response["response"]).ToLower().TrimStart().TrimEnd();

                // Check if response it's invalid
                if (result != "conversation deleted.")
                {
                    // It's invalid, throw an error
                    throw new Exception("Error deleting the conversation. Got `" + result + "`; `conversation deleted.` expected.");
                }

                // It's a valid response, return
                return;
            }

            // Throw an error
            throw new Exception("Delete conversation error.");
        }

        public static void DeleteMemory(int Memory = -1)
        {
            /*
             * This will delete your current memory/memories ONLY on the connected server.
             * If `Memory` is -1 this will delete all the memories.
            */

            string cmd;

            if (Memory == -1)
            {
                // Set the command to delete all the memories
                cmd = "clear_memories";
            }
            else
            {
                // Set the command to delete a memory
                cmd = "clear_memory";
            }

            // Send request to the server and get the result
            IEnumerable<Dictionary<string, object>> res = ExecuteCommand(cmd, Memory.ToString());

            foreach (Dictionary<string, object> response in res)
            {
                if (!(bool)response["ended"])
                {
                    // Continue ignoring this message
                    continue;
                }

                // Set response variable
                string result = ((string)response["response"]).ToLower().TrimStart().TrimEnd();

                // Check if response it's invalid
                if (result != "memories deleted." && result != "memory deleted.")
                {
                    // It's invalid, throw an error
                    throw new Exception("Error deleting the memories/memory. Got `" + result + "`; `memories deleted.` or `memory deleted.` expected.");
                }

                // It's a valid response, return
                return;
            }

            // Throw an error
            throw new Exception("Delete memory/memories error.");
        }

        public static string GetTOS()
        {
            /*
             * Gets the server's Terms Of Service.
            */

            // Send command to the server and wait for response
            IEnumerable<Dictionary<string, object>> response = ExecuteCommand("get_tos");

            // For each response
            foreach (Dictionary<string, object> res in response)
            {
                // Check if it ended
                if (!(bool)res["ended"])
                {
                    // Continue ignoring this message
                    continue;
                }

                // It ended, get the text response
                string tResponse = (string)res["response"];

                // Trim the response
                tResponse = tResponse.TrimStart().TrimEnd();

                // Check the length of the response
                if (tResponse.Length == 0)
                {
                    // There are no TOS
                    return "No TOS.";
                }

                // There are TOS, return the text response
                return tResponse;
            }

            throw new Exception("Error getting TOS: No response from server.");
        }

        public static void OpenFile(string Path, bool WaitForExit = false, bool TemporalFile = false)
        {
            /*
             * This will open the file you want, this is meant to be used after the response of any service from the server.
            */

            // Check if the file exists
            if (!File.Exists(Path))
            {
                // Return an error if it doesn't
                throw new Exception("File doesn't exists.");
            }

            // Check the type of file and adjust the variables to it
            string programName = "";
            string programArgs = "";

            if (Path.EndsWith(".png", StringComparison.InvariantCulture) || Path.EndsWith(".jpeg", StringComparison.InvariantCulture) || Path.EndsWith(".jpg", StringComparison.InvariantCulture))
            {
                // It's an image
                programName = Conf.DefaultImagesProgram;
            }
            else if (Path.EndsWith(".wav", StringComparison.InvariantCulture) || Path.EndsWith(".mp3", StringComparison.InvariantCulture) || Path.EndsWith(".flac", StringComparison.InvariantCulture))
            {
                // It's an audio
                programName = Conf.DefaultAudiosProgram;
            }
            else
            {
                // Unknown type, return an error
                throw new Exception("Invalid/unknown file type.");
            }

            // Check if the program name is empty
            if (programName.Trim().Length == 0)
            {
                // If it is, set it to the path (to use the default system's program)
                programName = Path;
            }
            else
            {
                // If it isn't, set the args (to open the file with the specified program)
                programArgs = Path;
            }

            // Set the process info and create the process
            ProcessStartInfo info = new ProcessStartInfo()
            {
                UseShellExecute = false,
                CreateNoWindow = true,
                FileName = programName,
                Arguments = programArgs,
                RedirectStandardOutput = true,
                RedirectStandardError = true
            };
            Process p = new Process()
            {
                StartInfo = info
            };

            // Start the process
            p.Start();

            // Wait until the program is closed to continue (if the user requests it)
            if (WaitForExit)
            {
                p.WaitForExit();

                // When closed, delete the file if the user says it's temporal
                if (TemporalFile)
                {
                    File.Delete(Path);
                }
            }
        }
    }
}