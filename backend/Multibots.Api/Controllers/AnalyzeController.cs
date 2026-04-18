using Microsoft.AspNetCore.Mvc;
using Multibots.Api.Models;
using Multibots.Api.Services;

namespace Multibots.Api.Controllers;

[ApiController]
[Route("analyze")]
public class AnalyzeController(IPythonEngineClient pythonEngineClient) : ControllerBase
{
    [HttpPost]
    [ProducesResponseType(typeof(AnalyzeResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> Analyze([FromBody] AnalyzeRequest request, CancellationToken cancellationToken)
    {
        if (!ModelState.IsValid)
        {
            return BadRequest(ModelState);
        }

        if (request.Symbols.Any(string.IsNullOrWhiteSpace))
        {
            ModelState.AddModelError(nameof(request.Symbols), "Symbols cannot be empty.");
            return BadRequest(ModelState);
        }

        var normalized = request.Symbols
            .Select(symbol => symbol.Trim().ToUpperInvariant())
            .Distinct(StringComparer.Ordinal)
            .ToList();

        if (normalized.Count > 5)
        {
            ModelState.AddModelError(nameof(request.Symbols), "Maximum 5 symbols are supported.");
            return BadRequest(ModelState);
        }

        var response = await pythonEngineClient.AnalyzeAsync(
            new AnalyzeRequest { Symbols = normalized, Parameters = request.Parameters },
            cancellationToken);

        return Ok(response);
    }
}
