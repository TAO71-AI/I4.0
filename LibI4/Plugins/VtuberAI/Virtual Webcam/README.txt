In order to create a virtual webcam without errors, you need to install the following dependencies:
From NuGet (C#):
    · OpenTK (or OpenTK.GLControl for Mono).
    · You may need to install System.Drawing.Common in some cases.
    
ONLY if you use Linux, you must install this dependencies (using your package manager):
    · v4l2loopback.
    
ONLY if you use Windows, you must install this dependencies (from NuGet):
    · DirectShow.NET.
    
WARNING: This has only been tested on Arch Linux, if you use Windows or other Linux distribution you may have some errors.