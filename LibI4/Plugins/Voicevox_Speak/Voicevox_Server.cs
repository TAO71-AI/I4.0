using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Sockets;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;

namespace TAO71.I4.Plugins.Voicevox
{
    public static class VoicevoxServer
    {
        private static Socket ServerSocket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
        private static byte[] ReceiveBuffer = new byte[2048];
        public static string VoicevoxUrl = "http://localhost:50021";

        public static void Init()
        {
            ServerSocket.Bind(new IPEndPoint(IPAddress.Any, 28171));
            ServerSocket.Listen(10000);

            try
            {
                ServerSocket.BeginAccept(OnConnect, null);
            }
            catch
            {

            }
        }

        public static void Close()
        {
            ServerSocket.Shutdown(SocketShutdown.Both);
            ServerSocket.Close();
            ServerSocket = null;
        }

        public static async Task<byte[]> AudioQuery(string Text, int Speaker = 1)
        {
            HttpClient client = new HttpClient();

            //Audio query
            HttpRequestMessage aq_requestMessage = new HttpRequestMessage(
                new HttpMethod("POST"),
                VoicevoxUrl + "/audio_query?text=" + Text + "&speaker=" + Speaker
            );
            aq_requestMessage.Headers.TryAddWithoutValidation("accept", "application/json");

            aq_requestMessage.Content = new StringContent("");
            aq_requestMessage.Content.Headers.ContentType = MediaTypeHeaderValue.Parse("application/x-www-form-urlencoded");

            var aq_response = await client.SendAsync(aq_requestMessage);
            string aq = await aq_response.Content.ReadAsStringAsync();

            //Synthesis
            HttpRequestMessage requestMessage = new HttpRequestMessage(
                new HttpMethod("POST"),
                VoicevoxUrl + "/synthesis?speaker=" + Speaker + "&enable_interrogative_upspeak=true"
            );
            requestMessage.Headers.TryAddWithoutValidation("accept", "audio/wav");

            requestMessage.Content = new StringContent(aq);
            requestMessage.Content.Headers.ContentType = MediaTypeHeaderValue.Parse("application/json");

            var response = await client.SendAsync(requestMessage);
            return await response.Content.ReadAsByteArrayAsync();
        }

        private static void OnConnect(IAsyncResult ar)
        {
            Socket socket = ServerSocket.EndAccept(ar);

            try
            {
                socket.BeginReceive(ReceiveBuffer, 0, ReceiveBuffer.Length, SocketFlags.None, OnReceive, socket);
            }
            catch
            {

            }

            try
            {
                ServerSocket.BeginAccept(OnConnect, null);
            }
            catch
            {

            }
        }

        private static void OnReceive(IAsyncResult ar)
        {
            Socket socket = (Socket)ar.AsyncState;
            int rec_bytes = socket.EndReceive(ar);
            byte[] rec_data = new byte[rec_bytes];

            Array.Copy(ReceiveBuffer, rec_data, rec_bytes);
            ReceiveBuffer = new byte[ReceiveBuffer.Length];

            string rec_str = Encoding.UTF8.GetString(rec_data);
            string text = JsonConvert.DeserializeObject<dynamic>(rec_str)["text"][0];
            int speaker = Convert.ToInt32(JsonConvert.DeserializeObject<dynamic>(rec_str)["speaker"][0]);
            byte[] data = AudioQuery(text, speaker).Result;

            socket.Send(data);
            socket.Close();
        }
    }
}