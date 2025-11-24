using System.Collections.Concurrent;
using System.Text;

namespace NanoGpt.Core.Data;

public sealed class CharacterVocabulary
{
    private readonly Dictionary<char, int> _charToIndex;
    private readonly char[] _indexToChar;

    public CharacterVocabulary(IEnumerable<char> characters)
    {
        var unique = characters.Distinct().OrderBy(c => c).ToArray();
        _charToIndex = unique.Select((c, idx) => (c, idx)).ToDictionary(tuple => tuple.c, tuple => tuple.idx);
        _indexToChar = unique;
    }

    public int Size => _indexToChar.Length;

    public int Encode(char value) => _charToIndex[value];

    public int[] Encode(string text)
    {
        var indices = new int[text.Length];
        for (var i = 0; i < text.Length; i++)
        {
            indices[i] = Encode(text[i]);
        }

        return indices;
    }

    public string Decode(IEnumerable<int> tokenIds)
    {
        var sb = new StringBuilder();
        foreach (var token in tokenIds)
        {
            sb.Append(_indexToChar[token]);
        }

        return sb.ToString();
    }
}
