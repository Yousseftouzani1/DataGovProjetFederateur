import os
import requests
import json
from typing import Dict, List, Optional
from datetime import datetime

class AtlasClient:
    """
    Client for Apache Atlas (Data Governance)
    Handles metadata registration and lineage tracking.
    """
    
    def __init__(self, atlas_url: str = None):
        self.base_url = atlas_url or os.getenv("ATLAS_URL", "http://atlas:21000/api/atlas/v2")
        self.auth = (os.getenv("ATLAS_USER", "admin"), os.getenv("ATLAS_PASSWORD", "admin"))
        self.mock_mode = os.getenv("MOCK_GOVERNANCE", "true").lower() == "true"
        
        if not self.mock_mode:
            print(f"🔌 Apache Atlas Client initialized at {self.base_url}")
        else:
            print(f"⚠️ Apache Atlas Client running in MOCK mode")
            
    def _post(self, endpoint: str, data: Dict) -> Optional[Dict]:
        if self.mock_mode:
            # print(f"[MOCK ATLAS] POST {endpoint}: {json.dumps(data)[:100]}...")
            return {"guid": "mock-guid-" + datetime.now().isoformat()}
            
        try:
            resp = requests.post(f"{self.base_url}{endpoint}", json=data, auth=self.auth)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"❌ Atlas API Error: {e}")
            return None

    def register_dataset(self, name: str, description: str, owner: str, file_path: str, quality_score: float = None):
        """Register a dataset entity in Atlas"""
        entity = {
            "entity": {
                "typeName": "DataSet",
                "attributes": {
                    "qualifiedName": f"dataset@{name}",
                    "name": name,
                    "description": description,
                    "owner": owner,
                    "path": file_path,
                    "qualityScore": quality_score
                }
            }
        }
        resp = self._post("/entity", entity)
        if resp:
            print(f"✅ Registered dataset '{name}' in Atlas (GUID: {resp.get('guid')})")
        return resp

    def add_lineage(self, source_name: str, target_name: str, process_name: str):
        """Add lineage between datasets via a process"""
        # Simplified lineage creation
        # Real Atlas requires existing GUIDs and creating a Process entity linking inputs/outputs
        entity = {
            "entity": {
                "typeName": "Process",
                "attributes": {
                    "qualifiedName": f"process@{process_name}",
                    "name": process_name,
                    "inputs": [{"typeName": "DataSet", "uniqueAttributes": {"qualifiedName": f"dataset@{source_name}"}}],
                    "outputs": [{"typeName": "DataSet", "uniqueAttributes": {"qualifiedName": f"dataset@{target_name}"}}]
                }
            }
        }
        resp = self._post("/entity", entity)
        if resp:
            print(f"✅ Created lineage: {source_name} -> [{process_name}] -> {target_name}")
        return resp

    def add_classification(self, entity_guid: str, classification: str):
        """Add classification tag (e.g., PII, SENSITIVE)"""
        if self.mock_mode:
            print(f"🏷️ [MOCK] Added classification '{classification}' to {entity_guid}")
            return True
            
        try:
            url = f"{self.base_url}/entity/guid/{entity_guid}/classifications"
            requests.post(url, json=[{"typeName": classification}], auth=self.auth)
            return True
        except Exception as e:
            print(f"❌ Failed to add classification: {e}")
            return False
