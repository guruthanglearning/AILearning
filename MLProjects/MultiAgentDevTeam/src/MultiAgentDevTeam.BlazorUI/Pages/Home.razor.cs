using MultiAgentDevTeam.BlazorUI.Models;

namespace MultiAgentDevTeam.BlazorUI.Pages;

public partial class Home : IDisposable
{
    private enum PageState { Idle, Streaming, Completed, Error }

    private PageState _state = PageState.Idle;
    private PipelineFormModel _form = new();
    private readonly List<string> _progressMessages = [];
    private Dictionary<string, string> _artifacts = [];
    private string? _errorMessage;
    private CancellationTokenSource? _cts;

    private async Task HandleSubmitAsync()
    {
        _state = PageState.Streaming;
        _progressMessages.Clear();
        _artifacts.Clear();
        _errorMessage = null;
        _cts = new CancellationTokenSource();

        var request = new PipelineRequest
        {
            Requirement = _form.Requirement,
            SkipAgents = _form.ParsedSkipAgents,
            MaxReviewLoops = _form.MaxReviewLoops
        };

        try
        {
            await foreach (var msg in PipelineClient.StreamAsync(request, _cts.Token))
            {
                _progressMessages.Add(msg);
                await InvokeAsync(StateHasChanged);
            }

            _state = PageState.Completed;
        }
        catch (OperationCanceledException)
        {
            _state = PageState.Idle;
        }
        catch (Exception ex)
        {
            _state = PageState.Error;
            _errorMessage = ex.Message;
        }
        finally
        {
            await InvokeAsync(StateHasChanged);
        }
    }

    internal void Reset()
    {
        _state = PageState.Idle;
        _form = new();
        _progressMessages.Clear();
        _artifacts.Clear();
        _errorMessage = null;
        _cts?.Cancel();
        _cts?.Dispose();
        _cts = null;
    }

    public void Dispose()
    {
        _cts?.Cancel();
        _cts?.Dispose();
    }
}
