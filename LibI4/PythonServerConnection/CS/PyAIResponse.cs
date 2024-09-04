/*
 * REMEMBER: Both client-side code and server-side code can be updated and might not work with older versions.
 * This client-side code works for the versions: "v6.5.0".
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
        private static ClientWebSocket ClientSocket = null;

        // Actions
        public static Action<string> OnConnectingToServerAction = null;
        public static Action<string> OnConnectedToServerAction = null;
        public static Action OnDisconnectFromServerAction = null;
        public static Action<byte[]> OnSendDataAction = null;
        public static Action<byte[]> OnReceiveDataAction = null;

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
            byte[] streamBytes = new byte[8192];

            do
            {
                // Create a new buffer
                ArraySegment<byte> buffer = new ArraySegment<byte>(streamBytes);

                // Write the result to the buffer, then to the stream
                result = await ClientSocket.ReceiveAsync(buffer, CancellationToken.None);
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
            await ClientSocket.SendAsync(new ArraySegment<byte>(Data), WebSocketMessageType.Binary, true, CancellationToken.None);

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
            return Connected.Trim().Length > 0 && ClientSocket.State == WebSocketState.Open;
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

            // Check the service
            if (ServerService == Service.DepthEstimation || ServerService == Service.ImageToImage || ServerService == Service.ImageToText || ServerService == Service.NSFWFilterImage || ServerService == Service.ObjectDetection || ServerService == Service.RVC || ServerService == Service.UVR || ServerService == Service.SpeechToText)
            {
                // The service is a `file2any` service
                // Check if the file exists
                if (!File.Exists(Prompt))
                {
                    throw new FileNotFoundException();
                }

                try
                {
                    try
                    {
                        // Try to send the file/s to the server
                        // Check if the prompt is a file array, if not this will return an error
                        List<string> filests = JsonConvert.DeserializeObject<List<string>>(Prompt.TrimStart().TrimEnd());

                        // Reset prompt
                        Prompt = "";

                        // If it's a file array, send every file and get it's ID
                        foreach (string file in filests)
                        {
                            // Upload the file to the server and get the ID
                            int fID = SendFileToServer(file).Result;

                            // Set the file ID on the prompt
                            Prompt += fID.ToString() + " ";
                        }

                        // Trim the prompt
                        Prompt = Prompt.TrimStart().TrimEnd();
                    }
                    catch (JsonException)
                    {
                        // This means the prompt isn't a file array
                        // Upload the file to the server and get the ID
                        int fID = SendFileToServer(Prompt.TrimStart().TrimEnd()).Result;

                        // Set the prompt to the ID
                        Prompt = fID.ToString();
                    }
                    catch (Exception ex)
                    {
                        // This means another error occurred, return the error
                        throw ex;
                    }
                }
                catch (Exception ex)
                {
                    // An error occurs while sending the file/s
                    throw new Exception("Error sending file/s. Probably the server doesn't accept files?\nError details: " + ex.Message);
                }
            }

            // Set the files
            List<Dictionary<string, string>> files = new List<Dictionary<string, string>>();

            // Check for prompt templates
            switch (ServerService)
            {
                case Service.ImageGeneration:
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
                    break;
                case Service.ImageToImage:
                    // Set prompt to the Image2Image template
                    foreach (string file in Prompt.Split(' '))
                    {
                        files.Add(new Dictionary<string, string>()
                        {
                            {"type", "image"},
                            {"name", file}
                        });
                    }

                    Prompt = "";
                    break;
                case Service.ImageToText:
                    // Set prompt to the Image2Image template
                    foreach (string file in Prompt.Split(' '))
                    {
                        files.Add(new Dictionary<string, string>()
                        {
                            {"type", "image"},
                            {"name", file}
                        });
                    }

                    Prompt = "";
                    break;
                case Service.TTS:
                    // Set prompt to the TTS template
                    Prompt = JsonConvert.SerializeObject(new Dictionary<string, object>()
                    {
                        {"voice", Conf.TTS_Voice},
                        {"language", Conf.TTS_Language},
                        {"pitch", Conf.TTS_Pitch},
                        {"speed", Conf.TTS_Speed},
                        {"text", Prompt}
                    });
                    break;
                case Service.RVC:
                    // Set prompt to the RVC template
                    foreach (string file in Prompt.Split(' '))
                    {
                        files.Add(new Dictionary<string, string>()
                        {
                            {"type", "audio"},
                            {"name", file}
                        });
                    }

                    Prompt = JsonConvert.SerializeObject(new Dictionary<string, object>()
                    {
                        {"model", Conf.RVC_Model},
                        {"filter_radius", Conf.RVC_FilterRadius},
                        {"f0_up_key", Conf.RVC_F0},
                        {"protect", Conf.RVC_Protect}
                    });
                    break;
                case Service.UVR:
                    // Set prompt to the UVR template
                    foreach (string file in Prompt.Split(' '))
                    {
                        files.Add(new Dictionary<string, string>()
                        {
                            {"type", "audio"},
                            {"name", file}
                        });
                    }

                    Prompt = JsonConvert.SerializeObject(new Dictionary<string, object>()
                    {
                        {"agg", Conf.UVR_Agg}
                    });
                    break;
                case Service.DepthEstimation:
                    // Set prompt to the Depth Estimation template
                    foreach (string file in Prompt.Split(' '))
                    {
                        files.Add(new Dictionary<string, string>()
                        {
                            {"type", "image"},
                            {"name", file}
                        });
                    }

                    Prompt = "";
                    break;
                case Service.ObjectDetection:
                    // Set prompt to the Depth Estimation template
                    foreach (string file in Prompt.Split(' '))
                    {
                        files.Add(new Dictionary<string, string>()
                        {
                            {"type", "image"},
                            {"name", file}
                        });
                    }

                    Prompt = "";
                    break;
                case Service.NSFWFilterImage:
                    // Set prompt to the NSFW filter (images) template
                    foreach (string file in Prompt.Split(' '))
                    {
                        files.Add(new Dictionary<string, string>()
                        {
                            {"type", "image"},
                            {"name", file}
                        });
                    }

                    Prompt = "";
                    break;
                case Service.SpeechToText:
                    // Set prompt to the Speech Recognition template
                    foreach (string file in Prompt.Split(' '))
                    {
                        files.Add(new Dictionary<string, string>()
                        {
                            {"type", "audio"},
                            {"name", file}
                        });
                    }

                    Prompt = "";
                    break;
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
                    // Throw an error if it's not ended (expected only 1 response)
                    throw new Exception("Queue error: Invalid ended arg.");
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

            if (Conversation == null)
            {
                // Use the conversation set in the configuration
                Conversation = Conf.Chatbot_Conversation;
            }

            // Send request to the server and get the result
            IEnumerable<Dictionary<string, object>> res = ExecuteCommand("clear_conversation");

            foreach (Dictionary<string, object> response in res)
            {
                if (!(bool)response["ended"])
                {
                    // Throw an error if it's not ended (expected only 1 response)
                    throw new Exception("Delete conversation error: Invalid ended arg.");
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
            throw new Exception("Delete conversation error: Error getting queue.");
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
                    // The response didn't ended, return an error
                    throw new Exception("Error getting TOS: Invalid ended arg.");
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

        public static async Task<int> SendFileToServer(string FilePath)
        {
            /*
             * This will send files to the current connected server.           
            */

            // Check if the file exists
            if (!File.Exists(FilePath))
            {
                throw new Exception("File doesn't exists.");
            }

            // Check if the user is connected
            if (!IsConnected())
            {
                throw new Exception("Connect to a server first.");
            }

            // Create the client WebSocket and some other variables
            ClientWebSocket client = new ClientWebSocket();
            byte[] fileBytes = File.ReadAllBytes(FilePath);
            int chunkSize = 4096;
            int totalChunks = (int)Math.Ceiling((double)fileBytes.Length / chunkSize);
            int maxTime = 50;
            int time = 0;

            // Connect to I4.0's files server from the current connected server
            await client.ConnectAsync(new Uri("ws://" + Connected + ":8061"), CancellationToken.None);

            // Wait until connected
            while (client.State != WebSocketState.Open)
            {
                if (time > maxTime)
                {
                    // If the connecting time exceeds the max time, return an error
                    // This usually means that the server doesn't responds
                    throw new Exception("Could not connect to Rec Files server.");
                }

                time++;
                Thread.Sleep(100);
            }

            try
            {
                for (int i = 0; i < totalChunks; i++)
                {
                    // Calculate the current chunk to send
                    int offset = i * chunkSize;
                    int length = Math.Min(chunkSize, fileBytes.Length - offset);
                    byte[] chunk = new byte[length];

                    // Copy the chunk to an array
                    Array.Copy(fileBytes, offset, chunk, 0, length);

                    // Send the chunk to the server
                    await client.SendAsync(new ArraySegment<byte>(chunk), WebSocketMessageType.Binary, true, CancellationToken.None);

                    // Stop the loop if the current chunk is the total chunks to send - 1
                    // This means the file has been fully sent
                    if (i == totalChunks - 1)
                    {
                        break;
                    }
                }

                // Send an <end> meaning that the file is sent and telling the server to store it
                await client.SendAsync(new ArraySegment<byte>(Encoding.UTF8.GetBytes("<end>")), WebSocketMessageType.Binary, true, CancellationToken.None);
            }
            catch
            {
                // If there's any error, close the connection and return a error
                await client.CloseAsync(WebSocketCloseStatus.Empty, "", CancellationToken.None);
                throw new Exception("Bytes limit error.");
            }

            // Wait for the server's response with the stored file ID
            ArraySegment<byte> rbuffer = new ArraySegment<byte>(new byte[64]);
            await client.ReceiveAsync(rbuffer, CancellationToken.None);

            // Close the connection when done
            await client.CloseAsync(WebSocketCloseStatus.Empty, "", CancellationToken.None);

            // Return the received file ID as an integer
            return Convert.ToInt32(Encoding.UTF8.GetString(rbuffer.Array));
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