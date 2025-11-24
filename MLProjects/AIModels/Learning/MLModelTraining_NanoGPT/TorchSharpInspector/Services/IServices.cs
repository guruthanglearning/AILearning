using TorchSharpInspector.Models;

namespace TorchSharpInspector.Services
{
    public interface ITorchSharpInspectorService
    {
        Task<InspectorReport> GenerateFullReportAsync(string checkpointPath);
        Task<bool> ValidateCheckpointAsync(string checkpointPath);
    }

    public interface ISystemDiagnosticsService
    {
        Task<SystemDiagnostics> GetSystemDiagnosticsAsync();
        Task<bool> ValidateTorchSharpInstallationAsync();
    }

    public interface ICheckpointInspectionService
    {
        Task<CheckpointInfo> InspectCheckpointAsync(string checkpointPath);
        Task<Dictionary<string, object>> GetCheckpointMetadataAsync(string checkpointPath);
    }

    public interface IArchitectureAnalysisService
    {
        Task<ArchitectureInfo> AnalyzeArchitectureAsync(string checkpointPath);
        Task<List<LayerInfo>> GetLayerDetailsAsync(string checkpointPath);
    }

    public interface IPerformanceBenchmarkService
    {
        Task<BenchmarkResults> RunPerformanceBenchmarkAsync(string checkpointPath);
        Task<GenerationStats> TestTextGenerationAsync(string checkpointPath, string prompt, int maxTokens);
    }

    public interface ITensorOperationsService
    {
        Task<TensorOperationResults> TestTensorOperationsAsync();
        Task<bool> ValidateGpuAvailabilityAsync();
    }

    public interface IMemoryAnalysisService
    {
        Task<MemoryAnalysis> AnalyzeMemoryUsageAsync(string checkpointPath);
        Task<long> EstimateModelMemoryRequirementsAsync(string checkpointPath);
    }

    public interface IReportExportService
    {
        Task<byte[]> ExportReportAsJsonAsync(InspectorReport report);
        Task<byte[]> ExportReportAsCsvAsync(InspectorReport report);
        Task<string> SaveReportToFileAsync(InspectorReport report, string format);
    }
}