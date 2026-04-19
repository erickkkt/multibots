using Microsoft.AspNetCore.Mvc;
using Multibots.Api.Controllers;
using Multibots.Api.Models;
using Multibots.Api.Services;

namespace Multibots.Api.Tests;

public class DividendsControllerTests
{
    [Fact]
    public async Task Get_ReturnsDefaultDividendEvents_WhenNotConfigured()
    {
        var service = new StubAppSettingService();
        var controller = new DividendsController(service);

        var result = await controller.Get(null, CancellationToken.None);

        var ok = Assert.IsType<OkObjectResult>(result);
        var payload = Assert.IsType<List<DividendEventInput>>(ok.Value);
        Assert.NotEmpty(payload);
    }

    [Fact]
    public async Task Upsert_NormalizesTickerAndPersistsEvents()
    {
        var service = new StubAppSettingService();
        var controller = new DividendsController(service);

        var result = await controller.Upsert(
            [new DividendEventInput { Symbol = " hpg ", ExDate = new DateOnly(2026, 4, 1), Amount = 500m }],
            CancellationToken.None);

        var ok = Assert.IsType<OkObjectResult>(result);
        var payload = Assert.IsType<List<DividendEventInput>>(ok.Value);
        Assert.Equal("HPG", payload[0].Symbol);
        Assert.Equal("portfolio.dividend-events", service.LastUpsertedKey);
        Assert.False(string.IsNullOrWhiteSpace(service.LastUpsertedValue));
    }

    private sealed class StubAppSettingService : IAppSettingService
    {
        private readonly Dictionary<string, string> _settings = new(StringComparer.Ordinal);

        public string? LastUpsertedKey { get; private set; }
        public string? LastUpsertedValue { get; private set; }

        public Task<IReadOnlyList<SettingDto>> GetAllAsync(CancellationToken cancellationToken)
            => Task.FromResult<IReadOnlyList<SettingDto>>([]);

        public Task<SettingDto?> GetByKeyAsync(string key, CancellationToken cancellationToken)
        {
            if (_settings.TryGetValue(key, out var value))
            {
                return Task.FromResult<SettingDto?>(new SettingDto
                {
                    Key = key,
                    Value = value,
                    UpdatedAtUtc = DateTime.UtcNow
                });
            }

            return Task.FromResult<SettingDto?>(null);
        }

        public Task<SettingDto> UpsertAsync(string key, UpsertSettingRequest request, CancellationToken cancellationToken)
        {
            LastUpsertedKey = key;
            LastUpsertedValue = request.Value;
            _settings[key] = request.Value;
            return Task.FromResult(new SettingDto
            {
                Key = key,
                Value = request.Value,
                Description = request.Description,
                UpdatedAtUtc = DateTime.UtcNow
            });
        }

        public Task<bool> DeleteAsync(string key, CancellationToken cancellationToken) => Task.FromResult(false);
    }
}
