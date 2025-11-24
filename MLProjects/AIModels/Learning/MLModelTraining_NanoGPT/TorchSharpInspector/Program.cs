using Microsoft.AspNetCore.Mvc;
using Serilog;

var builder = WebApplication.CreateBuilder(args);

// Configure Serilog
Log.Logger = new LoggerConfiguration()
    .WriteTo.Console()
    .WriteTo.File("logs/torchsharp-inspector-.txt", rollingInterval: RollingInterval.Day)
    .CreateLogger();

builder.Host.UseSerilog();

// Add services to the container
builder.Services.AddControllersWithViews();

// Register our services
builder.Services.AddScoped<TorchSharpInspector.Services.ISystemDiagnosticsService, TorchSharpInspector.Services.SystemDiagnosticsService>();

// Configure API documentation
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new Microsoft.OpenApi.Models.OpenApiInfo
    {
        Title = "TorchSharp Inspector API",
        Version = "v1",
        Description = "Comprehensive model analysis and diagnostic tools for TorchSharp models"
    });
});

// Add health checks
builder.Services.AddHealthChecks()
    .AddCheck("self", () => Microsoft.Extensions.Diagnostics.HealthChecks.HealthCheckResult.Healthy("Application is running"));

var app = builder.Build();

// Ensure directories exist
Directory.CreateDirectory("./models");
Directory.CreateDirectory("./reports");
Directory.CreateDirectory("./logs");

// Configure the HTTP request pipeline
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Home/Error");
    app.UseHsts();
}
else
{
    app.UseDeveloperExceptionPage();
}

app.UseStaticFiles();
app.UseRouting();

// Health checks
app.MapHealthChecks("/health");
app.MapHealthChecks("/api/health");

// Enable Swagger
app.UseSwagger();
app.UseSwaggerUI(c =>
{
    c.SwaggerEndpoint("/swagger/v1/swagger.json", "TorchSharp Inspector API v1");
    c.RoutePrefix = "api-docs";
});

app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Home}/{action=Index}/{id?}");

// Simple API endpoints
app.MapGet("/api/version", () => Results.Ok(new 
{ 
    Version = "1.0.0", 
    Environment = app.Environment.EnvironmentName,
    Timestamp = DateTime.UtcNow
}));

try
{
    Log.Information("Starting TorchSharp Inspector Web Application");
    Console.WriteLine("🚀 TorchSharp Inspector is starting...");
    Console.WriteLine("📊 Web Interface: http://localhost:5000");
    Console.WriteLine("📋 API Documentation: http://localhost:5000/api-docs");
    Console.WriteLine("🏥 Health Check: http://localhost:5000/health");
    app.Run();
}
catch (Exception ex)
{
    Log.Fatal(ex, "Application terminated unexpectedly");
}
finally
{
    Log.CloseAndFlush();
}