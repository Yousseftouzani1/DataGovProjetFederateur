import pandas as pd


# ------------------------------------------------------------
# Compute global dataset profiling metrics
# ------------------------------------------------------------
def profile_dataset(df: pd.DataFrame) -> dict:
    profile = {}

    # Dataset shape
    profile["rows"] = len(df)
    profile["columns"] = len(df.columns)

    # Missing values
    total_cells = df.shape[0] * df.shape[1]
    total_missing = df.isnull().sum().sum()
    profile["missing_rate"] = round((total_missing / total_cells) * 100, 2)

    # Duplicates
    profile["duplicate_rows"] = int(df.duplicated().sum())

    # Column-level profiling
    profile["columns_profile"] = {}

    for col in df.columns:
        col_profile = {}
        col_data = df[col]

        col_profile["missing"] = int(col_data.isnull().sum())

        # Numeric columns
        if pd.api.types.is_numeric_dtype(col_data):
            col_profile["type"] = "numeric"
            col_profile["min"] = float(col_data.min()) if not col_data.isnull().all() else None
            col_profile["max"] = float(col_data.max()) if not col_data.isnull().all() else None
            col_profile["mean"] = float(col_data.mean()) if not col_data.isnull().all() else None

        # Categorical / text columns
        else:
            col_profile["type"] = "categorical"
            col_profile["unique_values"] = int(col_data.nunique(dropna=True))

        profile["columns_profile"][col] = col_profile

    return profile