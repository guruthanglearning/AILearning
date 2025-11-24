using Xunit;
using TorchSharpInspector.Services;
using TorchSharpInspector.Models;

namespace TorchSharpInspector.Tests
{
    public class SystemDiagnosticsServiceTests
    {
        [Fact]
        public async Task GetSystemDiagnosticsAsync_ReturnsValidDiagnostics()
        {
            // Arrange
            var service = new SystemDiagnosticsService();

            // Act
            var result = await service.GetSystemDiagnosticsAsync();

            // Assert
            Assert.NotNull(result);
            Assert.NotEmpty(result.ProcessorName);
            Assert.NotEmpty(result.OperatingSystem);
            Assert.NotEmpty(result.DotNetVersion);
            Assert.True(result.ProcessorCores > 0);
            Assert.True(result.TotalMemoryMB > 0);
            Assert.True(result.CheckTime <= DateTime.UtcNow);
        }

        [Fact]
        public async Task ValidateTorchSharpInstallationAsync_ReturnsValidationResult()
        {
            // Arrange
            var service = new SystemDiagnosticsService();

            // Act
            var result = await service.ValidateTorchSharpInstallationAsync();

            // Assert
            // TorchSharp should be available since it's referenced in the project
            Assert.True(result, "TorchSharp should be available in the test project");
        }
    }
}