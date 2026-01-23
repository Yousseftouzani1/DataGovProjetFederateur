"""
Sync Atlas Tags to Ranger Policies
==================================
Data Governance Project 2024-2025 - Section 12.5 (Integration Trinity)

This script automates the "Handshake" between Atlas and Ranger.
1. Queries Atlas for entities with critical tags (PII, SPI, etc.)
2. Generates Ranger Policies dynamically.
3. Pushes policies to Ranger API.
"""

import sys
import os
import requests
import json
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from atlas_integration.client import AtlasClient
from ranger_integration.policies import build_masking_policy, build_access_policy

# Config
RANGER_URL = "http://ranger-admin:6080"
RANGER_AUTH = ("admin", "admin123")
CLUSTER_NAME = "primary_cluster"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AtlasRangerSync")

def get_tagged_entities(atlas_client, tag_name):
    """Fetch all entities tagged with `tag_name` from Atlas"""
    try:
        # Atlas DSL Search
        query = f"DataSet where classification = '{tag_name}'"
        results = atlas_client.search_entity(query, "DataSet")
        return results.get("entities", [])
    except Exception as e:
        logger.error(f"Failed to fetch tags from Atlas: {e}")
        return []

def create_ranger_policy(policy_json):
    """Push policy to Ranger"""
    try:
        # Check if policy exists first (to update instead of create)
        policy_name = policy_json["name"]
        resp = requests.get(f"{RANGER_URL}/service/public/v2/api/policy?policyName={policy_name}", auth=RANGER_AUTH)
        
        if resp.status_code == 200 and len(resp.json()) > 0:
            # Update existing
            existing_id = resp.json()[0]["id"]
            policy_json["id"] = existing_id
            update_url = f"{RANGER_URL}/service/public/v2/api/policy/{existing_id}"
            requests.put(update_url, json=policy_json, auth=RANGER_AUTH)
            logger.info(f"🔄 Updated policy: {policy_name}")
        else:
            # Create new
            create_url = f"{RANGER_URL}/service/public/v2/api/policy"
            requests.post(create_url, json=policy_json, auth=RANGER_AUTH)
            logger.info(f"✅ Created policy: {policy_name}")
            
    except Exception as e:
        logger.error(f"Failed to push policy to Ranger: {e}")

def sync_pii_policies(atlas_client):
    """
    Sync PII tags -> Masking Policies
    Rules:
    - PII tag -> Mask * (Redact)
    - Entities tagged PII are denied for 'public' role
    """
    logger.info("Starting PII Policy Sync...")
    
    entities = get_tagged_entities(atlas_client, "PII")
    
    # Group by dataset (table) to avoid 1 policy per column
    schema_map = {} 
    
    for entity in entities:
        # Assuming qualifiedName format: column@dataset_name.column_name
        # or column@database.table.column
        qname = entity["attributes"]["qualifiedName"]
        if "column@" in qname:
             # Parse dataset and column
             # Format: column@dataset.col
             parts = qname.split('@')[1].split('.')
             if len(parts) >= 2:
                 dataset = parts[0]
                 col = parts[1]
                 if dataset not in schema_map:
                     schema_map[dataset] = []
                 schema_map[dataset].append(col)
                 
    # Create one policy per dataset
    for dataset, columns in schema_map.items():
        policy = build_masking_policy(
            policy_name=f"auto_pii_{dataset}",
            database="datagov", # Default DB
            table=dataset,
            columns=columns,
            users=["public", "analyst"], # Apply to these users
            mask_type="MASK"
        )
        create_ranger_policy(policy)

def sync_spi_policies(atlas_client):
    """
    Sync SPI tags -> Access Policies (Deny)
    """
    logger.info("Starting SPI Policy Sync...")
    entities = get_tagged_entities(atlas_client, "SPI")
    
    for entity in entities:
        qname = entity["attributes"]["qualifiedName"]
        # Logic similar to PII...
        pass # Placeholder for brevity

if __name__ == "__main__":
    try:
        atlas = AtlasClient()
        sync_pii_policies(atlas)
        # sync_spi_policies(atlas)
        logger.info("Sync Complete.")
    except Exception as e:
        logger.error(f"Sync failed: {e}")
