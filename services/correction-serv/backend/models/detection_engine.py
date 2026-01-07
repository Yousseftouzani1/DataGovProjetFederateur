import re
from datetime import datetime
from typing import List, Any
from .inconsistency import Inconsistency
from .rules_loader import load_rules


class DetectionEngine:
    """
    DetectionEngine
    =================
    Détection générique des incohérences de données (Data Quality V2)

    Principe clé :
    - Un champ a un TYPE ATTENDU
    - La valeur peut correspondre à un AUTRE TYPE SENSIBLE
    → incohérence sémantique
    """

    def __init__(self):
        self.rules = load_rules()
        self._compiled_patterns = self._compile_patterns()

    # ============================================================
    # API PUBLIQUE
    # ============================================================

    def detect(self, row: dict) -> List[Inconsistency]:
        issues: List[Inconsistency] = []

        issues += self._detect_format(row)
        issues += self._detect_domain(row)
        issues += self._detect_temporal(row)
        issues += self._detect_referential(row)
        issues += self._detect_statistical(row)
        issues += self._detect_semantic_type_mismatch(row)

        return issues

    # ============================================================
    # FORMAT
    # ============================================================

    def _detect_format(self, row: dict) -> List[Inconsistency]:
        issues = []
        date_fmt = self.rules.get("FORMAT", {}).get("date", {}).get("format")

        for field, value in row.items():
            if "date" in field.lower() and isinstance(value, str):
                if not self._is_valid_date(value, date_fmt):
                    issues.append(self._issue(
                        field, value, "FORMAT", "Invalid date format"
                    ))
        return issues

    # ============================================================
    # DOMAIN
    # ============================================================

    def _detect_domain(self, row: dict) -> List[Inconsistency]:
        issues = []
        ranges = self.rules.get("DOMAIN", {}).get("numeric_ranges", {})

        for field, cfg in ranges.items():
            if field in row:
                val = self._safe_number(row.get(field))
                if val is None or not (cfg["min"] <= val <= cfg["max"]):
                    issues.append(self._issue(
                        field, row.get(field), "DOMAIN", "Value out of allowed range"
                    ))
        return issues

    # ============================================================
    # TEMPORAL
    # ============================================================

    def _detect_temporal(self, row: dict) -> List[Inconsistency]:
        issues = []
        rule = self.rules.get("TEMPORAL", {}).get("date_order")

        if rule:
            start = self._parse_date(row.get(rule["start_field"]))
            end = self._parse_date(row.get(rule["end_field"]))
            if start and end and end < start:
                issues.append(self._issue(
                    rule["end_field"],
                    row.get(rule["end_field"]),
                    "TEMPORAL",
                    "End date is before start date"
                ))
        return issues

    # ============================================================
    # REFERENTIAL
    # ============================================================

    def _detect_referential(self, row: dict) -> List[Inconsistency]:
        issues = []
        pairs = self.rules.get("REFERENTIAL", {}).get("invalid_pairs", [])

        for p in pairs:
            if row.get(p["field_1"]) == p["value_1"] and row.get(p["field_2"]) == p["value_2"]:
                issues.append(self._issue(
                    p["field_1"],
                    row.get(p["field_1"]),
                    "REFERENTIAL",
                    p.get("message", "Invalid referential combination")
                ))
        return issues

    # ============================================================
    # STATISTICAL
    # ============================================================

    def _detect_statistical(self, row: dict) -> List[Inconsistency]:
        issues = []
        threshold = self.rules.get("STATISTICAL", {}).get("outliers", {}).get("default_threshold")

        for field, value in row.items():
            num = self._safe_number(value)
            if num is not None and threshold and abs(num) > threshold:
                issues.append(self._issue(
                    field, value, "STATISTICAL", "Statistical outlier detected"
                ))
        return issues

    # ============================================================
    # SEMANTIC — TYPE MISMATCH (CORE DEMAND)
    # ============================================================

    def _detect_semantic_type_mismatch(self, row: dict) -> List[Inconsistency]:
        """
        Détecte les cas où la valeur d’un champ correspond
        à une AUTRE catégorie sensible que celle attendue.
        """
        issues = []
        semantic_rules = self.rules.get("SEMANTIC", {}).get("type_mismatch", [])

        for field, value in row.items():
            if not isinstance(value, str):
                continue

            matched_types = self._detect_value_types(value)

            for rule in semantic_rules:
                expected = rule["expected_type"]
                forbidden = rule.get("forbidden_types", [])

                # Si la valeur correspond à un type interdit
                if expected not in matched_types:
                    for f in forbidden:
                        if f in matched_types:
                            issues.append(self._issue(
                                field,
                                value,
                                "SEMANTIC",
                                f"Value matches sensitive type '{f}' instead of '{expected}'"
                            ))
                            break

        return issues

    # ============================================================
    # HELPERS
    # ============================================================

    def _compile_patterns(self):
        """
        Compile toutes les regex de la taxonomie une seule fois (performance).
        """
        compiled = {}
        patterns = self.rules.get("FORMAT", {}).get("patterns", {})

        for name, cfg in patterns.items():
            try:
                compiled[name] = re.compile(cfg["regex"])
            except Exception:
                pass
        return compiled

    def _detect_value_types(self, value: str) -> List[str]:
        """
        Retourne la liste des TYPES sensibles que la valeur matche.
        """
        matches = []
        for type_name, pattern in self._compiled_patterns.items():
            if pattern.search(value):
                matches.append(type_name)
        return matches

    def _is_valid_date(self, value: str, fmt: str) -> bool:
        try:
            datetime.strptime(value, fmt)
            return True
        except Exception:
            return False

    def _parse_date(self, value: Any):
        try:
            fmt = self.rules["FORMAT"]["date"]["format"]
            return datetime.strptime(str(value), fmt)
        except Exception:
            return None

    def _safe_number(self, value: Any):
        try:
            return float(value)
        except Exception:
            return None

    def _issue(self, field: str, value: Any, issue_type: str, message: str) -> Inconsistency:
        return Inconsistency(
            field=field,
            value=value,
            type=issue_type,
            message=message
        )
