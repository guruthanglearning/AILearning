using Microsoft.AspNetCore.Mvc;
using TorchSharpInspector.Services;

namespace TorchSharpInspector.Controllers
{
    public class HomeController : Controller
    {
        private readonly ILogger<HomeController> _logger;
        private readonly ISystemDiagnosticsService _diagnosticsService;

        public HomeController(ILogger<HomeController> logger, ISystemDiagnosticsService diagnosticsService)
        {
            _logger = logger;
            _diagnosticsService = diagnosticsService;
        }

        public async Task<IActionResult> Index()
        {
            try
            {
                var diagnostics = await _diagnosticsService.GetSystemDiagnosticsAsync();
                
                ViewBag.Message = "TorchSharp Inspector is running successfully!";
                ViewBag.Version = "1.0.0";
                ViewBag.Environment = Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT") ?? "Development";
                ViewBag.Timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
                
                return View(diagnostics);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error getting system diagnostics");
                ViewBag.Error = $"Failed to load system diagnostics: {ex.Message}";
                return View();
            }
        }

        [HttpGet]
        public async Task<IActionResult> SystemDiagnostics()
        {
            try
            {
                var diagnostics = await _diagnosticsService.GetSystemDiagnosticsAsync();
                return Json(diagnostics);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error getting system diagnostics");
                return Json(new { error = ex.Message });
            }
        }

        [HttpGet]
        public async Task<IActionResult> ValidateTorchSharp()
        {
            try
            {
                var isValid = await _diagnosticsService.ValidateTorchSharpInstallationAsync();
                return Json(new { isValid, message = isValid ? "TorchSharp is properly installed" : "TorchSharp installation issues detected" });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error validating TorchSharp");
                return Json(new { isValid = false, message = ex.Message });
            }
        }

        public IActionResult About()
        {
            ViewBag.Features = new[]
            {
                "System Diagnostics",
                "Model Analysis", 
                "Performance Benchmarks",
                "Tensor Operations",
                "Memory Analysis",
                "Report Generation"
            };
            
            return View();
        }

        public IActionResult Privacy()
        {
            return View();
        }

        [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
        public IActionResult Error()
        {
            return View();
        }
    }
}