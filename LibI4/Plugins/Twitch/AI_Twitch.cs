using System;
using System.IO;
using TwitchLib;
using TwitchLib.Client;
using TwitchLib.Client.Events;
using TwitchLib.Client.Models;

namespace TAO.I4.Plugins.Twitch
{
    public static class AI_Twitch
    {
        private static string Username = "";
        private static string Password = "";
        private static string ChannelUsername = "";
        public static bool SaveMessages = true;
        public static readonly bool[] MessageData = new bool[]
        {
            //0 = Message, 1 = User, 2 = Time
            true, true, true
        };
        private static TwitchClient Client = new TwitchClient();
        public static Action<ChatMessage> OnReceiveMessageAction = null;

        public static void Init()
        {
            if (!Directory.Exists("TwitchPlugin/"))
            {
                Directory.CreateDirectory("TwitchPlugin/");
            }

            if (!File.Exists("TwitchPlugin/Credentials.txt"))
            {
                File.Create("TwitchPlugin/Credentials.txt").Close();
            }

            if (!File.Exists("TwitchPlugin/Messages.txt"))
            {
                File.Create("TwitchPlugin/Messages.txt").Close();
            }
        }

        public static void SetCredentials(string User, string Passwd, string ChannelName)
        {
            Username = User;
            Password = Passwd;
            ChannelUsername = ChannelName;
        }

        public static void SetCredentials()
        {
            Init();

            Username = "";
            Password = "";
            string[] fileLines = File.ReadAllLines("TwitchPlugin/Credentials.txt");

            if (fileLines.Length != 3)
            {
                return;
            }

            SetCredentials(fileLines[0], fileLines[1], fileLines[2]);
        }

        public static void LogIn()
        {
            Init();
            SetCredentials();

            Client.Initialize(new ConnectionCredentials(Username, Password), ChannelUsername);
            Client.OnMessageReceived += OnReceiveMessage;
            Client.Connect();
            Client.JoinChannel(ChannelUsername);
        }

        public static void SaveMessage(ChatMessage Message)
        {
            Init();
            string saveText = File.ReadAllText("TwitchPlugin/Messages.txt") + "\n";

            if (MessageData[2])
            {
                saveText += "[" + DateTime.Now.ToShortDateString() + " | " + DateTime.Now.ToLongTimeString() + "]: ";
            }

            if (MessageData[1])
            {
                saveText += "(" + Message.Username + "): ";
            }

            if (MessageData[0])
            {
                saveText += Message.Message;
            }
            else
            {
                saveText += "[PRIVATE]";
            }

            File.WriteAllText("TwitchPlugin/Messages.txt", saveText);
        }

        private static void OnReceiveMessage(object sender, OnMessageReceivedArgs e)
        {
            Init();

            if (SaveMessages)
            {
                SaveMessage(e.ChatMessage);
            }

            if (OnReceiveMessageAction != null)
            {
                OnReceiveMessageAction.Invoke(e.ChatMessage);
            }
        }
    }
}