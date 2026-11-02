#!/usr/bin/env python3
"""
revenue_report.py

Reads an orders CSV file (order_id, customer_id, amount, created_at),
skips and reports invalid rows, and prints revenue per customer per month
sorted by revenue (highest first).

Usage:
    python revenue_report.py                 # reads orders.csv
    python revenue_report.py path/to/file.csv
"""

import argparse
import csv
import sys
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation

REQUIRED_COLUMNS = ["order_id", "customer_id", "amount", "created_at"]

# Date formats we accept for created_at, tried in order.
DATE_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d",
]


def parse_date(value):
    """Turn a created_at string into a datetime, or raise ValueError."""
    value = value.strip()
    # fromisoformat handles most ISO 8601 variants 
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        pass
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"unrecognised date '{value}'")


def parse_amount(value):
    """Turn an amount string into a non-negative Decimal, or raise ValueError."""
    try:
        amount = Decimal(value.strip())
    except InvalidOperation:
        raise ValueError(f"amount '{value}' is not a number")
    if not amount.is_finite():
        raise ValueError(f"amount '{value}' is not a finite number")
    if amount < 0:
        raise ValueError(f"amount '{value}' is negative")
    return amount


def validate_row(row, seen_order_ids):
    """
    Check one CSV row. Returns (customer_id, month, amount) if valid,
    otherwise raises ValueError describing the first problem found.
    """
    # Missing or empty fields
    for col in REQUIRED_COLUMNS:
        if row.get(col) is None or row[col].strip() == "":
            raise ValueError(f"missing value for '{col}'")

    order_id = row["order_id"].strip()
    if order_id in seen_order_ids:
        raise ValueError(f"duplicate order_id '{order_id}'")

    customer_id = row["customer_id"].strip()
    amount = parse_amount(row["amount"])
    created_at = parse_date(row["created_at"])

    seen_order_ids.add(order_id)
    month = created_at.strftime("%Y-%m")
    return customer_id, month, amount


def read_orders(path):
    """
    Read the CSV, aggregate valid rows and collect invalid ones.
    Returns (revenue dict, list of invalid rows, number of valid rows).
    """
    revenue = defaultdict(Decimal)  # (customer_id, month) -> total
    invalid = []                    # (line_number, reason, raw_row)
    seen_order_ids = set()
    valid_count = 0

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise SystemExit(f"Error: CSV is missing required column(s): {', '.join(missing)}")

        # start=2 because line 1 is the header
        for line_no, row in enumerate(reader, start=2):
            # DictReader puts extra values under the key None
            if None in row:
                invalid.append((line_no, "too many columns", row))
                continue
            try:
                customer_id, month, amount = validate_row(row, seen_order_ids)
            except ValueError as e:
                invalid.append((line_no, str(e), row))
                continue
            revenue[(customer_id, month)] += amount
            valid_count += 1

    return revenue, invalid, valid_count


def print_invalid(invalid):
    """Report skipped rows on stderr so they don't mix with the report."""
    if not invalid:
        print("No invalid rows found.", file=sys.stderr)
        return
    print(f"Skipped {len(invalid)} invalid row(s):", file=sys.stderr)
    for line_no, reason, row in invalid:
        values = []
        for v in row.values():
            if isinstance(v, list):      # extra columns arrive as a list
                values.extend(v)
            else:
                values.append("" if v is None else v)
        raw = ",".join(values)
        print(f"  line {line_no}: {reason}  ->  {raw}", file=sys.stderr)
    print(file=sys.stderr)


def print_report(revenue):
    """Print revenue per customer per month, highest revenue first."""
    rows = sorted(
        revenue.items(),
        key=lambda item: (-item[1], item[0][0], item[0][1]),
    )
    print(f"{'customer_id':<15}{'month':<10}{'revenue':>12}")
    print("-" * 37)
    for (customer_id, month), total in rows:
        print(f"{customer_id:<15}{month:<10}{total:>12.2f}")


def main():
    parser = argparse.ArgumentParser(description="Revenue per customer per month.")
    parser.add_argument("csv_path", nargs="?", default="orders.csv",
                        help="path to the orders CSV (default: orders.csv)")
    args = parser.parse_args()

    try:
        revenue, invalid, valid_count = read_orders(args.csv_path)
    except FileNotFoundError:
        sys.exit(f"Error: file not found: {args.csv_path}")

    print_invalid(invalid)
    print(f"Valid rows: {valid_count} | Invalid rows: {len(invalid)}\n")
    print_report(revenue)


if __name__ == "__main__":
    main()
