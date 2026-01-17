
import os
import sys

# Ensure module access
sys.path.append(os.getcwd())

try:
    from atlas_integration.client import AtlasClient
    
    print("🗑️ Starting Atlas Purge...")
    client = AtlasClient()
    
    # 1. Purge Datasets
    print("   Searching for ALL DataSets...")
    dataset_count = client.purge_type("DataSet")
    print(f"✅ Deleted {dataset_count} DataSets.")
    
    # 2. Purge Processes (Lineage)
    print("   Searching for ALL Processes...")
    process_count = client.purge_type("Process")
    print(f"✅ Deleted {process_count} Processes.")
    
    print("✨ Atlas cleanup complete!")
    
except ImportError as e:
    print(f"❌ Error: {e}")
except Exception as e:
    print(f"❌ Unexpected Error: {e}")
