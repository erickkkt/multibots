import unittest
from unittest.mock import patch

from python_engine.engine import AnalysisParameters, build_signal, normalize_ohlcv, simulate_portfolio, synthetic_ohlcv


class EngineTests(unittest.TestCase):
    def test_normalize_ohlcv_maps_aliases(self):
        rows = normalize_ohlcv([
            {"time": "2026-01-01", "o": 10, "h": 11, "l": 9, "c": 10.5, "v": 12000}
        ])

        self.assertEqual(1, len(rows))
        self.assertEqual(10.5, rows[0]["close"])

    def test_build_signal_returns_action(self):
        rows = synthetic_ohlcv(120)
        result = build_signal("HPG", rows, AnalysisParameters())

        self.assertIn(result["action"], {"buy", "sell", "hold"})
        self.assertTrue(0.5 <= result["confidence"] <= 0.95)
        self.assertEqual("HPG", result["symbol"])

    def test_simulate_portfolio_applies_fee_on_buy_and_sell(self):
        rows = [
            {"date": "2026-01-01", "open": 100, "high": 102, "low": 99, "close": 100, "volume": 1000},
            {"date": "2026-01-02", "open": 100, "high": 103, "low": 98, "close": 100, "volume": 1000},
            {"date": "2026-01-03", "open": 100, "high": 101, "low": 97, "close": 100, "volume": 1000},
        ]
        actions = iter(["buy", "sell"])

        with patch("python_engine.engine.build_signal", side_effect=lambda symbol, data, params: {"action": next(actions)}):
            result = simulate_portfolio(
                ticker_rows={"AAA": rows},
                allocations_pct={"AAA": 100.0},
                initial_capital=1000.0,
                parameters=AnalysisParameters(),
                stop_loss_pct=0.0,
                take_profit_pct=0.0,
                fee_pct_per_side=0.1,
            )

        self.assertAlmostEqual(-1.998, result["pnlByTicker"]["AAA"], places=3)
        self.assertEqual("SellSignal", result["trades"][0]["exitReason"])

    def test_simulate_portfolio_triggers_stop_loss_with_intraday_low(self):
        rows = [
            {"date": "2026-01-01", "open": 100, "high": 102, "low": 99, "close": 100, "volume": 1000},
            {"date": "2026-01-02", "open": 100, "high": 103, "low": 98, "close": 100, "volume": 1000},
            {"date": "2026-01-03", "open": 100, "high": 101, "low": 94, "close": 99, "volume": 1000},
        ]

        with patch("python_engine.engine.build_signal", return_value={"action": "buy"}):
            result = simulate_portfolio(
                ticker_rows={"AAA": rows},
                allocations_pct={"AAA": 100.0},
                initial_capital=1000.0,
                parameters=AnalysisParameters(),
                stop_loss_pct=5.0,
                take_profit_pct=0.0,
                fee_pct_per_side=0.1,
            )

        self.assertEqual("StopLoss", result["trades"][0]["exitReason"])
        self.assertAlmostEqual(95.0, result["trades"][0]["exitPrice"], places=4)

    def test_simulate_portfolio_respects_t_plus_two_settlement_for_rebuy(self):
        rows = [
            {"date": "2026-01-01", "open": 100, "high": 101, "low": 99, "close": 100, "volume": 1000},
            {"date": "2026-01-02", "open": 100, "high": 101, "low": 99, "close": 100, "volume": 1000},
            {"date": "2026-01-03", "open": 100, "high": 101, "low": 99, "close": 100, "volume": 1000},
            {"date": "2026-01-04", "open": 110, "high": 111, "low": 109, "close": 110, "volume": 1000},
            {"date": "2026-01-05", "open": 120, "high": 121, "low": 119, "close": 120, "volume": 1000},
        ]
        actions = iter(["buy", "sell", "buy", "buy"])

        with patch("python_engine.engine.build_signal", side_effect=lambda symbol, data, params: {"action": next(actions)}):
            result = simulate_portfolio(
                ticker_rows={"AAA": rows},
                allocations_pct={"AAA": 100.0},
                initial_capital=1000.0,
                parameters=AnalysisParameters(),
                stop_loss_pct=0.0,
                take_profit_pct=0.0,
                fee_pct_per_side=0.0,
                settlement_days=2,
            )

        self.assertAlmostEqual(0.0, result["pnlByTicker"]["AAA"], places=4)

    def test_simulate_portfolio_includes_dividend_income_in_trade_and_pnl(self):
        rows = [
            {"date": "2026-01-01", "open": 100, "high": 101, "low": 99, "close": 100, "volume": 1000},
            {"date": "2026-01-02", "open": 100, "high": 101, "low": 99, "close": 100, "volume": 1000},
            {"date": "2026-01-03", "open": 100, "high": 101, "low": 99, "close": 100, "volume": 1000},
        ]
        actions = iter(["buy", "sell"])

        with patch("python_engine.engine.build_signal", side_effect=lambda symbol, data, params: {"action": next(actions)}):
            result = simulate_portfolio(
                ticker_rows={"AAA": rows},
                allocations_pct={"AAA": 100.0},
                initial_capital=1000.0,
                parameters=AnalysisParameters(),
                stop_loss_pct=0.0,
                take_profit_pct=0.0,
                fee_pct_per_side=0.0,
                dividend_events=[{"symbol": "AAA", "exDate": "2026-01-03", "amount": 5.0}],
            )

        self.assertAlmostEqual(50.0, result["pnlByTicker"]["AAA"], places=4)
        self.assertAlmostEqual(50.0, result["dividendByTicker"]["AAA"], places=4)
        self.assertAlmostEqual(50.0, result["trades"][0]["dividendIncome"], places=4)


if __name__ == "__main__":
    unittest.main()
