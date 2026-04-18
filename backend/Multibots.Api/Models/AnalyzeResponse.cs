namespace Multibots.Api.Models;

public class AnalyzeResponse
{
    public DateTime GeneratedAtUtc { get; init; }
    public List<SymbolSignal> Results { get; init; } = [];
}

public class SymbolSignal
{
    public string Symbol { get; init; } = string.Empty;
    public string Action { get; init; } = "hold";
    public double Confidence { get; init; }
    public string[] Reasons { get; init; } = [];
    public List<PricePoint> Prices { get; init; } = [];
}

public class PricePoint
{
    public string Date { get; init; } = string.Empty;
    public decimal Close { get; init; }
}
