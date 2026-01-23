
import pandas as pd
import json
import os

# Load Real Data
try:
    df_intl = pd.read_csv("DATAGOV_INTERNATIONAL.csv")
    df_maroc = pd.read_csv("DATAGOV_MOROCCO_FULL.csv")
    print("✅ Loaded datasets successfully.")
except Exception as e:
    print(f"❌ Failed to load datasets: {e}")
    exit(1)

def print_swagger_input(df, name, n=1):
    print(f"\nExample Input for {name} ({n} rows):")
    records = df.head(n).to_dict(orient='records')
    for i, row in enumerate(records):
        # Convert NaN to None for JSON
        row = {k: (v if pd.notnull(v) else None) for k, v in row.items()}
        print(f"--- Row {i+1} ---")
        print(json.dumps({"row": row, "dataset_id": name}, indent=2, ensure_ascii=False))

print("\n" + "="*60)
print("📋 SWAGGER INPUTS FOR MANUAL TESTING")
print("="*60)
print("Route: POST /detect OR POST /correct")

print("\n--- 1. DATAGOV_INTERNATIONAL.csv (Sample) ---")
print_swagger_input(df_intl, "DATAGOV_INTERNATIONAL")

print("\n--- 2. DATAGOV_MOROCCO_FULL.csv (Sample) ---")
print_swagger_input(df_maroc, "DATAGOV_MOROCCO_FULL")
