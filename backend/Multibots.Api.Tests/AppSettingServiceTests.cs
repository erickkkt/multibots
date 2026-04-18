using Microsoft.EntityFrameworkCore;
using Multibots.Api.Data;
using Multibots.Api.Models;
using Multibots.Api.Repositories;
using Multibots.Api.Services;

namespace Multibots.Api.Tests;

public class AppSettingServiceTests
{
    [Fact]
    public async Task UpsertAndGetByKey_PersistsSetting()
    {
        await using var dbContext = BuildDbContext();
        var repository = new AppSettingRepository(dbContext);
        var service = new AppSettingService(repository);

        await service.UpsertAsync("risk:max_position", new UpsertSettingRequest
        {
            Value = "5",
            Description = "max symbols"
        }, CancellationToken.None);

        var setting = await service.GetByKeyAsync("risk:max_position", CancellationToken.None);

        Assert.NotNull(setting);
        Assert.Equal("5", setting.Value);
        Assert.Equal("max symbols", setting.Description);
    }

    [Fact]
    public async Task Delete_RemovesSetting()
    {
        await using var dbContext = BuildDbContext();
        var repository = new AppSettingRepository(dbContext);
        var service = new AppSettingService(repository);

        await service.UpsertAsync("engine:timeout", new UpsertSettingRequest
        {
            Value = "15"
        }, CancellationToken.None);

        var deleted = await service.DeleteAsync("engine:timeout", CancellationToken.None);
        var setting = await service.GetByKeyAsync("engine:timeout", CancellationToken.None);

        Assert.True(deleted);
        Assert.Null(setting);
    }

    private static MultibotsDbContext BuildDbContext()
    {
        var options = new DbContextOptionsBuilder<MultibotsDbContext>()
            .UseInMemoryDatabase(Guid.NewGuid().ToString())
            .Options;

        return new MultibotsDbContext(options);
    }
}
