using Microsoft.Extensions.Logging;
using NanoGpt.Core.Configuration;
using NanoGpt.Core.Data;
using NanoGpt.Core.Metrics;
using NanoGpt.Core.Model;
using TorchSharp;
using TorchSharp.Modules;
using static TorchSharp.torch;

namespace NanoGpt.Core.Training;

public sealed class NanoGptTrainer
{
    private readonly TrainingConfig _config;
    private readonly ILogger<NanoGptTrainer> _logger;
    private readonly ILogger<TextDataSource> _dataLogger;
    private readonly TextDataSource _trainingData;
    private readonly TextDataSource _validationData;
    private readonly NanoGptLanguageModel _model;
    private readonly torch.optim.Optimizer _optimizer;
    private readonly List<TrainingStepMetrics> _history = new();
    private readonly torch.Device _device;

    public NanoGptTrainer(TrainingConfig config, ILoggerFactory loggerFactory)
    {
        _config = config;
        _logger = loggerFactory.CreateLogger<NanoGptTrainer>();
        _dataLogger = loggerFactory.CreateLogger<TextDataSource>();

        _device = torch.cuda.is_available() ? torch.CUDA : torch.CPU;
        _logger.LogInformation("Using device {Device}", _device.type.ToString());

        // Create unified vocabulary from both files
        var trainText = File.ReadAllText(config.Dataset.TrainingFile);
        var valText = File.ReadAllText(config.Dataset.ValidationFile);
        var unifiedVocab = new CharacterVocabulary(trainText.Concat(valText));
        
        _trainingData = new TextDataSource(config.Dataset.TrainingFile, config.Model.BlockSize, _dataLogger, unifiedVocab);
        _validationData = new TextDataSource(config.Dataset.ValidationFile, config.Model.BlockSize, _dataLogger, unifiedVocab);

        var modelConfig = config.Model with { VocabSize = _trainingData.Vocabulary.Size };
        _model = new NanoGptLanguageModel(modelConfig).to(_device);
        _optimizer = torch.optim.AdamW(_model.parameters(), lr: config.Optimization.LearningRate, weight_decay: config.Optimization.WeightDecay);
    }

    public Task<TrainingSummary> TrainAsync(CancellationToken cancellationToken = default)
    {
        Directory.CreateDirectory(_config.Checkpointing.OutputDirectory);
        Directory.CreateDirectory(_config.Monitoring.LogDirectory);

        EvaluationMetrics? bestMetrics = null;
        string? lastCheckpoint = null;

        for (var iteration = 1; iteration <= _config.Optimization.MaxIterations; iteration++)
        {
            cancellationToken.ThrowIfCancellationRequested();

            var (xb, yb) = _trainingData.GetBatch(_config.Optimization.BatchSize);
            using var inputs = xb.to(_device);
            using var targets = yb.to(_device);

            _optimizer.zero_grad();
            var (loss, _) = _model.ForwardWithLoss(inputs, targets);
            loss.backward();

            if (_config.Optimization.GradientClip > 0)
            {
                torch.nn.utils.clip_grad_norm_(_model.parameters(), _config.Optimization.GradientClip);
            }

            _optimizer.step();
            var lossValue = loss.ToSingle();

            double? validationLoss = null;
            EvaluationMetrics? evaluation = null;
            if (iteration % _config.Optimization.EvaluationInterval == 0)
            {
                var eval = EvaluateLoss(_config.Optimization.EvaluationIterations);
                evaluation = eval;
                validationLoss = eval.Loss;
                if (bestMetrics is not EvaluationMetrics currentBest || eval.Loss < currentBest.Loss)
                {
                    bestMetrics = eval;
                    lastCheckpoint = SaveCheckpoint(iteration, eval);
                }
            }

            var metrics = new TrainingStepMetrics(
                iteration,
                lossValue,
                validationLoss,
                _config.Optimization.LearningRate,
                DateTime.UtcNow);

            _history.Add(metrics);
            LogMetrics(metrics);

            if (_config.Checkpointing.SaveInterval > 0 && iteration % _config.Checkpointing.SaveInterval == 0)
            {
                lastCheckpoint = SaveCheckpoint(iteration, evaluation);
            }
        }

        var finalBest = bestMetrics ?? EvaluateLoss(_config.Optimization.EvaluationIterations);

        return Task.FromResult(new TrainingSummary(finalBest, _history, lastCheckpoint));
    }

    private EvaluationMetrics EvaluateLoss(int iterations)
    {
        var losses = new List<double>(iterations);
        for (var i = 0; i < iterations; i++)
        {
            var (xb, yb) = _validationData.GetBatch(_config.Optimization.BatchSize);
            using var inputs = xb.to(_device);
            using var targets = yb.to(_device);
            var result = _model.ForwardWithLoss(inputs, targets);
            using var loss = result.loss;
            losses.Add(loss.ToSingle());
        }

        var average = losses.Average();
        var perplexity = Math.Exp(average);
        _logger.LogInformation("Validation loss {Loss:F4}, perplexity {Perplexity:F4}", average, perplexity);
        return new EvaluationMetrics(average, perplexity);
    }

    private void LogMetrics(TrainingStepMetrics metrics)
    {
        _logger.LogInformation("Iter {Iteration} | train loss {Loss:F4} | val loss {ValLoss} | lr {LearningRate:E3}",
            metrics.Iteration,
            metrics.TrainingLoss,
            metrics.ValidationLoss?.ToString("F4") ?? "-",
            metrics.LearningRate);
    }

    private string SaveCheckpoint(int iteration, EvaluationMetrics? evaluation)
    {
        var fileName = $"nanogpt-iter{iteration:D6}.pt";
        var path = Path.Combine(_config.Checkpointing.OutputDirectory, fileName);
        var state = _model.state_dict();
        _model.save(path);
        if (evaluation is not null)
        {
            File.WriteAllText(Path.ChangeExtension(path, ".metrics"),
                $"loss={evaluation.Loss:F6},perplexity={evaluation.Perplexity:F6}");
        }

        _logger.LogInformation("Saved checkpoint {Path}", path);
        return path;
    }

    public string GenerateText(int maxTokens, string prompt = "")
    {
        using var scope = torch.NewDisposeScope();
        var device = _device;
        var vocab = _trainingData.Vocabulary;
        var input = string.IsNullOrEmpty(prompt)
            ? Enumerable.Repeat(' ', 1).ToArray()
            : prompt.ToCharArray();

        var indices = input.Select(vocab.Encode).ToList();
        var tokens = torch.tensor(indices.ToArray(), dtype: torch.int64, device: device).unsqueeze(0);

        for (var i = 0; i < maxTokens; i++)
        {
            var contextLength = Math.Min(tokens.shape[1], _config.Model.BlockSize);
            var start = Math.Max(0, tokens.shape[1] - contextLength);
            var idxCond = tokens.slice(1, start, tokens.shape[1], 1);
            
            using var logits = _model.Forward(idxCond);
            // Get the last position logits - use int64 indices
            var lastIndex = logits.shape[1] - 1;
            var lastLogits = logits[torch.tensor(0L, dtype: torch.int64), torch.tensor(lastIndex, dtype: torch.int64)];
            var probs = lastLogits.softmax(-1);
            var nextToken = torch.multinomial(probs, 1, replacement: true);
            tokens = torch.cat(new[] { tokens, nextToken.unsqueeze(0) }, dim: 1);
        }

        var output = tokens.squeeze().cpu().data<int>().ToArray();
        var decoded = vocab.Decode(output);
        return decoded.Substring(prompt.Length);
    }
}
