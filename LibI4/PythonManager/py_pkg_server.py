import socket
import sys
import os
import json
import threading
import base64

max_users = 10000

class PyPkg:
    name: str = ""
    version: str = ""
    author: str = ""
    license: str = ""
    dependencies: list[str] = []
    pip_dependencies: list[str] = []
    data: str = ""
    
    def __init__(self) -> None:
        self.name = ""
        self.version = ""
        self.author = ""
        self.license = ""
        self.dependencies = []
        self.pip_dependencies = []
        self.data = ""
    
    def tojson(self) -> str:
        self.data = base64.b64encode(self.data.encode("utf-8")).decode("utf-8")
        d = self.__dict__
        
        d["dependencies"] = self.dependencies
        d["pip_dependencies"] = self.pip_dependencies
        
        return json.dumps(d, ensure_ascii = False, skipkeys = False, indent = 4)

def init() -> None:
    if (not os.path.exists("pkgs/")):
        os.mkdir("pkgs/")

def pkg_from_json(data: str) -> PyPkg:
    d = json.loads(data)
    pkg = PyPkg()
        
    pkg.name = d["name"]
    pkg.version = d["version"]
    pkg.author = d["author"]
    pkg.license = d["license"]
    pkg.dependencies = list(d["dependencies"])
    pkg.pip_dependencies = list(d["pip_dependencies"])
    pkg.data = base64.b64decode(d["data"]).decode("utf-8")
    
    return pkg

def get_all_pkgs() -> list[PyPkg]:
    init()
    pkgs: list[PyPkg] = []
    
    for i in os.listdir("pkgs/"):
        print(i)
        
        with open("pkgs/" + i, "r") as f:
            pkg_data = pkg_from_json(f.read())
            f.close()
        
        pkgs.append(pkg_data)
    
    return pkgs

def get_all_pkgs_fast() -> list[str]:
    init()
    pkgs: list[str] = []
    
    for i in os.listdir("pkgs/"):
        pkgs.append(i)
    
    return pkgs

def get_pkg(name: str) -> PyPkg:
    pkgs = get_all_pkgs()
    
    for pkg in pkgs:
        if (pkg.name == name):
            return pkg
    
    return PyPkg()

def pkg_exists(name: str) -> bool:
    pkgs = get_all_pkgs_fast()
    
    for pkg in pkgs:
        if (pkg == name):
            return True
    
    return False

def create_pkg(data: PyPkg):
    init()
    pkg_name = data.name
    
    if (pkg_name.__contains__("/") or pkg_name.__contains__("\\")):
        try:
            pkg_name = pkg_name.split("/")[len(pkg_name.split("/")) - 1]
        except:
            pkg_name = pkg_name.split("\\")[len(pkg_name.split("\\")) - 1]
    
    data.name = pkg_name
    
    with open("pkgs/" + pkg_name, "w+") as f:
        f.write(str(data.tojson()))
        f.close()

def handle_client(client_socket: socket.socket, client_address) -> None:
    try:
        while True:
            data = client_socket.recv(4096)
            data = data.decode()
            rd = ""
            
            if (len(data.strip()) == 0):
                break
            
            print("Received from " + str(client_address) + ": '" + str(data) + "'.")
            
            if (data.lower().startswith("pkg_exists ")):
                rd = "true" if (pkg_exists(data[11:len(data)])) else "false"
            elif (data.lower().startswith("pkg_get ")):
                pkg = get_pkg(data[8:len(data)])
                rd = str(pkg.tojson())
            
            print("Sending to " + str(client_address) + ": '" + str(rd) + "'.")
            client_socket.send(rd.encode("utf-8"))
    except Exception as ex:
        print("Error on client: " + str(ex))
    
    client_socket.close()

def handle_clients() -> None:
    global server_socket
    
    while True:
        try:
            client_socket, client_address = server_socket.accept()
            print("Client connected from " + str(client_address))
            
            client_thread = threading.Thread(target = handle_client, args = (client_socket, client_address))
            client_thread.start()
        except Exception as ex:
            print("Error on server: " + str(ex))

init()

ip = "0.0.0.0"

if (len(sys.argv) > 1 and (sys.argv[1].lower() == "-localhost" or sys.argv[1].lower() == "-l")):
    ip = "127.0.0.1"

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("0.0.0.0", 8073))
server_socket.listen(max_users)

clients_thread = threading.Thread(target = handle_clients)
clients_thread.start()

while True:
    cmd = input(">$ ")
    
    if (cmd.lower().startswith("pkg_exists ")):
        print("true " if pkg_exists(cmd[11:len(cmd)]) else "false")
    elif (cmd.lower() == "exit" or cmd.lower() == "quit" or cmd.lower() == "stop"):
        print("Closing server...")
        os._exit(0)
    elif (cmd.lower().startswith("get_pkg ")):
        print(json.dumps(get_pkg(cmd[8:len(cmd)])))
    elif (cmd.lower() == "create_pkg"):
        data = PyPkg()
        data_name = input("Package file: ")
        
        data.name = data_name
        data.version = input("Version: ")
        data.author = input("Author: ")
        data.license = input("License: ")
        
        print("Package dependencies (no pip) (leave blank when done): ")
        
        while True:
            dep = input("dep: ")
            
            if (len(dep.split()) == 0):
                break
            
            if (not pkg_exists(dep)):
                print("Package " + dep + " does not exist in this server. Add anyway? [y/N] ")
                
                if (input().lower() != "y"):
                    continue
                
            data.dependencies.append(dep)
        
        print("Package pip dependencies (leave blank when done): ")
        
        while True:
            dep = input("pip_dep: ")
            
            if (len(dep.split()) == 0):
                break
                
            data.pip_dependencies.append(dep)
        
        with open(data_name, "r") as f:
            data.data = f.read()
            f.close()
        
        create_pkg(data)
        data = PyPkg()
    elif (len(cmd.split()) == 0):
        pass
    else:
        try:
            print(str(os.system(cmd)))
        except Exception as ex:
            print("Error on command: '" + str(ex) + "'.")