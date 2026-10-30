namespace MultiAgentDevTeam.Shared.Configuration;

/// <summary>Where the generated project's files are written once a run finishes.</summary>
public class ProjectOutputOptions
{
    public bool Enabled { get; set; } = true;

    /// <summary>Folder that gets a new project subfolder when the request names no location.</summary>
    public string DefaultRoot { get; set; } = @"C:\Temp";

    /// <summary>
    /// Set when the service runs in a container: the folder where the host's drives are mounted,
    /// one subfolder per drive letter (Docker Desktop: /run/desktop/mnt/host mounted at /host).
    /// Empty means paths are used as they are.
    /// </summary>
    public string HostDrivesPath { get; set; } = string.Empty;
}
