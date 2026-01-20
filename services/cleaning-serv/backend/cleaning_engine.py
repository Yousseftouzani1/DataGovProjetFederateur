import pandas as pd
import numpy as np
from ydata_profiling import ProfileReport
import re

def clean_dataframe(df: pd.DataFrame, config: dict = None) -> (pd.DataFrame, dict):
    """
    Implements the Data Cleaning Pipeline as per CDC Section 6.4.
    
    Returns:
        (pd.DataFrame, dict): The cleaned dataframe and a metrics dictionary for the report.
    """
    if config is None:
        config = {}
    
    metrics = {
        "rows_before": len(df),
        "steps": [],
        "errors": []
    }
    
    # ---------------------------------------------------------
    # 1. Remove Duplicates
    # ---------------------------------------------------------
    initial_rows = len(df)
    df = df.drop_duplicates()
    df = df.copy() 
    removed_dupes = initial_rows - len(df)
    metrics["steps"].append({"step": "duplicates", "removed": removed_dupes})
    
    # ---------------------------------------------------------
    # 2. Handle Missing Values
    # ---------------------------------------------------------
    missing_strategy = config.get("missing_strategy", "drop")
    initial_missing = df.isnull().sum().sum()
    
    if missing_strategy == "drop":
        df = df.dropna(how='any')
    elif missing_strategy == "mean":
        numeric_cols = df.select_dtypes(include=np.number).columns
        for col in numeric_cols:
            if df[col].isnull().any():
                df[col] = df[col].fillna(df[col].mean())
        for col in df.select_dtypes(exclude=np.number).columns:
             if not df[col].empty and df[col].isnull().any():
                df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else "")
    
    final_missing = df.isnull().sum().sum()
    metrics["steps"].append({"step": "missing_values", "corrected": int(initial_missing - final_missing)})
    
    # ---------------------------------------------------------
    # 3. Remove Outliers (IQR Method)
    # ---------------------------------------------------------
    outlier_multiplier = config.get("iqr_multiplier", 1.5)
    numeric_cols = df.select_dtypes(include=np.number).columns
    total_outliers_removed = 0
    
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - (outlier_multiplier * IQR)
        upper_bound = Q3 + (outlier_multiplier * IQR)
        
        original_len = len(df)
        df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
        total_outliers_removed += (original_len - len(df))
            
    metrics["steps"].append({"step": "outliers", "removed": total_outliers_removed})

    # ---------------------------------------------------------
    # 4. Normalize Data
    # ---------------------------------------------------------
    string_cols = df.select_dtypes(include='object').columns
    for col in string_cols:
        df[col] = df[col].astype(str).str.lower().str.strip()
        
    metrics["steps"].append({"step": "normalization", "status": "completed"})

    # ---------------------------------------------------------
    # 5. Validate (Constraint checks) - CDC Section 6.4.5
    # ---------------------------------------------------------
    # Example: Check for specific range constraints or regex in config
    validation_rules = config.get("validation_rules", {})
    validated_rows_removed = 0
    
    for col, rules in validation_rules.items():
        if col not in df.columns:
            continue
            
        original_len = len(df)
        # Apply min/max rules
        if "min" in rules:
            df = df[df[col] >= rules["min"]]
        if "max" in rules:
            df = df[df[col] <= rules["max"]]
        if "regex" in rules:
            df = df[df[col].astype(str).str.match(rules["regex"])]
            
        validated_rows_removed += (original_len - len(df))

    metrics["steps"].append({"step": "validation", "removed": validated_rows_removed})
    metrics["rows_after"] = len(df)
    metrics["cleaning_score"] = round((len(df) / metrics["rows_before"] * 100), 2) if metrics["rows_before"] > 0 else 0
    
    return df, metrics

def generate_profile(df: pd.DataFrame) -> (dict, dict):
    """
    Generates a ydata-profiling report and returns metadata summary.
    """
    # minimal=True for performance as per KPI < 5s
    profile = ProfileReport(df, title="Data Profiling Report", minimal=True)
    description = profile.get_description()
    
    # Handle BaseDescription object vs Dictionary (ydata-profiling version compatibility)
    if hasattr(description, "table"):
        table_stats = description.table
        # table_stats can be an object or a dict
        def get_stat(obj, key, default=0):
            if isinstance(obj, dict): return obj.get(key, default)
            return getattr(obj, key, default)

        stats = {
            "n_rows": int(get_stat(table_stats, "n")),
            "n_cols": int(get_stat(table_stats, "n_var")),
            "duplicates": int(get_stat(table_stats, "n_duplicates")),
            "missing_cells": int(get_stat(table_stats, "n_cells_missing")),
            "missing_percentage": round(float(get_stat(table_stats, "p_cells_missing")) * 100, 2),
            "memory_size": f"{get_stat(table_stats, 'memory_size', 0) / 1024:.2f} KB"
        }
    else:
        # Fallback for dict-only versions
        table = description.get("table", {})
        stats = {
            "n_rows": int(table.get("n", 0)),
            "n_cols": int(table.get("n_var", 0)),
            "duplicates": int(table.get("n_duplicates", 0)),
            "missing_cells": int(table.get("n_cells_missing", 0)),
            "missing_percentage": round(float(table.get("p_cells_missing", 0)) * 100, 2),
            "memory_size": f"{table.get('memory_size', 0) / 1024:.2f} KB"
        }
    
    return profile, stats

