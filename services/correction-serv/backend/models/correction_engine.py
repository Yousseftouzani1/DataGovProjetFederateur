from typing import List, Dict, Any, Tuple
from .inconsistency import Inconsistency
from .rules_loader import load_rules

# ML modules (lazy & encapsulated)
from .ml.text_correction_t5 import TextCorrectionT5
from .ml.numeric_regression import NumericRegressor


class CorrectionEngine:
    """
    CorrectionEngine
    =================
    Phase 2 — Algorithm 6 : Correction Automatique Intelligente

    - Règles déclaratives (YAML, gouvernées)
    - ML en fallback uniquement
    - Décision auto / revue humaine traçable
    """

    AUTO_APPLY_THRESHOLD = 0.9

    def __init__(self):
        self.rules = load_rules()

        # Initialisation ML lazy (latence maîtrisée)
        self.text_corrector = TextCorrectionT5()
        self.numeric_regressor = NumericRegressor()

    # =====================================================
    # API PUBLIQUE
    # =====================================================

    def correct(
        self,
        row: Dict[str, Any],
        inconsistencies: List[Inconsistency]
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:

        corrected_row = row.copy()
        correction_log: List[Dict[str, Any]] = []

        for inc in inconsistencies:
            candidates: List[Dict[str, Any]] = []

            # 1️⃣ Rule-based candidates
            candidates.extend(self._rule_based_candidates(corrected_row, inc))

            # 2️⃣ ML fallback si nécessaire
            if not candidates or self._best_score(candidates) < self.AUTO_APPLY_THRESHOLD:
                ml_candidate = self._ml_based_candidate(corrected_row, inc)
                if ml_candidate:
                    candidates.append(ml_candidate)

            # 3️⃣ Sélection finale
            if candidates:
                best = max(candidates, key=lambda c: c["score"])
            else:
                best = None

            if best and best["score"] >= self.AUTO_APPLY_THRESHOLD:
                corrected_row[inc.field] = best["value"]
                correction_log.append(self._log_auto(inc, best))
            else:
                correction_log.append(self._log_manual(inc, candidates))

        return corrected_row, correction_log

    # =====================================================
    # RULE-BASED CORRECTIONS (YAML DRIVEN)
    # =====================================================

    def _rule_based_candidates(
        self,
        row: Dict[str, Any],
        inc: Inconsistency
    ) -> List[Dict[str, Any]]:

        candidates = []
        section = self.rules.get(inc.type, {})
        rules = section.get("corrections", [])

        for rule in rules:
            if not self._rule_matches(rule, inc):
                continue

            value = self._apply_strategy(rule, row, inc)
            if value is not None:
                candidates.append({
                    "value": value,
                    "score": rule.get("confidence", 0.7),
                    "source": "RULE",
                    "strategy": rule.get("strategy")
                })

        return candidates

    def _rule_matches(self, rule: Dict[str, Any], inc: Inconsistency) -> bool:
        """
        Vérifie si une règle s'applique à l'incohérence.
        """
        field = rule.get("field")
        inc_type = rule.get("type")

        if field and field != inc.field:
            return False
        if inc_type and inc_type != inc.type:
            return False
        return True

    def _apply_strategy(
        self,
        rule: Dict[str, Any],
        row: Dict[str, Any],
        inc: Inconsistency
    ) -> Any:
        """
        Applique une stratégie déclarative de correction.
        """
        strategy = rule.get("strategy")

        if strategy == "RESET_NULL":
            return None

        if strategy == "CLAMP_MIN":
            return rule.get("min")

        if strategy == "CLAMP_MAX":
            return rule.get("max")

        if strategy == "REPLACE_WITH":
            return rule.get("value")

        # Stratégie inconnue → pas de correction auto
        return None

    # =====================================================
    # ML-BASED CORRECTIONS (FALLBACK)
    # =====================================================

    def _ml_based_candidate(
        self,
        row: Dict[str, Any],
        inc: Inconsistency
    ) -> Dict[str, Any] | None:

        # TEXT / FORMAT / SEMANTIC → T5
        if inc.type in {"FORMAT", "SEMANTIC"} and isinstance(inc.value, str):
            suggestion, score = self.text_corrector.correct(
                value=inc.value
            )
            return {
                "value": suggestion,
                "score": score,
                "source": "ML_TEXT"
            }

        # DOMAIN / STATISTICAL → Régression
        if inc.type in {"DOMAIN", "STATISTICAL"}:
            suggestion, score = self.numeric_regressor.correct(
                field=inc.field,
                value=inc.value
            )
            return {
                "value": suggestion,
                "score": score,
                "source": "ML_NUMERIC"
            }

        # REFERENTIAL → pas d'auto-correction
        return None

    # =====================================================
    # LOGGING & STATES
    # =====================================================

    def _log_auto(self, inc: Inconsistency, best: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "field": inc.field,
            "old_value": inc.value,
            "new_value": best["value"],
            "confidence": best["score"],
            "auto": True,
            "status": "AUTO_CORRECTED",
            "source": best["source"]
        }

    def _log_manual(
        self,
        inc: Inconsistency,
        candidates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        return {
            "field": inc.field,
            "old_value": inc.value,
            "candidates": candidates,
            "auto": False,
            "status": "REQUIRES_REVIEW" if candidates else "NO_CANDIDATE"
        }

    # =====================================================
    # UTILS
    # =====================================================

    def _best_score(self, candidates: List[Dict[str, Any]]) -> float:
        return max(c["score"] for c in candidates) if candidates else 0.0
