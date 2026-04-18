from __future__ import annotations

import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, List

try:
    from .engine import AnalysisParameters, build_signal
    from .vnstock_adapter import fetch_ohlcv
except ImportError:  # pragma: no cover
    from engine import AnalysisParameters, build_signal
    from vnstock_adapter import fetch_ohlcv


class AnalyzeHandler(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        if self.path != "/analyze":
            self._send(404, {"error": "Not Found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
            payload = json.loads(body)

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
                results.append(build_signal(ticker, rows, parameters))

            self._send(
                200,
                {
                    "generatedAtUtc": datetime.now(tz=timezone.utc).isoformat(),
                    "results": results,
                },
            )
        except Exception as exc:
            self._send(500, {"error": str(exc)})

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
