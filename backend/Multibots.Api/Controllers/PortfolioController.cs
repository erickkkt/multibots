using Microsoft.AspNetCore.Mvc;
using Multibots.Api.Models;
using Multibots.Api.Services;

namespace Multibots.Api.Controllers;

[ApiController]
[Route("api/portfolio")]
public class PortfolioController(IPythonEngineClient pythonEngineClient) : ControllerBase
{
    [HttpPost("simulate")]
    [ProducesResponseType(typeof(PortfolioSimulationResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> Simulate([FromBody] PortfolioSimulationRequest request, CancellationToken cancellationToken)
    {
        if (!ModelState.IsValid)
        {
            return BadRequest(ModelState);
        }

        if (request.DateRange?.StartDate is not null && request.DateRange?.EndDate is not null
            && request.DateRange.StartDate > request.DateRange.EndDate)
        {
            ModelState.AddModelError(nameof(request.DateRange), "dateRange.startDate must be <= dateRange.endDate.");
            return BadRequest(ModelState);
        }

        if (request.Tickers.Any(string.IsNullOrWhiteSpace))
        {
            ModelState.AddModelError(nameof(request.Tickers), "Tickers cannot be empty.");
            return BadRequest(ModelState);
        }

        var normalizedTickers = request.Tickers
            .Select(ticker => ticker.Trim().ToUpperInvariant())
            .Distinct(StringComparer.Ordinal)
            .ToList();

        if (normalizedTickers.Count != request.Tickers.Count)
        {
            ModelState.AddModelError(nameof(request.Tickers), "Tickers must be unique.");
            return BadRequest(ModelState);
        }

        var allocationGroups = request.Allocation
            .GroupBy(pair => pair.Key.Trim().ToUpperInvariant(), StringComparer.Ordinal)
            .ToList();
        if (allocationGroups.Any(group => group.Count() > 1))
        {
            ModelState.AddModelError(nameof(request.Allocation), "Allocation keys must be unique.");
            return BadRequest(ModelState);
        }

        var normalizedAllocation = allocationGroups.ToDictionary(group => group.Key, group => group.Single().Value, StringComparer.Ordinal);

        var missingTickers = normalizedTickers.Where(ticker => !normalizedAllocation.ContainsKey(ticker)).ToArray();
        if (missingTickers.Length > 0)
        {
            ModelState.AddModelError(nameof(request.Allocation), $"Missing allocation for: {string.Join(", ", missingTickers)}.");
            return BadRequest(ModelState);
        }

        if (normalizedAllocation.Keys.Except(normalizedTickers, StringComparer.Ordinal).Any())
        {
            ModelState.AddModelError(nameof(request.Allocation), "Allocation contains tickers not present in tickers list.");
            return BadRequest(ModelState);
        }

        if (normalizedAllocation.Values.Any(value => value <= 0 || value > 100))
        {
            ModelState.AddModelError(nameof(request.Allocation), "Each allocation percent must be > 0 and <= 100.");
            return BadRequest(ModelState);
        }

        var normalizedDividendEvents = (request.DividendEvents ?? [])
            .Select(x => new DividendEventInput
            {
                Symbol = x.Symbol.Trim().ToUpperInvariant(),
                ExDate = x.ExDate,
                Amount = x.Amount
            })
            .ToList();

        if (normalizedDividendEvents.Any(x => string.IsNullOrWhiteSpace(x.Symbol)))
        {
            ModelState.AddModelError(nameof(request.DividendEvents), "Dividend event symbol is required.");
            return BadRequest(ModelState);
        }

        var totalAllocation = normalizedAllocation.Values.Sum();
        if (Math.Abs(totalAllocation - 100m) > 0.0001m)
        {
            ModelState.AddModelError(nameof(request.Allocation), "Allocation must sum to exactly 100%.");
            return BadRequest(ModelState);
        }

        var normalizedRequest = new PortfolioSimulationRequest
        {
            Mode = request.Mode,
            LookbackDays = request.LookbackDays,
            DateRange = request.DateRange,
            Tickers = normalizedTickers,
            Allocation = normalizedAllocation,
            StopLossPct = request.StopLossPct,
            TakeProfitPct = request.TakeProfitPct,
            FeePctPerSide = request.FeePctPerSide,
            SettlementDays = request.SettlementDays,
            InitialCapital = request.InitialCapital,
            DividendEvents = normalizedDividendEvents,
            Parameters = request.Parameters
        };

        var response = await pythonEngineClient.SimulatePortfolioAsync(normalizedRequest, cancellationToken);
        return Ok(response);
    }
}
