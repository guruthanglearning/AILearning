using FluentAssertions;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.Options;
using MultiAgentDevTeam.Orchestrator.Services;
using MultiAgentDevTeam.Shared.Configuration;
using MultiAgentDevTeam.Shared.Models;
using Xunit;

namespace MultiAgentDevTeam.UnitTests.Services;

/// <summary>Writing the agents' files to the requested folder, or a new one under the default root.</summary>
public sealed class ProjectWriterTests : IDisposable
{
    private static readonly Guid SessionId = Guid.Parse("1a2b3c4d-0000-0000-0000-000000000000");

    private const string Code = """
        # Project
        ### File: src/App/Program.cs
        ```csharp
        Console.WriteLine("Hello, World!");
        ```

        ### File: `src/App/App.csproj`

        ```xml
        <Project Sdk="Microsoft.NET.Sdk" />
        ```
        """;

    private const string Tests = """
        ### File: tests/App.Tests/ProgramTests.cs
        ```csharp
        public class ProgramTests { }
        ```
        """;

    private readonly string _temp = Path.Combine(Path.GetTempPath(), "pw-tests-" + Guid.NewGuid().ToString("N"));

    public ProjectWriterTests() => Directory.CreateDirectory(_temp);

    public void Dispose()
    {
        if (Directory.Exists(_temp)) Directory.Delete(_temp, recursive: true);
    }

    private ProjectWriter Writer(Action<ProjectOutputOptions>? configure = null)
    {
        var options = new ProjectOutputOptions { DefaultRoot = _temp };
        configure?.Invoke(options);
        return new ProjectWriter(Options.Create(new AgentConfiguration { ProjectOutput = options }),
            NullLogger<ProjectWriter>.Instance);
    }

    private static Dictionary<ArtifactType, string> Artifacts(string code = Code) => new()
    {
        [ArtifactType.Requirements] = "# Requirements",
        [ArtifactType.SourceCode] = code,
        [ArtifactType.TestResults] = Tests,
        [ArtifactType.Documentation] = "# README"
    };

    // ── WriteAsync ─────────────────────────────────────────────────────────────

    [Fact]
    public async Task WriteAsync_RequestedFolder_WritesCodeTestsAndDocs()
    {
        var folder = Path.Combine(_temp, "Hello World");

        var result = await Writer().WriteAsync($"Create it under \"{folder}\" please", SessionId, Artifacts());

        result.Written.Should().BeTrue();
        result.Folder.Should().Be(folder);
        result.RequestedFolder.Should().Be(folder);
        result.Files.Should().BeEquivalentTo(
            "src/App/Program.cs", "src/App/App.csproj", "tests/App.Tests/ProgramTests.cs",
            "docs/Requirements.md", "docs/Documentation.md");
        result.Message.Should().Be($"📁 Wrote 5 files to {folder}");
        File.ReadAllText(Path.Combine(folder, "src", "App", "Program.cs")).Should().Be("Console.WriteLine(\"Hello, World!\");\n");
        File.ReadAllText(Path.Combine(folder, "docs", "Documentation.md")).Should().Be("# README");
    }

    [Fact]
    public async Task WriteAsync_NoFolderInRequest_CreatesOneUnderTheDefaultRoot()
    {
        var result = await Writer().WriteAsync("Build a TODO REST API with authentication", SessionId, Artifacts());

        result.Folder.Should().Be(Path.Combine(_temp, "todo-rest-api-authentication-1a2b3c4d"));
        result.RequestedFolder.Should().BeNull();
        File.Exists(Path.Combine(result.Folder!, "src", "App", "Program.cs")).Should().BeTrue();
    }

    [Fact]
    public async Task WriteAsync_FolderAlreadyHasFiles_WritesIntoANewSubfolderAndLeavesThemAlone()
    {
        var folder = Path.Combine(_temp, "Existing");
        Directory.CreateDirectory(folder);
        File.WriteAllText(Path.Combine(folder, "notes.txt"), "mine");

        var result = await Writer().WriteAsync($"Hello World in {folder}", SessionId, Artifacts());

        result.Folder.Should().Be(Path.Combine(folder, "hello-world-1a2b3c4d"));
        File.ReadAllText(Path.Combine(folder, "notes.txt")).Should().Be("mine");
        File.Exists(Path.Combine(result.Folder!, "src", "App", "Program.cs")).Should().BeTrue();
    }

    [Fact]
    public async Task WriteAsync_EmptyExistingFolder_IsUsedDirectly()
    {
        var folder = Path.Combine(_temp, "Empty");
        Directory.CreateDirectory(folder);

        var result = await Writer().WriteAsync($"Hello World in {folder}", SessionId, Artifacts());

        result.Folder.Should().Be(folder);
    }

    [Fact]
    public async Task WriteAsync_NoCodeFiles_WritesNothing()
    {
        var folder = Path.Combine(_temp, "Nothing");

        var result = await Writer().WriteAsync($"Hello World in {folder}", SessionId,
            new Dictionary<ArtifactType, string> { [ArtifactType.SourceCode] = "no files here", [ArtifactType.Documentation] = "# README" });

        result.Written.Should().BeFalse();
        result.RequestedFolder.Should().Be(folder);
        result.Message.Should().Contain("no files to write");
        Directory.Exists(folder).Should().BeFalse();
    }

    [Fact]
    public async Task WriteAsync_Disabled_WritesNothing()
    {
        var result = await Writer(o => o.Enabled = false).WriteAsync("Hello World", SessionId, Artifacts());

        result.Written.Should().BeFalse();
        result.Message.Should().Contain("turned off");
        Directory.EnumerateFileSystemEntries(_temp).Should().BeEmpty();
    }

    [Fact]
    public async Task WriteAsync_SkipsFilesThatWouldLandOutsideTheFolder()
    {
        var code = Code + """

            ### File: ../escape.cs
            ```csharp
            bad
            ```

            ### File: C:\Windows\evil.cs
            ```csharp
            bad
            ```
            """;

        var result = await Writer().WriteAsync("Hello World", SessionId, Artifacts(code));

        result.Files.Should().NotContain(f => f.Contains("escape") || f.Contains("evil"));
        File.Exists(Path.Combine(_temp, "escape.cs")).Should().BeFalse();
    }

    [Fact]
    public async Task WriteAsync_InContainer_MapsTheHostDriveAndReportsTheHostPath()
    {
        var drives = Path.Combine(_temp, "host");
        Directory.CreateDirectory(Path.Combine(drives, "d"));

        var result = await Writer(o => o.HostDrivesPath = drives.Replace('\\', '/'))
            .WriteAsync(@"Create the project under D:\Temp\App", SessionId, Artifacts());

        result.Folder.Should().Be(@"D:\Temp\App");
        File.Exists(Path.Combine(drives, "d", "Temp", "App", "src", "App", "Program.cs")).Should().BeTrue();
    }

    [Fact]
    public async Task WriteAsync_DriveNotShared_ReportsWhy()
    {
        var result = await Writer(o => o.HostDrivesPath = _temp.Replace('\\', '/'))
            .WriteAsync(@"Create the project under E:\Apps\Hello", SessionId, Artifacts());

        result.Written.Should().BeFalse();
        result.Message.Should().Be(@"⚠️ Could not write the project files: the service can't reach E:\Apps\Hello. Only drives shared with it can be written to");
    }

    [Fact]
    public async Task WriteAsync_TargetIsAFile_ReportsTheErrorInsteadOfThrowing()
    {
        var blocked = Path.Combine(_temp, "blocked");
        File.WriteAllText(blocked, "a file, not a folder");

        var result = await Writer().WriteAsync($"Hello World in {blocked}", SessionId, Artifacts());

        result.Written.Should().BeFalse();
        result.Message.Should().StartWith("⚠️ Could not write the project files:");
    }

    [Theory]
    [InlineData(@"Create it under C:\..\..\tmp\payload")]
    [InlineData(@"Create it under D:\Temp\App\..\..\Windows")]
    public async Task WriteAsync_RequestedFolderWithParentSegments_IsRefused(string requirement)
    {
        var drives = Path.Combine(_temp, "host");
        Directory.CreateDirectory(Path.Combine(drives, "c"));
        Directory.CreateDirectory(Path.Combine(drives, "d"));

        var result = await Writer(o => o.HostDrivesPath = drives.Replace('\\', '/'))
            .WriteAsync(requirement, SessionId, Artifacts());

        result.Written.Should().BeFalse();
        result.Message.Should().Contain("uses \"..\"");
        Directory.EnumerateFiles(_temp, "*", SearchOption.AllDirectories).Should().BeEmpty();
    }

    [Fact]
    public async Task WriteAsync_SubfolderAlsoTaken_PicksTheNextFreeName()
    {
        var folder = Path.Combine(_temp, "Existing");
        Directory.CreateDirectory(Path.Combine(folder, "hello-world-1a2b3c4d"));
        File.WriteAllText(Path.Combine(folder, "hello-world-1a2b3c4d", "keep.txt"), "mine");

        var result = await Writer().WriteAsync($"Hello World in {folder}", SessionId, Artifacts());

        result.Folder.Should().Be(Path.Combine(folder, "hello-world-1a2b3c4d-2"));
        File.ReadAllText(Path.Combine(folder, "hello-world-1a2b3c4d", "keep.txt")).Should().Be("mine");
    }

    [Fact]
    public async Task WriteAsync_TwoRunsToTheSameEmptyFolder_GetSeparateFolders()
    {
        var folder = Path.Combine(_temp, "Shared");
        var writer = Writer();

        var results = await Task.WhenAll(
            writer.WriteAsync($"Hello World in {folder}", SessionId, Artifacts()),
            writer.WriteAsync($"Hello World in {folder}", Guid.Parse("9f8e7d6c-0000-0000-0000-000000000000"), Artifacts()));

        results.Should().OnlyContain(r => r.Written);
        results.Select(r => r.Folder).Should().OnlyHaveUniqueItems();
        results.Should().OnlyContain(r => File.Exists(Path.Combine(r.Folder!, "src", "App", "Program.cs")));
    }

    // ── Parsing ────────────────────────────────────────────────────────────────

    [Fact]
    public void ParseFiles_ReadsPathAndContent()
    {
        ProjectWriter.ParseFiles(Code).Should().Equal(
            new ProjectFile("src/App/Program.cs", "Console.WriteLine(\"Hello, World!\");\n"),
            new ProjectFile("src/App/App.csproj", "<Project Sdk=\"Microsoft.NET.Sdk\" />\n"));
    }

    [Fact]
    public void ParseFiles_LongerFenceKeepsInnerFences()
    {
        var readme = "### File: README.md\n````markdown\n# App\n```bash\ndotnet run\n```\n````\n";

        ProjectWriter.ParseFiles(readme).Single().Content.Should().Be("# App\n```bash\ndotnet run\n```\n");
    }

    [Fact]
    public void ParseFiles_HandlesCrlfAndTrailingNotes()
    {
        var text = "## File: src/A.cs (updated)\r\n```csharp\r\nclass A {}\r\n```\r\n";

        ProjectWriter.ParseFiles(text).Should().Equal(new ProjectFile("src/A.cs", "class A {}\n"));
    }

    [Theory]
    [InlineData("`src/My App/Program.cs`", "src/My App/Program.cs")]
    [InlineData("\"src/My App/Program.cs\" (new)", "src/My App/Program.cs")]
    [InlineData("**`src/A.cs`**", "src/A.cs")]
    [InlineData("**src/A.cs**", "src/A.cs")]
    [InlineData("src/My App/Program.cs", "src/My App/Program.cs")]
    [InlineData("src/A.cs - entry point", "src/A.cs")]
    [InlineData("src/A.cs — entry point", "src/A.cs")]
    [InlineData("src/my-app/A.cs", "src/my-app/A.cs")]
    [InlineData("`src/John's/Program.cs`", "src/John's/Program.cs")]
    [InlineData("\"src/John's App/Program.cs\"", "src/John's App/Program.cs")]
    [InlineData("'src/A.cs' (new)", "src/A.cs")]
    public void ParseFiles_KeepsTheWholePathAndDropsNotes(string header, string expected)
    {
        ProjectWriter.ParseFiles($"### File: {header}\n```\nx\n```\n").Single().Path.Should().Be(expected);
    }

    [Fact]
    public void ParseFiles_HeaderWithoutCodeBlock_IsIgnored()
    {
        ProjectWriter.ParseFiles("### File: src/A.cs\nno code here").Should().BeEmpty();
    }

    [Fact]
    public void CollectFiles_LaterArtifactWinsForTheSamePath()
    {
        var artifacts = new Dictionary<ArtifactType, string>
        {
            [ArtifactType.SourceCode] = "### File: README.md\n```\ndev\n```",
            [ArtifactType.DeploymentConfig] = "### File: README.md\n```\ndevops\n```"
        };

        ProjectWriter.CollectFiles(artifacts, null).Single().Content.Should().Be("devops\n");
    }

    [Theory]
    [InlineData(@"src\App\Program.cs", null, "src/App/Program.cs")]
    [InlineData("./src//App.cs", null, "src/App.cs")]
    [InlineData(@"D:\Temp\App\src\Program.cs", @"D:\Temp\App", "src/Program.cs")]
    [InlineData("d:/temp/app/src/Program.cs", @"D:\Temp\App", "src/Program.cs")]
    [InlineData(@"D:\Other\Program.cs", @"D:\Temp\App", null)]
    [InlineData("/etc/passwd", null, null)]
    [InlineData("../outside.cs", null, null)]
    [InlineData("src/../../outside.cs", null, null)]
    [InlineData("src/bad|name.cs", null, null)]
    [InlineData("src/trailingdot.", null, null)]
    [InlineData("", null, null)]
    public void RelativePath_KeepsPathsInsideTheProject(string path, string? requested, string? expected)
    {
        ProjectWriter.RelativePath(path, requested).Should().Be(expected);
    }

    [Theory]
    [InlineData(@"2.) Create the project under this location D:\Temp\MultiAgentDevTeam_Test 3.) run it", @"D:\Temp\MultiAgentDevTeam_Test")]
    [InlineData(@"Put it in C:\Projects\Hello.", @"C:\Projects\Hello")]
    [InlineData(@"Put it in (C:\Projects\Hello)", @"C:\Projects\Hello")]
    [InlineData("Put it in \"C:\\My Projects\\Hello App\"", @"C:\My Projects\Hello App")]
    [InlineData("Put it in `D:/Work/App/`", "D:/Work/App")]
    [InlineData(@"Save it to D:\", @"D:\")]
    [InlineData("Build a TODO API", null)]
    [InlineData("Use the http://example.com API", null)]
    public void FindRequestedFolder_ReadsTheFirstWindowsPath(string requirement, string? expected)
    {
        ProjectWriter.FindRequestedFolder(requirement).Should().Be(expected);
    }

    [Theory]
    [InlineData("Perform the following. 1.) Create Hello world application using C#", "hello-world-application-c-1a2b3c4d")]
    [InlineData(@"Create it under D:\Temp\X", "project-1a2b3c4d")]
    [InlineData("!!!", "project-1a2b3c4d")]
    [InlineData("Supercalifragilisticexpialidocious extraordinarily longwinded", "supercalifragilisticexpialidocious-extra-1a2b3c4d")]
    public void FolderName_IsReadableAndUnique(string requirement, string expected)
    {
        ProjectWriter.FolderName(requirement, SessionId).Should().Be(expected);
    }

    [Fact]
    public void ToLocalPath_WithoutDriveMapping_UsesThePathAsIs()
    {
        var path = Path.Combine(_temp, "App");

        ProjectWriter.ToLocalPath(path, "").Should().Be(path);
    }

    [Fact]
    public void ToLocalPath_WithDriveMapping_TranslatesDriveLetters()
    {
        var drives = _temp.Replace('\\', '/');
        Directory.CreateDirectory(Path.Combine(_temp, "c"));

        ProjectWriter.ToLocalPath(@"C:\Temp\App\", drives).Should().Be($"{drives}/c/Temp/App");
        ProjectWriter.ToLocalPath(@"c:\", drives).Should().Be($"{drives}/c");
        ProjectWriter.ToLocalPath(@"D:\Temp", drives).Should().BeNull();
        ProjectWriter.ToLocalPath("relative/path", drives).Should().BeNull();
        ProjectWriter.ToLocalPath(@"C:\..\..\tmp", drives).Should().BeNull();
    }
}
