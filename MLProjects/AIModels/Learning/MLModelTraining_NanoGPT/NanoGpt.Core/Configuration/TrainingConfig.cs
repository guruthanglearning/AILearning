using System.Text.Json.Serialization;

namespace NanoGpt.Core.Configuration;

public sealed class TrainingConfig
{
    [JsonPropertyName("model")]
    public required ModelConfig Model { get; init; }

    [JsonPropertyName("optimization")]
    public required OptimizationConfig Optimization { get; init; }

    [JsonPropertyName("dataset")]
    public required DatasetConfig Dataset { get; init; }

    [JsonPropertyName("checkpointing")]
    public required CheckpointConfig Checkpointing { get; init; }

    [JsonPropertyName("monitoring")]
    public required MonitoringConfig Monitoring { get; init; }
}

public sealed record ModelConfig
{
    [JsonPropertyName("vocab_size")]
    public int VocabSize { get; init; } = 256;

    [JsonPropertyName("block_size")]
    public int BlockSize { get; init; } = 256;

    [JsonPropertyName("embedding_dim")]
    public int EmbeddingDimension { get; init; } = 384;

    [JsonPropertyName("num_layers")]
    public int NumLayers { get; init; } = 6;

    [JsonPropertyName("num_heads")]
    public int NumHeads { get; init; } = 6;

    [JsonPropertyName("dropout")]
    public double Dropout { get; init; } = 0.2;
}

public sealed class OptimizationConfig
{
    [JsonPropertyName("batch_size")]
    public int BatchSize { get; init; } = 64;

    [JsonPropertyName("learning_rate")]
    public double LearningRate { get; init; } = 3e-4;

    [JsonPropertyName("max_iters")]
    public int MaxIterations { get; init; } = 2000;

    [JsonPropertyName("eval_interval")]
    public int EvaluationInterval { get; init; } = 100;

    [JsonPropertyName("eval_iters")]
    public int EvaluationIterations { get; init; } = 20;

    [JsonPropertyName("weight_decay")]
    public double WeightDecay { get; init; } = 0.1;

    [JsonPropertyName("gradient_clip")]
    public double GradientClip { get; init; } = 1.0;
}

public sealed class DatasetConfig
{
    [JsonPropertyName("training_file")]
    public required string TrainingFile { get; init; }

    [JsonPropertyName("validation_file")]
    public required string ValidationFile { get; init; }
}

public sealed class CheckpointConfig
{
    [JsonPropertyName("output_directory")]
    public string OutputDirectory { get; init; } = "checkpoints";

    [JsonPropertyName("save_interval")]
    public int SaveInterval { get; init; } = 200;
}

public sealed class MonitoringConfig
{
    [JsonPropertyName("log_directory")]
    public string LogDirectory { get; init; } = "logs";

    [JsonPropertyName("enable_tensorboard")]
    public bool EnableTensorBoard { get; init; }
}
