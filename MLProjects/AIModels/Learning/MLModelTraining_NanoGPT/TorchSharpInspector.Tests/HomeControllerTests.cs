using Xunit;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using TorchSharpInspector.Controllers;
using TorchSharpInspector.Services;
using TorchSharpInspector.Models;
using Moq;

namespace TorchSharpInspector.Tests
{
    public class HomeControllerTests
    {
        [Fact]
        public async Task Index_ReturnsViewResult()
        {
            // Arrange
            var mockLogger = new Mock<ILogger<HomeController>>();
            var systemDiagnosticsService = new SystemDiagnosticsService();
            var controller = new HomeController(mockLogger.Object, systemDiagnosticsService);

            // Act
            var result = await controller.Index();

            // Assert
            Assert.IsType<ViewResult>(result);
        }

        [Fact]
        public async Task SystemDiagnostics_ReturnsJsonResult()
        {
            // Arrange
            var mockLogger = new Mock<ILogger<HomeController>>();
            var systemDiagnosticsService = new SystemDiagnosticsService();
            var controller = new HomeController(mockLogger.Object, systemDiagnosticsService);

            // Act
            var result = await controller.SystemDiagnostics();

            // Assert
            var jsonResult = Assert.IsType<JsonResult>(result);
            Assert.NotNull(jsonResult.Value);
            
            // The result should be a SystemDiagnostics object
            var systemDiagnostics = jsonResult.Value as SystemDiagnostics;
            Assert.NotNull(systemDiagnostics);
            Assert.NotEmpty(systemDiagnostics.ProcessorName);
        }

        [Fact]
        public async Task ValidateTorchSharp_ReturnsJsonResult()
        {
            // Arrange
            var mockLogger = new Mock<ILogger<HomeController>>();
            var systemDiagnosticsService = new SystemDiagnosticsService();
            var controller = new HomeController(mockLogger.Object, systemDiagnosticsService);

            // Act
            var result = await controller.ValidateTorchSharp();

            // Assert
            var jsonResult = Assert.IsType<JsonResult>(result);
            Assert.NotNull(jsonResult.Value);
        }

        [Fact]
        public void About_ReturnsViewResult()
        {
            // Arrange
            var mockLogger = new Mock<ILogger<HomeController>>();
            var systemDiagnosticsService = new SystemDiagnosticsService();
            var controller = new HomeController(mockLogger.Object, systemDiagnosticsService);

            // Act
            var result = controller.About();

            // Assert
            Assert.IsType<ViewResult>(result);
        }
    }
}