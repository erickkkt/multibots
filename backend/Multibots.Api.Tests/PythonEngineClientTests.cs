using System.Net;
using System.Text;
using Microsoft.Extensions.Caching.Memory;
using Multibots.Api.Models;
using Multibots.Api.Services;

namespace Multibots.Api.Tests;

public class PythonEngineClientTests
{
    [Fact]
    public async Task AnalyzeAsync_UsesCache_ForIdenticalRequest()
    {
        var handler = new CountingHandler();
        var httpClient = new HttpClient(handler) { BaseAddress = new Uri("http://localhost:8000") };
        var cache = new MemoryCache(new MemoryCacheOptions());
        var client = new PythonEngineClient(httpClient, cache);

        var request = new AnalyzeRequest
        {
            Symbols = ["HPG"],
            Parameters = new AnalysisParameters()
        };

        var first = await client.AnalyzeAsync(request, CancellationToken.None);
        var second = await client.AnalyzeAsync(request, CancellationToken.None);

        Assert.Single(first.Results);
        Assert.Equal("buy", first.Results[0].Action);
        Assert.Equal(1, handler.CallCount);
        Assert.Equal(first.GeneratedAtUtc, second.GeneratedAtUtc);
    }

    private sealed class CountingHandler : HttpMessageHandler
    {
        public int CallCount { get; private set; }

        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            CallCount++;
            var responseJson = """
            {
              "generatedAtUtc": "2026-01-01T00:00:00Z",
              "results": [{ "symbol": "HPG", "action": "buy", "confidence": 0.8, "reasons": ["ma"] }]
            }
            """;

            return Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(responseJson, Encoding.UTF8, "application/json")
            });
        }
    }
}
