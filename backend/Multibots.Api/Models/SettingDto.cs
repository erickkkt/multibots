namespace Multibots.Api.Models;

public class SettingDto
{
    public string Key { get; init; } = string.Empty;
    public string Value { get; init; } = string.Empty;
    public string? Description { get; init; }
    public DateTime UpdatedAtUtc { get; init; }
}
