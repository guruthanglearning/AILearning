using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;

namespace MultiAgentDevTeam.Shared.Models;

/// <summary>What it takes to satisfy a requirement.</summary>
[JsonConverter(typeof(JsonStringEnumConverter<RequirementKind>))]
public enum RequirementKind
{
    /// <summary>Built into the generated source or config files.</summary>
    Code,
    /// <summary>Needs a test or check written for it.</summary>
    Test,
    /// <summary>Something done outside the generated files: write to a folder, run the app, deploy.</summary>
    Action
}

[JsonConverter(typeof(JsonStringEnumConverter<RequirementStatus>))]
public enum RequirementStatus
{
    Passed,
    Failed,
    /// <summary>Agents only produce files, so a person (or an executor) has to perform and confirm it.</summary>
    Manual,
    /// <summary>An agent claimed it, but nothing checked the claim (the Verifier was skipped).</summary>
    Unverified
}

/// <summary>One entry of the PM agent's machine-readable checklist.</summary>
public record RequirementItem
{
    public string Id { get; init; } = string.Empty;
    public string Text { get; init; } = string.Empty;
    public RequirementKind Kind { get; init; } = RequirementKind.Code;
    public string? Criterion { get; init; }
}

/// <summary>A line from an agent's "Requirement Coverage" section.</summary>
public record CoverageClaim(string RequirementId, string AgentName, string Evidence, bool NotApplicable);

/// <summary>One entry of the Verifier agent's verdicts.</summary>
public record VerificationEntry
{
    public string Id { get; init; } = string.Empty;
    public string? Text { get; init; }
    public RequirementKind? Kind { get; init; }
    public RequirementStatus Status { get; init; } = RequirementStatus.Failed;
    public string? Evidence { get; init; }
}

/// <summary>The final verdict for one requirement, as shown to the user.</summary>
public record RequirementResult
{
    public string Id { get; init; } = string.Empty;
    public string Text { get; init; } = string.Empty;
    public RequirementKind Kind { get; init; }
    public RequirementStatus Status { get; init; }
    public List<string> CoveredBy { get; init; } = new();
    public string? Evidence { get; init; }

    /// <summary>"Product Manager" for checklist items, or the Verifier for requirements the PM dropped.</summary>
    public string Source { get; init; } = string.Empty;
}

/// <summary>
/// Parses the requirement checklist, the agents' coverage sections and the Verifier's verdicts,
/// and combines them into one result per requirement.
/// </summary>
public static class RequirementTracking
{
    public const string ChecklistFence = "requirements-checklist";
    public const string VerificationFence = "verification-results";
    public const string CoverageHeading = "Requirement Coverage";

    /// <summary>Appended to the system prompt of every agent that has to report coverage.</summary>
    public const string CoverageGuidance = """


        ## Requirement coverage
        Your context includes the requirement checklist: a `requirements-checklist` JSON block at the end
        of the Requirements, or a RequirementChecklist entry. End your output with this section, with one
        line for every id in the checklist:

        ## Requirement Coverage
        - FR-1: <the file, test or config in your output that satisfies it>
        - FR-2: N/A - <why your output doesn't cover it, e.g. "a test, written by QA">

        Only claim a requirement your output actually satisfies; a claim without a matching file is a defect.
        """;

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
        AllowTrailingCommas = true,
        ReadCommentHandling = JsonCommentHandling.Skip
    };

    private static readonly Regex CoverageHeadingLine = new(
        @"^#{1,4}\s*\**\s*Requirement Coverage\b.*$", RegexOptions.Multiline | RegexOptions.IgnoreCase | RegexOptions.Compiled);

    private static readonly Regex AnyHeadingLine = new(@"^#{1,4}\s", RegexOptions.Compiled);

    // "- FR-1: evidence", "* **NFR-2** — evidence", "- FR-3 - N/A: reason"
    private static readonly Regex CoverageLine = new(
        @"^\s*[-*]\s*\**\s*([A-Za-z]+-\d+)\s*\**\s*[:\-–—]\s*(.*)$", RegexOptions.Compiled);

    private static readonly Regex NotApplicable = new(
        @"^\**\s*(N/?A|not applicable|not covered|none)\b", RegexOptions.IgnoreCase | RegexOptions.Compiled);

    /// <summary>The PM's checklist, or null when the block is missing or not valid JSON.</summary>
    public static List<RequirementItem>? ParseChecklist(string requirements) =>
        ParseFencedJson<RequirementItem>(requirements, ChecklistFence)
            ?.Where(i => !string.IsNullOrWhiteSpace(i.Id))
            .DistinctBy(i => i.Id, StringComparer.OrdinalIgnoreCase)
            .ToList();

    /// <summary>The Verifier's verdicts, or null when the block is missing or not valid JSON.</summary>
    public static List<VerificationEntry>? ParseVerification(string report) =>
        ParseFencedJson<VerificationEntry>(report, VerificationFence)
            ?.Where(v => !string.IsNullOrWhiteSpace(v.Id))
            .ToList();

    /// <summary>The claims in the last "Requirement Coverage" section of an agent's output.</summary>
    public static List<CoverageClaim> ParseCoverage(string content, string agentName)
    {
        var claims = new List<CoverageClaim>();
        var headings = CoverageHeadingLine.Matches(content);
        if (headings.Count == 0) return claims;

        var section = content[(headings[^1].Index + headings[^1].Length)..];
        foreach (var rawLine in section.Split('\n'))
        {
            var line = rawLine.TrimEnd('\r');
            if (AnyHeadingLine.IsMatch(line)) break;

            var match = CoverageLine.Match(line);
            if (!match.Success) continue;

            var evidence = match.Groups[2].Value.Trim();
            claims.Add(new CoverageClaim(
                match.Groups[1].Value.ToUpperInvariant(), agentName, evidence,
                evidence.Length == 0 || NotApplicable.IsMatch(evidence)));
        }
        return claims;
    }

    /// <summary>Checklist items of <paramref name="kind"/> that no agent claimed.</summary>
    public static List<RequirementItem> Uncovered(
        IEnumerable<RequirementItem> checklist, IEnumerable<CoverageClaim> claims, RequirementKind kind)
    {
        var claimed = claims.Where(c => !c.NotApplicable)
            .Select(c => c.RequirementId)
            .ToHashSet(StringComparer.OrdinalIgnoreCase);
        return checklist.Where(i => i.Kind == kind && !claimed.Contains(i.Id)).ToList();
    }

    /// <summary>
    /// One result per checklist item, plus any requirement the Verifier found in the original request
    /// that the checklist left out.
    /// </summary>
    public static List<RequirementResult> Evaluate(
        IReadOnlyList<RequirementItem> checklist,
        IReadOnlyList<CoverageClaim> claims,
        IReadOnlyList<VerificationEntry>? verification,
        string checklistSource = "Product Manager",
        string verifierSource = "Verifier")
    {
        var verdicts = (verification ?? [])
            .GroupBy(v => v.Id, StringComparer.OrdinalIgnoreCase)
            .ToDictionary(g => g.Key, g => g.First(), StringComparer.OrdinalIgnoreCase);
        var results = new List<RequirementResult>();

        foreach (var item in checklist)
        {
            var coveredBy = claims
                .Where(c => !c.NotApplicable && string.Equals(c.RequirementId, item.Id, StringComparison.OrdinalIgnoreCase))
                .Select(c => c.AgentName)
                .Distinct()
                .ToList();
            verdicts.TryGetValue(item.Id, out var verdict);

            var (status, evidence) = item.Kind switch
            {
                // Generated files can't prove a folder was written or an app was run, so a pass
                // from the Verifier is downgraded; a failure still stands
                RequirementKind.Action => verdict?.Status == RequirementStatus.Failed
                    ? (RequirementStatus.Failed, verdict.Evidence)
                    : (RequirementStatus.Manual, verdict?.Evidence ?? "Agents only produce files; perform and confirm this step yourself."),
                _ when coveredBy.Count == 0 =>
                    (RequirementStatus.Failed, JoinEvidence("No agent reported covering it.", verdict?.Evidence)),
                _ when verdict is not null => (verdict.Status, verdict.Evidence),
                _ => (RequirementStatus.Unverified, ClaimEvidence(claims, item.Id))
            };

            results.Add(new RequirementResult
            {
                Id = item.Id,
                Text = item.Text,
                Kind = item.Kind,
                Status = status,
                CoveredBy = coveredBy,
                Evidence = evidence,
                Source = checklistSource
            });
        }

        var known = checklist.Select(i => i.Id).ToHashSet(StringComparer.OrdinalIgnoreCase);
        foreach (var verdict in verdicts.Values.Where(v => !known.Contains(v.Id)))
        {
            var kind = verdict.Kind ?? RequirementKind.Code;
            results.Add(new RequirementResult
            {
                Id = verdict.Id,
                Text = verdict.Text ?? verdict.Id,
                Kind = kind,
                Status = kind == RequirementKind.Action && verdict.Status == RequirementStatus.Passed
                    ? RequirementStatus.Manual
                    : verdict.Status,
                Evidence = verdict.Evidence,
                Source = verifierSource
            });
        }

        return results;
    }

    /// <summary>A compact JSON copy of the checklist, for agents that don't receive the full Requirements.</summary>
    public static string ToJson(IEnumerable<RequirementItem> checklist) =>
        JsonSerializer.Serialize(checklist, new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
            DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
        });

    public static string StatusIcon(RequirementStatus status) => status switch
    {
        RequirementStatus.Passed => "✅",
        RequirementStatus.Failed => "❌",
        RequirementStatus.Manual => "🖐️",
        _ => "❔"
    };

    private static string? ClaimEvidence(IEnumerable<CoverageClaim> claims, string id)
    {
        var evidence = claims
            .Where(c => !c.NotApplicable && string.Equals(c.RequirementId, id, StringComparison.OrdinalIgnoreCase))
            .Select(c => $"{c.AgentName}: {c.Evidence}")
            .ToList();
        return evidence.Count == 0 ? null : string.Join("; ", evidence);
    }

    private static string JoinEvidence(string first, string? second) =>
        string.IsNullOrWhiteSpace(second) ? first : $"{first} {second}";

    private static List<T>? ParseFencedJson<T>(string content, string fence)
    {
        if (string.IsNullOrWhiteSpace(content)) return null;

        var matches = Regex.Matches(content, $@"```[ \t]*{Regex.Escape(fence)}[^\n]*\n(.*?)```", RegexOptions.Singleline);
        if (matches.Count == 0) return null;

        try
        {
            return JsonSerializer.Deserialize<List<T>>(matches[^1].Groups[1].Value, JsonOptions);
        }
        catch (JsonException)
        {
            return null;
        }
    }
}
