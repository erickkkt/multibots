from __future__ import annotations

import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, List

try:
    from .engine import AnalysisParameters, build_signal, simulate_portfolio, project_ohlcv_forward
    from .vnstock_adapter import fetch_ohlcv, fetch_foreign_trade
except ImportError:  # pragma: no cover
    from engine import AnalysisParameters, build_signal, simulate_portfolio, project_ohlcv_forward
    from vnstock_adapter import fetch_ohlcv, fetch_foreign_trade


class AnalyzeHandler(BaseHTTPRequestHandler):
    DEFAULT_DIVIDEND_EVENTS = [
        {"symbol": "HPG", "exDate": "2026-01-15", "amount": 500.0},
        {"symbol": "FPT", "exDate": "2026-02-20", "amount": 2000.0},
    ]

    def do_POST(self):  # noqa: N802
        if self.path not in {"/analyze", "/simulate"}:
            self._send(404, {"error": "Not Found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
            payload = json.loads(body)

            if self.path == "/simulate":
                self._simulate(payload)
                return

            symbols: List[str] = payload.get("symbols", [])
            if not isinstance(symbols, list) or not symbols or len(symbols) > 5:
                self._send(400, {"error": "symbols is required and must contain 1..5 tickers"})
                return

            parameter_data: Dict = payload.get("parameters", {})
            parameters = AnalysisParameters(
                short_ma_period=int(parameter_data.get("shortMaPeriod", 9)),
                long_ma_period=int(parameter_data.get("longMaPeriod", 21)),
                rsi_period=int(parameter_data.get("rsiPeriod", 14)),
                volume_lookback=int(parameter_data.get("volumeLookback", 20)),
                candles=int(parameter_data.get("candles", 120)),
            )

            results = []
            for symbol in symbols:
                ticker = str(symbol).strip().upper()
                rows = fetch_ohlcv(ticker, parameters.candles)
                signal = build_signal(ticker, rows, parameters)
                foreign_trade = fetch_foreign_trade(ticker, 30)
                signal["foreignTrade"] = foreign_trade
                results.append(signal)

            self._send(
                200,
                {
                    "generatedAtUtc": datetime.now(tz=timezone.utc).isoformat(),
                    "results": results,
                },
            )
        except Exception as exc:
            self._send(500, {"error": str(exc)})

    def _simulate(self, payload: Dict):
        symbols: List[str] = payload.get("tickers", [])
        if not isinstance(symbols, list) or not symbols:
            self._send(400, {"error": "tickers is required and must contain at least one ticker"})
            return

        allocation = payload.get("allocation", {})
        if not isinstance(allocation, dict) or not allocation:
            self._send(400, {"error": "allocation is required"})
            return

        allocation_sum = sum(float(value) for value in allocation.values())
        if abs(allocation_sum - 100.0) > 1e-6:
            self._send(400, {"error": "allocation must sum to 100%"})
            return

        lookback_days = int(payload.get("lookbackDays", 180))
        date_range = payload.get("dateRange", {}) if isinstance(payload.get("dateRange"), dict) else {}
        start_date = str(date_range.get("startDate", "")).strip()
        end_date = str(date_range.get("endDate", "")).strip()

        stop_loss_pct = float(payload.get("stopLossPct", 0.0))
        take_profit_pct = float(payload.get("takeProfitPct", 0.0))
        fee_pct_per_side = float(payload.get("feePctPerSide", 0.1))
        initial_capital = float(payload.get("initialCapital", 100000000.0))
        mode = str(payload.get("mode", "Backtest"))
        settlement_days = int(payload.get("settlementDays", 2))
        enable_dividend_signal_adjustment = bool(payload.get("enableDividendSignalAdjustment", True))
        raw_dividend_events = payload.get("dividendEvents", [])
        if not isinstance(raw_dividend_events, list) or not raw_dividend_events:
            raw_dividend_events = self.DEFAULT_DIVIDEND_EVENTS

        parameter_data: Dict = payload.get("parameters", {})
        parameters = AnalysisParameters(
            short_ma_period=int(parameter_data.get("shortMaPeriod", 9)),
            long_ma_period=int(parameter_data.get("longMaPeriod", 21)),
            rsi_period=int(parameter_data.get("rsiPeriod", 14)),
            volume_lookback=int(parameter_data.get("volumeLookback", 20)),
            candles=max(int(parameter_data.get("candles", max(lookback_days, 120))), max(lookback_days, 120)),
        )

        allocation_normalized_input = {str(key).strip().upper(): float(value) for key, value in allocation.items()}
        ticker_rows: Dict[str, List[Dict]] = {}
        normalized_allocation: Dict[str, float] = {}
        is_realtime = mode.lower() == "realtime"

        for symbol in symbols:
            ticker = str(symbol).strip().upper()
            historical = fetch_ohlcv(ticker, parameters.candles)

            if is_realtime:
                # Forward projection: use historical data to calibrate, then project forward
                rows = project_ohlcv_forward(historical, lookback_days, ticker)
            else:
                rows = historical
                if start_date:
                    rows = [row for row in rows if str(row.get("date", "")) >= start_date]
                if end_date:
                    rows = [row for row in rows if str(row.get("date", "")) <= end_date]

            if not rows:
                self._send(400, {"error": f"No OHLC data found for ticker {ticker} in selected range"})
                return

            ticker_rows[ticker] = rows
            normalized_allocation[ticker] = float(allocation_normalized_input.get(ticker, 0.0))

        if any(value <= 0 for value in normalized_allocation.values()):
            self._send(400, {"error": "allocation must be provided for every ticker and greater than 0"})
            return

        result = simulate_portfolio(
            ticker_rows=ticker_rows,
            allocations_pct=normalized_allocation,
            initial_capital=initial_capital,
            parameters=parameters,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct,
            fee_pct_per_side=fee_pct_per_side,
            settlement_days=settlement_days,
            dividend_events=raw_dividend_events,
            enable_dividend_signal_adjustment=enable_dividend_signal_adjustment,
        )
        self._send(
            200,
            {
                "generatedAtUtc": datetime.now(tz=timezone.utc).isoformat(),
                "mode": mode,
                "settlementDays": max(0, settlement_days),
                "enableDividendSignalAdjustment": enable_dividend_signal_adjustment,
                "equityCurve": result["equityCurve"],
                "pnlByTicker": result["pnlByTicker"],
                "dividendByTicker": result["dividendByTicker"],
                "trades": result["trades"],
            },
        )

    def log_message(self, format, *args):  # noqa: A003
        return

    def _send(self, code: int, payload: Dict):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def run_server(port: int = 8000):
    server = HTTPServer(("0.0.0.0", port), AnalyzeHandler)
    print(f"Python engine listening on port {port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
