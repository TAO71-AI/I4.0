-----
DOCUMENTATION VERSION: v6.0.0
-----

# Download C# compiler
> [!NOTE]
> If you're using Windows, .NET usually is installed with the OS.

First of all, you need to download .NET or Mono for C#.
**To download .NET**, please follow the instructions [here](https://dotnet.microsoft.com/en-us/download/dotnet/8.0).
**To download Mono**, please follow the instructions [here](https://www.mono-project.com/download/stable/).

You only need to install one of this compilers.
If you're using Windows or have a x86_64 GNU/Linux distribution, we recommend to download `.NET`, **else** we recommend to download `Mono`.

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

# Install NuGet dependencies
Once your C# project is created, you need to install the NuGet dependencies for C#.
The dependencies are:
```
Newtonsoft.Json
NAudio.Core
```

If you want to use any I4.0 C# plugin, you need to download it NuGet dependencies. The dependencies of the plugins should be mentioned in the `README.txt` or `README.md` file inside the plugin directory.
If there is no `README.txt` or `README.md` files or the dependencies are not mentioned, it means that the plugin doesn't need any extra dependencies.

# Programming the connection
## Automatically connect to an I4.0 server
If you want to connect automatically to an I4.0 server, you can use this code:
```cs
// Put this at the beginning of your code.
using TAO.I4;
using TAO.I4.PythonManager;

// Put this function inside your class.
public void AutoConnectFunction()
{
    PyAIResponse.DisconnectFromServer();        // Close any active connection.
    PyAIResponse.ClearServersTasks();           // Clear the tasks.

    int id = PyAIResponse.TryAllServer(true);   // Automatically connect to the first active server (from the servers list).

    if (id < 0)
    {
        throw new Exception("Error connecting to all servers.");
    }
    
    Console.WriteLine("Connected to the server " + id.ToString());

    PyAIResponse.DefaultServer = id;            // Set the active server as default.
    return id;                                  // Return the list ID of the connected server.
}
```

## Connect manually to an I4.0 server
If you want to connect manually to an I4.0 server, you can use this code:
```cs
// Put this at the beginning of your code.
using TAO.I4;
using TAO.I4.PythonManager;

// Put this function inside your class.
public void ConnectToTheServerFunction(string Server)
{
    PyAIResponse.DisconnectFromServer();        // Close any active connection.
    PyAIResponse.ClearServersTasks();           // Clear the tasks.
    PyAIResponse.ConnectToServer(Server);       // Connect to the server.
}
```

## Modify the servers list
To modify the servers list to add or remove servers, you can use the following code:
```cs
// Put this at the beginning of your code.
using TAO.I4;
using TAO.I4.PythonManager;

// Put this code inside your function
PyAIResponse.Servers.Add("SERVER IP");          // Adds a server.
PyAIResponse.Servers.Remove("SERVER IP");       // Removes a server.
```