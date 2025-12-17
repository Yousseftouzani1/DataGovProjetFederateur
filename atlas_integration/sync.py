# atlas_integration/sync.py

from collections import defaultdict
from typing import Dict, List

from atlas_integration.client import AtlasClient
from atlas_integration.entities import create_dataset, create_data_attribute
from atlas_integration.mapper import map_detection
from atlas_integration.tags import build_tags


def sync_analyze_response_to_atlas(
    analyze_response: Dict,
    dataset_name: str
) -> Dict:
    """
    Synchronise la sortie du moteur de détection vers Apache Atlas
    - 1 dataset
    - N attributs uniques
    - Tags PII/SPI/CRITICAL
    """

    # 🔒 Sécurité : aucune détection → rien à synchroniser
    detections = analyze_response.get("detections", [])
    if not detections:
        return {
            "status": "skipped",
            "reason": "no_detections",
            "entities_synced": 0
        }

    atlas = AtlasClient()

    # ============================================================
    # 1️⃣ Création du DATASET (idempotent)
    # ============================================================

    domain = detections[0].get("domain", "UNKNOWN")

    dataset_payload = create_dataset(dataset_name, domain)
    dataset_resp = atlas.post("/entity", dataset_payload)

    dataset_guid = next(iter(dataset_resp["guidAssignments"].values()))

    # ============================================================
    # 2️⃣ Dé-duplication des entités détectées
    # (évite créer 10 fois IBAN si trouvé 10 fois)
    # ============================================================

    unique_attributes: Dict[str, dict] = {}

    for det in detections:
        mapped = map_detection(det)
        attr_name = mapped["attribute"]

        # On garde UNE seule instance par type logique
        if attr_name not in unique_attributes:
            unique_attributes[attr_name] = mapped

    # ============================================================
    # 3️⃣ Création des ATTRIBUTS + TAGS
    # ============================================================

    synced_attributes = []

    for attr_name, mapped in unique_attributes.items():

        # --- Création attribut ---
        attr_payload = create_data_attribute(dataset_name, attr_name)
        attr_resp = atlas.post("/entity", attr_payload)

        attr_guid = next(iter(attr_resp["guidAssignments"].values()))

        # --- Application des tags ---
        tags = build_tags(mapped)

        for tag in tags:
            atlas.post(
                f"/entity/guid/{attr_guid}/classifications",
                tag
            )

        synced_attributes.append(attr_name)

    # ============================================================
    # 4️⃣ Résultat final
    # ============================================================

    return {
        "status": "success",
        "dataset": dataset_name,
        "dataset_guid": dataset_guid,
        "attributes_synced": synced_attributes,
        "entities_synced": len(synced_attributes)
    }
