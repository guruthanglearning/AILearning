using System.Text;
using System.Text.RegularExpressions;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using MultiAgentDevTeam.Shared.Configuration;
using MultiAgentDevTeam.Shared.Models;

namespace MultiAgentDevTeam.Orchestrator.Services;

/// <summary>A file the agents produced, with its path relative to the project folder.</summary>
public record ProjectFile(string Path, string Content);

/// <summary>What happened when the project was written to disk.</summary>
public record ProjectWriteResult
{
    public bool Written { get; init; }

    /// <summary>The project folder as the user sees it (a host path, even when the service runs in a container).</summary>
    public string? Folder { get; init; }

    /// <summary>The location the request asked for, when it named one.</summary>
    public string? RequestedFolder { get; init; }

    public IReadOnlyList<string> Files { get; init; } = [];
    public string Message { get; init; } = string.Empty;
}

public interface IProjectWriter
{
    Task<ProjectWriteResult> WriteAsync(
        string requirement, Guid sessionId, IReadOnlyDictionary<ArtifactType, string> artifacts, CancellationToken ct = default);
}

/// <summary>
/// Turns the "### File: path" blocks in the agents' output into a project folder: the location named
/// in the request, or a new folder under <see cref="ProjectOutputOptions.DefaultRoot"/>.
/// Never overwrites anything: a folder that already has files gets a new subfolder instead.
/// </summary>
public partial class ProjectWriter : IProjectWriter
{
    // Later sources win when two agents write the same path
    private static readonly ArtifactType[] CodeSources =
        [ArtifactType.SourceCode, ArtifactType.TestResults, ArtifactType.DeploymentConfig];

    // Written whole into docs/ so the design and review notes travel with the code
    private static readonly ArtifactType[] DocSources =
        [ArtifactType.Requirements, ArtifactType.Architecture, ArtifactType.Documentation,
         ArtifactType.ReviewNotes, ArtifactType.SecurityReport];

    private const int MaxFiles = 500;

    private static readonly HashSet<string> StopWords = new(StringComparer.OrdinalIgnoreCase)
    {
        "a", "an", "and", "the", "to", "of", "for", "with", "in", "on", "under", "at", "this", "that", "is",
        "be", "been", "it", "using", "use", "please", "perform", "following", "create", "build", "make",
        "develop", "write", "generate", "project", "location", "folder", "then", "once", "just", "open", "run"
    };

    private readonly ProjectOutputOptions _options;
    private readonly ILogger<ProjectWriter> _logger;

    public ProjectWriter(IOptions<AgentConfiguration> config, ILogger<ProjectWriter> logger)
    {
        _options = config.Value.ProjectOutput;
        _logger = logger;
    }

    public async Task<ProjectWriteResult> WriteAsync(
        string requirement, Guid sessionId, IReadOnlyDictionary<ArtifactType, string> artifacts, CancellationToken ct = default)
    {
        if (!_options.Enabled)
            return new ProjectWriteResult { Message = "📁 Project output is turned off, so no files were written" };

        var requested = FindRequestedFolder(requirement);
        var files = CollectFiles(artifacts, requested);
        if (files.Count == 0)
            return new ProjectWriteResult
            {
                RequestedFolder = requested,
                Message = "📁 The agents' output had no files to write, so no project folder was created"
            };

        var folder = requested ?? JoinHost(_options.DefaultRoot, FolderName(requirement, sessionId));
        if (HasParentSegment(folder))
            return Failed(requested, $"{folder} uses \"..\". Name the folder directly");

        // One run at a time picks and fills its folder, so two runs can't both claim the same empty one
        await WriteLock.WaitAsync(ct);
        try
        {
            var local = ToLocalPath(folder, _options.HostDrivesPath);
            if (local is null)
                return Failed(requested, $"the service can't reach {folder}. Only drives shared with it can be written to");

            // Never mix generated files into a folder that already has content
            var name = FolderName(requirement, sessionId);
            var baseFolder = folder;
            var baseLocal = local;
            for (var n = 1; HasContent(local); n++)
            {
                var candidate = n == 1 ? name : $"{name}-{n}";
                folder = JoinHost(baseFolder, candidate);
                local = Path.Combine(baseLocal, candidate);
            }

            var root = Path.GetFullPath(local);
            foreach (var file in files)
            {
                var target = Path.GetFullPath(Path.Combine(root, file.Path));
                if (!target.StartsWith(root.TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase))
                    continue;
                Directory.CreateDirectory(Path.GetDirectoryName(target)!);
                // CreateNew: a file something else put there in the meantime is an error, never overwritten
                await using var stream = new FileStream(target, FileMode.CreateNew, FileAccess.Write);
                await using var writer = new StreamWriter(stream, new UTF8Encoding(false));
                await writer.WriteAsync(file.Content.AsMemory(), ct);
            }

            _logger.LogInformation("Wrote {Count} project files for session {SessionId} to {Folder}", files.Count, sessionId, folder);
            return new ProjectWriteResult
            {
                Written = true,
                Folder = folder,
                RequestedFolder = requested,
                Files = files.Select(f => f.Path).ToList(),
                Message = $"📁 Wrote {files.Count} files to {folder}"
            };
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or ArgumentException or NotSupportedException)
        {
            _logger.LogWarning(ex, "Could not write the project for session {SessionId} to {Folder}", sessionId, folder);
            return Failed(requested, $"{ex.Message}");
        }
        finally
        {
            WriteLock.Release();
        }
    }

    private static readonly SemaphoreSlim WriteLock = new(1, 1);

    private static bool HasContent(string path) =>
        File.Exists(path) || (Directory.Exists(path) && Directory.EnumerateFileSystemEntries(path).Any());

    private static bool HasParentSegment(string path) =>
        path.Split('\\', '/').Any(s => s == "..");

    private static ProjectWriteResult Failed(string? requested, string reason) => new()
    {
        RequestedFolder = requested,
        Message = $"⚠️ Could not write the project files: {reason}"
    };

    /// <summary>Every file in the code artifacts, plus the design documents under docs/; empty when there is no code.</summary>
    public static List<ProjectFile> CollectFiles(IReadOnlyDictionary<ArtifactType, string> artifacts, string? requestedFolder)
    {
        var files = new Dictionary<string, ProjectFile>(StringComparer.OrdinalIgnoreCase);
        foreach (var type in CodeSources)
        {
            if (!artifacts.TryGetValue(type, out var content)) continue;
            foreach (var file in ParseFiles(content))
            {
                var path = RelativePath(file.Path, requestedFolder);
                if (path is not null && (files.Count < MaxFiles || files.ContainsKey(path)))
                    files[path] = file with { Path = path };
            }
        }
        if (files.Count == 0) return [];

        foreach (var type in DocSources)
        {
            var path = $"docs/{type}.md";
            if (artifacts.TryGetValue(type, out var content) && !string.IsNullOrWhiteSpace(content) && !files.ContainsKey(path))
                files[path] = new ProjectFile(path, content);
        }
        return files.Values.ToList();
    }

    [GeneratedRegex(@"^\#{2,4}[ \t]*File:[ \t]*(?<path>[^\r\n]+?)[ \t]*\r?\n(?:[ \t]*\r?\n)*(?<fence>`{3,}|~{3,})[^\r\n]*\r?\n(?<body>.*?)\r?\n\k<fence>[ \t]*\r?$",
        RegexOptions.Multiline | RegexOptions.Singleline)]
    private static partial Regex FileBlock();

    /// <summary>The "### File: path" blocks in an agent's output, as written (paths not yet checked).</summary>
    public static List<ProjectFile> ParseFiles(string artifact) =>
        FileBlock().Matches(artifact)
            .Select(m => new ProjectFile(
                HeaderPath(m.Groups["path"].Value),
                m.Groups["body"].Value.ReplaceLineEndings("\n") + "\n"))
            .Where(f => f.Path.Length > 0)
            .ToList();

    // `src/My App/Program.cs` (new) keeps its spaces; an unquoted path drops a trailing note such as
    // "(updated)" or "- entry point"
    [GeneratedRegex(@"^\**\s*(?:(?<q>[`""'])(?<path>[^`""'\r\n]+)\k<q>.*|(?<path>.+?)(?:\s+(?:\(|-\s|—|–|#).*)?\s*\**\s*)$")]
    private static partial Regex HeaderPathPattern();

    private static string HeaderPath(string header)
    {
        var match = HeaderPathPattern().Match(header.Trim());
        return match.Success ? match.Groups["path"].Value.Trim().Trim('*') : string.Empty;
    }

    /// <summary>
    /// A safe path inside the project folder, or null. An agent that repeats the requested folder
    /// (D:\Temp\App\src\Program.cs) gets it stripped; any other absolute path or ".." is rejected.
    /// </summary>
    public static string? RelativePath(string path, string? requestedFolder)
    {
        var p = path.Replace('\\', '/');
        if (requestedFolder is not null)
        {
            var prefix = requestedFolder.Replace('\\', '/').TrimEnd('/') + "/";
            if (p.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
                p = p[prefix.Length..];
        }
        if (p.StartsWith('/') || DriveLetter().IsMatch(p)) return null;

        var parts = p.Split('/', StringSplitOptions.RemoveEmptyEntries).Where(s => s != ".").ToList();
        if (parts.Count == 0 || parts.Any(s => s == ".." || s.IndexOfAny(InvalidChars) >= 0 || s.EndsWith('.') || s.EndsWith(' ')))
            return null;
        return string.Join('/', parts);
    }

    private static readonly char[] InvalidChars = ['<', '>', ':', '"', '|', '?', '*', .. Enumerable.Range(0, 32).Select(i => (char)i)];

    [GeneratedRegex(@"^[A-Za-z]:")]
    private static partial Regex DriveLetter();

    // A quoted path may contain spaces; an unquoted one ends at whitespace
    [GeneratedRegex(@"[""'`](?<path>[A-Za-z]:[\\/][^""'`\r\n]*)[""'`]|(?<![\w\\/])(?<path>[A-Za-z]:[\\/][^\s""'`<>|?*,;]*)")]
    private static partial Regex WindowsPath();

    /// <summary>The first Windows folder path the request names, such as D:\Temp\MyApp; null when it names none.</summary>
    public static string? FindRequestedFolder(string requirement)
    {
        var match = WindowsPath().Match(requirement);
        if (!match.Success) return null;

        var path = match.Groups["path"].Value.TrimEnd('.', ')', ']', '}', ':', '!');
        path = path.TrimEnd('\\', '/');
        return path.Length == 2 ? path + "\\" : path;
    }

    /// <summary>A readable, unique folder name such as "todo-rest-api-authentication-1a2b3c4d".</summary>
    public static string FolderName(string requirement, Guid sessionId)
    {
        var words = Regex.Matches(WindowsPath().Replace(requirement, " "), "[A-Za-z0-9]+")
            .Select(m => m.Value.ToLowerInvariant())
            .Where(w => !StopWords.Contains(w) && !(w.Length == 1 && char.IsDigit(w[0])))
            .Take(4);
        var slug = string.Join('-', words);
        if (slug.Length > 40) slug = slug[..40].TrimEnd('-');
        return $"{(slug.Length > 0 ? slug : "project")}-{sessionId.ToString("N")[..8]}";
    }

    /// <summary>
    /// Where a host path lives for this process. In a container the host's drives are mounted under
    /// <paramref name="hostDrivesPath"/> (D:\Temp\App becomes /host/d/Temp/App); null when that drive isn't there.
    /// </summary>
    public static string? ToLocalPath(string hostPath, string hostDrivesPath)
    {
        var drive = Regex.Match(hostPath, @"^(?<letter>[A-Za-z]):[\\/]?(?<rest>.*)$");
        if (string.IsNullOrEmpty(hostDrivesPath))
            return drive.Success && !OperatingSystem.IsWindows() ? null : hostPath;
        if (!drive.Success) return null;

        var driveRoot = $"{hostDrivesPath.TrimEnd('/')}/{drive.Groups["letter"].Value.ToLowerInvariant()}";
        if (!Directory.Exists(driveRoot)) return null;

        var rest = drive.Groups["rest"].Value.Replace('\\', '/').Trim('/');
        // "/host/c/../../tmp" would leave the shared drives
        if (rest.Split('/').Contains("..")) return null;
        return rest.Length == 0 ? driveRoot : $"{driveRoot}/{rest}";
    }

    private static string JoinHost(string folder, string name)
    {
        var separator = folder.Contains('\\') || DriveLetter().IsMatch(folder) ? '\\' : '/';
        return folder.TrimEnd('\\', '/') + separator + name;
    }
}
