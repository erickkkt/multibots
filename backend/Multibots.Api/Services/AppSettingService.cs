using Multibots.Api.Data.Entities;
using Multibots.Api.Models;
using Multibots.Api.Repositories;

namespace Multibots.Api.Services;

public class AppSettingService(IAppSettingRepository repository) : IAppSettingService
{
    public async Task<IReadOnlyList<SettingDto>> GetAllAsync(CancellationToken cancellationToken)
    {
        var settings = await repository.GetAllAsync(cancellationToken);
        return settings.Select(Map).ToList();
    }

    public async Task<SettingDto?> GetByKeyAsync(string key, CancellationToken cancellationToken)
    {
        var setting = await repository.GetByKeyAsync(key, cancellationToken);
        return setting is null ? null : Map(setting);
    }

    public async Task<SettingDto> UpsertAsync(string key, UpsertSettingRequest request, CancellationToken cancellationToken)
    {
        var setting = await repository.UpsertAsync(key, request.Value.Trim(), request.Description?.Trim(), cancellationToken);
        return Map(setting);
    }

    public Task<bool> DeleteAsync(string key, CancellationToken cancellationToken)
    {
        return repository.DeleteAsync(key, cancellationToken);
    }

    private static SettingDto Map(AppSetting setting)
    {
        return new SettingDto
        {
            Key = setting.Key,
            Value = setting.Value,
            Description = setting.Description,
            UpdatedAtUtc = setting.UpdatedAtUtc
        };
    }
}
