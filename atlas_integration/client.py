# atlas_integration/client.py

import logging
import requests
from typing import Dict, Any, Optional
from atlas_integration.config import ATLAS_CONFIG

logger = logging.getLogger(__name__)

class AtlasClient:
    def __init__(self):
        base = ATLAS_CONFIG["BASE_URL"]
        prefix = ATLAS_CONFIG["API_PREFIX"]
        # Ensure single cleanup
        if base.endswith(prefix):
             self.base_url = base
        else:
             self.base_url = f"{base.rstrip('/')}{prefix}"
        
        self.auth = (ATLAS_CONFIG["USERNAME"], ATLAS_CONFIG["PASSWORD"])
        self.timeout = ATLAS_CONFIG["TIMEOUT"]
        self.headers = {"Content-Type": "application/json"}
        
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Unified response handler with error logging"""
        try:
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.HTTPError as e:
            logger.error(f"Atlas API Error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Atlas Connection Error: {str(e)}")
            raise

    def post(self, endpoint: str, payload: dict) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}{endpoint}",
            json=payload,
            headers=self.headers,
            auth=self.auth,
            timeout=self.timeout
        )
        return self._handle_response(response)

    def get(self, endpoint: str) -> Dict[str, Any]:
        response = requests.get(
            f"{self.base_url}{endpoint}",
            auth=self.auth,
            timeout=self.timeout
        )
        return self._handle_response(response)

    # =========================================================
    #  ENHANCED METHODS FOR PROJECT REQUIREMENTS
    # =========================================================

    def create_entity(self, entity_def: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create or update an entity in Atlas.
        Usage: 
          entity_def = {"entity": {"typeName": "hdfs_path", "attributes": {...}}}
        """
        return self.post("/entity", entity_def)
    
    def create_classification(self, entity_guid: str, classification_name: str, attributes: Dict[str, Any] = None) -> None:
        """
        Add a classification (e.g., PII_DATA) to an entity GUID.
        """
        payload = [{"typeName": classification_name, "attributes": attributes or {}}]
        self.post(f"/entity/guid/{entity_guid}/classifications", payload)
        
    def get_entity_by_guid(self, guid: str) -> Dict[str, Any]:
        return self.get(f"/entity/guid/{guid}")
        
    def search_entity(self, query: str, type_name: str = None) -> Dict[str, Any]:
        """
        Basic search for entities.
        """
        params = f"?query={query}"
        if type_name:
             params += f"&typeName={type_name}"
        return self.get(f"/search/basic{params}")

    def create_lineage(self, source_guid: str, target_guid: str, process_name: str, process_type: str = "Process") -> Dict[str, Any]:
        """
        Create a lineage process entity linking source to target.
        """
        process_entity = {
            "entity": {
                "typeName": process_type,
                "attributes": {
                    "qualifiedName": f"{process_name}@{ATLAS_CONFIG.get('CLUSTER_NAME', 'primary')}",
                    "name": process_name,
                    "inputs": [{"guid": source_guid, "typeName": "DataSet"}],
                    "outputs": [{"guid": target_guid, "typeName": "DataSet"}]
                }
            }
        }
        return self.create_entity(process_entity)
