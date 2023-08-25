using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using Newtonsoft.Json;

namespace TAO.I4.PythonManager
{
    public static class PythonDownloader
    {
        public static List<string> Servers = new List<string>()
        {
            "147.78.87.113", // TAO Official Server
            "127.0.0.1", // Localhost
        };
        public static int DefaultServer = 0;
        public static int MaxBufferLength = 2500000;
        private static Socket SC = null;
        public static Action<string> OnWarningAction = null;

        public static void Init()
        {
            if (!Directory.Exists("PythonCode/"))
            {
                Directory.CreateDirectory("PythonCode/");
            }
        }

        public static (string, int) ExecutePythonCode(string Name, string Args, string PythonCommand = "python")
        {
            Init();
            PythonCodeIsInstalled(Name, true);

            try
            {
                ProcessStartInfo psi = new ProcessStartInfo();

                psi.UseShellExecute = false;
                psi.RedirectStandardOutput = true;
                psi.FileName = "python";
                psi.Arguments = "PythonCode/" + Name + " " + Args;

                Process p = new Process
                {
                    StartInfo = psi
                };
                p.Start();
                p.WaitForExit();

                return (p.StandardOutput.ReadToEnd(), p.ExitCode);
            }
            catch (Exception ex)
            {
                if (OnWarningAction != null)
                {
                    OnWarningAction.Invoke("An error has occurred. (ERROR: " + ex.Message + ")");
                }

                return ("ERROR", -1);
            }
        }

        public static (string, int) GetServerData(string Data)
        {
            string ip = "";
            int port = -1;

            try
            {
                if (!ip.Contains(":"))
                {
                    throw new Exception();
                }

                port = Convert.ToInt32(Data.Substring(Data.IndexOf(":") + 1));
                ip = Data.Substring(0, Data.IndexOf(":"));
            }
            catch
            {
                port = 8073;
                ip = Data;
            }

            return (ip, port);
        }

        public static (string, int) GetServerData(int ServerID)
        {
            if (ServerID >= 0 && ServerID < Servers.Count)
            {
                return GetServerData(Servers[ServerID]);
            }

            return ("", -1);
        }

        private static void ConnectToServer((string, int) Server)
        {
            DisconnectFromServer();

            SC = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
            SC.Connect(new IPEndPoint(IPAddress.Parse(Server.Item1), Server.Item2));
        }

        private static void DisconnectFromServer()
        {
            if (SC != null)
            {
                SC.Close();
                SC = null;
            }
        }

        private static byte[] SendToServerAndWaitResponse(byte[] Data)
        {
            SC.Send(Data);

            byte[] buffer = new byte[MaxBufferLength];
            byte[] rbuffer = new byte[MaxBufferLength];
            int response = SC.Receive(buffer);

            Array.Copy(buffer, rbuffer, response);
            return rbuffer;
        }

        public static bool PythonCodeExists(string Name, int Server = -1)
        {
            if (Server <= 0 || Server >= Servers.Count)
            {
                Server = DefaultServer;
            }

            string r = "false";

            ConnectToServer(GetServerData(Server));
            r = Encoding.UTF8.GetString(SendToServerAndWaitResponse(Encoding.UTF8.GetBytes("pkg_exists " + Name)));
            DisconnectFromServer();

            r = r.Trim().ToLower();
            return bool.Parse(r);
        }

        public static bool PythonCodeIsInstalled(string Name, bool DownloadIfNot = false, int Server = -1)
        {
            if (!File.Exists("PythonCode/" + Name) && DownloadIfNot)
            {
                DownloadCode(Name, Server);
                return true;
            }

            return File.Exists("PythonCode/" + Name);
        }

        public static PyPkg DownloadCode(string Name, int Server = -1)
        {
            Init();

            if (Server <= 0 || Server >= Servers.Count)
            {
                Server = DefaultServer;
            }

            if (!PythonCodeExists(Name, Server))
            {
                if (OnWarningAction != null)
                {
                    OnWarningAction.Invoke("Package '" + Name + "' doesn't exists in this server.");
                }

                return new PyPkg();
            }

            ConnectToServer(GetServerData(Server));
            byte[] response = SendToServerAndWaitResponse(Encoding.UTF8.GetBytes("pkg_get " + Name));
            DisconnectFromServer();

            if (!File.Exists("PythonCode/" + Name))
            {
                File.Create("PythonCode/" + Name).Close();
            }
            else
            {
                if (OnWarningAction != null)
                {
                    OnWarningAction.Invoke("Package '" + Name + "' alredy exists, updating.");
                }
            }

            try
            {
                PyPkg pkg = JsonConvert.DeserializeObject<PyPkg>(Encoding.UTF8.GetString(response));
                File.WriteAllBytes("PythonCode/" + Name, pkg.Data);

                foreach (string dep in pkg.Dependencies)
                {
                    DownloadCode(dep, Server);
                }

                foreach (string dep in pkg.PipDependencies)
                {
                    Process p = Process.Start("pip", "install " + dep);
                    p.WaitForExit();

                    if (p.ExitCode != 0)
                    {
                        p = Process.Start("python", "-m pip install " + dep);
                        p.WaitForExit();
                    }
                }

                return pkg;
            }
            catch (Exception ex)
            {
                if (OnWarningAction != null)
                {
                    OnWarningAction.Invoke("An error has occurred! (ERROR: " + ex.Message + ")");
                }

                return new PyPkg();
            }
        }
    }
}