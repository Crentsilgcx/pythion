
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
        self.assertEqual(validate_moisture("0.5"), 0.5)
        self.assertEqual(validate_moisture("13.1"), 13.1)
        with self.assertRaises(ValueError):
            validate_moisture("-1")
        with self.assertRaises(ValueError):
            validate_moisture("101")
        with self.assertRaises(ValueError):
            validate_moisture("nan")

    def test_positive_number_rejects_non_finite(self):
        with self.assertRaises(ValueError):
            validate_positive_number("nan", "Quantity")
        with self.assertRaises(ValueError):
            validate_positive_number("inf", "Quantity")

    def test_grade_calculations(self):
        original, deduction, accepted = calculate_values(10, 1000, "Grade 1")
        self.assertEqual((original, deduction, accepted), (10000, 0, 10000))

        original, deduction, accepted = calculate_values(10, 1000, "Grade 2")
        self.assertEqual((original, deduction, accepted), (10000, 500, 9500))

        original, deduction, accepted = calculate_values(10, 1000, "Rejected")
        self.assertEqual((original, deduction, accepted), (10000, 10000, 0))

    @staticmethod
    def sample_record(receipt="GCX-TAM-20260720-001"):
        return {
            "receipt_no": receipt,
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
        }

    def test_database_and_report(self):
        with tempfile.TemporaryDirectory() as temp:
            db = GCXDatabase(Path(temp) / "test.db")
            db.add_delivery(self.sample_record())
            records = db.fetch_deliveries({"date": "2026-07-20"})
            report = build_daily_report(records, "Tamale", "2026-07-20")
            self.assertIn("Total Deliveries: 1", report)
            self.assertIn("Maize: 20.00 MT", report)
            db.close()

    def test_get_update_delete(self):
        with tempfile.TemporaryDirectory() as temp:
            db = GCXDatabase(Path(temp) / "test.db")
            db.add_delivery(self.sample_record())
            record_id = db.fetch_deliveries()[0]["id"]

            fetched = db.get_delivery(record_id)
            self.assertEqual(fetched["depositor_name"], "Test Farmer")
            self.assertIsNone(fetched["updated_at"])

            db.update_delivery(record_id, {
                "depositor_name": "Corrected Farmer",
                "quantity_mt": 25.0,
                "updated_at": "2026-07-21T09:00:00",
            })
            updated = db.get_delivery(record_id)
            self.assertEqual(updated["depositor_name"], "Corrected Farmer")
            self.assertEqual(updated["quantity_mt"], 25.0)
            self.assertEqual(updated["updated_at"], "2026-07-21T09:00:00")
            # untouched fields keep their values
            self.assertEqual(updated["receipt_no"], "GCX-TAM-20260720-001")

            db.delete_delivery(record_id)
            self.assertIsNone(db.get_delivery(record_id))
            self.assertEqual(len(db.fetch_deliveries()), 0)
            db.close()

    def test_updated_at_migration(self):
        # simulate a database created by the old schema (no updated_at column)
        import sqlite3
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "old.db"
            conn = sqlite3.connect(path)
            conn.execute(
                """
                CREATE TABLE deliveries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_no TEXT UNIQUE NOT NULL,
                    depositor_name TEXT NOT NULL,
                    warehouse_location TEXT NOT NULL,
                    commodity_type TEXT NOT NULL,
                    quantity_mt REAL NOT NULL,
                    moisture_content REAL NOT NULL,
                    quality_grade TEXT NOT NULL,
                    price_per_mt REAL NOT NULL,
                    original_value REAL NOT NULL,
                    quality_deduction REAL NOT NULL,
                    accepted_value REAL NOT NULL,
                    received_at TEXT NOT NULL
                )
                """
            )
            conn.commit()
            conn.close()

            db = GCXDatabase(path)  # must add the missing column without error
            db.add_delivery(self.sample_record())
            row = db.fetch_deliveries()[0]
            self.assertIsNone(row["updated_at"])
            db.close()


if __name__ == "__main__":
    unittest.main()
