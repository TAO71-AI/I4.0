using System.Collections.Generic;

namespace TAO71.I4
{
    public static class Extra
    {
        public static string DictionaryToJson(Dictionary<object, object> Dictionary)
        {
            string jsonDict = "{";
            int i = 0;

            foreach (object key in Dictionary.Keys)
            {
                jsonDict += "\"" + key + "\": \"" + Dictionary[key] + "\"";

                if (i < Dictionary.Count - 1)
                {
                    jsonDict += ", ";
                }

                i++;
            }

            jsonDict += "}";
            return jsonDict;
        }

        public static string ArrayToJson(params object[] Array)
        {
            string jsonArray = "[";

            for (int i = 0; i < Array.Length; i++)
            {
                jsonArray += "\"" + Array[i].ToString().Replace("\"", "\'") + "\"";

                if (i < Array.Length - 1)
                {
                    jsonArray += ", ";
                }
            }

            jsonArray += "]";
            return jsonArray;
        }
    }
}