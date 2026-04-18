using System.ComponentModel.DataAnnotations;

namespace Multibots.Api.Models;

public class UpsertSettingRequest
{
    [Required]
    [StringLength(4000, MinimumLength = 1)]
    public string Value { get; init; } = string.Empty;

    [StringLength(500)]
    public string? Description { get; init; }
}
