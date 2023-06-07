using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Threading.Tasks;
using Discord;
using Discord.Commands;
using Discord.WebSocket;
using Microsoft.Extensions.DependencyInjection;

namespace TAO.NeuroN.Plugins.DiscordBot
{
    public static class AI_Discord
    {
        private static DiscordSocketClient Client = new DiscordSocketClient();
        private static CommandService Commands = new CommandService();
        private static IServiceProvider Services;
        private static string Token = "";
        public static Action<SocketUserMessage> OnReceiveMessage = null;

        public static async Task RunBotAsync()
        {
            if (!Directory.Exists("DiscordBot_Plugin/"))
            {
                Directory.CreateDirectory("DiscordBot_Plugin/");
            }

            if (!File.Exists("DiscordBot_Plugin/API_Key.txt"))
            {
                File.Create("DiscordBot_Plugin/API_Key.txt").Close();
            }

            Token = File.ReadAllText("DiscordBot_Plugin/API_Key.txt");
            Client.MessageReceived += HandleCommandAsync;

            await Client.LoginAsync(TokenType.Bot, Token);
            await Client.StartAsync();
        }

        private static async Task HandleCommandAsync(SocketMessage arg)
        {
            SocketUserMessage message = arg as SocketUserMessage;
            SocketCommandContext context = new SocketCommandContext(Client, message);

            if (message.Author.IsBot)
            {
                return;
            }

            if (OnReceiveMessage != null)
            {
                OnReceiveMessage.Invoke(message);
            }
        }

        public static async Task WriteMessage(string Message, IMessageChannel Channel, string[] Files)
        {
            if (Message.Length > 0)
            {
                await Channel.SendMessageAsync(Message);
            }

            if (Files.Length > 0)
            {
                List<FileAttachment> files = new List<FileAttachment>();

                foreach (string file in Files)
                {
                    files.Add(new FileAttachment(file));
                }

                await Channel.SendFilesAsync(files.ToArray());
            }
        }
    }
}