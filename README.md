
# GCX Warehouse Commodity Intake and Reporting System

## Overview

This is a complete Python desktop application developed from the GCX practical assignment. It uses:

- **Tkinter** for the graphical user interface.
- **SQLite** for persistent storage.
- Python functions for validation, calculations, searching, filtering and reporting.
- CSV, JSON and text export features.

## Main Requirements Covered

1. Record one commodity delivery.
2. Validate depositor, commodity, quantity, moisture, grade and price.
3. Calculate original value, quality deduction and accepted value.
4. Record multiple deliveries.
5. Generate the daily warehouse report.
6. Organise the program into reusable functions and classes.
7. Save and reload records using SQLite.
8. Search and filter records.
9. Generate receipt numbers automatically.
10. Record exact delivery date and time.
11. Warn when moisture exceeds a configured commodity limit.
12. Export records to CSV/JSON and reports to TXT.
13. Show the three largest deliveries.
14. Calculate reports by warehouse.

## Business Rules

- Accepted commodities: Maize, Soybean, Sesame and Sorghum.
- Grade 1: no deduction.
- Grade 2: 5% deduction.
- Rejected: final accepted value is GHS 0.00.
- Quantity and price must be greater than zero.
- Moisture must be between 0% and 100%.
- A warning is shown when moisture exceeds the per-commodity limit
  (Maize/Sorghum 13.5%, Soybean 13.0%, Sesame 8.0%).

## How to Run

1. Install Python 3.10 or later.
2. Extract the project folder.
3. Open Command Prompt or PowerShell in the folder.
4. Run:

```bash
python app.py
```

No external Python package is required.

## Files

- `app.py` – main application.
- `sample_deliveries.csv` – sample records.
- `sample_deliveries.json` – sample records in JSON format.
- `sample_gcx_warehouse.db` – a ready-made SQLite database with a few demo deliveries.
- `test_app.py` – unit tests for validation, calculations and reporting.
- `requirements.txt` – confirms that only the Python standard library is required.

## Loading the Sample Database (Optional)

The application reads and writes `gcx_warehouse.db` in the project folder. To
start from the bundled demo data instead of an empty database, copy the sample
over (this is optional and only needed once):

```bash
cp sample_gcx_warehouse.db gcx_warehouse.db
```

On Windows PowerShell:

```powershell
Copy-Item sample_gcx_warehouse.db gcx_warehouse.db
```

The sample file itself is never modified by the application, so you can always
copy it again to reset the demo data.

## Running the Tests

```bash
python -m unittest test_app.py -v
```

## Five-Minute Demonstration Guide

1. Start the application.
2. Enter a depositor, warehouse, commodity, quantity, moisture, grade and price.
3. Save the delivery and explain the generated receipt number.
4. Show the original value, deduction and accepted value.
5. Open **Search & Records** and demonstrate depositor, commodity, warehouse, grade and quantity filters.
6. Export filtered records.
7. Open **Daily Report**, enter a date and warehouse, and generate the report.
8. Explain that records remain available after restarting because they are stored in SQLite.

## Python Concepts Learned

Variables, strings, numeric conversion, conditionals, loops, exception handling, lists, dictionaries, functions, parameters, return values, classes, file handling, JSON, CSV, SQLite, searching, filtering, aggregation and GUI programming.

## Difficulties and Resolutions

- Invalid numeric input is handled with `try/except` and user-friendly messages.
- Repeated records are safely stored in SQLite.
- Receipt numbers are generated from warehouse code, date and daily sequence.
- Summary calculations use filtered database records.
- Empty reports return zeros rather than causing errors.

## Security and Data Handling Notes

- Do not enter sensitive personal data beyond what the warehouse process requires.
- Restrict access to the application folder and database.
- Back up `gcx_warehouse.db` regularly.
- For production deployment, add authenticated users, role-based access, encryption, audit logs and a central database.


## Interface

The application is organised into four tabs:

- **Dashboard** — total deliveries, total quantity, accepted value, rejected
  deliveries and a per-warehouse quantity summary.
- **New Delivery** — a single form for capturing a commodity delivery, with a
  saved-delivery preview showing the original value, deduction and accepted value.
- **Search & Records** — filter by depositor, commodity, warehouse, grade and
  minimum quantity; export the filtered results to CSV or JSON; and list the
  three largest deliveries.
- **Daily Report** — generate and export a daily warehouse report by date and
  (optionally) warehouse.

Visual features:

- Light and dark modes with a theme toggle in the header.
- GCX green accent colour.
- Dashboard metric cards, styled tables, fields and report panels.
- Warehouse drop-downs in intake, filters and reports.

Approved warehouses: Tamale, Kumasi, Tema, Wa, Takoradi, Accra and Bolgatanga.
