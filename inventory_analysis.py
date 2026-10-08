"""Retail Inventory and Order Analysis (Pandas).
Run: python inventory_analysis.py
Finds data quality problems, low-stock items, order trends and demand per SKU.
Writes CSV reports to outputs/ and a summary workbook. Sample data only.
"""
import pandas as pd

inv = pd.read_csv("data/inventory.csv", keep_default_na=False, na_values=[""])
orders = pd.read_csv("data/orders.csv", keep_default_na=False, na_values=[""])
AS_OF = pd.Timestamp("2025-12-31")

# ---------- 1. data quality report (before cleaning) ----------
issues = [
    ("inventory", "Duplicate SKU rows", int(inv.duplicated("sku").sum())),
    ("inventory", "Missing stock_on_hand", int(inv["stock_on_hand"].isna().sum())),
    ("inventory", "Negative stock_on_hand", int((inv["stock_on_hand"] < 0).sum())),
    ("inventory", "Missing reorder_level", int(inv["reorder_level"].isna().sum())),
    ("inventory", "Missing supplier", int(inv["supplier"].isna().sum())),
    ("orders", "Duplicate order_id rows", int(orders.duplicated("order_id").sum())),
    ("orders", "Missing sku", int(orders["sku"].isna().sum())),
    ("orders", "SKU not in inventory", int((orders["sku"].notna() & ~orders["sku"].isin(inv["sku"])).sum())),
    ("orders", "Missing order_date", int(orders["order_date"].isna().sum())),
    ("orders", "Zero or negative qty", int((orders["qty"] <= 0).sum())),
    ("orders", "Status label in different case", int((orders["status"] != orders["status"].str.title()).sum())),
]
issue_df = pd.DataFrame(issues, columns=["table", "issue", "rows"])

# ---------- 2. cleaning ----------
inv = inv.drop_duplicates("sku").copy()
inv["supplier"] = inv["supplier"].fillna("Unknown")
inv_issue_rows = inv[inv["stock_on_hand"].isna() | (inv["stock_on_hand"] < 0) | inv["reorder_level"].isna()]
inv_valid = inv.drop(inv_issue_rows.index)          # rows we cannot trust are reviewed, not guessed
o = orders.drop_duplicates("order_id").copy()
o["status"] = o["status"].str.title()
o = o.dropna(subset=["sku", "order_date"])
o = o[(o["qty"] > 0) & o["sku"].isin(inv["sku"])].copy()
o["order_date"] = pd.to_datetime(o["order_date"])
o["order_month"] = o["order_date"].dt.strftime("%Y-%m")
valid = o[o["status"].isin(["Delivered", "Shipped"])]   # cancelled and returned orders are not demand

# ---------- 3. analysis ----------
monthly = o.groupby("order_month").agg(orders=("order_id", "count"), units=("qty", "sum")).reset_index()
monthly["order_growth_pct"] = (monthly["orders"].pct_change() * 100).round(1)
status_share = o["status"].value_counts(normalize=True).mul(100).round(1).rename_axis("status").reset_index(name="share_pct")

last90 = valid[valid["order_date"] > AS_OF - pd.Timedelta(days=90)]
demand = last90.groupby("sku")["qty"].sum().rename("units_last_90d")
stock = inv_valid.merge(demand, on="sku", how="left").fillna({"units_last_90d": 0})
stock["daily_demand"] = (stock["units_last_90d"] / 90).round(2)
stock["days_of_cover"] = (stock["stock_on_hand"] / stock["daily_demand"]).where(stock["daily_demand"] > 0).round(0)
stock["low_stock"] = stock["stock_on_hand"] <= stock["reorder_level"]
low = stock[stock["low_stock"]].copy()
low["shortfall_to_reorder"] = low["reorder_level"] - low["stock_on_hand"]
low = low.sort_values(["days_of_cover", "shortfall_to_reorder"], ascending=[True, False])[
    ["sku", "product_name", "category", "stock_on_hand", "reorder_level", "shortfall_to_reorder", "units_last_90d", "days_of_cover", "supplier"]]
top_demand = valid.groupby(["sku"])["qty"].sum().sort_values(ascending=False).head(10).reset_index().merge(inv[["sku", "product_name", "category"]], on="sku")
cat_demand = valid.merge(inv[["sku", "category"]], on="sku").groupby("category")["qty"].sum().sort_values(ascending=False).reset_index()
review = inv_issue_rows[["sku", "product_name", "stock_on_hand", "reorder_level", "supplier"]]

issue_df.to_csv("outputs/data_quality_issues.csv", index=False)
low.to_csv("outputs/low_stock_items.csv", index=False)
monthly.to_csv("outputs/monthly_order_trend.csv", index=False)
top_demand.to_csv("outputs/top_demand_skus.csv", index=False)
review.to_csv("outputs/inventory_records_to_review.csv", index=False)
with pd.ExcelWriter("inventory_summary.xlsx") as xw:
    issue_df.to_excel(xw, sheet_name="Data_Quality", index=False); low.to_excel(xw, sheet_name="Low_Stock", index=False)
    monthly.to_excel(xw, sheet_name="Order_Trend", index=False); top_demand.to_excel(xw, sheet_name="Top_Demand", index=False)
    cat_demand.to_excel(xw, sheet_name="Category_Demand", index=False); review.to_excel(xw, sheet_name="To_Review", index=False)

print("DATA QUALITY"); print(issue_df.to_string(index=False))
print(f"\nOrders: {len(orders)} raw -> {len(o)} clean | Inventory: {len(pd.read_csv('data/inventory.csv'))} raw -> {len(inv)} SKUs")
print(f"\nLOW STOCK ITEMS ({len(low)}):"); print(low.to_string(index=False))
print("\nORDER TREND:"); print(monthly.to_string(index=False))
print("\nSTATUS SHARE:"); print(status_share.to_string(index=False))
print("\nTOP 5 SKUs BY UNITS:"); print(top_demand.head(5).to_string(index=False))
print(f"\nInventory records sent for review: {len(review)}")
