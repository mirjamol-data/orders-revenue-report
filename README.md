# Orders Revenue Report

A small Python script that reads an `orders.csv` file, skips and reports invalid rows, and prints **revenue per customer per month**, sorted by revenue (highest first).

Uses only the Python standard library, so there is nothing to install.

## Requirements

- Python 3.8+ (3.11+ recommended)

## Input format

`orders.csv` must have a header row with these columns:

| column        | description                        | example               |
|---------------|------------------------------------|-----------------------|
| `order_id`    | unique order identifier            | `1001`                |
| `customer_id` | customer identifier                | `C001`                |
| `amount`      | order amount, non-negative number  | `120.50`              |
| `created_at`  | order date/time (ISO style)        | `2026-01-05 10:15:00` |

Accepted date formats: `YYYY-MM-DD`, `YYYY-MM-DD HH:MM:SS`, `YYYY-MM-DDTHH:MM:SS`, and other ISO 8601 variants.

## Usage

```bash
python revenue_report.py              # reads ./orders.csv
python revenue_report.py data.csv     # reads a different file
```

Invalid rows are reported on **stderr** and the report goes to **stdout**, so you can save just the report:

```bash
python revenue_report.py > report.txt
```

## Validation rules

A row is skipped (and reported with its line number and reason) if:

- any required field is missing or empty
- `amount` is not a number, is not finite, or is negative
- `created_at` cannot be parsed as a date
- `order_id` was already seen earlier in the file (duplicate)
- the row has more columns than the header

If the file is missing a required column entirely, the script stops with an error.

## Example output

Using the sample `orders.csv` in this repo:

```
Skipped 6 invalid row(s):
  line 6: amount 'abc' is not a number  ->  5,C002,abc,2026-02-03
  line 7: missing value for 'customer_id'  ->  6,,35.00,2026-02-10
  line 9: unrecognised date 'not-a-date'  ->  8,C003,15.25,not-a-date
  line 10: amount '-10.00' is negative  ->  9,C002,-10.00,2026-02-20
  line 11: duplicate order_id '3'  ->  3,C004,99.99,2026-02-21
  line 13: too many columns  ->  11,C004,60.00,2026-03-01,extra

Valid rows: 7 | Invalid rows: 6

customer_id    month          revenue
-------------------------------------
C001           2026-02         300.00
C003           2026-02         200.00
C001           2026-01         170.00
C002           2026-02         150.00
C002           2026-01          80.00
C003           2026-03          75.75
```

## Design notes

- **`Decimal` instead of `float`** for money, so totals like `0.1 + 0.2` are exact.
- **Streaming read** with `csv.DictReader`: rows are processed one at a time, so large files don't need to fit in memory.
- **Sorting** is by revenue descending, then customer and month, so the output is deterministic.
