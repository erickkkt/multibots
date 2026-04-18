from __future__ import annotations

from typing import Dict, List

try:
    from .engine import normalize_ohlcv, synthetic_ohlcv
except ImportError:  # pragma: no cover
    from engine import normalize_ohlcv, synthetic_ohlcv


def fetch_ohlcv(symbol: str, candles: int) -> List[Dict]:
    """
    Cố gắng lấy dữ liệu từ vnstock. Nếu môi trường chưa cài hoặc lỗi mạng,
    trả về dữ liệu mẫu để engine vẫn hoạt động cho Phase 1.
    """
    try:
        from vnstock import Vnstock  # type: ignore

        stock = Vnstock().stock(symbol=symbol, source="VCI")
        raw = stock.quote.history(start="2024-01-01", end=None, interval="1D")

        if hasattr(raw, "to_dict"):
            records = raw.tail(candles).to_dict(orient="records")
        else:
            records = list(raw)[-candles:]

        normalized = normalize_ohlcv(records)
        if normalized:
            return normalized[-candles:]
    except Exception:
        pass

    return synthetic_ohlcv(candles)
