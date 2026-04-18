using Multibots.Api.Data.Entities;

namespace Multibots.Api.Repositories;

public interface IAppSettingRepository
{
    Task<IReadOnlyList<AppSetting>> GetAllAsync(CancellationToken cancellationToken);
    Task<AppSetting?> GetByKeyAsync(string key, CancellationToken cancellationToken);
    Task<AppSetting> UpsertAsync(string key, string value, string? description, CancellationToken cancellationToken);
    Task<bool> DeleteAsync(string key, CancellationToken cancellationToken);
}
