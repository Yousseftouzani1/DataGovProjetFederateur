# atlas_integration/tags.py

def build_tags(mapped: dict) -> list:
    tags = []

    # Sensibilité
    if mapped["sensitivity"] == "critical":
        tags.append({"typeName": "CRITICAL"})
    elif mapped["sensitivity"] == "high":
        tags.append({"typeName": "HIGH"})

    # Domaine
    if mapped["domain"].lower() == "financier":
        tags.extend([
            {"typeName": "FINANCIAL"},
            {"typeName": "SPI"}
        ])
    else:
        tags.append({"typeName": "PII"})

    return tags
