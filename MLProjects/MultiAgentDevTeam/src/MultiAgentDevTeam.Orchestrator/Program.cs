using Anthropic.SDK;
using Microsoft.AspNetCore.RateLimiting;
using Microsoft.Extensions.Options;
using Microsoft.OpenApi.Models;
using MultiAgentDevTeam.ArchitectAgent;
using MultiAgentDevTeam.DevOpsAgent;
using MultiAgentDevTeam.DeveloperAgent;
using MultiAgentDevTeam.DocsAgent;
using MultiAgentDevTeam.Orchestrator.Services;
using MultiAgentDevTeam.PMAgent;
using MultiAgentDevTeam.QAAgent;
using MultiAgentDevTeam.ReviewerAgent;
using MultiAgentDevTeam.SecurityAgent;
using MultiAgentDevTeam.Shared.Configuration;
using MultiAgentDevTeam.Shared.Interfaces;
using MultiAgentDevTeam.Shared.Models;
using System.Text.Json;
using System.Threading.RateLimiting;

var builder = WebApplication.CreateBuilder(args);

// Load secrets file if present (gitignored, never committed)
builder.Configuration.AddJsonFile("appsettings.secrets.json", optional: true, reloadOnChange: false);

// ── Configuration ──────────────────────────────────────────────────────────────
builder.Services.Configure<AgentConfiguration>(
    builder.Configuration.GetSection(AgentConfiguration.SectionName));

// ── Anthropic Client ───────────────────────────────────────────────────────────
var apiKey = builder.Configuration["AgentConfiguration:AnthropicApiKey"]
    ?? Environment.GetEnvironmentVariable("ANTHROPIC_API_KEY")
    ?? throw new InvalidOperationException("ANTHROPIC_API_KEY is required.");

builder.Services.AddSingleton(new AnthropicClient(apiKey));

// ── Register all agents as IAgent ─────────────────────────────────────────────
builder.Services.AddTransient<IAgent, PMAgent>();
builder.Services.AddTransient<IAgent, ArchitectAgent>();
builder.Services.AddTransient<IAgent, DeveloperAgent>();
builder.Services.AddTransient<IAgent, ReviewerAgent>();
builder.Services.AddTransient<IAgent, QAAgent>();
builder.Services.AddTransient<IAgent, SecurityAgent>();
builder.Services.AddTransient<IAgent, DevOpsAgent>();
builder.Services.AddTransient<IAgent, DocsAgent>();

// ── Orchestrator + Session Repository ─────────────────────────────────────────
builder.Services.AddSingleton<ISessionRepository, FileSessionRepository>();
builder.Services.AddTransient<IOrchestratorService, OrchestratorService>();

// ── Rate Limiting ──────────────────────────────────────────────────────────────
// RejectionStatusCode and OnRejected are set immediately; PermitLimit is deferred
// to IOptions<AgentConfiguration> so WebApplicationFactory config overrides work.
builder.Services.AddRateLimiter(options =>
{
    options.RejectionStatusCode = StatusCodes.Status429TooManyRequests;
    options.OnRejected = async (context, ct) =>
    {
        context.HttpContext.Response.ContentType = "application/json";
        await context.HttpContext.Response.WriteAsync(
            JsonSerializer.Serialize(new { error = "Too many requests. Please wait before submitting again." }), ct);
    };
});

// Deferred limiter configuration — reads RateLimitRequestsPerMinute from DI
// (after all configuration sources are finalized, including test in-memory overrides)
builder.Services.AddOptions<RateLimiterOptions>()
    .Configure<IOptions<AgentConfiguration>>((rateLimiterOptions, agentConfigOptions) =>
    {
        var requestsPerMinute = agentConfigOptions.Value.RateLimitRequestsPerMinute > 0
            ? agentConfigOptions.Value.RateLimitRequestsPerMinute : 10;
        rateLimiterOptions.AddFixedWindowLimiter("pipeline", limiterOptions =>
        {
            limiterOptions.Window = TimeSpan.FromMinutes(1);
            limiterOptions.PermitLimit = requestsPerMinute;
            limiterOptions.QueueLimit = 2;
            limiterOptions.QueueProcessingOrder = QueueProcessingOrder.OldestFirst;
        });
    });

// ── API / Swagger ──────────────────────────────────────────────────────────────
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new OpenApiInfo
    {
        Title = "Multi-Agent Dev Team API",
        Version = "v1",
        Description = "AI-powered engineering team orchestrator — submit a requirement, receive a complete software package."
    });
});

builder.Services.AddLogging(lb => lb.AddConsole().SetMinimumLevel(LogLevel.Information));

var app = builder.Build();

app.UseSwagger();
app.UseSwaggerUI(c =>
{
    c.SwaggerEndpoint("/swagger/v1/swagger.json", "Multi-Agent Dev Team API v1");
    c.RoutePrefix = string.Empty;
});

app.UseRateLimiter();

// ── Endpoints ──────────────────────────────────────────────────────────────────

// Health check
app.MapGet("/health", () => Results.Ok(new { status = "healthy", timestamp = DateTime.UtcNow }))
    .WithName("HealthCheck")
    .WithSummary("Returns service health status");

// Submit a requirement — full blocking pipeline
app.MapPost("/api/run", async (OrchestratorRequest request, IOrchestratorService orchestrator, CancellationToken ct) =>
{
    if (string.IsNullOrWhiteSpace(request.Requirement))
        return Results.BadRequest(new { error = "Requirement cannot be empty." });

    var result = await orchestrator.RunAsync(request, ct);
    return result.Success ? Results.Ok(result) : Results.Problem(result.ErrorMessage);
})
.WithName("RunPipeline")
.WithSummary("Submit a software requirement — returns all artifacts when pipeline completes")
.WithDescription("Runs the full pipeline: PM → Architect → Developer → Reviewer → QA + Security → DevOps → Docs")
.Produces<OrchestratorResponse>(200)
.ProducesProblem(400)
.ProducesProblem(500)
.RequireRateLimiting("pipeline");

// Submit a requirement — real-time streaming via Server-Sent Events
app.MapPost("/api/run/stream", async (OrchestratorRequest request, IOrchestratorService orchestrator, HttpResponse response, CancellationToken ct) =>
{
    if (string.IsNullOrWhiteSpace(request.Requirement))
    {
        response.StatusCode = 400;
        await response.WriteAsJsonAsync(new { error = "Requirement cannot be empty." }, ct);
        return;
    }

    response.Headers.ContentType = "text/event-stream";
    response.Headers.CacheControl = "no-cache";
    response.Headers.Connection = "keep-alive";

    await foreach (var message in orchestrator.StreamAsync(request, ct))
    {
        var payload = JsonSerializer.Serialize(new { message });
        await response.WriteAsync($"data: {payload}\n\n", ct);
        await response.Body.FlushAsync(ct);
    }
})
.WithName("StreamPipeline")
.WithSummary("Submit a requirement and receive real-time progress via Server-Sent Events")
.WithDescription("Streams pipeline progress as SSE events. Each event: data: {\"message\": \"...\"}")
.RequireRateLimiting("pipeline");

// Run only specific agents (skip others)
app.MapPost("/api/run/partial", async (OrchestratorRequest request, IOrchestratorService orchestrator, CancellationToken ct) =>
{
    if (string.IsNullOrWhiteSpace(request.Requirement))
        return Results.BadRequest(new { error = "Requirement cannot be empty." });

    var result = await orchestrator.RunAsync(request, ct);
    return result.Success ? Results.Ok(result) : Results.Problem(result.ErrorMessage);
})
.WithName("RunPartialPipeline")
.WithSummary("Run pipeline with specific agents skipped")
.Produces<OrchestratorResponse>(200)
.RequireRateLimiting("pipeline");

// Retrieve a past session by ID
app.MapGet("/api/sessions/{sessionId:guid}", async (Guid sessionId, ISessionRepository sessions, CancellationToken ct) =>
{
    var record = await sessions.GetAsync(sessionId, ct);
    return record is null
        ? Results.NotFound(new { error = $"Session {sessionId} not found." })
        : Results.Ok(record);
})
.WithName("GetSession")
.WithSummary("Retrieve a completed session by its ID");

// List recent sessions
app.MapGet("/api/sessions", async (ISessionRepository sessions, CancellationToken ct, int limit = 20) =>
{
    var list = await sessions.ListAsync(Math.Min(limit, 100), ct);
    return Results.Ok(list);
})
.WithName("ListSessions")
.WithSummary("List recent pipeline sessions (most recent first)");

app.Run();

// Required for WebApplicationFactory in integration tests
public partial class Program { }
