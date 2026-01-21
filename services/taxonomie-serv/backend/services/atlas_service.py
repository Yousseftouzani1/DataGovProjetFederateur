import sys
from fastapi import HTTPException
from backend.core.patterns import MOROCCAN_PATTERNS, ARABIC_PATTERNS

# Import Atlas Client (assuming /common is in path or needs insert)
# In main.py it was:
# sys.path.append('/common')
# from atlas_client import AtlasClient

async def sync_taxonomy_to_atlas(taxonomy_engine):
    """
    Sync taxonomy to Apache Atlas (Cahier Section 4.6)
    Creates entity type definitions for all 47+ Moroccan PII/SPI patterns
    """
    try:
        # Import Atlas client
        try:
            # Assumes environment is set up such that common is importable
            # If running in docker, /common might be in PYTHONPATH
            from atlas_client import AtlasClient
        except ImportError:
             # Fallback just in case
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'common'))
            from atlas_client import AtlasClient
        
        atlas = AtlasClient()
        
        if atlas.mock_mode:
            return {
                "warning": "Atlas in MOCK mode. Set MOCK_GOVERNANCE=false to sync to real Atlas",
                "mock_mode": True,
                "total_patterns": len(MOROCCAN_PATTERNS) + len(ARABIC_PATTERNS)
            }
        
        synced = 0
        errors = []
        
        # Sync all Moroccan patterns as entity types
        for entity_type, config in MOROCCAN_PATTERNS.items():
            try:
                # Calculate sensitivity
                sensitivity = taxonomy_engine.sensitivity_calc.calculate(entity_type)
                
                # Create entity definition
                entity_def = {
                    "entityDefs": [{
                        "name": f"pii_{entity_type.lower()}",
                        "superTypes": ["DataSet"],
                        "description": f"Moroccan PII/SPI: {entity_type}",
                        "attributeDefs": [
                            {"name": "sensitivity_level", "typeName": "string"},
                            {"name": "sensitivity_score", "typeName": "float"},
                            {"name": "category", "typeName": "string"},
                            {"name": "domain", "typeName": "string"},
                            {
                                "name": "legal_score",
                                "typeName": "float",
                                "defaultValue": str(sensitivity["breakdown"]["legal"])
                            },
                            {
                                "name": "risk_score",
                                "typeName": "float",
                                "defaultValue": str(sensitivity["breakdown"]["risk"])
                            },
                            {
                                "name": "impact_score",
                                "typeName": "float",
                                "defaultValue": str(sensitivity["breakdown"]["impact"])
                            }
                        ],
                        "options": {
                            "sensitivity": sensitivity["level"],
                            "category": config["category"],
                            "domain": config.get("domain", ""),
                            "cahier_section": "4.8"
                        }
                    }]
                }
                
                # Submit to Atlas
                result = atlas._post("/types/typedefs", entity_def)
                if result:
                    synced += 1
            except Exception as e:
                errors.append({"entity": entity_type, "error": str(e)})
        
        # Sync Arabic patterns
        for entity_type, config in ARABIC_PATTERNS.items():
            try:
                sensitivity = taxonomy_engine.sensitivity_calc.calculate(entity_type)
                
                entity_def = {
                    "entityDefs": [{
                        "name": f"pii_arabic_{entity_type.lower()}",
                        "superTypes": ["DataSet"],
                        "description": f"Arabic PII: {entity_type}",
                        "attributeDefs": [
                            {"name": "sensitivity_level", "typeName": "string"},
                            {"name": "category", "typeName": "string"}
                        ],
                        "options": {
                            "sensitivity": sensitivity["level"],
                            "language": "ar"
                        }
                    }]
                }
                
                result = atlas._post("/types/typedefs", entity_def)
                if result:
                    synced += 1
            except Exception as e:
                errors.append({"entity": entity_type, "error": str(e)})
        
        total = len(MOROCCAN_PATTERNS) + len(ARABIC_PATTERNS)
        
        return {
            "message": f"Synced {synced}/{total} entities to Apache Atlas",
            "synced": synced,
            "total": total,
            "errors": errors,
            "mock_mode": False
        }
        
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Atlas client not available: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Atlas sync failed: {str(e)}"
        )
