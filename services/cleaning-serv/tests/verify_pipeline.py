import sys
import os
from unittest.mock import MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock ydata_profiling if not installed
sys.modules["ydata_profiling"] = MagicMock()

import pandas as pd
import numpy as np
from backend.cleaning_engine import clean_dataframe

def test_pipeline():
    # Create dirty data
    data = {
        "id": [1, 2, 2, 3, 4, 100], # 2 is duplicate, 100 might be outlier (depending on distribution)
        "val": [10.0, 20.0, 20.0, None, 15.0, 1000.0], # 20 is duplicate, None is missing, 1000 is outlier
        "cat": [" A ", "b", "b", "c", "D", "e"] # Needs normalization
    }
    df = pd.DataFrame(data)
    
    print("--- Original Data ---")
    print(df)
    
    config = {
        "missing_strategy": "mean", # Fill None with mean
        "iqr_multiplier": 1.5,
        "remove_outliers": True
    }
    
    clean_df = clean_dataframe(df, config)
    
    print("\n--- Cleaned Data ---")
    print(clean_df)
    
    # Assertions
    # 1. Duplicates
    assert len(clean_df) < len(df), "Duplicates should be removed"
    assert clean_df['id'].is_unique, "ID should be unique after duplicate removal"
    
    # 2. Missing
    assert not clean_df['val'].isna().any(), "Missing values should be filled"
    expected_mean = df['val'].dropna().mean() # approx (10+20+20+15+1000)/5 = 213. Not exactly, since duplicate dropped first.
    # Logic: Drop duplicate first -> 1, 2, 3, 4, 100. Val: 10, 20, None, 15, 1000.
    # Mean of (10, 20, 15, 1000) = 261.25. So None -> 261.25.
    
    # 3. Outliers
    # Vals: 10, 20, 261.25, 15, 1000.
    # Q1 ~ 13.75, Q3 ~ 261.
    # IQR ~ 247.
    # Upper = 261 + 1.5*247 = 631.
    # 1000 should be removed.
    assert clean_df['val'].max() < 1000, "Outlier 1000 should be removed"
    
    # 4. Normalize
    assert clean_df['cat'].iloc[0] == "a", "String should be lowercased and stripped"

    print("\n✅ Verification Successful!")

if __name__ == "__main__":
    test_pipeline()
