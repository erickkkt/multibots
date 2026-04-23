from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date as date_type
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
            "currentPrice": round(float(latest["close"]), 2),
            "reasons": ["Không đủ dữ liệu"],
            "prices": [{"date": latest["date"], "close": round(float(latest["close"]), 2)}],
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
        "currentPrice": round(closes[-1], 2),
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


def _build_dividend_index(symbol: str, dividend_events: List[Dict]) -> Dict[str, float]:
    dividend_by_date: Dict[str, float] = {}
    symbol_upper = symbol.upper()
    for event in dividend_events:
        event_symbol = str(event.get("symbol", "")).strip().upper()
        ex_date = str(event.get("exDate", "")).strip()
        amount = float(event.get("amount", 0.0) or 0.0)
        if event_symbol != symbol_upper or not ex_date or amount <= 0:
            continue

        dividend_by_date[ex_date] = dividend_by_date.get(ex_date, 0.0) + amount

    return dividend_by_date


def _simulate_ticker(
    symbol: str,
    allocation_capital: float,
    rows: List[Dict],
    parameters: AnalysisParameters,
    stop_loss_pct: float,
    take_profit_pct: float,
    fee_pct_per_side: float,
    settlement_days: int,
    dividend_events: List[Dict],
    enable_dividend_signal_adjustment: bool,
) -> Tuple[List[Dict], float, List[Dict], float]:
    fee_rate = fee_pct_per_side / 100.0
    stop_rate = stop_loss_pct / 100.0
    take_rate = take_profit_pct / 100.0
    dividend_by_date = _build_dividend_index(symbol, dividend_events)
    adjusted_rows: List[Dict] = []
    for row in rows:
        date = str(row["date"])
        dividend_amount = dividend_by_date.get(date, 0.0)
        adjusted_rows.append(
            {
                "date": date,
                "open": max(0.0, float(row["open"]) - dividend_amount),
                "high": max(0.0, float(row["high"]) - dividend_amount),
                "low": max(0.0, float(row["low"]) - dividend_amount),
                "close": max(0.0, float(row["close"]) - dividend_amount),
                "volume": float(row["volume"]),
            }
        )

    signal_rows = build_signal_series(symbol, adjusted_rows, parameters)

    cash = allocation_capital
    quantity = 0.0
    entry_price = 0.0
    entry_date = ""
    entry_buy_fee = 0.0
    entry_dividend_income = 0.0
    pending_settlements: List[Tuple[int, float]] = []
    total_dividend_income = 0.0
    trades: List[Dict] = []
    equity_points: List[Dict] = []

    for index, row in enumerate(signal_rows):
        if pending_settlements:
            settled_cash = sum(amount for settle_index, amount in pending_settlements if settle_index <= index)
            if settled_cash:
                cash += settled_cash
            pending_settlements = [(settle_index, amount) for settle_index, amount in pending_settlements if settle_index > index]

        market_row = rows[index]
        close = float(market_row["close"])
        high = float(market_row["high"])
        low = float(market_row["low"])
        action = str(row["action"]).lower()
        date = str(row["date"])
        dividend_amount = dividend_by_date.get(date, 0.0)
        next_day_has_dividend = (
            index + 1 < len(rows) and dividend_by_date.get(str(rows[index + 1]["date"]), 0.0) > 0.0
        )

        if enable_dividend_signal_adjustment:
            if quantity == 0 and next_day_has_dividend and action == "hold":
                action = "buy"
            elif quantity > 0 and next_day_has_dividend and action == "sell":
                action = "hold"

        if quantity > 0 and dividend_amount > 0:
            dividend_income = quantity * dividend_amount
            cash += dividend_income
            entry_dividend_income += dividend_income
            total_dividend_income += dividend_income

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
                net_pnl = gross_pnl - entry_buy_fee - sell_fee + entry_dividend_income
                settled_sell_cash = sell_value - sell_fee
                if settlement_days > 0:
                    pending_settlements.append((index + settlement_days, settled_sell_cash))
                else:
                    cash += settled_sell_cash
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
                        "dividendIncome": round(entry_dividend_income, 4),
                        "exitReason": exit_reason,
                    }
                )
                quantity = 0.0
                entry_price = 0.0
                entry_date = ""
                entry_buy_fee = 0.0
                entry_dividend_income = 0.0

        if quantity == 0 and action == "buy" and close > 0:
            quantity = cash / (close * (1 + fee_rate))
            buy_value = quantity * close
            entry_buy_fee = buy_value * fee_rate
            cash -= buy_value + entry_buy_fee
            entry_price = close
            entry_date = date

        pending_cash = sum(amount for _, amount in pending_settlements)
        equity_points.append({"date": date, "value": round(cash + pending_cash + quantity * close, 4)})

    pending_cash = sum(amount for _, amount in pending_settlements)
    final_equity = cash + pending_cash + (quantity * rows[-1]["close"] if rows else 0.0)
    return equity_points, final_equity, trades, total_dividend_income


def simulate_portfolio(
    ticker_rows: Dict[str, List[Dict]],
    allocations_pct: Dict[str, float],
    initial_capital: float,
    parameters: AnalysisParameters,
    stop_loss_pct: float,
    take_profit_pct: float,
    fee_pct_per_side: float,
    settlement_days: int = 2,
    dividend_events: List[Dict] | None = None,
    enable_dividend_signal_adjustment: bool = True,
) -> Dict:
    per_ticker_equity: Dict[str, Dict[str, float]] = {}
    pnl_by_ticker: Dict[str, float] = {}
    dividend_by_ticker: Dict[str, float] = {}
    all_trades: List[Dict] = []
    effective_dividend_events = dividend_events or []

    for symbol, rows in ticker_rows.items():
        allocation_pct = float(allocations_pct[symbol])
        allocation_capital = initial_capital * (allocation_pct / 100.0)
        ticker_equity, final_equity, ticker_trades, ticker_dividend_income = _simulate_ticker(
            symbol=symbol,
            allocation_capital=allocation_capital,
            rows=rows,
            parameters=parameters,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct,
            fee_pct_per_side=fee_pct_per_side,
            settlement_days=max(0, int(settlement_days)),
            dividend_events=effective_dividend_events,
            enable_dividend_signal_adjustment=enable_dividend_signal_adjustment,
        )
        per_ticker_equity[symbol] = {point["date"]: float(point["value"]) for point in ticker_equity}
        pnl_by_ticker[symbol] = round(final_equity - allocation_capital, 4)
        dividend_by_ticker[symbol] = round(ticker_dividend_income, 4)
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
        "dividendByTicker": dividend_by_ticker,
        "trades": all_trades,
    }


def project_ohlcv_forward(historical_rows: List[Dict], n_trading_days: int, symbol: str = "") -> List[Dict]:
    """
    Project OHLCV data forward from the last historical row.
    Uses recent volatility and trend (last 30 candles) as a random-walk model.
    Returns rows with future dates starting from tomorrow (weekdays only).
    """
    # Use symbol + today as seed so results are consistent within a day but vary by symbol
    today = datetime.now(timezone.utc).date()
    seed = sum(ord(c) for c in symbol.upper()) * 1000 + today.toordinal()
    rng = random.Random(seed)

    if not historical_rows:
        return synthetic_ohlcv(symbol, n_trading_days)

    closes = [float(r["close"]) for r in historical_rows]
    last_close = closes[-1]
    last_volume = float(historical_rows[-1].get("volume", 100_000))

    # Calibrate from last 30 candles
    lookback = min(30, len(closes) - 1)
    if lookback > 1:
        returns = [(closes[i] - closes[i - 1]) / max(closes[i - 1], 0.01) for i in range(-lookback, 0)]
        mean_ret = sum(returns) / len(returns)
        variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
        std_ret = variance ** 0.5
    else:
        mean_ret = 0.0
        std_ret = 0.015

    # Parse last historical date
    last_date_str = str(historical_rows[-1].get("date", ""))
    try:
        current_date = datetime.strptime(last_date_str[:10], "%Y-%m-%d").date()
    except ValueError:
        current_date = today

    price = last_close
    projected: List[Dict] = []
    days_added = 0

    while days_added < n_trading_days:
        current_date += timedelta(days=1)
        if current_date.weekday() >= 5:  # skip weekends
            continue

        ret = rng.gauss(mean_ret, std_ret)
        price = max(0.01, price * (1.0 + ret))
        intraday_range = price * abs(rng.gauss(0, std_ret * 0.5))
        open_p = round(price * (1 + rng.gauss(0, std_ret * 0.3)), 2)
        high_p = round(price + intraday_range, 2)
        low_p = round(max(0.01, price - intraday_range), 2)
        volume = max(1.0, last_volume * rng.uniform(0.5, 1.5))

        projected.append(
            {
                "date": current_date.strftime("%Y-%m-%d"),
                "open": open_p,
                "high": high_p,
                "low": low_p,
                "close": round(price, 2),
                "volume": round(volume, 0),
            }
        )
        days_added += 1

    return projected


def synthetic_foreign_trade(symbol: str = "", n_days: int = 30) -> List[Dict]:
    """Generate synthetic foreign investor buy/sell data, seeded per symbol."""
    seed = sum(ord(c) for c in symbol.upper()) if symbol else 12345
    rng = random.Random(seed)
    start = datetime.now(timezone.utc) - timedelta(days=n_days)
    rows = []
    for i in range(n_days):
        buy_vol = rng.randint(200_000, 5_000_000)
        sell_vol = rng.randint(200_000, 5_000_000)
        price = 20.0 + rng.uniform(-2, 2)
        rows.append(
            {
                "date": (start + timedelta(days=i)).strftime("%Y-%m-%d"),
                "buyVol": float(buy_vol),
                "sellVol": float(sell_vol),
                "buyVal": round(buy_vol * price, 0),
                "sellVal": round(sell_vol * price, 0),
            }
        )
    return rows


def synthetic_ohlcv(symbol: str = "", candles: int = 120) -> List[Dict]:
    seed = sum(ord(c) for c in symbol.upper()) if symbol else 42
    rng = random.Random(seed)
    start = datetime.now(timezone.utc) - timedelta(days=candles)
    # Base price varies by symbol (10–80 range)
    price = 10.0 + (seed % 71)
    rows = []

    for i in range(candles):
        drift = rng.uniform(-0.8, 1.0)
        price = max(1.0, price + drift)
        volume = rng.randint(50_000, 500_000)
        rows.append(
            {
                "date": (start + timedelta(days=i)).strftime("%Y-%m-%d"),
                "open": round(price - rng.uniform(0, 0.5), 2),
                "high": round(price + rng.uniform(0, 0.8), 2),
                "low": round(price - rng.uniform(0, 0.8), 2),
                "close": round(price, 2),
                "volume": float(volume),
            }
        )

    return rows
