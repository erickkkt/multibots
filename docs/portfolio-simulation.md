# Portfolio Simulation API

## Endpoint

- `POST /api/portfolio/simulate`

## Request body

```json
{
  "mode": "Backtest",
  "lookbackDays": 180,
  "tickers": ["HPG", "FPT"],
  "allocation": {
    "HPG": 60,
    "FPT": 40
  },
  "stopLossPct": 3,
  "takeProfitPct": 6,
  "feePctPerSide": 0.1,
  "initialCapital": 100000000
}
```

### Notes

- `mode` supports `Backtest` and `Realtime` (default `Backtest`).
- `lookbackDays` defaults to 180 days.
- `allocation` must include all `tickers` and sum exactly to `100`.
- `feePctPerSide` is applied on both buy and sell sides (default `0.1%`).
- Stop-loss / take-profit use intraday touch logic:
  - Stop-loss triggers when candle `low <= entryPrice * (1 - stopLossPct/100)`.
  - Take-profit triggers when candle `high >= entryPrice * (1 + takeProfitPct/100)`.

## Response body

```json
{
  "generatedAtUtc": "2026-04-18T06:20:00Z",
  "mode": "Backtest",
  "equityCurve": [
    { "timestamp": "2026-01-02", "totalValue": 99900000 },
    { "timestamp": "2026-01-03", "totalValue": 100430000 }
  ],
  "pnlByTicker": {
    "HPG": 260000,
    "FPT": 170000
  },
  "trades": [
    {
      "symbol": "HPG",
      "entryDate": "2026-01-02",
      "exitDate": "2026-01-08",
      "entryPrice": 25.3,
      "exitPrice": 26.82,
      "quantity": 236700.12,
      "grossPnl": 359000,
      "netPnl": 311000,
      "exitReason": "TakeProfit"
    }
  ]
}
```
