using System;
using System.Collections.Generic;
using System.IO;
using System.Diagnostics;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using Newtonsoft.Json;

namespace TAO.NeuroN.PythonManager
{
    public static class PyCodeManager
    {
        public static List<IPEndPoint> Socket_Servers = new List<IPEndPoint>();
        private static Socket ClientSocket = null;

        public static void DownloadFromServer_Sockets(IPEndPoint Server_EP, string Name, bool Upgrade = false)
        {
            //Disconnect (if connected)
            if (ClientSocket != null)
            {
                ClientSocket.Close();
                ClientSocket = null;
            }

            //Connect to the server
            ClientSocket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
            ClientSocket.Connect(Server_EP);

            //Send package name
            ClientSocket.Send(Encoding.ASCII.GetBytes("pp=" + Name.ToLower()));

            //Wait for response
            byte[] receiveBuffer = new byte[8192];
            PyPackage pkg = null;
            ClientSocket.Receive(receiveBuffer);

            //On receive
            pkg = JsonConvert.DeserializeObject<PyPackage>(Encoding.ASCII.GetString(receiveBuffer));

            if (pkg == null)
            {
                throw new Exception("An error has ocurred.");
            }

            //Check if package isn't installed
            if (!pkg.WorkingDir.EndsWith("/"))
            {
                pkg.WorkingDir += "/";
            }

            if (Directory.Exists("PythonCodes/" + pkg.WorkingDir) && !Upgrade)
            {
                throw new Exception("Python code alredy installed!");
            }
            else if (!Directory.Exists("PythonCodes/" + pkg.WorkingDir))
            {
                Directory.CreateDirectory("PythonCodes/" + pkg.WorkingDir);
            }

            if (Upgrade)
            {
                DirectoryInfo info = new DirectoryInfo("PythonCodes/" + Name.ToLower());

                foreach (FileInfo finfo in info.GetFiles())
                {
                    File.Delete(finfo.FullName);
                }
            }

            foreach (PyDenpendency dep in pkg.Dependencies)
            {
                if (dep.FromPip)
                {
                    Process p = Process.Start("python", "-m pip install " + dep.Name);
                    p.WaitForExit();

                    if (p.ExitCode != 0)
                    {
                        throw new Exception("An error has ocurred installing dependency '" + dep.Name + "' from pip.");
                    }
                }
                else
                {
                    DownloadFromServer_Sockets(Server_EP, dep.Name);
                }
            }

            ClientSocket.Close();
            ClientSocket = null;

            if (File.Exists("PythonCodes/" + pkg.WorkingDir + pkg.Name))
            {
                File.Delete("PythonCodes/" + pkg.WorkingDir + pkg.Name);
            }

            File.Create("PythonCodes/" + pkg.WorkingDir + pkg.Name).Close();
            File.WriteAllBytes("PythonCodes/" + pkg.WorkingDir + pkg.Name, pkg.Data);
        }

        public static void DownloadFromServer_Sockets(int Server, string Name, bool Upgrade = false)
        {
            DownloadFromServer_Sockets(Socket_Servers[Server], Name, Upgrade);
        }

        public static void ExecuteDownloaded(string WorkingDir, string Name, bool DownloadIfNot = true)
        {
            try
            {
                Process code = Process.Start("python", "PythonCodes/" + WorkingDir + Name + ".py");
                code.WaitForExit();
            }
            catch
            {
                if (DownloadIfNot)
                {
                    DownloadFromServer_Sockets(0, Name, false);
                }
            }
        }
    }
}