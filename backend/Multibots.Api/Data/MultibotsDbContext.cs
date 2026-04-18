using Microsoft.EntityFrameworkCore;
using Multibots.Api.Data.Entities;

namespace Multibots.Api.Data;

public class MultibotsDbContext(DbContextOptions<MultibotsDbContext> options) : DbContext(options)
{
    public DbSet<AppSetting> AppSettings => Set<AppSetting>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<AppSetting>(entity =>
        {
            entity.ToTable("app_settings");
            entity.HasKey(x => x.Id);
            entity.HasIndex(x => x.Key).IsUnique();
            entity.Property(x => x.Key).HasMaxLength(128).IsRequired();
            entity.Property(x => x.Value).HasMaxLength(4000).IsRequired();
            entity.Property(x => x.Description).HasMaxLength(500);
            entity.Property(x => x.UpdatedAtUtc).IsRequired();
        });
    }
}
