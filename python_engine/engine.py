from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Tuple


@dataclass
class AnalysisParameters:
    short_ma_period: int = 9
    long_ma_period: int = 21
    rsi_period: int = 14
    volume_lookback: int = 20
    candles: int = 120


def normalize_ohlcv(raw_rows: Iterable[Dict]) -> List[Dict[str, float]]:
    normalized = []
    aliases = {
        "date": ["date", "time", "datetime", "trading_date"],
        "open": ["open", "o"],
        "high": ["high", "h"],
        "low": ["low", "l"],
        "close": ["close", "c"],
        "volume": ["volume", "vol", "v"],
    }

    for row in raw_rows:
        mapped = {}
        for target, candidates in aliases.items():
            value = None
            for key in candidates:
                if key in row and row[key] is not None:
                    value = row[key]
                    break
            mapped[target] = value

        if not all(mapped[field] is not None for field in ("open", "high", "low", "close", "volume")):
            continue

        mapped["date"] = str(mapped["date"] or "")
        mapped["open"] = float(mapped["open"])
        mapped["high"] = float(mapped["high"])
        mapped["low"] = float(mapped["low"])
        mapped["close"] = float(mapped["close"])
        mapped["volume"] = float(mapped["volume"])
        normalized.append(mapped)

    return normalized


def sma(values: List[float], period: int) -> float:
    if len(values) < period:
        return sum(values) / len(values)
    tail = values[-period:]
    return sum(tail) / period


def ema(values: List[float], period: int) -> float:
    multiplier = 2 / (period + 1)
    ema_value = values[0]
    for value in values[1:]:
        ema_value = (value - ema_value) * multiplier + ema_value
    return ema_value


def compute_rsi(closes: List[float], period: int) -> float:
    if len(closes) <= period:
        return 50.0

    gains = []
    losses = []
    for i in range(1, period + 1):
        delta = closes[-i] - closes[-i - 1]
        gains.append(max(delta, 0))
        losses.append(abs(min(delta, 0)))

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def compute_macd(closes: List[float]) -> tuple[float, float]:
    if len(closes) < 26:
        return 0.0, 0.0

    macd_series = []
    for idx in range(26, len(closes) + 1):
        window = closes[:idx]
        macd_series.append(ema(window, 12) - ema(window, 26))

    macd_line = macd_series[-1]
    signal_line = ema(macd_series, min(9, len(macd_series)))
    return macd_line, signal_line


def build_signal(symbol: str, rows: List[Dict], parameters: AnalysisParameters) -> Dict:
    if len(rows) < 2:
        latest = rows[-1] if rows else {"date": "", "close": 0.0}
        return {
            "symbol": symbol,
            "action": "hold",
            "confidence": 0.5,
            "reasons": ["Không đủ dữ liệu"],
            "prices": [{"date": latest["date"], "close": round(latest["close"], 2)}],
        }

    closes = [row["close"] for row in rows]
    volumes = [row["volume"] for row in rows]

    short_ma = sma(closes, parameters.short_ma_period)
    long_ma = sma(closes, parameters.long_ma_period)
    rsi = compute_rsi(closes, parameters.rsi_period)
    macd_line, signal_line = compute_macd(closes)

    recent_volume = volumes[-1]
    average_volume = sma(volumes, parameters.volume_lookback)
    volume_breakout = recent_volume > (average_volume * 1.5)

    score = 0
    reasons: List[str] = []

    if closes[-1] > short_ma > long_ma:
        score += 1
        reasons.append("MA xu hướng tăng")
    elif closes[-1] < short_ma < long_ma:
        score -= 1
        reasons.append("MA xu hướng giảm")

    if rsi < 35:
        score += 1
        reasons.append("RSI vùng quá bán")
    elif rsi > 70:
        score -= 1
        reasons.append("RSI vùng quá mua")

    if macd_line > signal_line:
        score += 1
        reasons.append("MACD cắt lên")
    elif macd_line < signal_line:
        score -= 1
        reasons.append("MACD cắt xuống")

    if volume_breakout:
        score += 1 if closes[-1] >= closes[-2] else -1
        reasons.append("Volume breakout")

    if score >= 2:
        action = "buy"
    elif score <= -2:
        action = "sell"
    else:
        action = "hold"

    confidence = min(0.95, 0.5 + abs(score) * 0.12)

    return {
        "symbol": symbol,
        "action": action,
        "confidence": round(confidence, 2),
        "reasons": reasons or ["Tín hiệu trung tính"],
        "prices": [{"date": row["date"], "close": round(row["close"], 2)} for row in rows[-30:]],
    }


def build_signal_series(symbol: str, rows: List[Dict], parameters: AnalysisParameters) -> List[Dict]:
    series: List[Dict] = []
    for index, row in enumerate(rows):
        if index < 1:
            action = "hold"
        else:
            action = build_signal(symbol, rows[: index + 1], parameters)["action"]

        series.append(
            {
                "date": row["date"],
                "action": action,
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
            }
        )

    return series


def _simulate_ticker(
    symbol: str,
    allocation_capital: float,
    rows: List[Dict],
    parameters: AnalysisParameters,
    stop_loss_pct: float,
    take_profit_pct: float,
    fee_pct_per_side: float,
) -> Tuple[List[Dict], float, List[Dict]]:
    fee_rate = fee_pct_per_side / 100.0
    stop_rate = stop_loss_pct / 100.0
    take_rate = take_profit_pct / 100.0
    signal_rows = build_signal_series(symbol, rows, parameters)

    cash = allocation_capital
    quantity = 0.0
    entry_price = 0.0
    entry_date = ""
    entry_buy_fee = 0.0
    trades: List[Dict] = []
    equity_points: List[Dict] = []

    for row in signal_rows:
        close = float(row["close"])
        high = float(row["high"])
        low = float(row["low"])
        action = str(row["action"]).lower()
        date = str(row["date"])

        if quantity > 0:
            stop_price = entry_price * (1 - stop_rate) if stop_rate > 0 else None
            take_price = entry_price * (1 + take_rate) if take_rate > 0 else None

            exit_reason = None
            exit_price = None
            if stop_price is not None and low <= stop_price:
                exit_reason = "StopLoss"
                exit_price = stop_price
            elif take_price is not None and high >= take_price:
                exit_reason = "TakeProfit"
                exit_price = take_price
            elif action == "sell":
                exit_reason = "SellSignal"
                exit_price = close

            if exit_reason and exit_price is not None:
                sell_value = quantity * exit_price
                sell_fee = sell_value * fee_rate
                entry_value = quantity * entry_price
                gross_pnl = sell_value - entry_value
                net_pnl = gross_pnl - entry_buy_fee - sell_fee
                cash += sell_value - sell_fee
                trades.append(
                    {
                        "symbol": symbol,
                        "entryDate": entry_date,
                        "exitDate": date,
                        "entryPrice": round(entry_price, 4),
                        "exitPrice": round(exit_price, 4),
                        "quantity": round(quantity, 8),
                        "grossPnl": round(gross_pnl, 4),
                        "netPnl": round(net_pnl, 4),
                        "exitReason": exit_reason,
                    }
                )
                quantity = 0.0
                entry_price = 0.0
                entry_date = ""
                entry_buy_fee = 0.0

        if quantity == 0 and action == "buy" and close > 0:
            quantity = cash / (close * (1 + fee_rate))
            buy_value = quantity * close
            entry_buy_fee = buy_value * fee_rate
            cash -= buy_value + entry_buy_fee
            entry_price = close
            entry_date = date

        equity_points.append({"date": date, "value": round(cash + quantity * close, 4)})

    final_equity = cash + (quantity * signal_rows[-1]["close"] if signal_rows else 0.0)
    return equity_points, final_equity, trades


def simulate_portfolio(
    ticker_rows: Dict[str, List[Dict]],
    allocations_pct: Dict[str, float],
    initial_capital: float,
    parameters: AnalysisParameters,
    stop_loss_pct: float,
    take_profit_pct: float,
    fee_pct_per_side: float,
) -> Dict:
    per_ticker_equity: Dict[str, Dict[str, float]] = {}
    pnl_by_ticker: Dict[str, float] = {}
    all_trades: List[Dict] = []

    for symbol, rows in ticker_rows.items():
        allocation_pct = float(allocations_pct[symbol])
        allocation_capital = initial_capital * (allocation_pct / 100.0)
        ticker_equity, final_equity, ticker_trades = _simulate_ticker(
            symbol=symbol,
            allocation_capital=allocation_capital,
            rows=rows,
            parameters=parameters,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct,
            fee_pct_per_side=fee_pct_per_side,
        )
        per_ticker_equity[symbol] = {point["date"]: float(point["value"]) for point in ticker_equity}
        pnl_by_ticker[symbol] = round(final_equity - allocation_capital, 4)
        all_trades.extend(ticker_trades)

    all_dates = sorted({date for ticker_map in per_ticker_equity.values() for date in ticker_map})
    equity_curve: List[Dict] = []
    for date in all_dates:
        total_value = 0.0
        for ticker_map in per_ticker_equity.values():
            if date in ticker_map:
                total_value += ticker_map[date]
            elif ticker_map:
                prior_values = [value for key, value in ticker_map.items() if key < date]
                total_value += prior_values[-1] if prior_values else 0.0
        equity_curve.append({"timestamp": date, "totalValue": round(total_value, 4)})

    return {
        "equityCurve": equity_curve,
        "pnlByTicker": pnl_by_ticker,
        "trades": all_trades,
    }


def synthetic_ohlcv(candles: int = 120) -> List[Dict]:
    start = datetime.now(timezone.utc) - timedelta(days=candles)
    price = 20.0
    rows = []

    for i in range(candles):
        drift = 0.02 if i % 7 != 0 else -0.05
        price = max(1.0, price + drift)
        volume = 100_000 + (i % 5) * 20_000
        rows.append(
            {
                "date": (start + timedelta(days=i)).strftime("%Y-%m-%d"),
                "open": round(price - 0.2, 2),
                "high": round(price + 0.4, 2),
                "low": round(price - 0.5, 2),
                "close": round(price, 2),
                "volume": float(volume),
            }
        )

    return rows
