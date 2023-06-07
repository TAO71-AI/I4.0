using System;
using System.Collections.Generic;
using System.IO;

namespace TAO.NeuroN
{
    public static class AIFilter
    {
        private static List<string> Words = new List<string>();

        private static void Init()
        {
            if (!File.Exists("Filter.txt"))
            {
                File.Create("Filter.txt").Close();
            }

            string[] words = File.ReadAllLines("Filter.txt");

            foreach (string word in words)
            {
                AddWord(word);
            }
        }

        public static void AddWord(string Word)
        {
            if (!Words.Contains(Word.ToLower()))
            {
                Words.Add(Word.ToLower());
            }
        }

        public static void RemoveWord(string Word)
        {
            if (Words.Contains(Word.ToLower()))
            {
                Words.Remove(Word.ToLower());
            }
        }

        public static string FilterText(string Text)
        {
            Init();
            string text = Text;

            foreach (string word in Words)
            {
                if (text.ToLower().Contains(word.ToLower()))
                {
                    text = CustomReplace(text, word.ToLower(), "[FILTERED]");
                }
            }

            return text;
        }

        public static string FilterTextReplaceSomeChars(string Text)
        {
            string normal = FilterText(Text);
            string[] replacedChars = new string[]
            {
                FilterText(Text.Replace("1", "I")),
                FilterText(Text.Replace("3", "E")),
                FilterText(Text.Replace("4", "A")),
                FilterText(Text.Replace("0", "O"))
            };

            if (normal.Contains("[FILTERED]"))
            {
                return normal;
            }

            foreach (string rc in replacedChars)
            {
                if (rc.Contains("[FILTERED]"))
                {
                    return rc;
                }
            }

            return Text;
        }

        private static string CustomReplace(string Text, string A, string B)
        {
            string t = "";
            string tl = Text.ToLower();
            string al = A.ToLower();

            if (!tl.Contains(al))
            {
                return Text;
            }
            else if (tl == al)
            {
                return B;
            }

            while (tl.Contains(al))
            {
                t = Text.Substring(0, tl.IndexOf(al)) + B + Text.Substring(tl.IndexOf(al) + al.Length);
                tl = t.ToLower();
            }

            return t;
        }
    }
}