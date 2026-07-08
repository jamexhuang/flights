import unittest
from fast_flights.parser import MetaList
from fast_flights.model import ResponseDiagnostics


class DiagnosticsShapeTest(unittest.TestCase):
    def test_metalist_defaults_diagnostics_none(self):
        self.assertIsNone(MetaList().diagnostics)

    def test_can_attach_diagnostics(self):
        m = MetaList()
        m.diagnostics = ResponseDiagnostics(status="empty", http_status=200, elapsed_ms=12.5)
        self.assertEqual(m.diagnostics.status, "empty")
        self.assertEqual(m.diagnostics.attempts, 1)  # default


if __name__ == "__main__":
    unittest.main()
