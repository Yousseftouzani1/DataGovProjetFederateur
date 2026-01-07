from typing import List, Dict, Any
from collections import defaultdict
from enum import Enum
import logging


class ValidationDecision(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    MODIFIED = "MODIFIED"


class CorrectionSource(str, Enum):
    RULE = "RULE"
    ML_TEXT = "ML_TEXT"
    ML_NUMERIC = "ML_NUMERIC"


class LearningEngine:
    """
    LearningEngine
    ===============
    Apprentissage continu supervisé (US-CORR-05).

    Objectifs :
    - Apprendre uniquement à partir des décisions humaines
    - Alimenter les améliorations futures (offline)
    - Garantir gouvernance, traçabilité et qualité
    """

    MIN_CONFIDENCE_FOR_LEARNING = 0.6

    def __init__(self):
        # Feedback agrégé par source / champ
        self.rule_feedback = defaultdict(lambda: {
            "accepted": 0,
            "rejected": 0,
            "modified": 0
        })

        # Datasets ML (offline training)
        self.ml_text_samples: List[Dict[str, str]] = []
        self.ml_numeric_samples: List[Dict[str, Any]] = []

        # KPI Learning
        self.learning_stats = defaultdict(int)

    # =====================================================
    # API PUBLIQUE
    # =====================================================

    def learn_from_validation(self, validation: Dict[str, Any]) -> None:
        """
        Apprend à partir d'une validation humaine.

        Format attendu (extrait) :
        {
          "field": "age",
          "old_value": -5,
          "new_value": 0,
          "confidence": 0.92,
          "source": "ML_NUMERIC",
          "decision": "ACCEPTED" | "REJECTED" | "MODIFIED"
        }
        """

        try:
            if not self._is_valid_for_learning(validation):
                return

            decision = ValidationDecision(validation["decision"])
            source = CorrectionSource(validation["source"])

            self._learn_feedback(validation, decision, source)
            self._learn_ml(validation, decision, source)

            self.learning_stats["total_validations"] += 1

        except Exception as e:
            logging.error(f"[LearningEngine] error: {e}")

    # =====================================================
    # VALIDATION FILTERING
    # =====================================================

    def _is_valid_for_learning(self, validation: Dict[str, Any]) -> bool:
        """
        Filtre les validations non exploitables.
        """
        if validation.get("confidence", 0) < self.MIN_CONFIDENCE_FOR_LEARNING:
            return False
        if "decision" not in validation or "source" not in validation:
            return False
        return True

    # =====================================================
    # FEEDBACK LEARNING (RULES / SOURCES)
    # =====================================================

    def _learn_feedback(
        self,
        validation: Dict[str, Any],
        decision: ValidationDecision,
        source: CorrectionSource
    ) -> None:
        """
        Agrège le feedback humain par champ et source.
        """
        key = f"{validation.get('field')}::{source.value}"

        if decision == ValidationDecision.ACCEPTED:
            self.rule_feedback[key]["accepted"] += 1
        elif decision == ValidationDecision.REJECTED:
            self.rule_feedback[key]["rejected"] += 1
        elif decision == ValidationDecision.MODIFIED:
            self.rule_feedback[key]["modified"] += 1

    # =====================================================
    # ML DATASET LEARNING (OFFLINE)
    # =====================================================

    def _learn_ml(
        self,
        validation: Dict[str, Any],
        decision: ValidationDecision,
        source: CorrectionSource
    ) -> None:
        """
        Prépare les datasets ML à partir des corrections validées.
        """

        if decision not in {ValidationDecision.ACCEPTED, ValidationDecision.MODIFIED}:
            return

        if source == CorrectionSource.ML_TEXT:
            self._add_text_sample(validation)

        elif source == CorrectionSource.ML_NUMERIC:
            self._add_numeric_sample(validation)

    # =====================================================
    # TEXT SAMPLES (T5)
    # =====================================================

    def _add_text_sample(self, validation: Dict[str, Any]) -> None:
        sample = {
            "input": f"correct: {validation['old_value']} context: {validation['field']}",
            "target": validation["new_value"]
        }
        self.ml_text_samples.append(sample)
        self.learning_stats["text_samples"] += 1

    # =====================================================
    # NUMERIC SAMPLES
    # =====================================================

    def _add_numeric_sample(self, validation: Dict[str, Any]) -> None:
        sample = {
            "field": validation["field"],
            "input": validation["old_value"],
            "target": validation["new_value"]
        }
        self.ml_numeric_samples.append(sample)
        self.learning_stats["numeric_samples"] += 1

    # =====================================================
    # EXPORT / KPI
    # =====================================================

    def export_learning_state(self) -> Dict[str, Any]:
        """
        Exporte l'état d'apprentissage (audit & offline training).
        """
        return {
            "rule_feedback": dict(self.rule_feedback),
            "ml_text_samples": self.ml_text_samples,
            "ml_numeric_samples": self.ml_numeric_samples,
            "learning_stats": dict(self.learning_stats)
        }
