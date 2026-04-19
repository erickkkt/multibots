using System.Text.Json;
using Microsoft.AspNetCore.Mvc;
using Multibots.Api.Models;
using Multibots.Api.Services;

namespace Multibots.Api.Controllers;

[ApiController]
[Route("api/dividends")]
public class DividendsController(IAppSettingService appSettingService) : ControllerBase
{
    private const string DividendSettingsKey = "portfolio.dividend-events";
    private static readonly JsonSerializerOptions JsonOptions = new() { PropertyNameCaseInsensitive = true };

    private static readonly List<DividendEventInput> DefaultDividendEvents =
    [
        new() { Symbol = "HPG", ExDate = new DateOnly(2026, 1, 15), Amount = 500m },
        new() { Symbol = "FPT", ExDate = new DateOnly(2026, 2, 20), Amount = 2000m }
    ];

    [HttpGet]
    [ProducesResponseType(typeof(List<DividendEventInput>), StatusCodes.Status200OK)]
    public async Task<IActionResult> Get([FromQuery] string? ticker, CancellationToken cancellationToken)
    {
        var events = await ReadDividendEventsAsync(cancellationToken);
        if (!string.IsNullOrWhiteSpace(ticker))
        {
            var normalizedTicker = ticker.Trim().ToUpperInvariant();
            events = events.Where(x => x.Symbol == normalizedTicker).ToList();
        }

        return Ok(events);
    }

    [HttpPut]
    [ProducesResponseType(typeof(List<DividendEventInput>), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> Upsert([FromBody] List<DividendEventInput> dividendEvents, CancellationToken cancellationToken)
    {
        if (!ModelState.IsValid)
        {
            return BadRequest(ModelState);
        }

        var normalizedEvents = dividendEvents
            .Select(x => new DividendEventInput
            {
                Symbol = x.Symbol.Trim().ToUpperInvariant(),
                ExDate = x.ExDate,
                Amount = x.Amount
            })
            .OrderBy(x => x.Symbol, StringComparer.Ordinal)
            .ThenBy(x => x.ExDate)
            .ToList();

        if (normalizedEvents.Any(x => string.IsNullOrWhiteSpace(x.Symbol)))
        {
            return BadRequest("Dividend symbol is required.");
        }

        var serialized = JsonSerializer.Serialize(normalizedEvents, JsonOptions);
        await appSettingService.UpsertAsync(
            DividendSettingsKey,
            new UpsertSettingRequest
            {
                Value = serialized,
                Description = "Dividend events used for portfolio simulation adjustments."
            },
            cancellationToken);

        return Ok(normalizedEvents);
    }

    private async Task<List<DividendEventInput>> ReadDividendEventsAsync(CancellationToken cancellationToken)
    {
        var setting = await appSettingService.GetByKeyAsync(DividendSettingsKey, cancellationToken);
        if (setting is null || string.IsNullOrWhiteSpace(setting.Value))
        {
            return [.. DefaultDividendEvents];
        }

        try
        {
            return JsonSerializer.Deserialize<List<DividendEventInput>>(setting.Value, JsonOptions) ?? [.. DefaultDividendEvents];
        }
        catch (JsonException)
        {
            return [.. DefaultDividendEvents];
        }
    }
}
