using Multibots.Api.Models;

namespace Multibots.Api.Services;

public interface IAppSettingService
{
    Task<IReadOnlyList<SettingDto>> GetAllAsync(CancellationToken cancellationToken);
    Task<SettingDto?> GetByKeyAsync(string key, CancellationToken cancellationToken);
    Task<SettingDto> UpsertAsync(string key, UpsertSettingRequest request, CancellationToken cancellationToken);
    Task<bool> DeleteAsync(string key, CancellationToken cancellationToken);
}
