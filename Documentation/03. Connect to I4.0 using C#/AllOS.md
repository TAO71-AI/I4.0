-----
DOCUMENTATION VERSION: v6.5.0
-----

# Download C# compiler
> [!NOTE]
> If you're using Windows, .NET usually is installed with the OS.

First of all, you need to download .NET or Mono for C#.
**To download .NET**, please follow the instructions [here](https://dotnet.microsoft.com/en-us/download/dotnet/8.0).
**To download Mono**, please follow the instructions [here](https://www.mono-project.com/download/stable/).

You only need to install one of this compilers.
If you're using Windows or have a x86_64 GNU/Linux distribution, we recommend to download `.NET`, **else** we recommend to download `Mono`.

> [!WARNING]
> For now I4.0 will still have compatibility with Mono and .NET, but in the future it will (probably) only be compatible with .NET.

# Download an IDE
Once you have downloaded a compiler, you should select an IDE to make some things easier for you.
There are many IDEs available for C#, but here we will only recommend 3 of them.

## Visual Studio
It's a very good IDE for C#, but only works on x86_64 Windows.
To download it, follow the instructions [here](https://visualstudio.microsoft.com/).

Requires to have .NET installed (it doesn't works with Mono).
License of the IDE: Private.

## Visual Studio Code
It's also a very good IDE, but it's not very good for programming with C# and only works with x86_64 Operating Systems.
To download it, follow the instructions [here](https://code.visualstudio.com/).

When you have installed Visual Studio Code, download the C# extension and it should work fine.
It also requires to have .NET installed and it doesn't works with Mono (usually).

License of the IDE: MIT (but the binaries are private).

## MonoDevelop
If you don't have an x86_64 Operation System, or you want to use Mono instead of .NET, this IDE will probably be the best for you.
To download it, follow the instructions [here](https://www.monodevelop.com/download/).

This IDE requires to have Mono installed and it doesn't works with .NET (usually).
License of the IDE: Unknown (but Open-Source).

# Create project
Now that you have an IDE, you need to create a project (of your choice, GUI, Console App, etc.) and add the I4.0/LibI4/ directory to it.

# Install dependencies
You can find all the dependencies you need to install in the file `CS_DEPENDENCIES.md`

If you want to use any I4.0 C# plugin, you need to download it NuGet dependencies. The dependencies of the plugins should be mentioned in the `README.txt` or `README.md` file inside the plugin directory.
If there is no `README.txt` or `README.md` files or the dependencies are not mentioned, it means that the plugin doesn't need any extra dependencies.

# Programming the connection
## Connect to an I4.0 server
If you want to connect to an I4.0 server, you can use this code:
```cs
// NOTE: In some cases, you don't need to connect to a server, some functions do it automatically if you allow it.
// Put this at the beginning of your code.
using TAO71.I4;
using TAO71.I4.PythonManager;

// Connect to the first server that have enabled the service you want to use.
public async void ConnectToTheServer()
{
    // WARNING: If the function can't find any server with the service you're asking for on the Servers list, it will return an error.

    int server = await PyAIResponse.FindFirstServer(SERVICE, true);     // Find the first available server for a service. Remember to replace SERVICE with the service you want.
    await PyAIResponse.Connect(server);                                 // Connect to the server.
}

// You can also connect using directly the IP of the server.
public async void ConnectToTheServerWithIP(string IP)
{
    await Connect(IP);
}
```

## Check if you're connected
To check if you're connected to any server, you can use the following code:
```cs
// Put this at the beginning of your code.
using TAO71.I4;
using TAO71.I4.PythonManager;

// Put this code inside your function
bool connected = PyAIResponse.IsConnected();
```

## Modify the servers list
To modify the servers list to add or remove servers, you can use the following code:
```cs
// Put this at the beginning of your code.
using TAO71.I4;
using TAO71.I4.PythonManager;

// Put this code inside your function
PyAIResponse.Conf.Servers.Add("SERVER IP");          // Adds a server.
PyAIResponse.Conf.Servers.Remove("SERVER IP");       // Removes a server.
```