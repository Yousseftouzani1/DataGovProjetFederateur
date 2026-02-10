import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class AtlasClient:
    def __init__(self):
        self.atlas_url = os.getenv("ATLAS_URL")
        if not self.atlas_url:
            raise RuntimeError("ATLAS_URL environment variable is required. Set it in .env file.")
        self.user = os.getenv("ATLAS_USER", "admin")
        self.password = os.getenv("ATLAS_PASSWORD")
        if not self.password:
            raise RuntimeError("ATLAS_PASSWORD environment variable is required. Set it in .env file.")
        self.base_api = f"{self.atlas_url}/api/atlas/v2"

    def is_healthy(self):
        try:
            resp = requests.get(f"{self.base_api}/types/typedefs", auth=(self.user, self.password), timeout=2)
            return resp.status_code == 200
        except:
            return False

    async def get_entity(self, guid):
        try:
            resp = requests.get(f"{self.base_api}/entity/guid/{guid}", auth=(self.user, self.password), timeout=5)
            return resp.json() if resp.status_code == 200 else None
        except Exception as e:
            print(f"Atlas get_entity failed: {e}")
            return None

    def get_entity_guid(self, name: str):
        try:
            resp = requests.get(
                f"{self.base_api}/search/basic?query={name}&typeName=DataSet",
                auth=(self.user, self.password),
                timeout=5
            )
            if resp.status_code == 200:
                results = resp.json().get("entities", [])
                if results:
                    return results[0].get("guid")
            return None
        except Exception as e:
            print(f"Atlas get_entity_guid failed: {e}")
            return None

    def get_classifications(self, guid):
        """Fetch live classifications for an entity from Atlas"""
        try:
            resp = requests.get(
                f"{self.base_api}/entity/guid/{guid}/classifications",
                auth=(self.user, self.password),
                timeout=2
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    return [c['typeName'] for c in data]
                elif isinstance(data, dict) and 'list' in data:
                    return [c['typeName'] for c in data['list']]
            return []
        except Exception as e:
            print(f"Error fetching Atlas classifications: {e}")
            return []


    def create_entity(self, entity_data):
        resp = requests.post(
            f"{self.base_api}/entity",
            json=entity_data,
            auth=(self.user, self.password),
            timeout=10
        )
        return resp.json()

    def register_dataset_and_get_guid(self, name, description, owner, file_path):
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
        if not res:
            return None

        try:
            mutated = res.get('mutatedEntities', {})
            if 'CREATE' in mutated and mutated['CREATE']:
                return mutated['CREATE'][0].get('guid')

            guid_assignments = res.get('guidAssignments', {})
            if guid_assignments:
                return list(guid_assignments.values())[0]

            return None
        except Exception as e:
            print(f"Error extracting GUID from Atlas response: {e}")
            return None

    def create_type_definitions(self, type_defs):
        """Create or Update Type Definitions in Atlas"""
        resp = requests.put(
            f"{self.base_api}/types/typedefs",
            json=type_defs,
            auth=(self.user, self.password),
            timeout=10
        )
        return resp.json()

    def create_glossary(self, name, description):
        """Create a new Business Glossary"""
        glossaries = self._get("/glossary")
        if glossaries:
            for g in glossaries:
                if g.get("name") == name:
                    return g

        payload = {
            "name": name,
            "shortDescription": description,
            "longDescription": description,
            "language": "en"
        }
        return self._post("/glossary", payload)

    def create_glossary_term(self, glossary_guid, term_name, description):
        """Create a Term within a Glossary"""
        payload = {
            "anchor": {"glossaryGuid": glossary_guid},
            "name": term_name,
            "shortDescription": description
        }
        return self._post("/glossary/term", payload)

    def _post(self, endpoint, data):
        """Helper for POST requests"""
        try:
            resp = requests.post(
                f"{self.base_api}{endpoint}",
                json=data,
                auth=(self.user, self.password),
                timeout=10
            )
            return resp.json() if resp.status_code in [200, 201, 204, 409] else None
        except Exception as e:
            print(f"Atlas POST {endpoint} failed: {e}")
            return None

    def _put(self, endpoint, data):
        """Helper for PUT requests"""
        try:
            resp = requests.put(
                f"{self.base_api}{endpoint}",
                json=data,
                auth=(self.user, self.password),
                timeout=10
            )
            return resp.json() if resp.status_code in [200, 201, 204, 409] else None
        except Exception as e:
            print(f"Atlas PUT {endpoint} failed: {e}")
            return None

    def _get(self, endpoint):
        """Helper for GET requests"""
        try:
            resp = requests.get(
                f"{self.base_api}{endpoint}",
                auth=(self.user, self.password),
                timeout=5
            )
            return resp.json() if resp.status_code == 200 else None
        except Exception as e:
            print(f"Atlas GET {endpoint} failed: {e}")
            return None

    def add_classification(self, guid, classification_name):
        """Add a classification (tag) to an entity."""
        payload = [
            {
                "typeName": classification_name,
                "propagate": True,
                "entityGuid": guid
            }
        ]

        try:
            resp = requests.post(
                f"{self.base_api}/entity/guid/{guid}/classifications",
                json=payload,
                auth=(self.user, self.password),
                timeout=5
            )
            return resp.status_code in [200, 204]
        except Exception as e:
            print(f"Failed to add classification: {e}")
            return False

    async def get_lineage(self, guid: str, direction: str = "BOTH", depth: int = 3):
        """Fetch real lineage from Atlas"""
        try:
            resp = requests.get(
                f"{self.base_api}/lineage/{guid}",
                params={"direction": direction, "depth": depth},
                auth=(self.user, self.password),
                timeout=10
            )
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception as e:
            print(f"Failed to fetch lineage from Atlas: {e}")
            return None
