using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Http;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace TAO.NeuroN.Plugins.Voicevox
{
    public static class Voicevox_ServerConnection
    {
        public static List<(TConnectionType, string)> WebServers = new List<(TConnectionType, string)>()
        {
            (TConnectionType.Http, "post:https://deprecatedapis.tts.quest/v2/voicevox/audio/"), // Third-party server
            (TConnectionType.Http, "post:https://api.su-shiki.com/v2/voicevox/audio/"), // Third-party server 2
            (TConnectionType.Socket, "147.78.87.113:28171"), // TAO Server
        };
        public static int DefaultServer = 0;
        public static Action OnConnectAction = null;
        public static Action OnGetResponseAction = null;

        public static async Task<byte[]> SendToServer(TParameter[] Parameters, int Server = -1)
        {
            if (Server < 0)
            {
                if (DefaultServer < 0 || DefaultServer >= WebServers.Count)
                {
                    throw new Exception("Server or default server must not be less than 0 or greather than the server list.");
                }

                Server = DefaultServer;
            }
            else if (Server < 0 || Server >= WebServers.Count)
            {
                throw new Exception("Server or default server must not be less than 0 or greather than the server list.");
            }

            Parameters = Voicevox_SpeakManager.FilterParameters(Parameters);

            if (OnConnectAction != null)
            {
                OnConnectAction.Invoke();
            }

            if (WebServers[Server].Item1 == TConnectionType.Http)
            {
                HttpClient http_client = new HttpClient();
                HttpResponseMessage response = null;

                try
                {
                    if (WebServers[Server].Item2.ToLower().StartsWith("get:"))
                    {
                        string paramsData = "?";
                        string url = WebServers[Server].Item2.Substring(4).TrimStart().TrimEnd();

                        for (int i = 0; i < Parameters.Length; i++)
                        {
                            if (i > 0)
                            {
                                paramsData += "&";
                            }

                            paramsData += Parameters[i].Name + "=" + Parameters[i].Value;
                        }

                        if (Parameters.Length <= 0)
                        {
                            paramsData = "";
                        }

                        response = await http_client.GetAsync(url + paramsData);
                        Console.WriteLine(url + paramsData);
                    }
                    else if (WebServers[Server].Item2.ToLower().StartsWith("post:"))
                    {
                        Dictionary<string, string> paramsData = new Dictionary<string, string>();
                        string getParamsData = "?";
                        string url = WebServers[Server].Item2.Substring(5).TrimStart().TrimEnd();

                        foreach (TParameter p in Parameters)
                        {
                            if (p.Type == TParamType.GET)
                            {
                                getParamsData += p.Name + "=" + p.Value + "&";
                            }
                            else
                            {
                                paramsData.Add(p.Name, p.Value);
                            }
                        }

                        getParamsData = getParamsData.Substring(0, getParamsData.Length - 1);
                        response = await http_client.PostAsync(url + getParamsData, new FormUrlEncodedContent(paramsData));
                    }
                }
                catch
                {

                }

                if (OnGetResponseAction != null)
                {
                    OnGetResponseAction.Invoke();
                }

                if (response == null || !response.IsSuccessStatusCode)
                {
                    return new byte[0];
                }

                return await response.Content.ReadAsByteArrayAsync();
            }

            string data = "{";
            Socket clientSocket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
            IPEndPoint ep = new IPEndPoint(
                IPAddress.Parse(WebServers[Server].Item2.Substring(0, WebServers[Server].Item2.IndexOf(":"))),
                Convert.ToInt32(WebServers[Server].Item2.Substring(WebServers[Server].Item2.IndexOf(":") + 1))
            );

            foreach (TParameter param in Parameters)
            {
                data += '"' + param.Name + '"' + ":[" + '"' + param.Value + '"' + "],";
            }

            data = data.Substring(0, data.LastIndexOf(","));
            data += "}";

            clientSocket.Connect(ep);
            clientSocket.Send(Encoding.UTF8.GetBytes(data));

            byte[] response_s = new byte[999999999];
            int rec_bytes = clientSocket.Receive(response_s);
            byte[] received_data = new byte[rec_bytes];

            Array.Copy(response_s, received_data, rec_bytes);

            clientSocket.Disconnect(false);
            clientSocket.Close();

            return response_s;
        }

        public static async Task<byte[]> SendToFirstWorkingServer(TParameter[] Parameters)
        {
            for (int i = 0; i < WebServers.Count; i++)
            {
                byte[] data = await SendToServer(Parameters, i);

                if (data.Length > 0)
                {
                    return data;
                }
            }

            return new byte[0];
        }
    }

    public class TParameter
    {
        public string Name;
        public string Value;
        public TParamType Type;

        public TParameter(string Name = "", string Value = "", TParamType Type = TParamType.Both)
        {
            this.Name = Name;
            this.Value = Value;
            this.Type = Type;
        }

        public override string ToString()
        {
            return "Name: " + Name + "; Value: " + Value + "; Type: " + Type;
        }
    }

    public enum TConnectionType
    {
        Http,
        Socket
    }

    public enum TParamType
    {
        GET,
        POST,
        Both
    }
}