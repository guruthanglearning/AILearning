using TorchSharpInspector.Models;

namespace TorchSharpInspector.Services
{
    public class TorchSharpInspectorService : ITorchSharpInspectorService
    {
        private readonly ILogger<TorchSharpInspectorService> _logger;
        private readonly ISystemDiagnosticsService _systemDiagnosticsService;
        private readonly ICheckpointInspectionService _checkpointInspectionService;
        private readonly IArchitectureAnalysisService _architectureAnalysisService;
        private readonly IPerformanceBenchmarkService _performanceBenchmarkService;
        private readonly ITensorOperationsService _tensorOperationsService;
        private readonly IMemoryAnalysisService _memoryAnalysisService;

        public TorchSharpInspectorService(
            ILogger<TorchSharpInspectorService> logger,
            ISystemDiagnosticsService systemDiagnosticsService,
            ICheckpointInspectionService checkpointInspectionService,
            IArchitectureAnalysisService architectureAnalysisService,
            IPerformanceBenchmarkService performanceBenchmarkService,
            ITensorOperationsService tensorOperationsService,
            IMemoryAnalysisService memoryAnalysisService)
        {
            _logger = logger;
            _systemDiagnosticsService = systemDiagnosticsService;
            _checkpointInspectionService = checkpointInspectionService;
            _architectureAnalysisService = architectureAnalysisService;
            _performanceBenchmarkService = performanceBenchmarkService;
            _tensorOperationsService = tensorOperationsService;
            _memoryAnalysisService = memoryAnalysisService;
        }

        public async Task<InspectorReport> GenerateFullReportAsync(string checkpointPath)
        {
            _logger.LogInformation("Starting full inspection report generation for {CheckpointPath}", checkpointPath);

            var report = new InspectorReport
            {
                CheckpointPath = checkpointPath,
                GeneratedAt = DateTime.UtcNow
            };

            try
            {
                // Run all analyses
                var tasks = new List<Task>
                {
                    Task.Run(async () => report.SystemInfo = await _systemDiagnosticsService.GetSystemDiagnosticsAsync()),
                    Task.Run(async () => report.CheckpointInfo = await _checkpointInspectionService.InspectCheckpointAsync(checkpointPath)),
                    Task.Run(async () => report.TensorResults = await _tensorOperationsService.TestTensorOperationsAsync())
                };

                await Task.WhenAll(tasks);

                // Run dependent analyses after checkpoint validation
                if (report.CheckpointInfo.IsValidCheckpoint)
                {
                    var dependentTasks = new List<Task>
                    {
                        Task.Run(async () => report.ArchitectureInfo = await _architectureAnalysisService.AnalyzeArchitectureAsync(checkpointPath)),
                        Task.Run(async () => report.BenchmarkResults = await _performanceBenchmarkService.RunPerformanceBenchmarkAsync(checkpointPath)),
                        Task.Run(async () => report.MemoryAnalysis = await _memoryAnalysisService.AnalyzeMemoryUsageAsync(checkpointPath))
                    };

                    await Task.WhenAll(dependentTasks);
                }
                else
                {
                    report.Warnings.Add("Checkpoint file is not valid or could not be loaded");
                }

                // Generate recommendations
                GenerateRecommendations(report);

                _logger.LogInformation("Full inspection report generated successfully for {CheckpointPath}", checkpointPath);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error generating full report for {CheckpointPath}", checkpointPath);
                report.Warnings.Add($"Error during analysis: {ex.Message}");
            }

            return report;
        }

        public async Task<bool> ValidateCheckpointAsync(string checkpointPath)
        {
            try
            {
                if (!File.Exists(checkpointPath))
                {
                    _logger.LogWarning("Checkpoint file does not exist: {CheckpointPath}", checkpointPath);
                    return false;
                }

                var checkpointInfo = await _checkpointInspectionService.InspectCheckpointAsync(checkpointPath);
                return checkpointInfo.IsValidCheckpoint;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error validating checkpoint {CheckpointPath}", checkpointPath);
                return false;
            }
        }

        private void GenerateRecommendations(InspectorReport report)
        {
            try
            {
                // System recommendations
                if (!report.SystemInfo.CudaAvailable)
                {
                    report.Recommendations.Add("Consider using GPU acceleration for better performance if available");
                }

                if (report.SystemInfo.AvailableMemoryMB < 4096)
                {
                    report.Recommendations.Add("System has limited memory. Consider closing other applications during training");
                }

                // Architecture recommendations
                if (report.ArchitectureInfo.TotalParameters > 100_000_000)
                {
                    report.Recommendations.Add("Large model detected. Consider model compression techniques for deployment");
                }

                // Performance recommendations
                if (report.BenchmarkResults.TokensPerSecond < 10)
                {
                    report.Recommendations.Add("Low inference speed detected. Consider optimizing model or using faster hardware");
                }

                // Memory recommendations
                if (report.MemoryAnalysis.MemoryUtilizationPercent > 85)
                {
                    report.Recommendations.Add("High memory utilization. Consider reducing batch size or model size");
                }

                // Tensor operations recommendations
                if (!report.TensorResults.BasicOperationsWorking)
                {
                    report.Recommendations.Add("Basic tensor operations failed. Check TorchSharp installation");
                }

                // Default recommendation if none generated
                if (report.Recommendations.Count == 0)
                {
                    report.Recommendations.Add("System appears to be well configured for the current model");
                }

                _logger.LogInformation("Generated {RecommendationCount} recommendations", report.Recommendations.Count);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error generating recommendations");
                report.Warnings.Add("Could not generate recommendations due to analysis errors");
            }
        }
    }
}