using Xunit;
using TorchSharpInspector.Models;

namespace TorchSharpInspector.Tests
{
    public class SimpleTests
    {
        [Fact]
        public void Test_SystemDiagnostics_Model_CanBeCreated()
        {
            // Arrange & Act
            var diagnostics = new SystemDiagnostics
            {
                ProcessorName = "Test Processor",
                TotalMemoryMB = 16000,
                OperatingSystem = "Test OS",
                CudaAvailable = true,
                TorchSharpVersion = "0.105.1",
                ProcessorCores = 8,
                AvailableMemoryMB = 8000
            };

            // Assert
            Assert.NotNull(diagnostics);
            Assert.Equal("Test Processor", diagnostics.ProcessorName);
            Assert.Equal(16000, diagnostics.TotalMemoryMB);
            Assert.Equal("Test OS", diagnostics.OperatingSystem);
            Assert.True(diagnostics.CudaAvailable);
            Assert.Equal("0.105.1", diagnostics.TorchSharpVersion);
            Assert.Equal(8, diagnostics.ProcessorCores);
            Assert.Equal(8000, diagnostics.AvailableMemoryMB);
        }

        [Fact]
        public void Test_Simple_Math_Operation()
        {
            // Arrange
            int a = 2;
            int b = 3;

            // Act
            int result = a + b;

            // Assert
            Assert.Equal(5, result);
        }

        [Fact]
        public void Test_String_Operations()
        {
            // Arrange
            string input = "TorchSharp";

            // Act
            string result = input.ToLower();

            // Assert
            Assert.Equal("torchsharp", result);
            Assert.NotEmpty(input);
            Assert.Contains("Sharp", input);
        }
    }
}