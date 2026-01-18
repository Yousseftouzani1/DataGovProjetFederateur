import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class AtlasClient:
    def __init__(self):
        self.atlas_url = os.getenv("ATLAS_URL", "http://100.91.176.196:21000")
        self.user = os.getenv("ATLAS_USER", "admin")
        self.password = os.getenv("ATLAS_PASSWORD", "ensias2025")
        self.mock_mode = os.getenv("MOCK_GOVERNANCE", "false").lower() == "true"
        self.base_api = f"{self.atlas_url}/api/atlas/v2"

    def is_healthy(self):
        if self.mock_mode:
            return True
        try:
            resp = requests.get(f"{self.base_api}/types/typedefs", auth=(self.user, self.password), timeout=5)
            return resp.status_code == 200
        except:
            return False

    def get_entity(self, guid):
        if self.mock_mode: return {"mock": True}
        resp = requests.get(f"{self.base_api}/entity/guid/{guid}", auth=(self.user, self.password))
        return resp.json() if resp.status_code == 200 else None

    def create_entity(self, entity_data):
        if self.mock_mode: return {"guid": "mock-guid"}
        resp = requests.post(
            f"{self.base_api}/entity",
            json=entity_data,
            auth=(self.user, self.password)
        )
        return resp.json()

    def register_dataset_and_get_guid(self, name, description, owner, file_path):
        if self.mock_mode: return "mock-guid-123"
        
        entity = {
            "entity": {
                "typeName": "DataSet",
                "attributes": {
                    "qualifiedName": f"dataset@{name}",
                    "name": name,
                    "description": description,
                    "owner": owner
                }
            }
        }
        res = self.create_entity(entity)
        try:
            # Atlas returns varied structures, trying to extract GUID safely
            if 'mutatedEntities' in res and 'CREATE' in res['mutatedEntities']:
                return res['mutatedEntities']['CREATE'][0]['guid']
            if 'guidAssignments' in res:
                return list(res['guidAssignments'].values())[0]
            return None
        except:
            return None
            
    def create_type_definitions(self, type_defs):
        """Create or Update Type Definitions in Atlas"""
        if self.mock_mode: return {"status": "mock_success"}
        
        # Check if exists first to decide update vs create logic if needed, 
        # but Atlas PUT often handles updates.
        resp = requests.put(
            f"{self.base_api}/types/typedefs",
            json=type_defs,
            auth=(self.user, self.password)
        )
        return resp.json()
