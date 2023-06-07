using System;
using System.Collections.Generic;

namespace TAO.NeuroN.PythonManager
{
    public class PyPackage
    {
        public string Name = "";
        public string WorkingDir = "";
        public List<PyDenpendency> Dependencies = new List<PyDenpendency>();
        public byte[] Data = new byte[0];
    }

    public class PyDenpendency
    {
        public string Name = "";
        public bool FromPip = false;
    }
}