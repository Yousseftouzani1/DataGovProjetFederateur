"""
Moroccan Base Recognizer for Microsoft Presidio
Implements Algorithm 3 (Weighted Scoring) as specified in Cahier des Charges Section 5.5
"""
import re
from typing import List, Optional, Callable
from presidio_analyzer import Pattern, PatternRecognizer, RecognizerResult

class MoroccanPatternRecognizer(PatternRecognizer):
    """
    Base class for Moroccan PII recognizers.
    Implements the specific weighted scoring formula from Section 5.5:
    score_final = 0.5 * score_pattern + 0.3 * score_context + 0.2 * score_validation
    """
    
    def __init__(
        self,
        supported_entity: str,
        patterns: List[Pattern],
        context: Optional[List[str]] = None,
        supported_language: str = "en",
        validator: Optional[Callable[[str], bool]] = None
    ):
        # We DO NOT pass context to super().__init__ to prevent Presidio's internal boosting.
        # We want strict control for Algorithm 3 implementation.
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=None,
            supported_language=supported_language,
        )
        self.supported_entity = supported_entity
        self.manual_context = context
        self.validator = validator
        self.supported_language = supported_language # Presidio expects this

    def analyze(self, text: str, entities: List[str], nlp_artifacts=None) -> List[RecognizerResult]:
        """
        Override analyze to implement Algorithm 3 (Weighted Scoring).
        """
        # 1. Get initial matches from patterns (Regex.findAll)
        results = super().analyze(text, entities, nlp_artifacts)
        
        # If no results or we are not in the requested entities, return early
        if not results or self.supported_entity not in entities:
            return results

        final_results = []
        
        for result in results:
            # Algorithm 3 - Line 6: score_pattern
            # We recover the pattern score from the result (Presidio puts it there)
            score_pattern = result.score
            
            # Algorithm 3 - Line 7: ComputeContextScore
            # Presidio sets score higher if context is found, but we want strict weighting
            # We check if context words were actually found near this match
            has_context = self._check_context_proximity(text, result.start, result.end, nlp_artifacts)
            score_context = 1.0 if has_context else 0.0
            
            # Algorithm 3 - Line 8: ValidatePattern
            # If no validator is provided, we assume 1.0 (neutral pass)
            # if validator fails, score is 0.0
            score_validation = 1.0
            if self.validator:
                match_text = text[result.start:result.end]
                score_validation = 1.0 if self.validator(match_text) else 0.0
            
            # Algorithm 3 - Line 9: score_final = 0.5·score_pattern + 0.3·score_context + 0.2·score_validation
            score_final = (0.5 * score_pattern) + (0.3 * score_context) + (0.2 * score_validation)
            
            # Update result score
            result.score = round(score_final, 3)
            
            # Algorithm 3 - Line 10: if score_final >= threshold (handled by AnalyzerEngine)
            final_results.append(result)
            
        return final_results

    def _check_context_proximity(self, text: str, start: int, end: int, nlp_artifacts=None) -> bool:
        """
        Check if context words are near the match.
        Strict weighting for Algorithm 3.
        """
        if not self.manual_context:
            return False
            
        # Proximity check: look for context words in a window around the match
        window_size = 100 # Enlarged window for better detection
        context_window = text[max(0, start - window_size):min(len(text), end + window_size)].lower()
        
        for word in self.manual_context:
            if word.lower() in context_window:
                return True
        return False
