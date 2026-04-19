using System.ComponentModel.DataAnnotations;

namespace Multibots.Api.Models;

public enum SimulationMode
{
    Backtest = 0,
    Realtime = 1
}

public class PortfolioSimulationRequest
{
    public SimulationMode Mode { get; init; } = SimulationMode.Backtest;

    [Range(1, 3650)]
    public int LookbackDays { get; init; } = 180;

    public DateRangeInput? DateRange { get; init; }

    [Required]
    [MinLength(1)]
    public List<string> Tickers { get; init; } = [];

    [Required]
    [MinLength(1)]
    public Dictionary<string, decimal> Allocation { get; init; } = [];

    [Range(0, 100)]
    public decimal StopLossPct { get; init; }

    [Range(0, 100)]
    public decimal TakeProfitPct { get; init; }

    [Range(0, 100)]
    public decimal FeePctPerSide { get; init; } = 0.1m;

    [Range(0, 10)]
    public int SettlementDays { get; init; } = 2;

    [Range(typeof(decimal), "1", "79228162514264337593543950335")]
    public decimal InitialCapital { get; init; }

    public List<DividendEventInput> DividendEvents { get; init; } = [];

    public AnalysisParameters Parameters { get; init; } = new();
}

public class DateRangeInput
{
    public DateOnly? StartDate { get; init; }
    public DateOnly? EndDate { get; init; }
}

public class PortfolioSimulationResponse
{
    public DateTime GeneratedAtUtc { get; init; }
    public string Mode { get; init; } = SimulationMode.Backtest.ToString();
    public int SettlementDays { get; init; } = 2;
    public List<EquityPoint> EquityCurve { get; init; } = [];
    public Dictionary<string, decimal> PnlByTicker { get; init; } = [];
    public Dictionary<string, decimal> DividendByTicker { get; init; } = [];
    public List<PortfolioTrade> Trades { get; init; } = [];
}

public class EquityPoint
{
    public string Timestamp { get; init; } = string.Empty;
    public decimal TotalValue { get; init; }
}

public class PortfolioTrade
{
    public string Symbol { get; init; } = string.Empty;
    public string EntryDate { get; init; } = string.Empty;
    public string ExitDate { get; init; } = string.Empty;
    public decimal EntryPrice { get; init; }
    public decimal ExitPrice { get; init; }
    public decimal Quantity { get; init; }
    public decimal GrossPnl { get; init; }
    public decimal NetPnl { get; init; }
    public decimal DividendIncome { get; init; }
    public string ExitReason { get; init; } = string.Empty;
}

public class DividendEventInput
{
    [Required]
    [StringLength(20, MinimumLength = 1)]
    public string Symbol { get; init; } = string.Empty;

    public DateOnly ExDate { get; init; }

    [Range(typeof(decimal), "0.0001", "79228162514264337593543950335")]
    public decimal Amount { get; init; }
}
