using System.Text.Json;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using NanoGpt.Core.Configuration;
using NanoGpt.Core.Training;
using Serilog;

namespace NanoGpt.Training;

class Program
{
    static async Task<int> Main(string[] args)
    {
        try
        {
            // Configure Serilog
            Log.Logger = new LoggerConfiguration()
                .MinimumLevel.Information()
                .WriteTo.Console()
                .WriteTo.File("logs/training_.log", rollingInterval: RollingInterval.Day)
                .CreateLogger();

            Console.WriteLine("NanoGPT Training Pipeline");
            Console.WriteLine("========================");

            // Parse command line arguments
            var configPath = args.Length > 0 ? args[0] : "config.json";
            if (!File.Exists(configPath))
            {
                Console.WriteLine($"Configuration file not found: {configPath}");
                Console.WriteLine("Usage: NanoGpt.Training [config-file]");
                return 1;
            }

            // Load configuration
            var configJson = await File.ReadAllTextAsync(configPath);
            var config = JsonSerializer.Deserialize<TrainingConfig>(configJson, new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
                ReadCommentHandling = JsonCommentHandling.Skip
            });

            if (config == null)
            {
                Console.WriteLine("Failed to parse configuration file.");
                return 1;
            }

            // Validate data files exist
            if (!File.Exists(config.Dataset.TrainingFile))
            {
                Console.WriteLine($"Training file not found: {config.Dataset.TrainingFile}");
                Console.WriteLine("Please ensure training data is available or run data download scripts first.");
                return 1;
            }

            if (!File.Exists(config.Dataset.ValidationFile))
            {
                Console.WriteLine($"Validation file not found: {config.Dataset.ValidationFile}");
                Console.WriteLine("Please ensure validation data is available or run data download scripts first.");
                return 1;
            }

            // Set up dependency injection and logging
            using var host = Host.CreateDefaultBuilder(args)
                .ConfigureServices(services =>
                {
                    services.AddLogging(builder =>
                    {
                        builder.ClearProviders();
                        builder.AddSerilog();
                    });
                })
                .Build();

            var loggerFactory = host.Services.GetRequiredService<ILoggerFactory>();
            var logger = loggerFactory.CreateLogger<Program>();

            logger.LogInformation("Starting NanoGPT training with configuration from {ConfigPath}", configPath);
            logger.LogInformation("Training file: {TrainingFile}", config.Dataset.TrainingFile);
            logger.LogInformation("Validation file: {ValidationFile}", config.Dataset.ValidationFile);
            logger.LogInformation("Max iterations: {MaxIterations}", config.Optimization.MaxIterations);
            logger.LogInformation("Batch size: {BatchSize}", config.Optimization.BatchSize);
            logger.LogInformation("Learning rate: {LearningRate}", config.Optimization.LearningRate);

            // Create trainer and start training
            var trainer = new NanoGptTrainer(config, loggerFactory);
            logger.LogInformation("Training started...");

            var stopwatch = System.Diagnostics.Stopwatch.StartNew();
            var summary = await trainer.TrainAsync();
            stopwatch.Stop();

            logger.LogInformation("Training completed in {ElapsedTime}", stopwatch.Elapsed);
            logger.LogInformation("Final validation loss: {FinalLoss:F6}", summary.BestValidation.Loss);
            logger.LogInformation("Final perplexity: {FinalPerplexity:F6}", summary.BestValidation.Perplexity);
            logger.LogInformation("Total training steps: {TotalSteps}", summary.History.Count);
            
            if (summary.LastCheckpointPath != null)
            {
                logger.LogInformation("Best model saved to: {CheckpointPath}", summary.LastCheckpointPath);
            }

            // Generate sample text
            Console.WriteLine("\nGenerating sample text:");
            Console.WriteLine("=======================");
            try
            {
                var sampleText = trainer.GenerateText(200, "The ");
                Console.WriteLine($"Generated: The{sampleText}");
            }
            catch (Exception ex)
            {
                logger.LogWarning("Failed to generate sample text: {Error}", ex.Message);
            }

            Console.WriteLine("\nTraining completed successfully!");
            return 0;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Training failed: {ex.Message}");
            Log.Logger.Error(ex, "Training failed");
            return 1;
        }
        finally
        {
            Log.CloseAndFlush();
        }
    }
}
