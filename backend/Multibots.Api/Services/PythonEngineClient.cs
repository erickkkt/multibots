using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.Extensions.Caching.Memory;
using Multibots.Api.Models;

namespace Multibots.Api.Services;

public class PythonEngineClient(HttpClient httpClient, IMemoryCache cache) : IPythonEngineClient
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        PropertyNameCaseInsensitive = true,
        Converters = { new JsonStringEnumConverter() }
    };

    public async Task<AnalyzeResponse> AnalyzeAsync(AnalyzeRequest request, CancellationToken cancellationToken)
    {
        var cacheKey = BuildCacheKey(request);
        if (cache.TryGetValue(cacheKey, out AnalyzeResponse? cachedResponse) && cachedResponse is not null)
        {
            return cachedResponse;
        }

        var payload = JsonSerializer.Serialize(request, JsonOptions);
        using var content = new StringContent(payload, Encoding.UTF8, "application/json");
        using var response = await httpClient.PostAsync("/analyze", content, cancellationToken);
        response.EnsureSuccessStatusCode();

        var json = await response.Content.ReadAsStringAsync(cancellationToken);
        var analysis = JsonSerializer.Deserialize<AnalyzeResponse>(json, JsonOptions)
            ?? throw new InvalidOperationException("Python engine returned an invalid payload.");

        cache.Set(cacheKey, analysis, TimeSpan.FromSeconds(10));
        return analysis;
    }

    public async Task<PortfolioSimulationResponse> SimulatePortfolioAsync(
        PortfolioSimulationRequest request,
        CancellationToken cancellationToken)
    {
        var payload = JsonSerializer.Serialize(request, JsonOptions);
        using var content = new StringContent(payload, Encoding.UTF8, "application/json");
        using var response = await httpClient.PostAsync("/simulate", content, cancellationToken);
        response.EnsureSuccessStatusCode();

        var json = await response.Content.ReadAsStringAsync(cancellationToken);
        return JsonSerializer.Deserialize<PortfolioSimulationResponse>(json, JsonOptions)
            ?? throw new InvalidOperationException("Python engine returned an invalid simulation payload.");
    }

    private static string BuildCacheKey(AnalyzeRequest request)
    {
        var symbolToken = string.Join('|', request.Symbols.Select(x => x.Trim().ToUpperInvariant()));
        var p = request.Parameters;
        return $"analyze:{symbolToken}:{p.ShortMaPeriod}:{p.LongMaPeriod}:{p.RsiPeriod}:{p.VolumeLookback}:{p.Candles}";
    }
}
