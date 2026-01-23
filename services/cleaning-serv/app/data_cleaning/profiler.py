import pandas as pd
from ydata_profiling import ProfileReport
import os

class DataProfiler:
    """
    Wrapper for ydata-profiling to generate HTML reports.
    Satisfies US-CLEAN-02.
    """
    
    @staticmethod
    def generate_report(df: pd.DataFrame, title: str = "Data Profiling Report") -> str:
        """
        Generates an HTML report from the dataframe.
        Returns the HTML content as a string.
        """
        try:
            profile = ProfileReport(
                df,
                title=title,
                minimal=True, # Optimized for performance (speed < 10s req)
                explorative=True
            )
            return profile.to_html()
        except Exception as e:
            print(f"Profiling error: {e}")
            return f"<html><body><h1>Filtering Report Failed</h1><p>{str(e)}</p></body></html>"

    @staticmethod
    def get_basic_stats(df: pd.DataFrame) -> dict:
        """
        Fast JSON stats for quick metadata without full HMTL generation.
        """
        return {
            "rows": len(df),
            "columns": len(df.columns),
            "missing_rate": round(df.isnull().mean().mean() * 100, 2),
            "duplicates": int(df.duplicated().sum()),
            "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2)
        }
