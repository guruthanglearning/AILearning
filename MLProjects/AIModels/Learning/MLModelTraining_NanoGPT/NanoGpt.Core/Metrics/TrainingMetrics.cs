namespace NanoGpt.Core.Metrics;

public sealed record TrainingStepMetrics(
    int Iteration,
    double TrainingLoss,
    double? ValidationLoss,
    double LearningRate,
    DateTime Timestamp
);

public sealed record EvaluationMetrics(
    double Loss,
    double Perplexity
);

public sealed record TrainingSummary(
    EvaluationMetrics BestValidation,
    IReadOnlyList<TrainingStepMetrics> History,
    string? LastCheckpointPath
);
