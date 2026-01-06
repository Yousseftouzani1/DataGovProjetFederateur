"""
MongoDB Taxonomy Collection Export Script
Exports taxonomy patterns to JSON file for documentation/backup
Cahier Section 4.9 - Deliverable #3
"""

import json
import sys
import os
from datetime import datetime

# Add paths
current_dir = os.path.dirname(os.path.abspath(__file__))
services_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, os.path.join(services_dir, 'common'))

from mongodb_client import get_collection

def export_taxonomy_collection():
    """Export entire taxonomy collection from MongoDB to JSON"""
    
    print("="*70)
    print("MONGODB TAXONOMY COLLECTION EXPORT")
    print("="*70)
    
    try:
        # Get taxonomies collection
        taxonomies = get_collection('taxonomies')
        
        # Fetch all Moroccan taxonomies
        moroccan_taxonomies = list(taxonomies.find(
            {"metadata.context": "Maroc"}
        ))
        
        print(f"\nFound {len(moroccan_taxonomies)} Moroccan taxonomy documents")
        
        # Convert ObjectId to string for JSON serialization
        for tax in moroccan_taxonomies:
            tax['_id'] = str(tax['_id'])
        
        # Calculate statistics
        total_patterns = sum(
            sum(len(cat.get('subclasses', [])) for cat in tax.get('categories', []))
            for tax in moroccan_taxonomies
        )
        
        # Create export data
        export_data = {
            "export_metadata": {
                "export_date": datetime.now().isoformat(),
                "total_documents": len(moroccan_taxonomies),
                "total_patterns": total_patterns,
                "database": "DataGovDB",
                "collection": "taxonomies",
                "context": "Maroc",
                "cahier_section": "4.9"
            },
            "taxonomies": moroccan_taxonomies
        }
        
        # Write to JSON file
        output_file = "taxonomy_collection_export.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n✅ Export successful!")
        print(f"   Output file: {output_file}")
        print(f"   Documents: {len(moroccan_taxonomies)}")
        print(f"   Total patterns: {total_patterns}")
        print(f"   File size: {os.path.getsize(output_file) / 1024:.2f} KB")
        
        # Summary by domain
        print(f"\n📊 Taxonomy Breakdown:")
        for tax in moroccan_taxonomies:
            domain_name = tax.get('metadata', {}).get('domain_name', 'Unknown')
            pattern_count = sum(len(cat.get('subclasses', [])) for cat in tax.get('categories', []))
            print(f"   - {domain_name}: {pattern_count} patterns")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = export_taxonomy_collection()
    sys.exit(0 if success else 1)
