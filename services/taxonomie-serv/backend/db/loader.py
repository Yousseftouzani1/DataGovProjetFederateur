"""
Pattern Loader - Load taxonomy patterns from MongoDB
"""

import sys
import os

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
# current_dir is backend/db
# services_dir should be ../../..
services_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.insert(0, os.path.join(services_dir, 'common'))

from mongodb_client import get_collection

def load_patterns_from_mongodb():
    """
    Load all Moroccan patterns from MongoDB taxonomies collection
    
    Returns:
        dict: Pattern dictionary compatible with TaxonomyEngine
        None: If loading fails
    """
    try:
        taxonomies = get_collection('taxonomies')
        
        # Get our Moroccan taxonomy document
        moroccan_tax = taxonomies.find_one({
            "metadata.domain_name": "IDENTITE_MAROCAINE_ETENDUE"
        })
        
        if not moroccan_tax:
            print("⚠️  Moroccan taxonomy not found in MongoDB")
            return None
        
        # Transform to engine format
        patterns = {}
        
        for category in moroccan_tax.get('categories', []):
            for subclass in category.get('subclasses', []):
                pattern_id = subclass['name']
                
                patterns[pattern_id] = {
                    'patterns': subclass.get('regex_patterns', []),
                    'category': category['class'],
                    'sensitivity': subclass.get('sensitivity_level', 'medium'),
                    'context_keywords': subclass.get('context_required', []),
                    'domain': subclass.get('domain', 'GENERAL'),
                    'description': subclass.get('name_en', pattern_id)
                }
        
        print(f"✅ Loaded {len(patterns)} patterns from MongoDB")
        
        # Add custom patterns if they exist
        try:
            custom_coll = get_collection('custom_patterns')
            for cp in custom_coll.find():
                p_id = cp.get('category', 'CUSTOM')
                patterns[p_id] = {
                    'patterns': [cp.get('pattern')] if isinstance(cp.get('pattern'), str) else cp.get('patterns', []),
                    'category': cp.get('class', 'CUSTOM'),
                    'sensitivity': cp.get('sensitivity', 'medium'),
                    'domain': cp.get('domain', 'GENERAL'),
                    'description': cp.get('description', p_id)
                }
            print(f"✅ Merged custom patterns from MongoDB")
        except:
            pass
            
        return patterns
        
    except Exception as e:
        print(f"❌ Error loading from MongoDB: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_pattern_count():
    """Get total number of patterns in MongoDB"""
    try:
        moroccan_tax = get_collection('taxonomies').find_one({
            "metadata.domain_name": "IDENTITE_MAROCAINE_ETENDUE"
        })
        
        if moroccan_tax:
            return sum(
                len(cat.get('subclasses', [])) 
                for cat in moroccan_tax.get('categories', [])
            )
        return 0
    except:
        return 0
