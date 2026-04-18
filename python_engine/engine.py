from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List


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
