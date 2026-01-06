"""
Pattern Migration Script
Migrates 47 Moroccan patterns from hardcoded dictionaries to MongoDB
"""

from datetime import datetime
import sys
import os

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
services_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, os.path.join(services_dir, 'common'))
sys.path.insert(0, os.path.dirname(current_dir))

from mongodb_client import get_collection

# Import patterns from main.py
from main import MOROCCAN_PATTERNS

def group_patterns_by_category():
    """Group patterns into categories for MongoDB structure"""
    
    categories_map = {}
    
    for pattern_id, pattern_data in MOROCCAN_PATTERNS.items():
        category = pattern_data.get('category', 'OTHER')
        
        if category not in categories_map:
            # Create category structure
            categories_map[category] = {
                "class": category,
                "class_en": category.replace('_', ' ').title(),
                "type": "PII" if "IDENTITE" in category or "COORDONNEES" in category else "SPI",
                "subclasses": []
            }
        
        # Create subclass (pattern) structure
        subclass = {
            "name": pattern_id,
            "name_en": pattern_data.get('description', pattern_id.replace('_', ' ').title()),
            "synonyms_fr": [],
            "synonyms_en": [],
            "acronyms_fr": [pattern_id],
            "acronyms_en": [],
            "regex_patterns": pattern_data.get('patterns', []),
            "sensitivity_level": pattern_data.get('sensitivity', 'medium'),
            "risk_level": pattern_data.get('sensitivity', 'medium').capitalize(),
            "regulations": ["Loi 09-08", "RGPD"],
            "context_required": pattern_data.get('context_keywords', []),
            "category": category,
            "domain": pattern_data.get('domain', 'GENERAL')
        }
        
        categories_map[category]['subclasses'].append(subclass)
    
    return list(categories_map.values())

def create_taxonomy_document():
    """Create complete taxonomy document for MongoDB"""
    
    categories = group_patterns_by_category()
    total_patterns = sum(len(cat['subclasses']) for cat in categories)
    
    taxonomy_doc = {
        "metadata": {
            "domain_id": "DOM-010",
            "domain_name": "IDENTITE_MAROCAINE_ETENDUE",
            "domain_name_en": "EXTENDED_MOROCCAN_IDENTITY",
            "version": "2.0",
            "context": "Maroc",
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "description": "Taxonomie PII/SPI marocaine étendue - 47 types - Cahier des Charges Section 4.8",
            "total_entities": total_patterns,
            "cahier_section": "4.8",
            "source": "taxonomy_service_v2"
        },
        "categories": categories,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    }
    
    return taxonomy_doc

def migrate_to_mongodb():
    """Main migration function"""
    
    print("=" * 70)
    print("TAXONOMY PATTERN MIGRATION TO MONGODB")
    print("=" * 70)
    print(f"\nMigrating 47 Moroccan PII/SPI patterns...")
    
    try:
        # Get taxonomies collection
        taxonomies = get_collection('taxonomies')
        
        # Create taxonomy document
        taxonomy_doc = create_taxonomy_document()
        
        print(f"\nTaxonomy Document:")
        print(f"  - Domain: {taxonomy_doc['metadata']['domain_name']}")
        print(f"  - Categories: {len(taxonomy_doc['categories'])}")
        print(f"  - Total Patterns: {taxonomy_doc['metadata']['total_entities']}")
        
        # Check if already exists
        existing = taxonomies.find_one({
            "metadata.domain_name": "IDENTITE_MAROCAINE_ETENDUE"
        })
        
        if existing:
            print(f"\n⚠️  Document already exists (ID: {existing['_id']})")
            choice = input("Update existing document? (y/n): ")
            
            if choice.lower() == 'y':
                result = taxonomies.update_one(
                    {"_id": existing["_id"]},
                    {"$set": taxonomy_doc}
                )
                print(f"✅ Updated {result.modified_count} document")
            else:
                print("❌ Migration cancelled")
                return False
        else:
            print("\n✅ Inserting new taxonomy document...")
            result = taxonomies.insert_one(taxonomy_doc)
            print(f"✅ Inserted with ID: {result.inserted_id}")
        
        # Verification
        print("\n" + "=" * 70)
        print("VERIFICATION")
        print("=" * 70)
        
        total_in_db = taxonomies.count_documents({"metadata.context": "Maroc"})
        print(f"Total Moroccan taxonomies in DB: {total_in_db}")
        
        # Get the document we just inserted/updated
        doc = taxonomies.find_one({"metadata.domain_name": "IDENTITE_MAROCAINE_ETENDUE"})
        if doc:
            total_patterns_db = sum(len(cat['subclasses']) for cat in doc['categories'])
            print(f"Patterns in our document: {total_patterns_db}")
            
            if total_patterns_db == 47:
                print("\n✅ MIGRATION SUCCESSFUL! All 47 patterns stored.")
                return True
            else:
                print(f"\n⚠️  Warning: Expected 47 patterns, found {total_patterns_db}")
                return False
        else:
            print("\n❌ Document not found after insertion!")
            return False
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate_to_mongodb()
    sys.exit(0 if success else 1)
