using System;
using System.Collections.Generic;
using System.IO;
using TAO.NeuroN.ServerConnection;

namespace TAO.NeuroN
{
    public static class Responses
    {
        public static List<Response> ResponsesList = new List<Response>()
        {
            new Response("What is your name?", "My name is TAO NeuroN."),
            new Response("Who is your creator?", "My creators are Alcoft and Codearduinopython."),
            new Response("Who are your creators?", "My creators are Alcoft and Codearduinopython.")
        };

        private static string GetResponseData(string Title)
        {
            for (int i = 0; i < ResponsesList.Count; i++)
            {
                if (ResponsesList[i].Title.ToLower() == Title.ToLower())
                {
                    return ResponsesList[i].ResponseText;
                }
            }

            return "[NO RESPONSE]";
        }

        public static string GetResponse(string Title)
        {
            string gr = GetResponseData(Title);

            if (gr == "[NO RESPONSE]")
            {
                if (!Title.EndsWith("?") && !Title.EndsWith("."))
                {
                    string gr2 = GetResponseData(Title + "?");

                    if (gr2 == "[NO RESPONSE]")
                    {
                        return GetResponseData(Title + ".");
                    }

                    return gr2;
                }
                else if (Title.EndsWith("?"))
                {
                    string gr2 = GetResponseData(Title.Substring(0, Title.LastIndexOf("?")) + ".");

                    if (gr2 == "[NO RESPONSE]")
                    {
                        return GetResponseData(Title.Substring(0, Title.LastIndexOf("?")));
                    }

                    return gr2;
                }
                else if (Title.EndsWith("."))
                {
                    string gr2 = GetResponseData(Title.Substring(0, Title.LastIndexOf(".")) + "?");

                    if (gr2 == "[NO RESPONSE]")
                    {
                        return GetResponseData(Title.Substring(0, Title.LastIndexOf(".")));
                    }

                    return gr2;
                }
            }

            return gr;
        }

        public static Response[] AddFileAnswers(string FilePath)
        {
            if (!File.Exists(FilePath))
            {
                return new Response[0];
            }

            List<Response> responses = new List<Response>();
            string[] flines = File.ReadAllLines(FilePath);

            for (int i = 0; i < flines.Length; i++)
            {
                string line = flines[i];
                Response response = new Response();

                if (line.StartsWith("[") && line.Contains("]: "))
                {
                    response.Title = line.Substring(1, line.IndexOf("]: ") - 1);
                    response.ResponseText = line.Substring(line.IndexOf("]: ") + 3);

                    responses.Add(response);
                    ResponsesList.Add(response);
                }
            }

            return responses.ToArray();
        }
    }

    public class Response
    {
        public string Title = "";
        public string ResponseText = "";

        public Response()
        {

        }

        public Response(string Title, string ResponseText)
        {
            this.Title = Title;
            this.ResponseText = ResponseText;
        }

        public override string ToString()
        {
            return "(" + Title + ", " + ResponseText + ")";
        }
    }
}