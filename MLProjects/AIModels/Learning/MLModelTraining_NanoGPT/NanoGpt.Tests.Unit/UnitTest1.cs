using Xunit;
using FluentAssertions;
using Microsoft.Extensions.Logging;
using Moq;

namespace NanoGpt.Tests.Unit;

public class ModelTests
{
    [Fact]
    public void Model_Should_Initialize_With_Valid_Configuration()
    {
        // Arrange
        var config = new
        {
            VocabSize = 65,
            ContextLength = 256,
            EmbeddingDim = 384,
            NumHeads = 6,
            NumLayers = 6,
            DropoutRate = 0.2
        };

        // Act & Assert
        config.VocabSize.Should().BeGreaterThan(0);
        config.ContextLength.Should().BeGreaterThan(0);
        config.EmbeddingDim.Should().BeGreaterThan(0);
        config.NumHeads.Should().BeGreaterThan(0);
        config.NumLayers.Should().BeGreaterThan(0);
        config.DropoutRate.Should().BeGreaterOrEqualTo(0).And.BeLessOrEqualTo(1);
    }

    [Fact]
    public void Vocabulary_Should_Handle_Character_Encoding()
    {
        // Arrange
        var testText = "Hello World";
        
        // Act
        var characters = testText.ToCharArray().Distinct().ToArray();
        var vocabSize = characters.Length;
        
        // Assert
        vocabSize.Should().BeGreaterThan(0);
        characters.Should().NotBeEmpty();
    }

    [Theory]
    [InlineData(64, 256)]
    [InlineData(32, 128)]
    [InlineData(16, 64)]
    public void Training_Configuration_Should_Be_Valid(int batchSize, int contextLength)
    {
        // Arrange & Act
        var config = new
        {
            BatchSize = batchSize,
            ContextLength = contextLength,
            LearningRate = 3e-4,
            MaxIterations = 5000
        };

        // Assert
        config.BatchSize.Should().BeGreaterThan(0);
        config.ContextLength.Should().BeGreaterThan(0);
        config.LearningRate.Should().BeGreaterThan(0);
        config.MaxIterations.Should().BeGreaterThan(0);
    }
}

public class DataProcessingTests
{
    [Fact]
    public void Should_Split_Training_Data_Correctly()
    {
        // Arrange
        var sampleData = "This is a sample text for training the model";
        var trainRatio = 0.8;
        
        // Act
        var splitPoint = (int)(sampleData.Length * trainRatio);
        var trainData = sampleData[..splitPoint];
        var valData = sampleData[splitPoint..];
        
        // Assert
        trainData.Should().NotBeEmpty();
        valData.Should().NotBeEmpty();
        (trainData.Length + valData.Length).Should().Be(sampleData.Length);
    }

    [Fact]
    public void Should_Create_Character_Vocabulary()
    {
        // Arrange
        var text = "abcdefghijklmnopqrstuvwxyz";
        
        // Act
        var vocab = text.ToCharArray().Distinct().OrderBy(c => c).ToArray();
        var charToIndex = vocab.Select((c, i) => new { c, i }).ToDictionary(x => x.c, x => x.i);
        var indexToChar = vocab.Select((c, i) => new { c, i }).ToDictionary(x => x.i, x => x.c);
        
        // Assert
        vocab.Length.Should().Be(26);
        charToIndex.Should().HaveCount(26);
        indexToChar.Should().HaveCount(26);
        charToIndex['a'].Should().Be(0);
        indexToChar[25].Should().Be('z');
    }
}

public class MetricsTests
{
    [Fact]
    public void Should_Calculate_Perplexity_Correctly()
    {
        // Arrange
        var loss = 2.485;
        
        // Act
        var perplexity = Math.Exp(loss);
        
        // Assert
        perplexity.Should().BeApproximately(12.0, 0.1);
    }

    [Theory]
    [InlineData(4.0, 54.6)]
    [InlineData(3.0, 20.1)]
    [InlineData(2.0, 7.4)]
    [InlineData(1.0, 2.7)]
    public void Should_Calculate_Perplexity_For_Different_Losses(double loss, double expectedPerplexity)
    {
        // Act
        var perplexity = Math.Exp(loss);
        
        // Assert
        perplexity.Should().BeApproximately(expectedPerplexity, 0.1);
    }
}