"""
Migrate MongoDB Atlas data to local MongoDB container.

Usage:
  1. Make sure local mongo container is running:  docker compose up mongo -d
  2. Run:  python migrate_atlas_to_local.py

This connects to Atlas (source), reads all collections from DataGovDB,
and writes them to the local MongoDB container.
"""
import sys
from pymongo import MongoClient

# ── Configuration ──────────────────────────────────────────────
ATLAS_URI = "mongodb+srv://projetFD:ensias2025@datagovdb.sjhsdum.mongodb.net/?retryWrites=true&w=majority&appName=DataGovDB"
# Use "mongo" hostname when running inside Docker network, "localhost" when running locally
LOCAL_URI = "mongodb://mongo:27017"
DATABASE_NAME = "DataGovDB"


def migrate():
    print(f"Connecting to Atlas...")
    try:
        atlas_client = MongoClient(ATLAS_URI, serverSelectionTimeoutMS=10000)
        atlas_client.admin.command("ping")
        print("  Atlas connection OK")
    except Exception as e:
        print(f"  ERROR: Cannot connect to Atlas: {e}")
        print("  Make sure you have internet connectivity for this one-time migration.")
        sys.exit(1)

    print(f"Connecting to local MongoDB (localhost:27017)...")
    try:
        local_client = MongoClient(LOCAL_URI, serverSelectionTimeoutMS=5000)
        local_client.admin.command("ping")
        print("  Local MongoDB connection OK")
    except Exception as e:
        print(f"  ERROR: Cannot connect to local MongoDB: {e}")
        print("  Make sure the mongo container is running: docker compose up mongo -d")
        sys.exit(1)

    atlas_db = atlas_client[DATABASE_NAME]
    local_db = local_client[DATABASE_NAME]

    collections = atlas_db.list_collection_names()
    if not collections:
        print(f"\nNo collections found in Atlas database '{DATABASE_NAME}'.")
        print("Nothing to migrate.")
        return

    print(f"\nFound {len(collections)} collections in Atlas '{DATABASE_NAME}':")
    for c in sorted(collections):
        count = atlas_db[c].count_documents({})
        print(f"  - {c}: {count} documents")

    print("\n--- Starting migration ---\n")
    total_docs = 0
    for col_name in sorted(collections):
        atlas_col = atlas_db[col_name]
        local_col = local_db[col_name]
        docs = list(atlas_col.find({}))

        if not docs:
            print(f"  {col_name}: 0 documents (skipped)")
            continue

        # Drop existing local collection to avoid duplicates
        local_col.drop()

        # Copy indexes (except _id which is automatic)
        indexes = atlas_col.index_information()
        for idx_name, idx_info in indexes.items():
            if idx_name == "_id_":
                continue
            try:
                keys = idx_info["key"]
                opts = {}
                if idx_info.get("unique"):
                    opts["unique"] = True
                if idx_info.get("sparse"):
                    opts["sparse"] = True
                local_col.create_index(keys, name=idx_name, **opts)
            except Exception:
                pass  # Skip indexes that fail (e.g. text indexes with language)

        # Insert documents
        result = local_col.insert_many(docs)
        count = len(result.inserted_ids)
        total_docs += count
        print(f"  {col_name}: {count} documents migrated")

    print(f"\n--- Migration complete ---")
    print(f"Total: {total_docs} documents across {len(collections)} collections")

    # Also migrate other databases on Atlas (auto, no interactive prompt)
    all_dbs = atlas_client.list_database_names()
    other_dbs = [d for d in all_dbs if d not in ("admin", "local", "config", DATABASE_NAME)]
    if other_dbs:
        print(f"\nAlso migrating other databases: {other_dbs}")
        for db_name in other_dbs:
            db = atlas_client[db_name]
            cols = db.list_collection_names()
            if cols:
                local_other_db = local_client[db_name]
                for col_name in cols:
                    docs = list(db[col_name].find({}))
                    if docs:
                        local_other_db[col_name].drop()
                        local_other_db[col_name].insert_many(docs)
                        print(f"    {db_name}.{col_name}: {len(docs)} documents migrated")

    atlas_client.close()
    local_client.close()
    print("\nDone! You can now use local MongoDB without Atlas.")


if __name__ == "__main__":
    migrate()
