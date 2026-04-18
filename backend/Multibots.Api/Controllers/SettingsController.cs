using Microsoft.AspNetCore.Mvc;
using Multibots.Api.Models;
using Multibots.Api.Services;

namespace Multibots.Api.Controllers;

[ApiController]
[Route("settings")]
public class SettingsController(IAppSettingService service) : ControllerBase
{
    [HttpGet]
    [ProducesResponseType(typeof(IReadOnlyList<SettingDto>), StatusCodes.Status200OK)]
    public async Task<IActionResult> GetAll(CancellationToken cancellationToken)
    {
        var settings = await service.GetAllAsync(cancellationToken);
        return Ok(settings);
    }

    [HttpGet("{key}")]
    [ProducesResponseType(typeof(SettingDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetByKey(string key, CancellationToken cancellationToken)
    {
        if (!TryNormalizeKey(key, out var normalizedKey, out var validationError))
        {
            return BadRequest(validationError);
        }

        var setting = await service.GetByKeyAsync(normalizedKey, cancellationToken);
        return setting is null ? NotFound() : Ok(setting);
    }

    [HttpPut("{key}")]
    [ProducesResponseType(typeof(SettingDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> Upsert(string key, [FromBody] UpsertSettingRequest request, CancellationToken cancellationToken)
    {
        if (!TryNormalizeKey(key, out var normalizedKey, out var validationError))
        {
            return BadRequest(validationError);
        }

        if (!ModelState.IsValid)
        {
            return BadRequest(ModelState);
        }

        var setting = await service.UpsertAsync(normalizedKey, request, cancellationToken);
        return Ok(setting);
    }

    [HttpDelete("{key}")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Delete(string key, CancellationToken cancellationToken)
    {
        if (!TryNormalizeKey(key, out var normalizedKey, out var validationError))
        {
            return BadRequest(validationError);
        }

        var deleted = await service.DeleteAsync(normalizedKey, cancellationToken);
        return deleted ? NoContent() : NotFound();
    }

    private static bool TryNormalizeKey(string key, out string normalizedKey, out string? validationError)
    {
        normalizedKey = key.Trim();
        validationError = null;

        if (string.IsNullOrWhiteSpace(normalizedKey))
        {
            validationError = "Setting key is required.";
            return false;
        }

        if (normalizedKey.Length > 128)
        {
            validationError = "Setting key must be 128 characters or fewer.";
            return false;
        }

        return true;
    }
}
