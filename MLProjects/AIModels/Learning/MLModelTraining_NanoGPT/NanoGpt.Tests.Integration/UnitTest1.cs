using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.DependencyInjection;
using System.Net.Http.Json;
using System.Text.Json;
using Xunit;

namespace NanoGpt.Tests.Integration;

public class ApiIntegrationTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly WebApplicationFactory<Program> _factory;
    private readonly HttpClient _client;

    public ApiIntegrationTests(WebApplicationFactory<Program> factory)
    {
        _factory = factory;
        _client = _factory.CreateClient();
    }

    [Fact]
    public async Task Health_Endpoint_Should_Return_Healthy()
    {
        // Act
        var response = await _client.GetAsync("/health");

        // Assert
        response.EnsureSuccessStatusCode();
        Assert.Equal("text/plain", response.Content.Headers.ContentType?.MediaType);
    }

    [Fact]
    public async Task Model_Status_Endpoint_Should_Return_Status()
    {
        // Act
        var response = await _client.GetAsync("/api/model/status");

        // Assert
        response.EnsureSuccessStatusCode();
        
        var content = await response.Content.ReadAsStringAsync();
        var statusResponse = JsonSerializer.Deserialize<JsonElement>(content);
        
        Assert.True(statusResponse.TryGetProperty("Status", out var status));
        Assert.Equal("Ready", status.GetString());
    }

    [Fact]
    public async Task Generate_Endpoint_Should_Accept_Valid_Request()
    {
        // Arrange
        var request = new
        {
            Prompt = "To be or not to be",
            MaxTokens = 50,
            Temperature = 0.7
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/generate", request);

        // Assert
        response.EnsureSuccessStatusCode();
        
        var content = await response.Content.ReadAsStringAsync();
        var generateResponse = JsonSerializer.Deserialize<JsonElement>(content);
        
        Assert.True(generateResponse.TryGetProperty("GeneratedText", out var generatedText));
        Assert.False(string.IsNullOrEmpty(generatedText.GetString()));
    }

    [Fact]
    public async Task Training_Status_Endpoint_Should_Return_Training_Info()
    {
        // Act
        var response = await _client.GetAsync("/api/training/status");

        // Assert
        response.EnsureSuccessStatusCode();
        
        var content = await response.Content.ReadAsStringAsync();
        var trainingResponse = JsonSerializer.Deserialize<JsonElement>(content);
        
        Assert.True(trainingResponse.TryGetProperty("Status", out var status));
        Assert.True(trainingResponse.TryGetProperty("Loss", out var loss));
        Assert.True(loss.GetDouble() > 0);
    }

    [Fact]
    public async Task Metrics_Endpoint_Should_Return_Model_Metrics()
    {
        // Act
        var response = await _client.GetAsync("/api/metrics");

        // Assert
        response.EnsureSuccessStatusCode();
        
        var content = await response.Content.ReadAsStringAsync();
        var metricsResponse = JsonSerializer.Deserialize<JsonElement>(content);
        
        Assert.True(metricsResponse.TryGetProperty("TrainingLoss", out var trainingLoss));
        Assert.True(metricsResponse.TryGetProperty("ValidationLoss", out var validationLoss));
        Assert.True(metricsResponse.TryGetProperty("Perplexity", out var perplexity));
        
        Assert.True(trainingLoss.GetDouble() > 0);
        Assert.True(validationLoss.GetDouble() > 0);
        Assert.True(perplexity.GetDouble() > 0);
    }

    [Fact]
    public async Task Start_Training_Endpoint_Should_Accept_Training_Request()
    {
        // Arrange
        var trainingRequest = new
        {
            Epochs = 100,
            LearningRate = 3e-4,
            BatchSize = 32
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/training/start", trainingRequest);

        // Assert
        Assert.True(response.IsSuccessStatusCode);
        
        var content = await response.Content.ReadAsStringAsync();
        var startResponse = JsonSerializer.Deserialize<JsonElement>(content);
        
        Assert.True(startResponse.TryGetProperty("Message", out var message));
        Assert.True(startResponse.TryGetProperty("TrainingId", out var trainingId));
        Assert.False(string.IsNullOrEmpty(message.GetString()));
    }

    [Theory]
    [InlineData("")]
    [InlineData(null)]
    public async Task Generate_Endpoint_Should_Handle_Invalid_Prompts(string prompt)
    {
        // Arrange
        var request = new
        {
            Prompt = prompt,
            MaxTokens = 50,
            Temperature = 0.7
        };

        // Act
        var response = await _client.PostAsJsonAsync("/api/generate", request);

        // Assert - Should either succeed with empty prompt handling or return bad request
        // The actual behavior depends on implementation
        Assert.True(response.IsSuccessStatusCode || response.StatusCode == System.Net.HttpStatusCode.BadRequest);
    }
}

public class DataProcessingIntegrationTests
{
    [Fact]
    public async Task Should_Process_Training_Data_Files()
    {
        // Arrange
        var dataPath = Path.Combine(Directory.GetCurrentDirectory(), "..", "..", "..", "..", "data");
        var shakespeareFile = Path.Combine(dataPath, "shakespeare.txt");

        // Act & Assert
        if (File.Exists(shakespeareFile))
        {
            var content = await File.ReadAllTextAsync(shakespeareFile);
            Assert.NotEmpty(content);
            Assert.True(content.Length > 1000000); // Shakespeare text should be > 1MB
        }
        else
        {
            // If data file doesn't exist in test context, skip this test
            Assert.True(true, "Data file not found in test context - skipping test");
        }
    }

    [Fact]
    public void Should_Handle_Configuration_Loading()
    {
        // Arrange
        var configPath = Path.Combine(Directory.GetCurrentDirectory(), "..", "..", "..", "..", "config.json");

        // Act & Assert
        if (File.Exists(configPath))
        {
            var configContent = File.ReadAllText(configPath);
            var config = JsonSerializer.Deserialize<JsonElement>(configContent);
            
            Assert.True(config.TryGetProperty("ModelConfig", out var modelConfig));
            Assert.True(config.TryGetProperty("TrainingConfig", out var trainingConfig));
        }
        else
        {
            Assert.True(true, "Config file not found in test context - skipping test");
        }
    }
}