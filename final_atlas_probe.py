from services.common.atlas_client import AtlasClient
import json

def test_live_search():
    print("--- Probing Live Atlas for DataSets ---")
    client = AtlasClient()
    
    # Check health first
    if client.is_healthy():
        print("✅ Atlas is HEALTHY")
    else:
        print("❌ Atlas is UNREACHABLE")
        return

    # Basic search for DataSets
    print("\nSearching for 'DataSet' entities...")
    entities = client.basic_search("DataSet")
    print(f"Entities found: {len(entities)}")
    
    for ent in entities:
        name = ent.get("attributes", {}).get("name")
        print(f"- {name} (GUID: {ent.get('guid')})")

    # Fetch Classifications
    print("\nFetching Classifications...")
    classifications = client.get_all_classifications()
    print(f"Classifications found: {len(classifications)}")
    print(f"Sample: {classifications[:5]}")

if __name__ == "__main__":
    test_live_search()
