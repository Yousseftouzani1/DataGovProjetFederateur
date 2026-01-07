from typing import Tuple
from functools import lru_cache
import logging

try:
    from transformers import T5ForConditionalGeneration, T5Tokenizer
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class TextCorrectionT5:
    """
    TextCorrectionT5
    =================
    Correcteur textuel basé sur T5 (Sequence-to-Sequence).

    Conforme au Cahier des Charges :
    - Format d’entrée imposé
    - Score de confiance explicable
    - ML en fallback uniquement
    - Latence maîtrisée
    """

    MODEL_NAME = "t5-base"
    MAX_INPUT_LENGTH = 128
    MAX_OUTPUT_LENGTH = 64

    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._device = None

        if not TRANSFORMERS_AVAILABLE:
            logging.warning("Transformers not available – TextCorrectionT5 disabled")

    # =====================================================
    # API PUBLIQUE
    # =====================================================

    def correct(self, value: str, context: str) -> Tuple[str, float]:
        """
        Propose une correction textuelle + score de confiance.
        """
        if not TRANSFORMERS_AVAILABLE:
            return value, 0.0

        self._ensure_model_loaded()

        prompt = f"correct: {value} context: {context}"

        try:
            corrected, model_score = self._generate(prompt)
            confidence = self._estimate_confidence(value, corrected, model_score)
            return corrected, confidence
        except Exception:
            return value, 0.0

    # =====================================================
    # MODEL LOADING
    # =====================================================

    def _ensure_model_loaded(self):
        if self._model is not None:
            return

        self._device = "cuda" if torch.cuda.is_available() else "cpu"

        self._tokenizer = T5Tokenizer.from_pretrained(self.MODEL_NAME)
        self._model = T5ForConditionalGeneration.from_pretrained(self.MODEL_NAME)
        self._model.to(self._device)
        self._model.eval()

    # =====================================================
    # GENERATION
    # =====================================================

    @lru_cache(maxsize=512)
    def _generate(self, prompt: str) -> Tuple[str, float]:
        """
        Génère une correction + score modèle (log-probabilité moyenne).
        """

        inputs = self._tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.MAX_INPUT_LENGTH
        ).to(self._device)

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_length=self.MAX_OUTPUT_LENGTH,
                num_beams=4,
                output_scores=True,
                return_dict_in_generate=True
            )

        decoded = self._tokenizer.decode(
            outputs.sequences[0],
            skip_special_tokens=True
        )

        # Score modèle = moyenne des logits normalisés
        scores = outputs.scores
        if scores:
            avg_score = sum(s.max().item() for s in scores) / len(scores)
        else:
            avg_score = 0.0

        return decoded, avg_score

    # =====================================================
    # CONFIDENCE
    # =====================================================

    def _estimate_confidence(
        self,
        original: str,
        corrected: str,
        model_score: float
    ) -> float:
        """
        Score de confiance gouvernable et explicable.
        """

        if not corrected or corrected == original:
            return 0.4

        confidence = 0.6

        # Impact de la modification
        if abs(len(corrected) - len(original)) > 5:
            confidence += 0.1

        # Impact du modèle
        if model_score > 5:
            confidence += 0.2
        elif model_score > 2:
            confidence += 0.1

        return min(confidence, 0.95)
