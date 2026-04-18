using Microsoft.EntityFrameworkCore;
using Multibots.Api.Data;
using Multibots.Api.Data.Entities;

namespace Multibots.Api.Repositories;

public class AppSettingRepository(MultibotsDbContext dbContext) : IAppSettingRepository
{
    public async Task<IReadOnlyList<AppSetting>> GetAllAsync(CancellationToken cancellationToken)
    {
        return await dbContext.AppSettings
            .OrderBy(x => x.Key)
            .ToListAsync(cancellationToken);
    }

    public Task<AppSetting?> GetByKeyAsync(string key, CancellationToken cancellationToken)
    {
        return dbContext.AppSettings
            .SingleOrDefaultAsync(x => x.Key == key, cancellationToken);
    }

    public async Task<AppSetting> UpsertAsync(string key, string value, string? description, CancellationToken cancellationToken)
    {
        var existing = await GetByKeyAsync(key, cancellationToken);

        if (existing is null)
        {
            existing = new AppSetting
            {
                Id = Guid.NewGuid(),
                Key = key
            };
            dbContext.AppSettings.Add(existing);
        }

        existing.Value = value;
        existing.Description = description;
        existing.UpdatedAtUtc = DateTime.UtcNow;

        await dbContext.SaveChangesAsync(cancellationToken);
        return existing;
    }

    public async Task<bool> DeleteAsync(string key, CancellationToken cancellationToken)
    {
        var existing = await GetByKeyAsync(key, cancellationToken);
        if (existing is null)
        {
            return false;
        }

        dbContext.AppSettings.Remove(existing);
        await dbContext.SaveChangesAsync(cancellationToken);
        return true;
    }
}
