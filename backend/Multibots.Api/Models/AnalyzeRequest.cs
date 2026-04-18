using System.ComponentModel.DataAnnotations;

namespace Multibots.Api.Models;

public class AnalyzeRequest
{
    [Required]
    [MinLength(1)]
    [MaxLength(5)]
    public List<string> Symbols { get; init; } = [];

    public AnalysisParameters Parameters { get; init; } = new();
}

public class AnalysisParameters
{
    [Range(2, 200)]
    public int ShortMaPeriod { get; init; } = 9;

    [Range(3, 300)]
    public int LongMaPeriod { get; init; } = 21;

    [Range(2, 100)]
    public int RsiPeriod { get; init; } = 14;

    [Range(2, 120)]
    public int VolumeLookback { get; init; } = 20;

    [Range(30, 500)]
    public int Candles { get; init; } = 120;
}
