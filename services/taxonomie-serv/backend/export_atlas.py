"""
Apache Atlas Classifications Export Script
Exports Atlas entity types and classifications to JSON
Cahier Section 4.9 - Deliverable #4
"""

import json
import sys
import os
from datetime import datetime

# Add paths
current_dir = os.path.dirname(os.path.abspath(__file__))
services_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, os.path.join(services_dir, 'common'))
sys.path.insert(0, os.path.dirname(current_dir))

from mongodb_client import get_collection

def create_atlas_entity_type(pattern_id, pattern_data, category):
    """Create Atlas entity type definition for a pattern"""
    
    return {
        "typeName": "data_attribute",
        "name": pattern_id,
        "description": pattern_data.get('description', pattern_id),
        "superTypes": ["Asset"],
        "attributeDefs": [
            {
                "name": "qualifiedName",
                "typeName": "string",
                "isOptional": False,
                "cardinality": "SINGLE",
                "valuesMinCount": 1,
                "valuesMaxCount": 1,
                "isUnique": True,
                "isIndexable": True
            },
            {
                "name": "sensitivity_level",
                "typeName": "string",
                "isOptional": False,
                "cardinality": "SINGLE"
            },
            {
                "name": "legal_basis",
                "typeName": "array<string>",
                "isOptional": False,
                "cardinality": "SET"
            },
            {
                "name": "encryption_required",
                "typeName": "boolean",
                "isOptional": False,
                "cardinality": "SINGLE"
            },
            {
                "name": "regex_patterns",
                "typeName": "array<string>",
                "isOptional": True,
                "cardinality": "SET"
            }
        ]
    }

def create_atlas_classification(sensitivity_level):
    """Create Atlas classification definition"""
    
    return {
        "classificationDefs": [
            {
                "name": "PII",
                "description": "Personally Identifiable Information",
                "superTypes": [],
                "attributeDefs": []
            },
            {
                "name": "SPI",
                "description": "Sensitive Personal Information",
                "superTypes": ["PII"],
                "attributeDefs": []
            },
            {
                "name": f"{sensitivity_level.upper()}_SENSITIVITY",
                "description": f"{sensitivity_level.title()} sensitivity level data",
                "superTypes": [],
                "attributeDefs": [
                    {
                        "name": "sensitivity_score",
                        "typeName": "float",
                        "isOptional": True,
                        "cardinality": "SINGLE"
                    }
                ]
            }
        ]
    }

def export_atlas_types():
    """Export Atlas entity types and classifications to JSON"""
    
    print("="*70)
    print("APACHE ATLAS TYPES & CLASSIFICATIONS EXPORT")
    print("="*70)
    
    try:
        # Get patterns from MongoDB
        taxonomies = get_collection('taxonomies')
        moroccan_tax = taxonomies.find_one({
            "metadata.domain_name": "IDENTITE_MAROCAINE_ETENDUE"
        })
        
        if not moroccan_tax:
            print("❌ Moroccan taxonomy not found in MongoDB")
            return False
        
        entity_types = []
        classifications_set = set()
        entity_instances = []
        
        # Process all patterns
        for category in moroccan_tax.get('categories', []):
            for subclass in category.get('subclasses', []):
                pattern_id = subclass['name']
                sensitivity = subclass.get('sensitivity_level', 'medium')
                
                # Create entity type
                entity_type = create_atlas_entity_type(pattern_id, subclass, category['class'])
                entity_types.append(entity_type)
                
                # Track classifications
                classifications_set.add(sensitivity)
                
                # Create entity instance example
                entity_instance = {
                    "typeName": "data_attribute",
                    "attributes": {
                        "name": pattern_id,
                        "qualifiedName": f"{category['class']}::{pattern_id}",
                        "sensitivity_level": sensitivity,
                        "legal_basis": ["RGPD Art.6", "Loi 09-08 Art.3"],
                        "encryption_required": sensitivity in ["critical", "high"],
                        "regex_patterns": subclass.get('regex_patterns', [])
                    },
                    "classifications": [
                        {"typeName": "SPI" if "SPI" in category.get('type', 'PII') else "PII"},
                        {"typeName": f"{sensitivity.upper()}_SENSITIVITY"}
                    ]
                }
                entity_instances.append(entity_instance)
        
        # Create classifications
        all_classifications = {
            "classificationDefs": [
                {
                    "name": "PII",
                    "description": "Personally Identifiable Information - RGPD compliant",
                    "superTypes": [],
                    "attributeDefs": []
                },
                {
                    "name": "SPI",
                    "description": "Sensitive Personal Information - Article 9 RGPD",
                    "superTypes": ["PII"],
                    "attributeDefs": []
                }
            ]
        }
        
        # Add sensitivity classifications
        for sensitivity in classifications_set:
            all_classifications["classificationDefs"].append({
                "name": f"{sensitivity.upper()}_SENSITIVITY",
                "description": f"{sensitivity.title()} sensitivity level - Loi 09-08 compliant",
                "superTypes": [],
                "attributeDefs": [
                    {
                        "name": "sensitivity_score",
                        "typeName": "float",
                        "isOptional": True,
                        "cardinality": "SINGLE"
                    },
                    {
                        "name": "legal_basis",
                        "typeName": "array<string>",
                        "isOptional": True,
                        "cardinality": "SET"
                    }
                ]
            })
        
        # Create complete export
        atlas_export = {
            "export_metadata": {
                "export_date": datetime.now().isoformat(),
                "total_entity_types": len(entity_types),
                "total_classifications": len(all_classifications["classificationDefs"]),
                "total_instances": len(entity_instances),
                "database": "DataGovDB",
                "cahier_section": "4.9"
            },
            "entityDefs": entity_types,
            "classificationDefs": all_classifications["classificationDefs"],
            "entity_instances": entity_instances
        }
        
        # Write to JSON file
        output_file = "atlas_types_classifications_export.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(atlas_export, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Export successful!")
        print(f"   Output file: {output_file}")
        print(f"   Entity types: {len(entity_types)}")
        print(f"   Classifications: {len(all_classifications['classificationDefs'])}")
        print(f"   Entity instances: {len(entity_instances)}")
        print(f"   File size: {os.path.getsize(output_file) / 1024:.2f} KB")
        
        print(f"\n📊 Classifications:")
        for classification in all_classifications["classificationDefs"]:
            print(f"   - {classification['name']}: {classification['description']}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = export_atlas_types()
    sys.exit(0 if success else 1)
