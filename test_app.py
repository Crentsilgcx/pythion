
import tempfile
import unittest
from pathlib import Path
from app import (
    validate_non_empty,
    validate_positive_number,
    validate_moisture,
    calculate_values,
    build_daily_report,
    GCXDatabase,
)


class TestGCXApp(unittest.TestCase):
    def test_non_empty(self):
        self.assertEqual(validate_non_empty(" David ", "Name"), "David")
        with self.assertRaises(ValueError):
            validate_non_empty("   ", "Name")

    def test_positive_number(self):
        self.assertEqual(validate_positive_number("10.5", "Quantity"), 10.5)
        with self.assertRaises(ValueError):
            validate_positive_number("0", "Quantity")
        with self.assertRaises(ValueError):
            validate_positive_number("abc", "Quantity")

    def test_moisture(self):
        self.assertEqual(validate_moisture("13"), 13.0)
        with self.assertRaises(ValueError):
            validate_moisture("0.5")
        with self.assertRaises(ValueError):
            validate_moisture("13.1")

    def test_grade_calculations(self):
        original, deduction, accepted = calculate_values(10, 1000, "Grade 1")
        self.assertEqual((original, deduction, accepted), (10000, 0, 10000))

        original, deduction, accepted = calculate_values(10, 1000, "Grade 2")
        self.assertEqual((original, deduction, accepted), (10000, 500, 9500))

        original, deduction, accepted = calculate_values(10, 1000, "Rejected")
        self.assertEqual((original, deduction, accepted), (10000, 10000, 0))

    def test_database_and_report(self):
        with tempfile.TemporaryDirectory() as temp:
            db = GCXDatabase(Path(temp) / "test.db")
            db.add_delivery({
                "receipt_no": "GCX-TAM-20260720-001",
                "depositor_name": "Test Farmer",
                "warehouse_location": "Tamale",
                "commodity_type": "Maize",
                "quantity_mt": 20.0,
                "moisture_content": 12.5,
                "quality_grade": "Grade 1",
                "price_per_mt": 3000.0,
                "original_value": 60000.0,
                "quality_deduction": 0.0,
                "accepted_value": 60000.0,
                "received_at": "2026-07-20T10:30:00",
            })
            records = db.fetch_deliveries({"date": "2026-07-20"})
            report = build_daily_report(records, "Tamale", "2026-07-20")
            self.assertIn("Total Deliveries: 1", report)
            self.assertIn("Maize: 20.00 MT", report)
            db.close()


if __name__ == "__main__":
    unittest.main()
