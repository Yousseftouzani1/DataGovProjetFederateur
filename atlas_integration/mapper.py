# atlas_integration/mapper.py

def map_detection(detection: dict) -> dict:
    """
    Input: DetectionResult (TON moteur)
    Output: Objet normalisé pour Atlas
    """
    return {
        "attribute": detection["entity_type"],
        "domain": detection.get("domain", "UNKNOWN"),
        "category": detection.get("category", "UNKNOWN"),
        "sensitivity": detection.get("sensitivity_level", "unknown")
    }
