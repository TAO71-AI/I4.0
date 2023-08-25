using System;

namespace TAO.I4.PythonManager
{
    public class PyPkg
    {
        public string Name = "";
        public string Version = "";
        public string Author = "";
        public string License = "";
        public string[] Dependencies = new string[0];
        public string[] PipDependencies = new string[0];
        public byte[] Data = new byte[0];

        public static PyPkg LoadFromJson(dynamic JsonData)
        {
            PyPkg pkg = new PyPkg();

            pkg.Name = JsonData["name"];
            pkg.Version = JsonData["version"];
            pkg.Author = JsonData["author"];
            pkg.License = JsonData["license"];
            pkg.Dependencies = JsonData["dependencies"];
            pkg.PipDependencies = JsonData["pip_dependencies"];
            pkg.Data = JsonData["data"];

            return pkg;
        }
    }
}