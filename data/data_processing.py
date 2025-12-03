# data/data_processing.py
import glob
import pandas as pd
import os

# files pattern (adjust if filenames differ)
files = glob.glob(os.path.join(os.path.dirname(__file__), "daily_sales_data_*.csv"))

if not files:
    raise FileNotFoundError("No CSV files found with pattern data/daily_sales_data_*.csv")

dfs = []
for f in files:
    df = pd.read_csv(f, dtype=str)  # read as string first to clean reliably
    dfs.append(df)

# combine
df = pd.concat(dfs, ignore_index=True)

# normalize column names (strip + lower) in case CSVs have slight differences
df.columns = [c.strip() for c in df.columns]

# Ensure required columns exist
required = {"product", "price", "quantity", "date", "region"}
missing = required - set(c.lower() for c in df.columns)
if missing:
    raise KeyError(f"Missing required columns in CSVs: {missing}")

# Work with consistent lower-case keys
# create mapping from lower-case to actual column names (to preserve original names if they vary)
col_map = {c.lower(): c for c in df.columns}
prod_col = col_map["product"]
price_col = col_map["price"]
qty_col = col_map["quantity"]
date_col = col_map["date"]
region_col = col_map["region"]

# Filter: only Pink Morsel (case-insensitive, strip whitespace)
df[prod_col] = df[prod_col].astype(str).str.strip()
is_pink = df[prod_col].str.lower() == "pink morsel"
df = df[is_pink].copy()

# Clean price: remove currency symbols, commas, whitespace; convert to float
def clean_price(x):
    if pd.isna(x):
        return float("nan")
    s = str(x).strip()
    # remove $ or other currency symbols and commas
    s = s.replace("$", "").replace("£", "").replace("€", "").replace(",", "")
    s = s.replace(" ", "")
    try:
        return float(s)
    except ValueError:
        return float("nan")

df["__price"] = df[price_col].apply(clean_price)

# Clean quantity to numeric (integers/floats)
def clean_qty(x):
    if pd.isna(x):
        return float("nan")
    s = str(x).strip().replace(",", "")
    try:
        # quantity may be integer; use float to be safe
        return float(s)
    except ValueError:
        return float("nan")

df["__quantity"] = df[qty_col].apply(clean_qty)

# Drop rows where price or quantity couldn't be parsed
df = df.dropna(subset=["__price", "__quantity"]).copy()

# Compute sales
df["Sales"] = df["__price"] * df["__quantity"]

# Parse date column robustly (let pandas infer format)
df[date_col] = pd.to_datetime(df[date_col], errors="coerce", dayfirst=False)

# If any dates failed, try dayfirst inference
if df[date_col].isna().any():
    df[date_col] = pd.to_datetime(df[date_col].astype(str), errors="coerce", dayfirst=True)

# Drop rows with invalid dates
df = df.dropna(subset=[date_col]).copy()

# Prepare final dataframe with required columns: Sales, Date, Region
# Format Date as ISO YYYY-MM-DD for clarity
final = pd.DataFrame({
    "Sales": df["Sales"].round(2),
    "Date": df[date_col].dt.strftime("%Y-%m-%d"),
    "Region": df[region_col].astype(str).str.strip()
})

# Optional: sort by date
final = final.sort_values("Date").reset_index(drop=True)

# Save to CSV
out_path = os.path.join(os.path.dirname(__file__), "pink_morsel_sales.csv")
final.to_csv(out_path, index=False)

print(f"Processed {len(final):,} rows. Output saved to: {out_path}")
