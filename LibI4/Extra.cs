using System;
using System.Collections.Generic;

namespace TAO.I4
{
    public static class Extra
    {
        public static string DictionaryToJson(Dictionary<object, object> Dictionary)
        {
            string jsonDict = "{";

            foreach (object key in Dictionary.Keys)
            {
                jsonDict += "\"" + key + "\": \"" + Dictionary[key] + "\"";
            }

            jsonDict += "}";
            return jsonDict;
        }

        public static string ArrayToJson(params object[] Array)
        {
            string jsonArray = "[";

            foreach (object obj in Array)
            {
                jsonArray += "\"" + obj.ToString().Replace("\"", "\'") + "\"";
            }

            jsonArray += "]";
            return jsonArray;
        }
    }
}