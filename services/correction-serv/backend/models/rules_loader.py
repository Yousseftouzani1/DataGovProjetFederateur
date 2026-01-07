import os
import yaml
import re
from typing import Dict, Any

# Cache global (évite relecture disque + recompilation regex)
_RULES_CACHE: Dict[str, Any] | None = None


def load_rules(force_reload: bool = False) -> Dict[str, Any]:
    """
    Charge et retourne l'ensemble des règles de gouvernance.

    - YAML gouverné par Data Steward
    - Cache mémoire pour performance
    - Précompilation des regex
    """

    global _RULES_CACHE

    if _RULES_CACHE is not None and not force_reload:
        return _RULES_CACHE

    base_path = os.path.join(os.path.dirname(__file__), "../rules")

    rules: Dict[str, Any] = {}

    # --------------------------------------------------
    # 1. Charger les règles de correction principales
    # --------------------------------------------------
    rules_path = os.path.join(base_path, "correction_rules.yaml")
    if not os.path.exists(rules_path):
        raise FileNotFoundError("correction_rules.yaml not found")

    with open(rules_path, "r", encoding="utf-8") as f:
        rules = yaml.safe_load(f) or {}

    # --------------------------------------------------
    # 2. Précompiler les patterns regex (performance)
    # --------------------------------------------------
    rules["__compiled_patterns__"] = _compile_patterns(rules)

    # --------------------------------------------------
    # 3. Normalisation minimale (sécurité)
    # --------------------------------------------------
    _ensure_required_sections(rules)

    _RULES_CACHE = rules
    return rules


# ======================================================
# INTERNAL HELPERS
# ======================================================

def _compile_patterns(rules: Dict[str, Any]) -> Dict[str, re.Pattern]:
    """
    Compile toutes les regex déclarées dans les règles.

    Retour :
    {
      "EMAIL": re.Pattern,
      "PHONE_MA": re.Pattern,
      ...
    }
    """
    compiled = {}

    format_section = rules.get("FORMAT", {})
    patterns = format_section.get("patterns", {})

    for name, cfg in patterns.items():
        regex = cfg.get("regex")
        if not regex:
            continue
        try:
            compiled[name] = re.compile(regex)
        except re.error as e:
            raise ValueError(f"Invalid regex for pattern '{name}': {e}")

    return compiled


def _ensure_required_sections(rules: Dict[str, Any]) -> None:
    """
    Vérifie que les sections minimales existent
    (évite des KeyError plus tard).
    """
    required = [
        "FORMAT",
        "DOMAIN",
        "SEMANTIC",
        "STATISTICAL",
        "TEMPORAL",
        "REFERENTIAL"
    ]

    for section in required:
        rules.setdefault(section, {})
