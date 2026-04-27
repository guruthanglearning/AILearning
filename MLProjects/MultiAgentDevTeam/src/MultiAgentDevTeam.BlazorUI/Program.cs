using MultiAgentDevTeam.BlazorUI.Components;
using MultiAgentDevTeam.BlazorUI.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();

var orchestratorBaseUrl = builder.Configuration["OrchestratorApi:BaseUrl"] ?? "http://localhost:5000";

builder.Services.AddHttpClient<IPipelineClient, PipelineClient>(client =>
{
    client.BaseAddress = new Uri(orchestratorBaseUrl);
    client.Timeout = TimeSpan.FromMinutes(30);
});

builder.Services.AddHttpClient<ISessionApiClient, SessionApiClient>(client =>
{
    client.BaseAddress = new Uri(orchestratorBaseUrl);
    client.Timeout = TimeSpan.FromSeconds(30);
});

builder.Services.AddLogging(lb => lb.AddConsole().SetMinimumLevel(LogLevel.Information));

var app = builder.Build();

if (!app.Environment.IsDevelopment())
    app.UseExceptionHandler("/Error");

app.UseStaticFiles();
app.UseAntiforgery();

app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

app.Run();

public partial class Program { }
