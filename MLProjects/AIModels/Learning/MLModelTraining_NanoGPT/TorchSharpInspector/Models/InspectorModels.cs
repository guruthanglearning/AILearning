using System.ComponentModel.DataAnnotations;

namespace TorchSharpInspector.Models
{
    public class InspectorReport
    {
        public DateTime GeneratedAt { get; set; } = DateTime.UtcNow;
        public string CheckpointPath { get; set; } = string.Empty;
        public SystemDiagnostics SystemInfo { get; set; } = new();
        public CheckpointInfo CheckpointInfo { get; set; } = new();
        public ArchitectureInfo ArchitectureInfo { get; set; } = new();
        public BenchmarkResults BenchmarkResults { get; set; } = new();
        public TensorOperationResults TensorResults { get; set; } = new();
        public MemoryAnalysis MemoryAnalysis { get; set; } = new();
        public List<string> Warnings { get; set; } = new();
        public List<string> Recommendations { get; set; } = new();
    }

    public class SystemDiagnostics
    {
        public string TorchSharpVersion { get; set; } = string.Empty;
        public string DotNetVersion { get; set; } = string.Empty;
        public string OperatingSystem { get; set; } = string.Empty;
        public string ProcessorName { get; set; } = string.Empty;
        public int ProcessorCores { get; set; }
        public long TotalMemoryMB { get; set; }
        public long AvailableMemoryMB { get; set; }
        public bool CudaAvailable { get; set; }
        public string CudaVersion { get; set; } = string.Empty;
        public List<string> AvailableDevices { get; set; } = new();
        public DateTime CheckTime { get; set; } = DateTime.UtcNow;
    }

    public class CheckpointInfo
    {
        public string FilePath { get; set; } = string.Empty;
        public long FileSizeMB { get; set; }
        public DateTime CreatedDate { get; set; }
        public Dictionary<string, object> Metadata { get; set; } = new();
        public List<string> StateKeys { get; set; } = new();
        public bool IsValidCheckpoint { get; set; }
        public string CheckpointType { get; set; } = string.Empty;
        public int ParameterCount { get; set; }
        public string ModelFormat { get; set; } = string.Empty;
    }

    public class ArchitectureInfo
    {
        public int NumLayers { get; set; }
        public int EmbeddingDim { get; set; }
        public int NumHeads { get; set; }
        public int VocabSize { get; set; }
        public int ContextLength { get; set; }
        public int FeedForwardDim { get; set; }
        public long TotalParameters { get; set; }
        public List<LayerInfo> Layers { get; set; } = new();
        public Dictionary<string, object> Config { get; set; } = new();
    }

    public class LayerInfo
    {
        public int LayerIndex { get; set; }
        public string LayerType { get; set; } = string.Empty;
        public List<int> InputShape { get; set; } = new();
        public List<int> OutputShape { get; set; } = new();
        public long ParameterCount { get; set; }
        public Dictionary<string, object> Parameters { get; set; } = new();
    }

    public class BenchmarkResults
    {
        public double InferenceTimeMs { get; set; }
        public double TokensPerSecond { get; set; }
        public double MemoryUsageMB { get; set; }
        public double LoadTimeMs { get; set; }
        public List<GenerationStats> GenerationTests { get; set; } = new();
        public DateTime BenchmarkTime { get; set; } = DateTime.UtcNow;
        public string TestConfiguration { get; set; } = string.Empty;
    }

    public class GenerationStats
    {
        public string Prompt { get; set; } = string.Empty;
        public string GeneratedText { get; set; } = string.Empty;
        public int TokensGenerated { get; set; }
        public double GenerationTimeMs { get; set; }
        public double TokensPerSecond { get; set; }
        public double Temperature { get; set; }
        public int MaxTokens { get; set; }
    }

    public class TensorOperationResults
    {
        public bool BasicOperationsWorking { get; set; }
        public bool GpuAvailable { get; set; }
        public List<string> SupportedDevices { get; set; } = new();
        public Dictionary<string, double> OperationTimings { get; set; } = new();
        public List<string> TestResults { get; set; } = new();
        public DateTime TestTime { get; set; } = DateTime.UtcNow;
    }

    public class MemoryAnalysis
    {
        public long ModelSizeMB { get; set; }
        public long RuntimeMemoryMB { get; set; }
        public long PeakMemoryMB { get; set; }
        public long AvailableMemoryMB { get; set; }
        public double MemoryUtilizationPercent { get; set; }
        public List<string> MemoryRecommendations { get; set; } = new();
        public Dictionary<string, long> ComponentMemoryUsage { get; set; } = new();
    }

    public class InspectionRequest
    {
        [Required]
        [Display(Name = "Checkpoint Path")]
        public string CheckpointPath { get; set; } = string.Empty;
        
        [Display(Name = "Include Performance Benchmarks")]
        public bool IncludeBenchmarks { get; set; } = true;
        
        [Display(Name = "Include Memory Analysis")]
        public bool IncludeMemoryAnalysis { get; set; } = true;
        
        [Display(Name = "Test Prompt")]
        public string TestPrompt { get; set; } = "Once upon a time";
        
        [Range(1, 500)]
        [Display(Name = "Max Tokens for Test")]
        public int MaxTokens { get; set; } = 50;
        
        [Range(0.1, 2.0)]
        [Display(Name = "Temperature")]
        public double Temperature { get; set; } = 1.0;
    }

    public class ApiResponse<T>
    {
        public bool Success { get; set; }
        public T? Data { get; set; }
        public string Message { get; set; } = string.Empty;
        public List<string> Errors { get; set; } = new();
        public DateTime Timestamp { get; set; } = DateTime.UtcNow;
    }
}