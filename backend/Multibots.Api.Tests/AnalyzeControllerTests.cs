using Microsoft.AspNetCore.Mvc;
using Multibots.Api.Controllers;
using Multibots.Api.Models;
using Multibots.Api.Services;

namespace Multibots.Api.Tests;

public class AnalyzeControllerTests
{
    [Fact]
    public async Task Analyze_ReturnsBadRequest_WhenSymbolCountExceedsLimit()
    {
        var controller = new AnalyzeController(new StubPythonEngineClient());
        var request = new AnalyzeRequest
        {
            Symbols = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"],
            Parameters = new AnalysisParameters()
        };

        var result = await controller.Analyze(request, CancellationToken.None);

        var badRequest = Assert.IsType<BadRequestObjectResult>(result);
        Assert.Equal(400, badRequest.StatusCode);
    }

    private sealed class StubPythonEngineClient : IPythonEngineClient
    {
        public Task<AnalyzeResponse> AnalyzeAsync(AnalyzeRequest request, CancellationToken cancellationToken)
        {
            return Task.FromResult(new AnalyzeResponse
            {
                GeneratedAtUtc = DateTime.UtcNow,
                Results =
                [
                    new SymbolSignal { Symbol = "AAA", Action = "hold", Confidence = 0.5 }
                ]
            });
        }
    }
}
