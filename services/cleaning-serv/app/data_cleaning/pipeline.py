
import pandas as pd
from typing import Tuple, Dict, Any
from .validators import SchemaValidator
from sklearn.preprocessing import MinMaxScaler

class CleaningPipeline:
    """
    Orchestrates the 7-step cleaning pipeline defined in CDC Section 6.4.
    """

    def __init__(self, df: pd.DataFrame, config: Dict[str, Any]):
        self.df = df
        self.config = config
        self.metrics = {}

    def run(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Execute the pipeline sequence:
        1. Raw Data (Ingested)
        2. Profiling Initial (Handled by profiler.py separately or stats here)
        3. Remove Duplicates
        4. Handle Missing
        5. Remove Outliers (Algorithm 4)
        6. Normalize
        7. Validate
        """
        # Step 0: Initial Metrics
        self.metrics["rows_before"] = len(self.df)
        self.metrics["columns"] = len(self.df.columns)
        self.metrics["missing_before"] = self._calculate_missing_rate()

        # Step 3: Remove Duplicates (US-CLEAN-KPI: 0% Duplicates)
        if self.config.get("remove_duplicates", True):
            self._remove_duplicates()

        # Step 4: Handle Missing Values (US-CLEAN-KPI: < 5%)
        self._handle_missing_values()

        # Step 5: Remove Outliers (Algorithm 4 IQR)
        if self.config.get("remove_outliers", True):
            self._remove_outliers_iqr()

        # Step 6: Normalize (Optional but in pipeline figure)
        if self.config.get("normalize", False):
            self._normalize_data()

        # Step 7: Validate
        validator = SchemaValidator()
        integrity = validator.check_integrity(self.df)
        self.metrics["is_valid"] = integrity

        # Final Metrics
        self.metrics["rows_after"] = len(self.df)
        self.metrics["missing_after"] = self._calculate_missing_rate()
        
        return self.df, self.metrics

    def _calculate_missing_rate(self) -> float:
        if self.df.empty: return 0.0
        return round(self.df.isnull().mean().mean() * 100, 2)

    def _remove_duplicates(self):
        before = len(self.df)
        self.df = self.df.drop_duplicates()
        removed = before - len(self.df)
        self.metrics["duplicates_removed"] = removed

    def _handle_missing_values(self):
        strategy = self.config.get("handle_missing", "mean")
        
        for col in self.df.columns:
            if pd.api.types.is_numeric_dtype(self.df[col]):
                if strategy == "mean":
                    self.df[col] = self.df[col].fillna(self.df[col].mean())
                elif strategy == "median":
                    self.df[col] = self.df[col].fillna(self.df[col].median())
            else:
                # Mode for text/categorical
                mode_val = self.df[col].mode()
                if not mode_val.empty:
                    self.df[col] = self.df[col].fillna(mode_val[0])
                    
    def _remove_outliers_iqr(self):
        """
        Algorithm 4: Outlier Detection (IQR)
        Ref: CDC Section 6.5
        """
        m = self.config.get("iqr_multiplier", 1.5)
        numeric_cols = self.df.select_dtypes(include="number").columns
        initial_rows = len(self.df)
        
        # Note: CDC algorithm implies independent filtering or iterative?
        # Usually row deletion. We verify row by row or filter per col?
        # CDC Line 7: D <- D[(D[col] >= lower) & (D[col] <= upper)]
        # This implies filtering the DataFrame for each column.
        
        for col in numeric_cols:
            Q1 = self.df[col].quantile(0.25)
            Q3 = self.df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - (m * IQR)
            upper_bound = Q3 + (m * IQR)
            
            # Apply filter
            self.df = self.df[(self.df[col] >= lower_bound) & (self.df[col] <= upper_bound)]
            
        self.metrics["outliers_removed"] = initial_rows - len(self.df)

    def _normalize_data(self):
        """
        Step 6: Normalize using MinMax (Scikit-Learn)
        """
        numeric_cols = self.df.select_dtypes(include="number").columns
        if not numeric_cols.empty:
            scaler = MinMaxScaler()
            self.df[numeric_cols] = scaler.fit_transform(self.df[numeric_cols])
            self.metrics["normalized"] = True
