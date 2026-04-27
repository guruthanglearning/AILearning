using Microsoft.AspNetCore.Components;
using MultiAgentDevTeam.BlazorUI.Models;

namespace MultiAgentDevTeam.BlazorUI.Pages;

public partial class Sessions : ComponentBase
{
    private bool _loading = true;
    private List<SessionSummary> _sessions = [];

    protected override async Task OnInitializedAsync()
    {
        _sessions = (await SessionClient.ListAsync()).ToList();
        _loading = false;
    }
}
