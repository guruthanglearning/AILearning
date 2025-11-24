using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using System.Text.Json;
using System.Text;

namespace NanoGpt.Dashboard.Pages;

public class IndexModel : PageModel
{
    private readonly ILogger<IndexModel> _logger;
    private readonly IHttpClientFactory _httpClientFactory;

    public IndexModel(ILogger<IndexModel> logger, IHttpClientFactory httpClientFactory)
    {
        _logger = logger;
        _httpClientFactory = httpClientFactory;
    }

    [BindProperty]
    public string InputPrompt { get; set; } = "HAMLET:";
    
    [BindProperty]
    public int MaxTokens { get; set; } = 100;
    
    [BindProperty]
    public double Temperature { get; set; } = 0.7;

    public string? GeneratedText { get; set; }
    public bool ApiHealthy { get; set; }
    public string? HealthStatus { get; set; }
    public TimeSpan? ResponseTime { get; set; }
    public int? TokenCount { get; set; }
    public string? ErrorMessage { get; set; }

    public async Task OnGetAsync()
    {
        await CheckApiHealthAsync();
    }

    public async Task<IActionResult> OnPostGenerateAsync()
    {
        await CheckApiHealthAsync();
        
        if (!ApiHealthy)
        {
            ErrorMessage = "API is not available. Please ensure the NanoGPT API is running.";
            return Page();
        }

        try
        {
            var httpClient = _httpClientFactory.CreateClient("NanoGptApi");
            
            var requestBody = new
            {
                prompt = InputPrompt,
                maxTokens = MaxTokens,
                temperature = Temperature
            };

            var json = JsonSerializer.Serialize(requestBody, new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase
            });

            var content = new StringContent(json, Encoding.UTF8, "application/json");
            var startTime = DateTime.UtcNow;
            
            var response = await httpClient.PostAsync("api/generate", content);
            var endTime = DateTime.UtcNow;
            
            ResponseTime = endTime - startTime;

            if (response.IsSuccessStatusCode)
            {
                var responseJson = await response.Content.ReadAsStringAsync();
                var result = JsonSerializer.Deserialize<GenerateResponse>(responseJson, new JsonSerializerOptions
                {
                    PropertyNamingPolicy = JsonNamingPolicy.CamelCase
                });

                GeneratedText = result?.GeneratedText;
                TokenCount = result?.TokenCount;
                ErrorMessage = null;
            }
            else
            {
                ErrorMessage = $"API Error: {response.StatusCode} - {await response.Content.ReadAsStringAsync()}";
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error calling NanoGPT API");
            ErrorMessage = $"Error: {ex.Message}";
        }

        return Page();
    }

    private async Task CheckApiHealthAsync()
    {
        try
        {
            var httpClient = _httpClientFactory.CreateClient("NanoGptApi");
            var response = await httpClient.GetAsync("health");
            
            ApiHealthy = response.IsSuccessStatusCode;
            HealthStatus = ApiHealthy ? await response.Content.ReadAsStringAsync() : "Unhealthy";
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to check API health");
            ApiHealthy = false;
            HealthStatus = "Unavailable";
        }
    }

    public class GenerateResponse
    {
        public string? GeneratedText { get; set; }
        public int TokenCount { get; set; }
        public string? CompletionTime { get; set; }
    }
}
