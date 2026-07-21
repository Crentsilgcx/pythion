
import csv
import json
import math
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
from pathlib import Path

APP_TITLE = "GCX Warehouse Commodity Intake and Reporting System"
DB_FILE = Path(__file__).with_name("gcx_warehouse.db")

COMMODITIES = ("Maize", "Soybean", "Sesame", "Sorghum")
GRADES = ("Grade 1", "Grade 2", "Rejected")
WAREHOUSES = ("Tamale", "Kumasi", "Tema", "Wa", "Takoradi", "Accra", "Bolgatanga")
MIN_MOISTURE = 0.0
MAX_MOISTURE = 100.0

MOISTURE_LIMITS = {
    "Maize": 13.5,
    "Soybean": 13.0,
    "Sesame": 8.0,
    "Sorghum": 13.5,
}


def money(value):
    return f"GHS {value:,.2f}"


class GCXDatabase:
    def __init__(self, db_path=DB_FILE):
        self.db_path = Path(db_path)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS deliveries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_no TEXT UNIQUE NOT NULL,
                depositor_name TEXT NOT NULL,
                warehouse_location TEXT NOT NULL,
                commodity_type TEXT NOT NULL,
                quantity_mt REAL NOT NULL CHECK(quantity_mt > 0),
                moisture_content REAL NOT NULL CHECK(moisture_content BETWEEN 0 AND 100),
                quality_grade TEXT NOT NULL,
                price_per_mt REAL NOT NULL CHECK(price_per_mt > 0),
                original_value REAL NOT NULL,
                quality_deduction REAL NOT NULL,
                accepted_value REAL NOT NULL,
                received_at TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def generate_receipt_no(self, warehouse, received_at):
        code = "".join(ch for ch in warehouse.upper() if ch.isalnum())[:3] or "WH"
        day = received_at.strftime("%Y%m%d")
        prefix = f"GCX-{code}-{day}-"
        rows = self.connection.execute(
            "SELECT receipt_no FROM deliveries WHERE receipt_no LIKE ?",
            (prefix + "%",),
        ).fetchall()
        highest = 0
        for row in rows:
            suffix = row["receipt_no"][len(prefix):]
            if suffix.isdigit():
                highest = max(highest, int(suffix))
        return f"{prefix}{highest + 1:03d}"

    def add_delivery(self, record):
        columns = ", ".join(record.keys())
        placeholders = ", ".join("?" for _ in record)
        self.connection.execute(
            f"INSERT INTO deliveries ({columns}) VALUES ({placeholders})",
            tuple(record.values()),
        )
        self.connection.commit()

    def fetch_deliveries(self, filters=None):
        filters = filters or {}
        sql = "SELECT * FROM deliveries WHERE 1=1"
        params = []

        if filters.get("depositor"):
            sql += " AND LOWER(depositor_name) LIKE ?"
            params.append(f"%{filters['depositor'].lower()}%")
        if filters.get("commodity"):
            sql += " AND commodity_type = ?"
            params.append(filters["commodity"])
        if filters.get("warehouse"):
            sql += " AND LOWER(warehouse_location) LIKE ?"
            params.append(f"%{filters['warehouse'].lower()}%")
        if filters.get("grade"):
            sql += " AND quality_grade = ?"
            params.append(filters["grade"])
        if filters.get("min_quantity") is not None:
            sql += " AND quantity_mt > ?"
            params.append(filters["min_quantity"])
        if filters.get("date"):
            sql += " AND DATE(received_at) = ?"
            params.append(filters["date"])

        sql += " ORDER BY received_at DESC, id DESC"
        return self.connection.execute(sql, params).fetchall()

    def close(self):
        self.connection.close()


def validate_non_empty(value, field_name):
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name} must not be empty.")
    return value


def validate_positive_number(value, field_name):
    try:
        number = float(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid number.") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field_name} must be a valid number.")
    if number <= 0:
        raise ValueError(f"{field_name} must be greater than zero.")
    return number


def validate_moisture(value):
    try:
        number = float(value)
    except ValueError as exc:
        raise ValueError("Moisture content must be a valid number.") from exc
    if not math.isfinite(number) or not MIN_MOISTURE <= number <= MAX_MOISTURE:
        raise ValueError("Moisture content must be between 0% and 100%.")
    return number

def calculate_values(quantity, price, grade):
    original = quantity * price
    if grade == "Grade 1":
        deduction = 0.0
        accepted = original
    elif grade == "Grade 2":
        deduction = original * 0.05
        accepted = original - deduction
    else:
        deduction = original
        accepted = 0.0
    return original, deduction, accepted


def build_daily_report(records, warehouse, report_date):
    total_deliveries = len(records)
    total_quantity = sum(r["quantity_mt"] for r in records)
    accepted_value = sum(r["accepted_value"] for r in records)
    grade_counts = {
        "Grade 1": sum(r["quality_grade"] == "Grade 1" for r in records),
        "Grade 2": sum(r["quality_grade"] == "Grade 2" for r in records),
        "Rejected": sum(r["quality_grade"] == "Rejected" for r in records),
    }

    commodity_totals = {}
    for row in records:
        commodity_totals[row["commodity_type"]] = (
            commodity_totals.get(row["commodity_type"], 0) + row["quantity_mt"]
        )

    highest_commodity = max(commodity_totals, key=commodity_totals.get) if commodity_totals else "N/A"
    largest_delivery = max((r["quantity_mt"] for r in records), default=0)
    average_moisture = (
        sum(r["moisture_content"] for r in records) / total_deliveries
        if total_deliveries else 0
    )

    lines = [
        "GCX DAILY WAREHOUSE REPORT",
        f"Warehouse: {warehouse or 'All Warehouses'}",
        f"Date: {report_date}",
        "",
        f"Total Deliveries: {total_deliveries}",
        f"Total Quantity: {total_quantity:,.2f} MT",
        f"Accepted Commodity Value: {money(accepted_value)}",
        "",
        f"Grade 1 Deliveries: {grade_counts['Grade 1']}",
        f"Grade 2 Deliveries: {grade_counts['Grade 2']}",
        f"Rejected Deliveries: {grade_counts['Rejected']}",
        "",
        f"Commodity with Highest Total Quantity: {highest_commodity}",
        f"Largest Individual Delivery: {largest_delivery:,.2f} MT",
        f"Average Moisture Content: {average_moisture:,.2f}%",
        "",
        "COMMODITY SUMMARY",
    ]
    if commodity_totals:
        for commodity in sorted(commodity_totals):
            lines.append(f"{commodity}: {commodity_totals[commodity]:,.2f} MT")
    else:
        lines.append("No records found.")
    return "\n".join(lines)


class GCXApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("980x760")
        self.minsize(820, 650)
        self.db = GCXDatabase()
        self.dark_mode = False
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self.status_var = tk.StringVar(value="Ready")
        self.apply_theme()
        self.create_header()
        self.create_tabs()
        self.create_status_bar()
        self.refresh_table()

    def theme_colours(self):
        if self.dark_mode:
            return {
                "bg": "#101714",
                "surface": "#18221E",
                "surface_alt": "#24332C",
                "text": "#F2F7F4",
                "muted": "#A9B8B0",
                "primary": "#36B785",
                "primary_active": "#2CA474",
                "border": "#31433A",
                "entry": "#202D27",
                "danger": "#E97979",
            }
        return {
            "bg": "#F2F6F4",
            "surface": "#FFFFFF",
            "surface_alt": "#E7F0EC",
            "text": "#17231D",
            "muted": "#68766F",
            "primary": "#0B6B50",
            "primary_active": "#075640",
            "border": "#D5E1DB",
            "entry": "#FFFFFF",
            "danger": "#B84444",
        }

    def apply_theme(self):
        c = self.theme_colours()
        self.configure(bg=c["bg"])

        self.style.configure(".", font=("Segoe UI", 10))
        self.style.configure("TFrame", background=c["bg"])
        self.style.configure("Header.TFrame", background=c["surface"])
        self.style.configure(
            "TLabel",
            background=c["bg"],
            foreground=c["text"],
        )
        self.style.configure(
            "HeaderTitle.TLabel",
            background=c["surface"],
            foreground=c["muted"],
            font=("Segoe UI", 11),
        )
        self.style.configure(
            "Brand.TLabel",
            background=c["surface"],
            foreground=c["primary"],
            font=("Segoe UI", 22, "bold"),
        )
        self.style.configure(
            "Title.TLabel",
            background=c["bg"],
            foreground=c["text"],
            font=("Segoe UI", 18, "bold"),
        )
        self.style.configure(
            "MetricTitle.TLabel",
            background=c["surface"],
            foreground=c["muted"],
            font=("Segoe UI", 9),
        )
        self.style.configure(
            "MetricValue.TLabel",
            background=c["surface"],
            foreground=c["text"],
            font=("Segoe UI", 16, "bold"),
        )

        self.style.configure(
            "TLabelframe",
            background=c["surface"],
            bordercolor=c["border"],
            relief="solid",
            borderwidth=1,
        )
        self.style.configure(
            "TLabelframe.Label",
            background=c["surface"],
            foreground=c["text"],
            font=("Segoe UI", 10, "bold"),
        )

        self.style.configure(
            "TEntry",
            fieldbackground=c["entry"],
            foreground=c["text"],
            insertcolor=c["text"],
            bordercolor=c["border"],
            padding=8,
        )
        self.style.configure(
            "TCombobox",
            fieldbackground=c["entry"],
            foreground=c["text"],
            arrowcolor=c["text"],
            bordercolor=c["border"],
            padding=7,
        )

        self.style.configure(
            "TButton",
            background=c["surface_alt"],
            foreground=c["text"],
            borderwidth=0,
            padding=(12, 9),
        )
        self.style.map(
            "TButton",
            background=[("active", c["border"])],
        )
        self.style.configure(
            "Primary.TButton",
            background=c["primary"],
            foreground="#FFFFFF",
            borderwidth=0,
            padding=(14, 10),
            font=("Segoe UI", 10, "bold"),
        )
        self.style.map(
            "Primary.TButton",
            background=[("active", c["primary_active"])],
        )
        self.style.configure(
            "Secondary.TButton",
            background=c["surface_alt"],
            foreground=c["text"],
            borderwidth=0,
            padding=(12, 9),
        )

        self.style.configure(
            "TNotebook",
            background=c["bg"],
            borderwidth=0,
        )
        self.style.configure(
            "TNotebook.Tab",
            background=c["surface_alt"],
            foreground=c["muted"],
            padding=(14, 10),
            borderwidth=0,
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", c["surface"])],
            foreground=[("selected", c["primary"])],
        )

        self.style.configure(
            "Treeview",
            background=c["surface"],
            fieldbackground=c["surface"],
            foreground=c["text"],
            rowheight=30,
            bordercolor=c["border"],
        )
        self.style.configure(
            "Treeview.Heading",
            background=c["surface_alt"],
            foreground=c["text"],
            font=("Segoe UI", 9, "bold"),
            padding=7,
        )
        self.style.map(
            "Treeview",
            background=[("selected", c["primary"])],
            foreground=[("selected", "#FFFFFF")],
        )

        self.style.configure(
            "Status.TLabel",
            background=c["surface"],
            foreground=c["muted"],
            padding=(10, 6),
        )

        for name in ("preview", "report_text"):
            widget = getattr(self, name, None)
            if widget is not None:
                try:
                    widget.configure(
                        bg=c["entry"],
                        fg=c["text"],
                        insertbackground=c["text"],
                        selectbackground=c["primary"],
                        relief="flat",
                        highlightthickness=1,
                        highlightbackground=c["border"],
                        highlightcolor=c["primary"],
                    )
                except tk.TclError:
                    pass

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        if hasattr(self, "theme_button"):
            self.theme_button.configure(
                text="☀ Light" if self.dark_mode else "🌙 Dark"
            )

    def create_header(self):
        self.header = ttk.Frame(self, style="Header.TFrame", padding=(18, 12))
        self.header.pack(fill="x")

        brand = ttk.Frame(self.header, style="Header.TFrame")
        brand.pack(side="left", fill="x", expand=True)

        ttk.Label(
            brand,
            text="GCX",
            style="Brand.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            brand,
            text="Warehouse Commodity Intake & Reporting",
            style="HeaderTitle.TLabel",
        ).pack(anchor="w")

        controls = ttk.Frame(self.header, style="Header.TFrame")
        controls.pack(side="right")

        self.theme_button = ttk.Button(
            controls,
            text="🌙 Dark",
            command=self.toggle_theme,
            style="Secondary.TButton",
        )
        self.theme_button.pack(side="right")


    def create_tabs(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(10, 8))

        self.dashboard_tab = ttk.Frame(self.notebook, padding=12)
        self.intake_tab = ttk.Frame(self.notebook, padding=16)
        self.records_tab = ttk.Frame(self.notebook, padding=12)
        self.report_tab = ttk.Frame(self.notebook, padding=12)

        self.notebook.add(self.dashboard_tab, text="Dashboard")
        self.notebook.add(self.intake_tab, text="New Delivery")
        self.notebook.add(self.records_tab, text="Search & Records")
        self.notebook.add(self.report_tab, text="Daily Report")

        self.build_dashboard_tab()
        self.build_intake_tab()
        self.build_records_tab()
        self.build_report_tab()

    def create_status_bar(self):
        ttk.Label(
            self,
            textvariable=self.status_var,
            anchor="w",
            style="Status.TLabel",
        ).pack(fill="x", side="bottom")

    def build_dashboard_tab(self):
        ttk.Label(
            self.dashboard_tab,
            text="Warehouse Dashboard",
            style="Title.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            self.dashboard_tab,
            text="Commodity intake overview across all warehouse locations.",
        ).pack(anchor="w", pady=(2, 12))

        cards = ttk.Frame(self.dashboard_tab)
        cards.pack(fill="x")

        self.dashboard_labels = {}
        metrics = (
            ("deliveries", "Total Deliveries"),
            ("quantity", "Total Quantity"),
            ("value", "Accepted Value"),
            ("rejected", "Rejected Deliveries"),
        )
        for index, (key, label) in enumerate(metrics):
            card = ttk.LabelFrame(cards, padding=14)
            card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=6, pady=6)
            ttk.Label(card, text=label, style="MetricTitle.TLabel").pack(anchor="w")
            value = ttk.Label(card, text="0", style="MetricValue.TLabel")
            value.pack(anchor="w", pady=(5, 0))
            self.dashboard_labels[key] = value
        cards.columnconfigure(0, weight=1)
        cards.columnconfigure(1, weight=1)

        warehouse_frame = ttk.LabelFrame(
            self.dashboard_tab,
            text="Warehouse Quantity Summary",
            padding=10,
        )
        warehouse_frame.pack(fill="both", expand=True, pady=(12, 8))

        self.dashboard_tree = ttk.Treeview(
            warehouse_frame,
            columns=("warehouse", "deliveries", "quantity"),
            show="headings",
            height=8,
        )
        self.dashboard_tree.heading("warehouse", text="Warehouse")
        self.dashboard_tree.heading("deliveries", text="Deliveries")
        self.dashboard_tree.heading("quantity", text="Quantity (MT)")
        self.dashboard_tree.column("warehouse", width=180, anchor="w")
        self.dashboard_tree.column("deliveries", width=100, anchor="center")
        self.dashboard_tree.column("quantity", width=130, anchor="center")
        self.dashboard_tree.pack(fill="both", expand=True)

        ttk.Label(
            self.dashboard_tab,
            text="Per-commodity moisture limits — Maize/Sorghum 13.5%, Soybean 13.0%, Sesame 8.0%",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(4, 6))

        ttk.Button(
            self.dashboard_tab,
            text="Refresh Dashboard",
            command=self.refresh_dashboard,
            style="Primary.TButton",
        ).pack(anchor="e")

        self.refresh_dashboard()

    def refresh_dashboard(self):
        if not hasattr(self, "dashboard_labels"):
            return

        records = self.db.fetch_deliveries()
        total_quantity = sum(row["quantity_mt"] for row in records)
        total_value = sum(row["accepted_value"] for row in records)
        rejected = sum(row["quality_grade"] == "Rejected" for row in records)

        self.dashboard_labels["deliveries"].configure(text=str(len(records)))
        self.dashboard_labels["quantity"].configure(text=f"{total_quantity:,.2f} MT")
        self.dashboard_labels["value"].configure(text=money(total_value))
        self.dashboard_labels["rejected"].configure(text=str(rejected))

        stats = {
            warehouse: {"deliveries": 0, "quantity": 0.0}
            for warehouse in WAREHOUSES
        }
        for row in records:
            warehouse = row["warehouse_location"]
            if warehouse not in stats:
                stats[warehouse] = {"deliveries": 0, "quantity": 0.0}
            stats[warehouse]["deliveries"] += 1
            stats[warehouse]["quantity"] += row["quantity_mt"]

        for item in self.dashboard_tree.get_children():
            self.dashboard_tree.delete(item)

        for warehouse in WAREHOUSES:
            values = stats[warehouse]
            self.dashboard_tree.insert(
                "",
                "end",
                values=(
                    warehouse,
                    values["deliveries"],
                    f'{values["quantity"]:,.2f}',
                ),
            )

    def build_intake_tab(self):
        form = ttk.LabelFrame(self.intake_tab, text="Commodity Delivery Details", padding=18)
        form.pack(fill="x")

        self.form_vars = {
            "depositor": tk.StringVar(),
            "warehouse": tk.StringVar(value=WAREHOUSES[0]),
            "commodity": tk.StringVar(value=COMMODITIES[0]),
            "quantity": tk.StringVar(),
            "moisture": tk.StringVar(),
            "grade": tk.StringVar(value=GRADES[0]),
            "price": tk.StringVar(),
        }

        fields = [
            ("Depositor / Farmer Name", "depositor"),
            ("Warehouse Location", "warehouse"),
            ("Commodity Type", "commodity"),
            ("Quantity Delivered (MT)", "quantity"),
            ("Moisture Content (%)", "moisture"),
            ("Quality Grade", "grade"),
            ("Price per Metric Tonne (GHS)", "price"),
        ]

        for idx, (label, key) in enumerate(fields):
            row = idx // 2
            col = (idx % 2) * 2
            ttk.Label(form, text=label).grid(row=row, column=col, sticky="w", padx=8, pady=8)
            if key == "warehouse":
                widget = ttk.Combobox(
                    form, textvariable=self.form_vars[key],
                    values=WAREHOUSES, state="readonly", width=34
                )
            elif key == "commodity":
                widget = ttk.Combobox(
                    form, textvariable=self.form_vars[key],
                    values=COMMODITIES, state="readonly", width=34
                )
            elif key == "grade":
                widget = ttk.Combobox(
                    form, textvariable=self.form_vars[key],
                    values=GRADES, state="readonly", width=34
                )
            else:
                widget = ttk.Entry(form, textvariable=self.form_vars[key], width=37)
            widget.grid(row=row, column=col + 1, sticky="ew", padx=8, pady=8)

        for col in (1, 3):
            form.columnconfigure(col, weight=1)

        hint = (
            "Moisture content must be between 0% and 100%. "
            "Warehouse locations are selected from the approved GCX list. "
            "Grade 2 attracts a 5% deduction; rejected deliveries have GHS 0.00 accepted value."
        )
        ttk.Label(self.intake_tab, text=hint, wraplength=1050).pack(anchor="w", pady=(12, 6))

        btns = ttk.Frame(self.intake_tab)
        btns.pack(fill="x", pady=8)
        ttk.Button(btns, text="Save Delivery", command=self.save_delivery, style="Primary.TButton").pack(side="left")
        ttk.Button(btns, text="Clear Form", command=self.clear_form).pack(side="left", padx=8)

        self.preview = tk.Text(self.intake_tab, height=13, wrap="word", state="disabled")
        self.preview.pack(fill="both", expand=True, pady=(10, 0))
        self.apply_theme()

    def build_records_tab(self):
        filters = ttk.LabelFrame(self.records_tab, text="Search and Filter", padding=10)
        filters.pack(fill="x")

        self.filter_vars = {
            "depositor": tk.StringVar(),
            "commodity": tk.StringVar(value="All"),
            "warehouse": tk.StringVar(),
            "grade": tk.StringVar(value="All"),
            "min_quantity": tk.StringVar(),
        }

        ttk.Label(filters, text="Depositor").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(filters, textvariable=self.filter_vars["depositor"], width=20).grid(row=0, column=1, padx=5)
        ttk.Label(filters, text="Commodity").grid(row=0, column=2, padx=5)
        ttk.Combobox(
            filters, textvariable=self.filter_vars["commodity"],
            values=("All",) + COMMODITIES, state="readonly", width=14
        ).grid(row=0, column=3, padx=5)
        ttk.Label(filters, text="Warehouse").grid(row=0, column=4, padx=5)
        ttk.Combobox(
            filters,
            textvariable=self.filter_vars["warehouse"],
            values=("",) + WAREHOUSES,
            state="readonly",
            width=16,
        ).grid(row=0, column=5, padx=5)
        ttk.Label(filters, text="Grade").grid(row=0, column=6, padx=5)
        ttk.Combobox(
            filters, textvariable=self.filter_vars["grade"],
            values=("All",) + GRADES, state="readonly", width=12
        ).grid(row=0, column=7, padx=5)
        ttk.Label(filters, text="Quantity Above").grid(row=0, column=8, padx=5)
        ttk.Entry(filters, textvariable=self.filter_vars["min_quantity"], width=12).grid(row=0, column=9, padx=5)

        ttk.Button(filters, text="Apply", command=self.refresh_table, style="Primary.TButton").grid(row=0, column=10, padx=5)
        ttk.Button(filters, text="Reset", command=self.reset_filters).grid(row=0, column=11, padx=5)

        columns = (
            "receipt", "date", "depositor", "warehouse", "commodity", "quantity",
            "moisture", "grade", "price", "accepted"
        )
        tree_frame = ttk.Frame(self.records_tab)
        tree_frame.pack(fill="both", expand=True, pady=(10, 0))
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
        headings = {
            "receipt": "Receipt No.",
            "date": "Received",
            "depositor": "Depositor",
            "warehouse": "Warehouse",
            "commodity": "Commodity",
            "quantity": "Qty (MT)",
            "moisture": "Moisture %",
            "grade": "Grade",
            "price": "Price/MT",
            "accepted": "Accepted Value",
        }
        widths = {
            "receipt": 160, "date": 125, "depositor": 150, "warehouse": 130,
            "commodity": 95, "quantity": 80, "moisture": 85, "grade": 80,
            "price": 100, "accepted": 125
        }
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center")

        yscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(self.records_tab, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        yscroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        xscroll.pack(fill="x")

        actions = ttk.Frame(self.records_tab)
        actions.pack(fill="x", pady=8)
        ttk.Button(actions, text="Export Filtered CSV", command=self.export_csv).pack(side="left")
        ttk.Button(actions, text="Export Filtered JSON", command=self.export_json).pack(side="left", padx=8)
        ttk.Button(actions, text="Show Three Largest", command=self.show_three_largest).pack(side="left")

    def build_report_tab(self):
        controls = ttk.Frame(self.report_tab)
        controls.pack(fill="x")

        self.report_date = tk.StringVar(value=date.today().isoformat())
        self.report_warehouse = tk.StringVar()

        ttk.Label(controls, text="Report Date (YYYY-MM-DD)").pack(side="left")
        ttk.Entry(controls, textvariable=self.report_date, width=14).pack(side="left", padx=6)
        ttk.Label(controls, text="Warehouse (blank = all)").pack(side="left", padx=(16, 0))
        ttk.Combobox(
            controls,
            textvariable=self.report_warehouse,
            values=("",) + WAREHOUSES,
            state="readonly",
            width=20,
        ).pack(side="left", padx=6)
        ttk.Button(controls, text="Generate Report", command=self.generate_report, style="Primary.TButton").pack(side="left", padx=6)
        ttk.Button(controls, text="Export Report TXT", command=self.export_report).pack(side="left")

        self.report_text = tk.Text(self.report_tab, wrap="word", font=("Consolas", 11))
        self.report_text.pack(fill="both", expand=True, pady=(12, 0))
        self.apply_theme()

    def save_delivery(self):
        try:
            depositor = validate_non_empty(self.form_vars["depositor"].get(), "Depositor name")
            warehouse = validate_non_empty(self.form_vars["warehouse"].get(), "Warehouse location")
            commodity = self.form_vars["commodity"].get()
            if commodity not in COMMODITIES:
                raise ValueError("Commodity must be maize, soybean, sesame or sorghum.")
            quantity = validate_positive_number(self.form_vars["quantity"].get(), "Quantity")
            moisture = validate_moisture(self.form_vars["moisture"].get())
            grade = self.form_vars["grade"].get()
            if grade not in GRADES:
                raise ValueError("Grade must be Grade 1, Grade 2 or Rejected.")
            price = validate_positive_number(self.form_vars["price"].get(), "Price")

            received_at = datetime.now()
            original, deduction, accepted = calculate_values(quantity, price, grade)

            record = {
                "depositor_name": depositor,
                "warehouse_location": warehouse,
                "commodity_type": commodity,
                "quantity_mt": quantity,
                "moisture_content": moisture,
                "quality_grade": grade,
                "price_per_mt": price,
                "original_value": original,
                "quality_deduction": deduction,
                "accepted_value": accepted,
                "received_at": received_at.isoformat(timespec="seconds"),
            }
            # Regenerate the receipt number and retry if a concurrent write
            # already claimed the same number (UNIQUE constraint violation).
            for attempt in range(5):
                receipt = self.db.generate_receipt_no(warehouse, received_at)
                try:
                    self.db.add_delivery({"receipt_no": receipt, **record})
                    break
                except sqlite3.IntegrityError:
                    if attempt == 4:
                        raise
            else:
                raise sqlite3.IntegrityError("Could not allocate a unique receipt number.")

            warning = ""
            limit = MOISTURE_LIMITS.get(commodity)
            if limit is not None and moisture > limit:
                warning = (
                    f"\n\nWARNING: Moisture content {moisture:.2f}% exceeds the "
                    f"configured {commodity} limit of {limit:.2f}%."
                )

            summary = (
                f"DELIVERY SAVED SUCCESSFULLY\n\n"
                f"Receipt Number: {receipt}\n"
                f"Depositor: {depositor}\n"
                f"Warehouse: {warehouse}\n"
                f"Commodity: {commodity}\n"
                f"Quantity: {quantity:,.2f} MT\n"
                f"Moisture Content: {moisture:,.2f}%\n"
                f"Quality Grade: {grade}\n"
                f"Price per MT: {money(price)}\n"
                f"Original Value: {money(original)}\n"
                f"Quality Deduction: {money(deduction)}\n"
                f"Final Accepted Value: {money(accepted)}\n"
                f"Date/Time Received: {received_at:%d %B %Y, %H:%M:%S}"
                f"{warning}"
            )
            self.preview.configure(state="normal")
            self.preview.delete("1.0", "end")
            self.preview.insert("1.0", summary)
            self.preview.configure(state="disabled")
            self.status_var.set(f"Saved delivery {receipt}")
            self.refresh_table()
            messagebox.showinfo("Delivery Saved", f"Delivery saved.\nReceipt: {receipt}")
        except ValueError as exc:
            messagebox.showerror("Invalid Information", str(exc))
        except sqlite3.Error as exc:
            messagebox.showerror(
                "Save Failed",
                f"The delivery could not be saved.\n\n{exc}",
            )

    def clear_form(self):
        for key in ("depositor", "quantity", "moisture", "price"):
            self.form_vars[key].set("")
        self.form_vars["warehouse"].set(WAREHOUSES[0])
        self.form_vars["commodity"].set(COMMODITIES[0])
        self.form_vars["grade"].set(GRADES[0])
        self.status_var.set("Form cleared")

    def get_filter_values(self):
        filters = {}
        if self.filter_vars["depositor"].get().strip():
            filters["depositor"] = self.filter_vars["depositor"].get().strip()
        if self.filter_vars["commodity"].get() != "All":
            filters["commodity"] = self.filter_vars["commodity"].get()
        if self.filter_vars["warehouse"].get().strip():
            filters["warehouse"] = self.filter_vars["warehouse"].get().strip()
        if self.filter_vars["grade"].get() != "All":
            filters["grade"] = self.filter_vars["grade"].get()
        if self.filter_vars["min_quantity"].get().strip():
            filters["min_quantity"] = validate_positive_number(
                self.filter_vars["min_quantity"].get(), "Quantity filter"
            )
        return filters

    def refresh_table(self):
        try:
            filters = self.get_filter_values() if hasattr(self, "filter_vars") else {}
            records = self.db.fetch_deliveries(filters)
        except ValueError as exc:
            messagebox.showerror("Invalid Filter", str(exc))
            return

        if hasattr(self, "tree"):
            for item in self.tree.get_children():
                self.tree.delete(item)
            for row in records:
                self.tree.insert(
                    "", "end",
                    values=(
                        row["receipt_no"],
                        row["received_at"].replace("T", " "),
                        row["depositor_name"],
                        row["warehouse_location"],
                        row["commodity_type"],
                        f"{row['quantity_mt']:,.2f}",
                        f"{row['moisture_content']:,.2f}",
                        row["quality_grade"],
                        f"{row['price_per_mt']:,.2f}",
                        f"{row['accepted_value']:,.2f}",
                    ),
                )
            self.status_var.set(f"{len(records)} record(s) displayed")
            self.refresh_dashboard()

    def reset_filters(self):
        self.filter_vars["depositor"].set("")
        self.filter_vars["commodity"].set("All")
        self.filter_vars["warehouse"].set("")
        self.filter_vars["grade"].set("All")
        self.filter_vars["min_quantity"].set("")
        self.refresh_table()

    def export_csv(self):
        try:
            records = self.db.fetch_deliveries(self.get_filter_values())
        except ValueError as exc:
            messagebox.showerror("Invalid Filter", str(exc))
            return
        if not records:
            messagebox.showwarning("No Records", "There are no records to export.")
            return
        path = filedialog.asksaveasfilename(
            title="Export CSV", defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(records[0].keys())
            writer.writerows([tuple(r) for r in records])
        self.status_var.set(f"CSV exported to {path}")

    def export_json(self):
        try:
            records = self.db.fetch_deliveries(self.get_filter_values())
        except ValueError as exc:
            messagebox.showerror("Invalid Filter", str(exc))
            return
        if not records:
            messagebox.showwarning("No Records", "There are no records to export.")
            return
        path = filedialog.asksaveasfilename(
            title="Export JSON", defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump([dict(r) for r in records], f, indent=2)
        self.status_var.set(f"JSON exported to {path}")

    def show_three_largest(self):
        records = sorted(
            self.db.fetch_deliveries(),
            key=lambda r: r["quantity_mt"],
            reverse=True
        )[:3]
        if not records:
            messagebox.showinfo("Three Largest Deliveries", "No deliveries have been recorded.")
            return
        text = "\n".join(
            f"{i}. {r['receipt_no']} - {r['commodity_type']} - {r['quantity_mt']:,.2f} MT"
            for i, r in enumerate(records, 1)
        )
        messagebox.showinfo("Three Largest Deliveries", text)

    def generate_report(self):
        try:
            datetime.strptime(self.report_date.get(), "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid Date", "Use the date format YYYY-MM-DD.")
            return
        filters = {"date": self.report_date.get()}
        warehouse = self.report_warehouse.get().strip()
        if warehouse:
            filters["warehouse"] = warehouse
        records = self.db.fetch_deliveries(filters)
        report = build_daily_report(records, warehouse, self.report_date.get())
        self.report_text.delete("1.0", "end")
        self.report_text.insert("1.0", report)
        self.status_var.set("Daily report generated")

    def export_report(self):
        report = self.report_text.get("1.0", "end").strip()
        if not report:
            self.generate_report()
            report = self.report_text.get("1.0", "end").strip()
        path = filedialog.asksaveasfilename(
            title="Export Daily Report", defaultextension=".txt",
            filetypes=[("Text files", "*.txt")]
        )
        if not path:
            return
        Path(path).write_text(report, encoding="utf-8")
        self.status_var.set(f"Report exported to {path}")

    def on_close(self):
        self.db.close()
        self.destroy()


if __name__ == "__main__":
    app = GCXApp()
    app.mainloop()
