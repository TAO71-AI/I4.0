using System;
using System.IO;
using System.Reflection;
using System.Threading.Tasks;
using Discord;
using Discord.Commands;
using Discord.WebSocket;
using Microsoft.Extensions.DependencyInjection;

namespace TAO.I4.Plugins.DiscordBot
{
    public static class AI_Discord
    {
        private static DiscordSocketClient Client = new DiscordSocketClient(new DiscordSocketConfig()
        {
            GatewayIntents = GatewayIntents.MessageContent
        });
        private static CommandService Commands = new CommandService();
        private static IServiceProvider Services;
        private static string Token = "";
        public static string Prefix = "ai_response ";
        public static Action<SocketUserMessage> OnReceiveMessage = null;
        public static Action<LogMessage> OnLog = null;

        public static void Init()
        {
            if (!Directory.Exists("DiscordBot_Plugin/"))
            {
                Directory.CreateDirectory("DiscordBot_Plugin/");
            }

            if (!File.Exists("DiscordBot_Plugin/API_Key.txt"))
            {
                File.Create("DiscordBot_Plugin/API_Key.txt").Close();
            }

            Token = File.ReadAllText("DiscordBot_Plugin/API_Key.txt").Trim();
        }

        public static async Task RunBotAsync()
        {
            Init();

            Services = new ServiceCollection()
                .AddSingleton(Client)
                .AddSingleton(Commands)
                .BuildServiceProvider();

            Client.Log += OnLogFunc;
            Client.MessageReceived += OnReceiveMessageFunc;
            await Commands.AddModulesAsync(Assembly.GetEntryAssembly(), Services);
            
            await Client.LoginAsync(TokenType.Bot, Token);
            await Client.StartAsync();
            await Task.Delay(-1);
        }

        private static async Task OnLogFunc(LogMessage Arg)
        {
            if (OnLog != null)
            {
                OnLog.Invoke(Arg);
            }
        }

        private static async Task OnReceiveMessageFunc(SocketMessage Arg)
        {
            SocketUserMessage message = Arg as SocketUserMessage;
            SocketCommandContext context = new SocketCommandContext(Client, message);

            Console.WriteLine("DISCORD: '" + message.Content + "'.");

            if (message.Author.IsBot)
            {
                return;
            }

            int argPos = 0;

            if (message.HasStringPrefix(Prefix, ref argPos))
            {
                IResult result = await Commands.ExecuteAsync(context, argPos, Services);

                if (!result.IsSuccess)
                {
                    return;
                }

                if (OnReceiveMessage != null)
                {
                    OnReceiveMessage.Invoke(message);
                }
            }
        }

        /*public static async Task OnReceiveMessageFunc(SocketMessage Arg)
        {
            SocketUserMessage message = Arg as SocketUserMessage;
            int argPos = 0;

            if (!message.HasStringPrefix(Prefix, ref argPos) || message.Author.IsBot)
            {
                return;
            }

            SocketCommandContext context = new SocketCommandContext(Client, message);

            await Commands.ExecuteAsync(context: context, argPos: argPos, services: null);
        }*/

        public static async Task SendMessage(string Message, ulong? Channel)
        {
            if (!Channel.HasValue)
            {
                return;
            }

            SocketTextChannel channel = Client.GetChannel(Channel.Value) as SocketTextChannel;
            await channel.SendMessageAsync(Message);
        }
    }
}