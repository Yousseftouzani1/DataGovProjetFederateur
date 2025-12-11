"""
Taxonomy Loader - Load JSON taxonomies into MongoDB Atlas
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import sys

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database.mongodb import sync_db, test_sync_connection, COLLECTIONS

# ============================================================
# CONFIGURATION
# ============================================================

DOMAINS_DIR = Path(__file__).parent.parent / "taxonomie" / "domains"

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def load_json_file(filepath: Path) -> Optional[Dict]:
    """Load and parse a JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading {filepath}: {e}")
        return None

def flatten_entities(taxonomy: Dict) -> List[Dict]:
    """Flatten taxonomy into individual entity documents"""
    entities = []
    metadata = taxonomy.get("metadata", {})
    domain_id = metadata.get("domain_id", "UNKNOWN")
    domain_name = metadata.get("domain_name", "UNKNOWN")
    
    entity_counter = 1
    
    for category in taxonomy.get("categories", []):
        category_name = category.get("class", "UNKNOWN")
        category_type = category.get("type", "PII")
        
        for subclass in category.get("subclasses", []):
            entity = {
                "entity_id": f"{domain_id}-ENT-{str(entity_counter).zfill(3)}",
                "name": subclass.get("name", ""),
                "name_en": subclass.get("name_en", ""),
                "domain_id": domain_id,
                "domain_name": domain_name,
                "category": category_name,
                "category_en": category.get("class_en", ""),
                "type": category_type,
                "sensitivity_level": subclass.get("sensitivity_level", "unknown"),
                "risk_level": subclass.get("risk_level", ""),
                "synonyms_fr": subclass.get("synonyms_fr", []),
                "synonyms_en": subclass.get("synonyms_en", []),
                "acronyms_fr": subclass.get("acronyms_fr", []),
                "acronyms_en": subclass.get("acronyms_en", []),
                "regex_patterns": subclass.get("regex_patterns", []),
                "format": subclass.get("format", ""),
                "regulations": subclass.get("regulations", []),
                "why_sensitive": subclass.get("why_sensitive", ""),
                "context_required": subclass.get("context_required", []),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            entities.append(entity)
            entity_counter += 1
    
    return entities

def extract_domain_metadata(taxonomy: Dict) -> Dict:
    """Extract domain metadata from taxonomy"""
    metadata = taxonomy.get("metadata", {})
    
    # Count total entities
    total_entities = sum(
        len(cat.get("subclasses", []))
        for cat in taxonomy.get("categories", [])
    )
    
    return {
        "domain_id": metadata.get("domain_id", ""),
        "domain_name": metadata.get("domain_name", ""),
        "domain_name_en": metadata.get("domain_name_en", ""),
        "version": metadata.get("version", "1.0"),
        "context": metadata.get("context", "Maroc"),
        "description": metadata.get("description", ""),
        "total_entities": total_entities,
        "categories_count": len(taxonomy.get("categories", [])),
        "last_updated": metadata.get("last_updated", ""),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

# ============================================================
# MAIN LOADER FUNCTIONS
# ============================================================

def load_single_taxonomy(filepath: Path, clear_existing: bool = False) -> Dict:
    """Load a single taxonomy file into MongoDB"""
    print(f"\n📁 Loading: {filepath.name}")
    
    taxonomy = load_json_file(filepath)
    if not taxonomy:
        return {"status": "error", "file": filepath.name, "message": "Failed to load JSON"}
    
    domain_id = taxonomy.get("metadata", {}).get("domain_id", "UNKNOWN")
    
    # Get collections
    taxonomies_col = sync_db[COLLECTIONS["taxonomies"]]
    entities_col = sync_db[COLLECTIONS["entities"]]
    domains_col = sync_db[COLLECTIONS["domains"]]
    
    # Clear existing data for this domain if requested
    if clear_existing:
        taxonomies_col.delete_many({"metadata.domain_id": domain_id})
        entities_col.delete_many({"domain_id": domain_id})
        domains_col.delete_many({"domain_id": domain_id})
    
    # Insert taxonomy document
    taxonomy["created_at"] = datetime.utcnow()
    taxonomy["updated_at"] = datetime.utcnow()
    
    try:
        taxonomies_col.replace_one(
            {"metadata.domain_id": domain_id},
            taxonomy,
            upsert=True
        )
        print(f"  ✅ Taxonomy document inserted/updated")
    except Exception as e:
        print(f"  ❌ Error inserting taxonomy: {e}")
    
    # Insert domain metadata
    domain_meta = extract_domain_metadata(taxonomy)
    try:
        domains_col.replace_one(
            {"domain_id": domain_id},
            domain_meta,
            upsert=True
        )
        print(f"  ✅ Domain metadata inserted/updated")
    except Exception as e:
        print(f"  ❌ Error inserting domain: {e}")
    
    # Insert flattened entities
    entities = flatten_entities(taxonomy)
    entities_inserted = 0
    
    for entity in entities:
        try:
            entities_col.replace_one(
                {"entity_id": entity["entity_id"]},
                entity,
                upsert=True
            )
            entities_inserted += 1
        except Exception as e:
            print(f"  ❌ Error inserting entity {entity.get('name', 'UNKNOWN')}: {e}")
    
    print(f"  ✅ {entities_inserted} entities inserted/updated")
    
    return {
        "status": "success",
        "file": filepath.name,
        "domain_id": domain_id,
        "entities_count": entities_inserted
    }

def load_all_taxonomies(clear_existing: bool = True) -> Dict:
    """Load all taxonomy files from the domains directory"""
    print("\n" + "=" * 60)
    print("🚀 TAXONOMY LOADER - Loading JSON files to MongoDB Atlas")
    print("=" * 60)
    
    # Test connection first
    conn_result = test_sync_connection()
    if conn_result.get("status") != "connected":
        print(f"❌ MongoDB connection failed: {conn_result.get('message')}")
        return {"status": "error", "message": "MongoDB connection failed"}
    
    print(f"✅ Connected to MongoDB: {conn_result.get('database')}")
    
    # Find all JSON files
    if not DOMAINS_DIR.exists():
        print(f"❌ Domains directory not found: {DOMAINS_DIR}")
        return {"status": "error", "message": "Domains directory not found"}
    
    json_files = list(DOMAINS_DIR.glob("*.json"))
    print(f"\n📂 Found {len(json_files)} taxonomy files in {DOMAINS_DIR}")
    
    results = []
    total_entities = 0
    
    for filepath in sorted(json_files):
        result = load_single_taxonomy(filepath, clear_existing=clear_existing)
        results.append(result)
        if result.get("status") == "success":
            total_entities += result.get("entities_count", 0)
    
    # Create indexes
    print("\n📊 Creating indexes...")
    create_indexes()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    print(f"  Total files processed: {len(results)}")
    print(f"  Successful: {sum(1 for r in results if r.get('status') == 'success')}")
    print(f"  Total entities loaded: {total_entities}")
    
    # Show collection stats
    print("\n📈 Collection Statistics:")
    for col_name in ["taxonomies", "domains", "entities"]:
        count = sync_db[COLLECTIONS[col_name]].count_documents({})
        print(f"  - {col_name}: {count} documents")
    
    print("\n" + "=" * 60)
    print("✅ LOADING COMPLETE!")
    print("=" * 60)
    
    return {
        "status": "success",
        "files_processed": len(results),
        "total_entities": total_entities,
        "results": results
    }

def create_indexes():
    """Create MongoDB indexes for optimal query performance"""
    # Taxonomies collection indexes
    taxonomies_col = sync_db[COLLECTIONS["taxonomies"]]
    try:
        taxonomies_col.create_index("metadata.domain_id", unique=True)
        taxonomies_col.create_index("metadata.domain_name")
        taxonomies_col.create_index("categories.class")
        print("  ✅ Taxonomies indexes created")
    except Exception as e:
        print(f"  ⚠️ Taxonomies indexes: {e}")
    
    # Entities collection indexes
    entities_col = sync_db[COLLECTIONS["entities"]]
    try:
        entities_col.create_index("entity_id", unique=True)
        entities_col.create_index("domain_id")
        entities_col.create_index("category")
        entities_col.create_index("sensitivity_level")
        entities_col.create_index("type")
        entities_col.create_index([("name", "text"), ("synonyms_fr", "text")])
        print("  ✅ Entities indexes created")
    except Exception as e:
        print(f"  ⚠️ Entities indexes: {e}")
    
    # Domains collection indexes
    domains_col = sync_db[COLLECTIONS["domains"]]
    try:
        domains_col.create_index("domain_id", unique=True)
        domains_col.create_index("domain_name", unique=True)
        print("  ✅ Domains indexes created")
    except Exception as e:
        print(f"  ⚠️ Domains indexes: {e}")

def get_statistics() -> Dict:
    """Get statistics from MongoDB collections"""
    stats = {
        "database": "DataGovDB",
        "collections": {}
    }
    
    for col_name, col_key in COLLECTIONS.items():
        try:
            count = sync_db[col_key].count_documents({})
            stats["collections"][col_name] = count
        except:
            stats["collections"][col_name] = 0
    
    # Get entities by sensitivity level
    try:
        pipeline = [
            {"$group": {"_id": "$sensitivity_level", "count": {"$sum": 1}}}
        ]
        sensitivity_stats = list(sync_db[COLLECTIONS["entities"]].aggregate(pipeline))
        stats["entities_by_sensitivity"] = {s["_id"]: s["count"] for s in sensitivity_stats}
    except:
        stats["entities_by_sensitivity"] = {}
    
    # Get entities by domain
    try:
        pipeline = [
            {"$group": {"_id": "$domain_name", "count": {"$sum": 1}}}
        ]
        domain_stats = list(sync_db[COLLECTIONS["entities"]].aggregate(pipeline))
        stats["entities_by_domain"] = {d["_id"]: d["count"] for d in domain_stats}
    except:
        stats["entities_by_domain"] = {}
    
    return stats

# ============================================================
# CLI INTERFACE
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Load taxonomies into MongoDB")
    parser.add_argument("--clear", action="store_true", help="Clear existing data before loading")
    parser.add_argument("--stats", action="store_true", help="Show statistics only")
    parser.add_argument("--test", action="store_true", help="Test connection only")
    
    args = parser.parse_args()
    
    if args.test:
        result = test_sync_connection()
        print(f"Connection test: {result}")
    elif args.stats:
        stats = get_statistics()
        print(json.dumps(stats, indent=2, default=str))
    else:
        load_all_taxonomies(clear_existing=args.clear or True)
