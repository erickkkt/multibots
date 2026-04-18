import unittest

from python_engine.engine import AnalysisParameters, build_signal, normalize_ohlcv, synthetic_ohlcv


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


if __name__ == "__main__":
    unittest.main()
