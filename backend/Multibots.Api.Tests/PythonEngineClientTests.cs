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

    [Fact]
    public async Task SimulatePortfolioAsync_ParsesSimulationPayload()
    {
        var handler = new SimulationHandler();
        var httpClient = new HttpClient(handler) { BaseAddress = new Uri("http://localhost:8000") };
        var cache = new MemoryCache(new MemoryCacheOptions());
        var client = new PythonEngineClient(httpClient, cache);

        var request = new PortfolioSimulationRequest
        {
            InitialCapital = 1000000m,
            Tickers = ["HPG"],
            Allocation = new Dictionary<string, decimal> { ["HPG"] = 100m }
        };

        var response = await client.SimulatePortfolioAsync(request, CancellationToken.None);

        Assert.Equal("Backtest", response.Mode);
        Assert.Equal(2, response.SettlementDays);
        Assert.True(response.EnableDividendSignalAdjustment);
        Assert.Single(response.EquityCurve);
        Assert.Equal(12500m, response.PnlByTicker["HPG"]);
        Assert.Equal(5000m, response.DividendByTicker["HPG"]);
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

    private sealed class SimulationHandler : HttpMessageHandler
    {
        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            var responseJson = """
            {
              "generatedAtUtc": "2026-01-01T00:00:00Z",
              "mode": "Backtest",
              "settlementDays": 2,
              "enableDividendSignalAdjustment": true,
              "equityCurve": [{ "timestamp": "2026-01-01", "totalValue": 1012500 }],
              "pnlByTicker": { "HPG": 12500 },
              "dividendByTicker": { "HPG": 5000 },
              "trades": [{ "symbol": "HPG", "entryDate": "2026-01-01", "exitDate": "2026-01-02", "entryPrice": 10, "exitPrice": 11, "quantity": 100, "grossPnl": 100, "netPnl": 99, "dividendIncome": 5, "exitReason": "SellSignal" }]
            }
            """;

            return Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(responseJson, Encoding.UTF8, "application/json")
            });
        }
    }
}
