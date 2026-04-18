using Microsoft.AspNetCore.Mvc;
using Multibots.Api.Controllers;
using Multibots.Api.Models;
using Multibots.Api.Services;

namespace Multibots.Api.Tests;

public class PortfolioControllerTests
{
    [Fact]
    public async Task Simulate_ReturnsBadRequest_WhenAllocationDoesNotSumTo100()
    {
        var controller = new PortfolioController(new StubPythonEngineClient());
        var request = new PortfolioSimulationRequest
        {
            InitialCapital = 1000000m,
            Tickers = ["AAA", "BBB"],
            Allocation = new Dictionary<string, decimal>
            {
                ["AAA"] = 60m,
                ["BBB"] = 30m
            }
        };

        var result = await controller.Simulate(request, CancellationToken.None);

        var badRequest = Assert.IsType<BadRequestObjectResult>(result);
        Assert.Equal(400, badRequest.StatusCode);
    }

    [Fact]
    public async Task Simulate_ReturnsBadRequest_WhenAllocationMissingTicker()
    {
        var controller = new PortfolioController(new StubPythonEngineClient());
        var request = new PortfolioSimulationRequest
        {
            InitialCapital = 1000000m,
            Tickers = ["AAA", "BBB"],
            Allocation = new Dictionary<string, decimal>
            {
                ["AAA"] = 100m
            }
        };

        var result = await controller.Simulate(request, CancellationToken.None);

        var badRequest = Assert.IsType<BadRequestObjectResult>(result);
        Assert.Equal(400, badRequest.StatusCode);
    }

    private sealed class StubPythonEngineClient : IPythonEngineClient
    {
        public Task<AnalyzeResponse> AnalyzeAsync(AnalyzeRequest request, CancellationToken cancellationToken)
            => Task.FromResult(new AnalyzeResponse());

        public Task<PortfolioSimulationResponse> SimulatePortfolioAsync(PortfolioSimulationRequest request, CancellationToken cancellationToken)
            => Task.FromResult(new PortfolioSimulationResponse());
    }
}
