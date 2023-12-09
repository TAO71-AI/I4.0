using System;
using System.Collections.Generic;
using System.Text;

namespace TAO.I4.Plugins.Voicevox
{
    public static class KatakanaTranslator
    {
        public static char Separator = '-';
        public static char LongSeparator = '·';
        public static Dictionary<string, string> EsToJA_D = new Dictionary<string, string>()
            {
                //Vocals
                {"a", "ア"}, {"i", "イ"}, {"y", "イ"}, {"u", "ウ"}, {"e", "エ"}, {"o", "オ"},
                //k
                {"ka", "カ"}, {"ki", "キ"}, {"ky", "キ"}, {"ku", "ク"}, {"ke", "ケ"}, {"ko", "コ"},
                //c
                {"ca", "カ"}, {"ci", "シ"}, {"cy", "シ"}, {"cu", "ク"}, {"ce", "セ"}, {"co", "コ"},
                //sh
                {"sha", "シャ"}, {"shi", "シ"}, {"shy", "シ"}, {"shu", "シュ"}, {"she", "シェ"}, {"sho", "ショ"},
                //ch
                {"cha", "チャ"}, {"chi", "チ"}, {"chy", "チ"}, {"chu", "チュ"}, {"che", "チェ"}, {"cho", "チョ"},
                {"ch", "チ"},
                //s
                {"sa", "サ"}, {"si", "シ"}, {"sy", "シ"}, {"su", "ス"}, {"se", "セ"}, {"so", "ソ"},
                {"s", "ス"}, {"es", "エス"},
                //t
                {"ta", "タ"}, {"tu", "トゥー"}, {"te", "テ"}, {"to", "ト"}, {"tsu", "ツ"},
                //n
                {"na", "ナ"}, {"ni", "ニ"}, {"ny", "ニ"}, {"nu", "ヌ"}, {"ne", "ネ"}, {"no", "ノ"},
                {"nya", "ニャ"}, {"nyu", "ニュ"}, {"nyo", "ニョ"},
                //ñ
                {"ña", "ニャ"}, {"ñi", "ニイ"}, {"ñy", "ニイ"}, {"ñu", "ニュ"}, {"ñe", "ニエ"}, {"ño", "ニョ"},
                //h
                {"ha", "ハ"}, {"hi", "ヒ"}, {"hy", "ヒ"}, {"fu", "フ"}, {"he", "ヘ"}, {"ho", "ホ"},
                {"hya", "ヒャ"}, {"hyu", "ヒュ"}, {"hyo", "ヒョ"},
                //m
                {"ma", "マ"}, {"mi", "ミ"}, {"my", "ミ"}, {"mu", "ム"}, {"me", "メ"}, {"mo", "モ"},
                {"mya", "ミャ"}, {"myu", "ミュ"}, {"myo", "ミョ"},
                {"m", "ム"},
                //y
                {"ya", "ヤ"}, {"yi", "イィ"}, {"yy", "イィ"}, {"yu", "ユ"}, {"ye", "エ"}, {"yo", "ヨ"},
                //l
                {"la", "ラ"}, {"li", "リ"}, {"ly", "リ"}, {"lu", "ル"}, {"le", "レ"}, {"lo", "ロ"},
                //ll
                {"lla", "ヤ"}, {"lli", "イィ"}, {"lly", "イィ"}, {"llu", "ユ"}, {"lle", "エ"}, {"llo", "ヨ"},
                {"ll", "イ"},
                //r
                {"ra", "ラ"}, {"ri", "リ"}, {"ry", "リ"}, {"ru", "ル"}, {"re", "レ"}, {"ro", "ロ"},
                {"rya", "リャ"}, {"ryu", "リュ"}, {"ryo", "リョ"},
                //w
                {"wa", "ワ"}, {"wi", "ヰ"}, {"wy", "ヰ"}, {"wu", "ウゥ"}, {"we", "ヱ"}, {"wo", "ヲ"},
                //g
                {"ga", "ガ"}, {"gi", "ギ"}, {"gy", "ギ"}, {"gu", "グ"}, {"ge", "ゲ"}, {"go", "ゴ"},
                {"gya", "ギャ"}, {"gyu", "ギュ"}, {"gyo", "ギョ"},
                //z
                {"za", "ザ"}, {"zu", "ズ"}, {"ze", "ゼ"}, {"zo", "ゾ"},
                //d
                {"da", "ダ"}, {"di", "ヂ"}, {"du", "ヅ"}, {"de", "デ"}, {"do", "ド"},
                //b
                {"ba", "バ"}, {"bi", "ビ"}, {"by", "ビ"}, {"bu", "ブ"}, {"be", "ベ"}, {"bo", "ボ"},
                {"bya", "ビャ"}, {"byu", "ビュ"}, {"byo", "ビョ"},
                {"b", "ブ"},
                //p
                {"pa", "パ"}, {"pi", "ピ"}, {"py", "ピ"}, {"pu", "プ"}, {"pe", "ペ"}, {"po", "ポ"},
                {"pya", "ピャ"}, {"pyu", "ピュ"}, {"pyo", "ピョ"},
                //f
                {"fa", "ファ"}, {"fi", "フィ"}, {"fe", "フェ"}, {"fo", "フォ"},
                //j
                {"ja", "ジャ"}, {"ji", "ジ"}, {"jy", "ジ"}, {"ju", "ジュ"}, {"je", "ジェ"}, {"jo", "ジョ"},
                //n (final nasal)
                {"an", "アン"}, {"in", "イン"}, {"yn", "イン"}, {"un", "ウン"}, {"en", "エン"}, {"on", "オン"}, {"n", "ン"},
                //numbers
                {"0", "zero"}, {"1", "uno"}, {"2", "dos"}, {"3", "tres"}, {"4", "cuatro"}, {"5", "zinco"}, {"6", "seis"},
                {"7", "siete"}, {"8", "オチョ"}, {"9", "nueve"},
                //Special characters
                {"º", "オ"}, {"ª", "ア"},
                //Distance
                {"cm", "centímetros"}, {"mm", "milímetros"}, {"km", "kilómetros"},
                //Weight
                {"cg", "centígramos"}, {"mg", "milígramos"}, {"kg", "kilogramos"},
                //Extra
                {"nombre", "ノンブレ"},
                {"r", "ru"}, {"p", "pu"}, {"t", "tu"}, {"h", ""}, {"k", "ku"}, {"v", "bu"},
                {"z", "zu"}, {"d", "du"}, {"g", "gu"}, {"c", "cu"}, {"j", "ju"}, {"f", "fu"},
                {"x", "xu"}, {"w", "wu"}, {"xu", "chu"}, {"l", "lu"}, {"ñ", "ñu"},
            };

        private static bool IsVocal(char Character)
        {
            Character = Character.ToString().ToLower()[0];

            if (Character == 'a' || Character == 'i' || Character == 'u' || Character == 'e' || Character == 'o')
            {
                return true;
            }

            return false;
        }

        public static string RemoveAccentMarkEtc(string Text)
        {
            return Text.ToLower()
                //a
                .Replace('á', 'a')
                .Replace('à', 'a')
                .Replace('ä', 'a')
                .Replace('â', 'a')
                .Replace('ā', 'a')
                //e
                .Replace('é', 'e')
                .Replace('è', 'e')
                .Replace('ë', 'e')
                .Replace('ê', 'e')
                .Replace('ē', 'e')
                //i
                .Replace('í', 'i')
                .Replace('ì', 'i')
                .Replace('ï', 'i')
                .Replace('î', 'i')
                .Replace('ī', 'i')
                //o
                .Replace('ó', 'o')
                .Replace('ò', 'o')
                .Replace('ö', 'o')
                .Replace('ô', 'o')
                .Replace('ō', 'o')
                //u
                .Replace('ú', 'u')
                .Replace('ù', 'u')
                .Replace('ü', 'u')
                .Replace('û', 'u')
                .Replace('ū', 'u')
                //Other
                .Replace("¡", "")
                .Replace("¿", "");
        }

        public static string TranslateFromDictionary(string Text, Dictionary<string, string> Dict, int Filter = 2)
        {
            string ktkn = "";
            List<int> ignore = new List<int>();

            foreach (string word in Text.Split(Separator, LongSeparator, ' '))
            {
                if (Dict.ContainsKey(word.ToLower()))
                {
                    Text = Text.Replace(word, Dict[word.ToLower()]);
                    continue;
                }
            }

            Text = RemoveAccentMarkEtc(Text)
                .Replace("qu", "k")
                .Replace("q", "k");

            for (int i = 0; i < Text.Length; i++)
            {
                if (ignore.Contains(i))
                {
                    continue;
                }

                if (i + 3 < Text.Length &&
                    Dict.ContainsKey(Text[i].ToString() + Text[i + 1].ToString() + Text[i + 2].ToString() + Text[i + 3].ToString()))
                {
                    ktkn += Dict[Text[i].ToString() + Text[i + 1].ToString() + Text[i + 2].ToString() + Text[i + 3].ToString()];

                    ignore.Add(i + 1);
                    ignore.Add(i + 2);
                    ignore.Add(i + 3);

                    continue;
                }

                if (i + 2 < Text.Length &&
                    Dict.ContainsKey(Text[i].ToString() + Text[i + 1].ToString() + Text[i + 2].ToString()))
                {
                    ktkn += Dict[Text[i].ToString() + Text[i + 1].ToString() + Text[i + 2].ToString()];

                    ignore.Add(i + 1);
                    ignore.Add(i + 2);

                    continue;
                }

                if (i + 1 < Text.Length &&
                    Dict.ContainsKey(Text[i].ToString() + Text[i + 1].ToString()))
                {
                    ktkn += Dict[Text[i].ToString() + Text[i + 1].ToString()];
                    ignore.Add(i + 1);

                    continue;
                }

                if (Text[i] == '.' || Text[i] == ',' || Text[i] == ':' ||
                    Text[i] == ';' || Text[i] == '!' || Text[i] == '?')
                {
                    ktkn += Text[i].ToString() + LongSeparator;
                    continue;
                }

                if (Dict.ContainsKey(Text[i].ToString()))
                {
                    ktkn += Dict[Text[i].ToString()];
                    continue;
                }

                ktkn += Text[i];
            }

            Text = Text.Replace("l", "r");

            if (Filter > 0)
            {
                ktkn = TranslateFromDictionary(ktkn, Dict, Filter - 1);
            }

            ktkn = ktkn
                .Replace(' ', Separator);

            return ktkn;
        }

        public static string EStoJA(string Text)
        {
            return TranslateFromDictionary(Text, EsToJA_D, 2);
        }
    }
}