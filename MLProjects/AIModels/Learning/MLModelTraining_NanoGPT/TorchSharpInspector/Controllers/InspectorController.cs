using Microsoft.AspNetCore.Mvc;
using TorchSharpInspector.Models;
using TorchSharpInspector.Services;

namespace TorchSharpInspector.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class InspectorController : ControllerBase
    {
        private readonly ILogger<InspectorController> _logger;
        private readonly ITorchSharpInspectorService _inspectorService;
        private readonly ISystemDiagnosticsService _systemDiagnosticsService;
        private readonly IReportExportService _reportExportService;

        public InspectorController(
            ILogger<InspectorController> logger,
            ITorchSharpInspectorService inspectorService,
            ISystemDiagnosticsService systemDiagnosticsService,
            IReportExportService reportExportService)
        {
            _logger = logger;
            _inspectorService = inspectorService;
            _systemDiagnosticsService = systemDiagnosticsService;
            _reportExportService = reportExportService;
        }

        /// <summary>
        /// Get system diagnostics information
        /// </summary>
        [HttpGet("system")]
        public async Task<ActionResult<ApiResponse<SystemDiagnostics>>> GetSystemDiagnostics()
        {
            try
            {
                var systemInfo = await _systemDiagnosticsService.GetSystemDiagnosticsAsync();
                return Ok(new ApiResponse<SystemDiagnostics>
                {
                    Success = true,
                    Data = systemInfo,
                    Message = "System diagnostics retrieved successfully"
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving system diagnostics");
                return StatusCode(500, new ApiResponse<SystemDiagnostics>
                {
                    Success = false,
                    Message = "Error retrieving system diagnostics",
                    Errors = new List<string> { ex.Message }
                });
            }
        }

        /// <summary>
        /// Validate a checkpoint file
        /// </summary>
        [HttpPost("validate")]
        public async Task<ActionResult<ApiResponse<bool>>> ValidateCheckpoint([FromBody] string checkpointPath)
        {
            try
            {
                if (string.IsNullOrEmpty(checkpointPath))
                {
                    return BadRequest(new ApiResponse<bool>
                    {
                        Success = false,
                        Message = "Checkpoint path is required",
                        Errors = new List<string> { "checkpointPath cannot be null or empty" }
                    });
                }

                var isValid = await _inspectorService.ValidateCheckpointAsync(checkpointPath);
                return Ok(new ApiResponse<bool>
                {
                    Success = true,
                    Data = isValid,
                    Message = isValid ? "Checkpoint is valid" : "Checkpoint is not valid"
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error validating checkpoint {CheckpointPath}", checkpointPath);
                return StatusCode(500, new ApiResponse<bool>
                {
                    Success = false,
                    Message = "Error validating checkpoint",
                    Errors = new List<string> { ex.Message }
                });
            }
        }

        /// <summary>
        /// Generate a full inspection report for a checkpoint
        /// </summary>
        [HttpPost("inspect")]
        public async Task<ActionResult<ApiResponse<InspectorReport>>> InspectCheckpoint([FromBody] InspectionRequest request)
        {
            try
            {
                if (!ModelState.IsValid)
                {
                    return BadRequest(new ApiResponse<InspectorReport>
                    {
                        Success = false,
                        Message = "Invalid request",
                        Errors = ModelState.Values.SelectMany(v => v.Errors).Select(e => e.ErrorMessage).ToList()
                    });
                }

                var report = await _inspectorService.GenerateFullReportAsync(request.CheckpointPath);
                return Ok(new ApiResponse<InspectorReport>
                {
                    Success = true,
                    Data = report,
                    Message = "Inspection report generated successfully"
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error generating inspection report for {CheckpointPath}", request?.CheckpointPath);
                return StatusCode(500, new ApiResponse<InspectorReport>
                {
                    Success = false,
                    Message = "Error generating inspection report",
                    Errors = new List<string> { ex.Message }
                });
            }
        }

        /// <summary>
        /// Export inspection report in specified format
        /// </summary>
        [HttpPost("export/{format}")]
        public async Task<IActionResult> ExportReport([FromRoute] string format, [FromBody] InspectorReport report)
        {
            try
            {
                var formatUpper = format.ToUpper();
                if (formatUpper != "JSON" && formatUpper != "CSV")
                {
                    return BadRequest(new ApiResponse<object>
                    {
                        Success = false,
                        Message = "Unsupported format. Use 'json' or 'csv'",
                        Errors = new List<string> { $"Format '{format}' is not supported" }
                    });
                }

                byte[] data;
                string contentType;
                string fileName;

                if (formatUpper == "JSON")
                {
                    data = await _reportExportService.ExportReportAsJsonAsync(report);
                    contentType = "application/json";
                    fileName = $"inspector_report_{DateTime.Now:yyyyMMdd_HHmmss}.json";
                }
                else
                {
                    data = await _reportExportService.ExportReportAsCsvAsync(report);
                    contentType = "text/csv";
                    fileName = $"inspector_report_{DateTime.Now:yyyyMMdd_HHmmss}.csv";
                }

                return File(data, contentType, fileName);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error exporting report in format {Format}", format);
                return StatusCode(500, new ApiResponse<object>
                {
                    Success = false,
                    Message = "Error exporting report",
                    Errors = new List<string> { ex.Message }
                });
            }
        }

        /// <summary>
        /// Get available checkpoint files in a directory
        /// </summary>
        [HttpGet("checkpoints")]
        public async Task<ActionResult<ApiResponse<List<string>>>> GetAvailableCheckpoints([FromQuery] string? directory = null)
        {
            try
            {
                var searchDirectory = directory ?? Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "models");
                
                if (!Directory.Exists(searchDirectory))
                {
                    return Ok(new ApiResponse<List<string>>
                    {
                        Success = true,
                        Data = new List<string>(),
                        Message = "Directory does not exist or no checkpoints found"
                    });
                }

                var checkpoints = Directory.GetFiles(searchDirectory, "*", SearchOption.AllDirectories)
                    .Where(f => Path.GetExtension(f).ToLower() is ".pt" or ".pth" or ".ckpt")
                    .ToList();

                return Ok(new ApiResponse<List<string>>
                {
                    Success = true,
                    Data = checkpoints,
                    Message = $"Found {checkpoints.Count} checkpoint files"
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving available checkpoints");
                return StatusCode(500, new ApiResponse<List<string>>
                {
                    Success = false,
                    Message = "Error retrieving checkpoint files",
                    Errors = new List<string> { ex.Message }
                });
            }
        }
    }
}