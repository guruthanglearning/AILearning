using System.ComponentModel.DataAnnotations;

namespace MultiAgentDevTeam.BlazorUI.Models;

public class PipelineFormModel
{
    [Required(ErrorMessage = "Requirement is required.")]
    [MinLength(10, ErrorMessage = "Requirement must be at least 10 characters.")]
    public string Requirement { get; set; } = string.Empty;

    public string SkipAgents { get; set; } = string.Empty;

    [Range(1, 10, ErrorMessage = "Max review loops must be between 1 and 10.")]
    public int MaxReviewLoops { get; set; } = 3;

    public List<string> ParsedSkipAgents =>
        SkipAgents
            .Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
            .ToList();
}
