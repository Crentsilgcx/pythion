
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
- `test_app.py` – unit tests for validation, calculations and reporting.
- `requirements.txt` – confirms that only the Python standard library is required.
- `screenshots/` – sample application views.

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


## Modern Interface Update

The application now includes:

- A professional **Light Theme** for bright office environments.
- A modern **Dark Theme** for low-light use.
- A theme toggle in the application header.
- A four-step guided commodity intake process:
  1. Depositor and warehouse
  2. Commodity and quantity
  3. Quality and pricing
  4. Review and submit
- Step-by-step validation before the officer can continue.
- A final review page showing the original value, deduction and accepted value.
- Modern cards, improved spacing, clearer buttons and enhanced record tables.

The light/dark theme affects the main interface, forms, tables, reports and navigation controls.


## Login, Edit and Update Workflow

### Login

The application opens with a secure login page. Passwords are stored as PBKDF2-SHA256 hashes with unique salts rather than plain text.

Default demonstration account:

- Username: `admin`
- Password: `GCX@2026`

Change this account before real operational deployment.

### Correcting an Existing Delivery

1. Sign in.
2. Open **Search & Records**.
3. Select the incorrect record.
4. Click **Edit Selected**, or double-click the record.
5. Correct the depositor, warehouse, commodity, quantity, moisture, grade or price.
6. Proceed through the guided steps.
7. Review the corrected values.
8. Click **Update Delivery**.
9. Confirm the update to commit the corrected record to SQLite.

The system records the update date/time and the username of the officer who made the correction.

### Submitting a New Delivery

Complete the four steps and click **Submit Delivery**. This commits the new record to the database and generates a receipt number.


## Review and Submit Controls

The final review page now includes:

- **Edit Details** — returns the officer to the first step without losing entered data.
- **Save Draft** — stores the delivery in SQLite so it can be reopened and completed later.
- **Submit Delivery** — commits the final record after confirmation.
- A confirmation checkbox that must be selected before submitting or updating a record.

The Submit and Update buttons remain disabled until the warehouse officer confirms that the reviewed information is correct.


## Dashboard, Warehouse List and Moisture Limit

The application includes a dashboard with total deliveries, total quantity, accepted value, rejected deliveries and warehouse-level quantity summaries.

Approved warehouses:
Tamale, Kumasi, Tema, Wa, Takoradi, Accra and Bolgatanga.

Moisture content validation accepts values from 1% to 13% inclusive.


## Modern Light and Dark Interface

This dashboard version now uses the same modern visual theme as the mobile-style application:

- Light and dark modes
- Theme toggle in the header
- GCX green accent colour
- Modern dashboard metric cards
- Improved tabs, tables, fields and buttons
- Compact responsive desktop layout
- Styled report and preview panels
- Warehouse drop-downs in intake, filters and reports
