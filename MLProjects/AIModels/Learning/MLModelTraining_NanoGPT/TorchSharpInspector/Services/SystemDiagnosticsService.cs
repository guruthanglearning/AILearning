using System.Diagnostics;
using System.Runtime.InteropServices;
using TorchSharpInspector.Models;

namespace TorchSharpInspector.Services
{
    public class SystemDiagnosticsService : ISystemDiagnosticsService
    {
        public async Task<SystemDiagnostics> GetSystemDiagnosticsAsync()
        {
            return await Task.FromResult(new SystemDiagnostics
            {
                // Hardware Information
                ProcessorName = GetProcessorName(),
                ProcessorCores = Environment.ProcessorCount,
                TotalMemoryMB = (long)GetTotalMemoryMB(),
                AvailableMemoryMB = (long)GetAvailableMemoryMB(),
                
                // System Information
                OperatingSystem = GetOperatingSystemInfo(),
                DotNetVersion = Environment.Version.ToString(),
                
                // TorchSharp Information
                TorchSharpVersion = GetTorchSharpVersion(),
                CudaAvailable = false, // Will be implemented later
                CudaVersion = "Not Available",
                AvailableDevices = new List<string> { "CPU" },
                
                CheckTime = DateTime.UtcNow
            });
        }

        public async Task<bool> ValidateTorchSharpInstallationAsync()
        {
            try
            {
                // Try to load TorchSharp assembly
                var torchSharpAssembly = AppDomain.CurrentDomain.GetAssemblies()
                    .FirstOrDefault(a => a.GetName().Name?.Contains("TorchSharp") == true);
                
                if (torchSharpAssembly == null)
                {
                    return false;
                }

                // Additional validation could include:
                // - Testing basic tensor operations
                // - Checking CUDA availability
                // - Verifying native libraries
                
                return await Task.FromResult(true);
            }
            catch
            {
                return false;
            }
        }

        private string GetProcessorName()
        {
            try
            {
                if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
                {
                    using var process = new Process
                    {
                        StartInfo = new ProcessStartInfo
                        {
                            FileName = "wmic",
                            Arguments = "cpu get name /value",
                            UseShellExecute = false,
                            RedirectStandardOutput = true,
                            CreateNoWindow = true
                        }
                    };
                    process.Start();
                    var output = process.StandardOutput.ReadToEnd();
                    process.WaitForExit();
                    
                    var lines = output.Split('\n');
                    var nameLine = lines.FirstOrDefault(l => l.StartsWith("Name="));
                    return nameLine?.Substring(5).Trim() ?? "Unknown CPU";
                }
                
                return "CPU Information Not Available";
            }
            catch
            {
                return "Unknown CPU";
            }
        }

        private double GetTotalMemoryMB()
        {
            try
            {
                var totalMemory = GC.GetTotalMemory(false);
                
                // This is an approximation - in a real implementation, you'd use
                // platform-specific APIs to get actual total system memory
                return Math.Round(totalMemory / (1024.0 * 1024.0), 2);
            }
            catch
            {
                return 0;
            }
        }

        private double GetAvailableMemoryMB()
        {
            try
            {
                // This is a simplified version - real implementation would use
                // system-specific memory APIs
                var availableMemory = GC.GetTotalMemory(false);
                return Math.Round(availableMemory / (1024.0 * 1024.0), 2);
            }
            catch
            {
                return 0;
            }
        }

        private string GetOperatingSystemInfo()
        {
            return RuntimeInformation.OSDescription;
        }

        private string GetTorchSharpVersion()
        {
            try
            {
                var torchSharpAssembly = AppDomain.CurrentDomain.GetAssemblies()
                    .FirstOrDefault(a => a.GetName().Name?.Contains("TorchSharp") == true);
                
                return torchSharpAssembly?.GetName().Version?.ToString() ?? "Not Installed";
            }
            catch
            {
                return "Not Available";
            }
        }

    }
}