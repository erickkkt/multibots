from __future__ import annotations

from typing import Dict, List

try:
    from .engine import normalize_ohlcv, synthetic_ohlcv, synthetic_foreign_trade
except ImportError:  # pragma: no cover
    from engine import normalize_ohlcv, synthetic_ohlcv, synthetic_foreign_trade


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

    return synthetic_ohlcv(symbol, candles)


def fetch_foreign_trade(symbol: str, n_days: int = 30) -> List[Dict]:
    """
    Lấy dữ liệu giao dịch khối ngoại từ vnstock.
    Fallback về dữ liệu tổng hợp nếu lỗi.
    """
    try:
        from vnstock import Vnstock  # type: ignore

        stock = Vnstock().stock(symbol=symbol, source="VCI")
        raw = stock.trading.foreign_trading(start="2024-01-01", end=None)

        if hasattr(raw, "to_dict"):
            records = raw.tail(n_days).to_dict(orient="records")
        else:
            records = list(raw)[-n_days:]

        normalized = []
        date_aliases = ["time", "date", "datetime", "trading_date"]
        for row in records:
            date_val = ""
            for k in date_aliases:
                if k in row and row[k] is not None:
                    date_val = str(row[k])[:10]
                    break

            buy_vol = float(row.get("buyVol") or row.get("buy_vol") or row.get("buyvol") or 0)
            sell_vol = float(row.get("sellVol") or row.get("sell_vol") or row.get("sellvol") or 0)
            buy_val = float(row.get("buyVal") or row.get("buy_val") or row.get("buyval") or 0)
            sell_val = float(row.get("sellVal") or row.get("sell_val") or row.get("sellval") or 0)

            if date_val:
                normalized.append(
                    {
                        "date": date_val,
                        "buyVol": buy_vol,
                        "sellVol": sell_vol,
                        "buyVal": buy_val,
                        "sellVal": sell_val,
                    }
                )

        if normalized:
            return normalized[-n_days:]
    except Exception:
        pass

    return synthetic_foreign_trade(symbol, n_days)
