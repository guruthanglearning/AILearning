using Microsoft.Extensions.Logging;
using TorchSharp;

namespace NanoGpt.Core.Data;

public sealed class TextDataSource
{
    private readonly ILogger<TextDataSource> _logger;
    private readonly CharacterVocabulary _vocabulary;
    private readonly int[] _encodedText;
    private readonly int _blockSize;

    public TextDataSource(string textFilePath, int blockSize, ILogger<TextDataSource> logger)
    {
        if (!File.Exists(textFilePath))
        {
            throw new FileNotFoundException("Training data file not found", textFilePath);
        }

        _logger = logger;
        var text = File.ReadAllText(textFilePath);
        _vocabulary = new CharacterVocabulary(text);
        _encodedText = _vocabulary.Encode(text);
        _blockSize = blockSize;

        _logger.LogInformation("Loaded corpus '{File}' with {TokenCount} tokens and vocabulary size {VocabSize}",
            textFilePath, _encodedText.Length, _vocabulary.Size);
    }

    public TextDataSource(string textFilePath, int blockSize, ILogger<TextDataSource> logger, CharacterVocabulary vocabulary)
    {
        if (!File.Exists(textFilePath))
        {
            throw new FileNotFoundException("Training data file not found", textFilePath);
        }

        _logger = logger;
        _vocabulary = vocabulary;
        var text = File.ReadAllText(textFilePath);
        _encodedText = _vocabulary.Encode(text);
        _blockSize = blockSize;

        _logger.LogInformation("Loaded corpus '{File}' with {TokenCount} tokens using unified vocabulary size {VocabSize}",
            textFilePath, _encodedText.Length, _vocabulary.Size);
    }

    public CharacterVocabulary Vocabulary => _vocabulary;

    public (torch.Tensor, torch.Tensor) GetBatch(int batchSize)
    {
        var maxIndex = _encodedText.Length - _blockSize - 1;
        if (maxIndex <= 0)
        {
            throw new InvalidOperationException("Corpus is smaller than block size; provide more text.");
        }

        var inputs = torch.zeros(new long[] { batchSize, _blockSize }, dtype: torch.int64);
        var targets = torch.zeros(new long[] { batchSize, _blockSize }, dtype: torch.int64);
        var random = Random.Shared;

        for (var i = 0; i < batchSize; i++)
        {
            var start = random.Next(0, maxIndex);
            var inputSlice = _encodedText.AsSpan(start, _blockSize);
            var targetSlice = _encodedText.AsSpan(start + 1, _blockSize);

            for (var j = 0; j < _blockSize; j++)
            {
                inputs[i, j] = inputSlice[j];
                targets[i, j] = targetSlice[j];
            }
        }

        return (inputs, targets);
    }
}
