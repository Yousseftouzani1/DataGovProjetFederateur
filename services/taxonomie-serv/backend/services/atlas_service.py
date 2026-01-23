import asyncio
import httpx
from fastapi import HTTPException
from backend.core.patterns import MOROCCAN_PATTERNS, ARABIC_PATTERNS

async def sync_taxonomy_to_atlas(taxonomy_engine):
    """
    Sync FULL taxonomy to Apache Atlas with strict throttling to prevent VM overload.
    1. Technical Sync: EntityDefs & ClassificationDefs (Batch=3, Sleep=2s)
    2. Business Sync: Glossary & Terms
    """
    try:
        from atlas_client import AtlasClient
        atlas_base = AtlasClient()
        
        if atlas_base.mock_mode:
            return {"warning": "Atlas in MOCK mode", "mock_mode": True}

        auth = (atlas_base.user, atlas_base.password)
        base_url = f"{atlas_base.base_api}/types/typedefs"
        
        # --- PHASE 1: TECHNICAL SYNC (Classifications) ---
        # Using 3 items per batch with 2s delay to be extremely safe
        def chunk_list(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i:i + n]

        entity_types = list(MOROCCAN_PATTERNS.keys())
        total_synced = 0
        batch_size = 3
        
        print(f"🚀 Starting FULL Technical Sync ({len(entity_types)} patterns)...")
        
        async with httpx.AsyncClient(auth=auth, timeout=30.0) as client:
            for batch in chunk_list(entity_types, batch_size):
                tasks = []
                for et in batch:
                    # 1. Entity Definition
                    tasks.append(client.post(base_url, json={
                        "entityDefs": [{
                            "name": f"pii_{et.lower()}",
                            "superTypes": ["DataSet"],
                            "description": f"Moroccan PII: {et}",
                            "attributeDefs": [{"name": "sensitivity", "typeName": "string"}]
                        }]
                    }))
                    # 2. Classification Definition
                    tasks.append(client.post(base_url, json={
                        "classificationDefs": [{"name": et, "description": f"Moroccan {et}"}]
                    }))

                await asyncio.gather(*tasks, return_exceptions=True)
                total_synced += len(batch)
                await asyncio.sleep(2.0)  # Slow down for VM safety

        # --- PHASE 2: BUSINESS SYNC (Glossary) ---
        print("📘 Starting Business Glossary Sync...")
        glossary = atlas_base.create_glossary(
            name="DataSentinel Glossary", 
            description="Business definitions for Moroccan PII/SPI detected by DataSentinel."
        )
        
        if glossary and "guid" in glossary:
            glossary_guid = glossary["guid"]
            term_count = 0
            # Sync Terms sequentially to be gentle
            for et in entity_types:
                try:
                    atlas_base.create_glossary_term(
                        glossary_guid=glossary_guid,
                        term_name=et.replace("_", " ").title(), # e.g. "CIN_MAROC" -> "Cin Maroc"
                        description=f"Automatically detected pattern for {et}"
                    )
                    term_count += 1
                except:
                    pass
        else:
            term_count = 0

        return {
            "message": f"Full Sync Complete: {total_synced} Classifications & {term_count} Glossary Terms.",
            "synced_technical": total_synced,
            "synced_glossary": term_count,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Async Atlas sync failed: {str(e)}")
