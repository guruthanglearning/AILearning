using Microsoft.AspNetCore.Components;
using MultiAgentDevTeam.BlazorUI.Models;

namespace MultiAgentDevTeam.BlazorUI.Pages;

public partial class SessionDetail : ComponentBase
{
    [Parameter] public Guid SessionId { get; set; }

    private bool _loading = true;
    private SessionRecord? _session;

    protected override async Task OnParametersSetAsync()
    {
        _loading = true;
        _session = await SessionClient.GetAsync(SessionId);
        _loading = false;
    }
}
