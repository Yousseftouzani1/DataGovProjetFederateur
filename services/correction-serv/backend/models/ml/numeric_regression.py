from typing import Any, Tuple, Optional, List, Dict
import math
import numpy as np


class NumericRegressor:
    """
    NumericRegressor
    =================
    Enhanced statistical correction for DOMAIN & STATISTICAL inconsistencies
    
    Features:
    - IQR and Z-score outlier detection (per Section 8.3)
    - Domain-specific clamping
    - Imputation strategies
    - Low latency (<5ms per value)
    """
    
    DEFAULT_CONFIDENCE = 0.85
    OUTLIER_ABS_THRESHOLD = 1_000_000
    
    # Statistical thresholds
    Z_SCORE_THRESHOLD = 3.0
    IQR_MULTIPLIER = 1.5
    
    def __init__(self):
        self.field_statistics = {}  # Cache for field-level stats
    
    # =====================================================
    # API PUBLIQUE
    # =====================================================
    
    def correct(
        self, 
        field: str,
        value: Any,
        context_values: Optional[List[float]] = None
    ) -> Tuple[Any, float]:
        """
        Propose une correction numérique
        
        Args:
            field: Field name for context-aware correction
            value: Value to correct
            context_values: Other values in the same field for statistical analysis
            
        Returns:
            (suggested_value, confidence)
        """
        num = self._safe_float(value)
        if num is None:
            return value, 0.0
        
        # Valeurs non finies
        if math.isnan(num) or math.isinf(num):
            return 0, 0.95
        
        # Check if outlier using statistical methods
        if context_values:
            is_outlier, method = self._is_statistical_outlier(num, context_values)
            if is_outlier:
                # Use median as correction for outliers
                corrected = float(np.median(context_values))
                return corrected, 0.75
        
        # Outliers extrêmes (absolute threshold)
        if abs(num) > self.OUTLIER_ABS_THRESHOLD:
            return self._reduce_outlier(num)
        
        # Valeurs négatives suspectes (domain-specific)
        if num < 0 and field in ['age', 'salary', 'percentage', 'count']:
            return abs(num), 0.85  # Take absolute value
        
        # Valeur acceptable
        return num, self.DEFAULT_CONFIDENCE
    
    def _is_statistical_outlier(
        self, 
        value: float, 
        values: List[float],
        method: str = "IQR"
    ) -> Tuple[bool, str]:
        """
        Detect outliers using statistical methods (Section 8.3)
        
        Args:
            value: Value to check
            values: Distribution of values
            method: "IQR" or "Z_SCORE"
            
        Returns:
            (is_outlier, method_used)
        """
        if len(values) < 10:  # Need enough data for statistics
            return False, "insufficient_data"
        
        values_array = np.array([v for v in values if not (math.isnan(v) or math.isinf(v))])
        
        if method == "IQR":
            # Interquartile Range method
            q1 = np.percentile(values_array, 25)
            q3 = np.percentile(values_array, 75)
            iqr = q3 - q1
            
            lower_bound = q1 - (self.IQR_MULTIPLIER * iqr)
            upper_bound = q3 + (self.IQR_MULTIPLIER * iqr)
            
            is_outlier = value < lower_bound or value > upper_bound
            return is_outlier, "IQR"
        
        elif method == "Z_SCORE":
            # Z-score method
            mean = np.mean(values_array)
            std = np.std(values_array)
            
            if std == 0:
                return False, "zero_variance"
            
            z_score = abs((value - mean) / std)
            is_outlier = z_score > self.Z_SCORE_THRESHOLD
            return is_outlier, "Z_SCORE"
        
        return False, "unknown_method"
    
    def calculate_field_statistics(
        self, 
        field: str, 
        values: List[float]
    ) -> Dict[str, float]:
        """
        Calculate and cache statistics for a field
        
        Used for more accurate correction suggestions
        """
        clean_values = [v for v in values if not (math.isnan(v) or math.isinf(v))]
        
        if len(clean_values) < 2:
            return {}
        
        stats = {
            "mean": float(np.mean(clean_values)),
            "median": float(np.median(clean_values)),
            "std": float(np.std(clean_values)),
            "min": float(np.min(clean_values)),
            "max": float(np.max(clean_values)),
            "q1": float(np.percentile(clean_values, 25)),
            "q3": float(np.percentile(clean_values, 75))
        }
        
        self.field_statistics[field] = stats
        return stats
    
    # =====================================================
    # STRATÉGIES INTERNES
    # =====================================================
    
    def _reduce_outlier(self, value: float) -> Tuple[float, float]:
        """Reduce extreme outliers using logarithmic scaling"""
        try:
            reduced = math.copysign(math.log(abs(value) + 1), value) * 100
            return round(reduced, 2), 0.70
        except Exception:
            return value, 0.0
    
    # =====================================================
    # HELPERS
    # =====================================================
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float"""
        try:
            return float(value)
        except Exception:
            return None

