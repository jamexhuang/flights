import logging
import unittest
from unittest.mock import patch, MagicMock
from fast_flights.shopping import _extract_full_flights_list


class LoggingTest(unittest.TestCase):
    def test_extract_failure_logs_debug(self):
        with self.assertLogs("fast_flights", level="DEBUG") as cm:
            # malformed input triggers the except path
            out = _extract_full_flights_list("[[not json")
        self.assertIsNone(out)
        self.assertTrue(any("shopping" in m.lower() or "parse" in m.lower() or "extract" in m.lower()
                            for m in cm.output))


if __name__ == "__main__":
    unittest.main()
