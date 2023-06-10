using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using Newtonsoft.Json;

namespace TAO.NeuroN.PythonManager
{
    public static class PyServer
    {
        private static Socket ServerSocket = null;
        private static byte[] ServerBuffer = new byte[128];
        public static Action<string> OnErrorAction = null;
        public static Action<EndPoint> OnConnectAction = null;
        public static Action<byte[]> OnReceiveAction = null;

        public static void Init()
        {
            if (!Directory.Exists("Server_PythonPackages/"))
            {
                Directory.CreateDirectory("Server_PythonPackages/");
            }
        }

        public static void Start(int Port = 71711, int MaxConnections = 1000)
        {
            Init();
            Stop();

            ServerSocket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
            ServerSocket.Bind(new IPEndPoint(IPAddress.Any, Port));
            ServerSocket.Listen(MaxConnections);

            try
            {
                ServerSocket.BeginAccept(OnConnect, null);
            }
            catch (Exception ex)
            {
                if (OnErrorAction != null)
                {
                    OnErrorAction.Invoke(ex.Message);
                }
            }
        }

        public static void Stop()
        {
            if (ServerSocket != null)
            {
                ServerSocket.Close();
                ServerSocket = null;
            }
        }

        public static void SendData(byte[] Data, EndPoint To)
        {
            try
            {
                ServerSocket.SendTo(Data, To);
            }
            catch (Exception ex)
            {
                if (OnErrorAction != null)
                {
                    OnErrorAction.Invoke(ex.Message);
                }
            }
        }

        public static PyPackage[] GetPackages(string Name)
        {
            Init();
            DirectoryInfo info = new DirectoryInfo("Server_PythonPackages/");
            List<PyPackage> packages = new List<PyPackage>();

            foreach (DirectoryInfo dinfo in info.GetDirectories())
            {
                if (dinfo.Name.ToLower() == Name.ToLower())
                {
                    foreach (FileInfo finfo in dinfo.GetFiles())
                    {
                        packages.Add(JsonConvert.DeserializeObject<PyPackage>(File.ReadAllText(finfo.FullName)));
                    }

                    break;
                }

                bool p = false;

                foreach (FileInfo finfo in dinfo.GetFiles())
                {
                    if (finfo.Name.ToLower() == Name.ToLower() || p)
                    {
                        p = true;
                        packages.Add(JsonConvert.DeserializeObject<PyPackage>(File.ReadAllText(finfo.FullName)));
                    }
                }

                if (p)
                {
                    break;
                }
            }

            return packages.ToArray();
        }

        /*public static void CreatePackage(PyPackage Package, bool Upgrade = false)
        {
            if ((GetPackages(Package.WorkingDir).Length > 0 || GetPackages(Package.Name).Length > 0) && !Upgrade)
            {
                throw new Exception("Package alredy exists! Use upgrade to fix this.");
            }

            if (Directory.Exists("Server_PythonPackages/" + Package.WorkingDir))
            {
                Directory.Delete("Server_PythonPackages/" + Package.WorkingDir);
            }


        }*/

        private static void OnConnect(IAsyncResult ar)
        {
            try
            {
                Socket clientSocket = ServerSocket.EndAccept(ar);

                if (OnConnectAction != null)
                {
                    OnConnectAction.Invoke(clientSocket.RemoteEndPoint);
                }

                clientSocket.BeginReceive(ServerBuffer, 0, ServerBuffer.Length, SocketFlags.None, OnReceive, clientSocket);
                ServerSocket.BeginAccept(OnConnect, null);
            }
            catch (Exception ex)
            {
                if (OnErrorAction != null)
                {
                    OnErrorAction.Invoke(ex.Message);
                }
            }
        }

        private static void OnReceive(IAsyncResult ar)
        {
            try
            {
                Socket clientSocket = (Socket)ar.AsyncState;
                byte[] tmpData = new byte[ServerBuffer.Length];
                int receivedData = clientSocket.EndReceive(ar);

                Array.Copy(ServerBuffer, tmpData, receivedData);
                ServerBuffer = new byte[ServerBuffer.Length];

                if (OnReceiveAction != null)
                {
                    OnReceiveAction.Invoke(tmpData);
                }

                string msg = Encoding.ASCII.GetString(tmpData);

                if (msg.ToLower().StartsWith("pp="))
                {
                    string pkgName = msg.Substring(3);


                }
            }
            catch (Exception ex)
            {
                if (OnErrorAction != null)
                {
                    OnErrorAction.Invoke(ex.Message);
                }
            }
        }
    }
}