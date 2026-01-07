from typing import Any, Tuple
import math


class NumericRegressor:
    """
    NumericRegressor
    =================
    Correcteur numérique léger (statistique / heuristique).

    - DOMAIN & STATISTICAL fallback
    - Aucune dépendance métier
    - Latence ultra-faible
    """

    DEFAULT_CONFIDENCE = 0.85
    OUTLIER_ABS_THRESHOLD = 1_000_000

    def __init__(self):
        pass

    # =====================================================
    # API PUBLIQUE
    # =====================================================

    def correct(self, value: Any) -> Tuple[Any, float]:
        """
        Propose une correction numérique prudente.

        Retour :
        (suggested_value, confidence)
        """

        num = self._safe_float(value)
        if num is None:
            return value, 0.0

        # Valeurs non finies
        if math.isnan(num) or math.isinf(num):
            return 0, 0.95

        # Outliers extrêmes
        if abs(num) > self.OUTLIER_ABS_THRESHOLD:
            return self._reduce_outlier(num)

        # Valeurs négatives suspectes
        if num < 0:
            return 0, 0.9

        # Valeur acceptable
        return num, self.DEFAULT_CONFIDENCE

    # =====================================================
    # STRATÉGIES INTERNES
    # =====================================================

    def _reduce_outlier(self, value: float) -> Tuple[float, float]:
        try:
            reduced = math.copysign(math.log(abs(value) + 1), value) * 100
            return round(reduced, 2), 0.9
        except Exception:
            return value, 0.0

    # =====================================================
    # HELPERS
    # =====================================================

    def _safe_float(self, value: Any) -> float | None:
        try:
            return float(value)
        except Exception:
            return None
