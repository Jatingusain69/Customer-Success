# Retail Inventory and Order Analysis

Self-directed project built on **sample (dummy) data**. It looks at inventory levels, orders, product demand and stock movement for a small retail business, finds low-stock items and flags missing or inconsistent records before reporting.

## What it does
- Reports data quality problems in both tables (duplicates, missing values, negative stock, unknown SKUs, invalid quantities, inconsistent status labels)
- Cleans orders and inventory; records it cannot trust are listed for review instead of being guessed
- Finds low-stock items (stock at or below reorder level) and estimates days of cover from the last 90 days of demand
- Shows monthly order trends with growth, top-demand SKUs, category demand and order status share
- Same logic in Python (Pandas) and SQL

## Results (sample data)
- Orders: 906 raw rows, 880 after cleaning. Inventory: 41 raw rows, 40 SKUs
- 11 data quality checks run; 7 inventory records sent for review (missing or negative stock, missing reorder level)
- 8 low-stock items; most urgent: Almonds 500g (about 22 days of cover), Smartwatch (50 days), Air Fryer (56 days)
- Orders rise sharply in Q4: 98 in October and 128 in November, against 46 to 76 in earlier months
- Order status: 78.8% delivered, 10.3% shipped, 7.0% cancelled, 3.9% returned
- Top SKU by units: Webcam (655 units), then Electric Kettle and Almonds 500g

## Files
| Path | Description |
|---|---|
| `data/inventory.csv`, `data/orders.csv` | Raw sample data with deliberate issues |
| `inventory_analysis.py` | Pandas script: quality report, cleaning, low stock, trends |
| `sql/inventory_orders.sql` | Quality checks, clean views and analysis queries |
| `inventory_summary.xlsx` | Summary workbook (data quality, low stock, trend, top demand, items to review) |
| `outputs/` | Report tables as CSV |

## How to run
```
pip install pandas openpyxl
python inventory_analysis.py
```

## Tools
Python (Pandas), SQL (window functions, joins, CASE), Excel

*All data is dummy and created for learning.*
