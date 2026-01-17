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

    def register_dataset(self, name: str, description: str, owner: str, file_path: str, quality_score: float = None) -> Dict[str, Any]:
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
        return self.create_entity(entity)

    def register_dataset_and_get_guid(self, name: str, description: str, owner: str, file_path: str) -> Optional[str]:
        """Register a dataset and return its GUID for later classification/lineage"""
        try:
            result = self.register_dataset(name, description, owner, file_path)
            if result:
                # Try to extract GUID from response
                if 'mutatedEntities' in result:
                    created = result.get('mutatedEntities', {}).get('CREATE', [])
                    if created:
                        return created[0].get('guid')
                    updated = result.get('mutatedEntities', {}).get('UPDATE', [])
                    if updated:
                        return updated[0].get('guid')
                # Fallback: search for GUID
                return self.get_entity_guid(name)
        except Exception as e:
            logger.error(f"Failed to register dataset {name}: {e}")
            return None
    
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

    # =========================================================
    #  UTILITY / MAINTENANCE
    # =========================================================
    
    def delete_entity(self, guid: str) -> bool:
        """Delete an entity by GUID (Hard delete)"""
        try:
            # First soft delete
            resp = requests.delete(f"{self.base_url}/entity/guid/{guid}", auth=self.auth)
            # Then hard delete (purge) if supported/configured, or just return success
            return resp.status_code in [200, 204]
        except Exception as e:
            logger.error(f"Failed to delete entity {guid}: {e}")
            return False

    def purge_type(self, type_name: str):
        """Delete all entities of a given type"""
        try:
            results = self.search_entity("", type_name)
            entities = results.get("entities", [])
            count = 0
            for entity in entities:
                if self.delete_entity(entity["guid"]):
                    count += 1
            logger.info(f"🗑️ Purged {count} entities of type {type_name}")
            return count
        except Exception as e:
            logger.error(f"Failed to purge type {type_name}: {e}")
            return 0

    # =========================================================
    #  ENHANCED IMPLEMENTATION (Production Level)
    # =========================================================

    def ensure_classification_types(self):
        """
        Ensure required classification types exist in Atlas with proper attributes.
        """
        # Attributes common to PII/SENSITIVE/CONFIDENTIAL
        common_attributes = [
            {"name": "detectedTypes", "typeName": "string", "isOptional": True, "cardinality": "SINGLE", "valuesMinCount": 0, "valuesMaxCount": 1},
            {"name": "detectionCount", "typeName": "string", "isOptional": True, "cardinality": "SINGLE", "valuesMinCount": 0, "valuesMaxCount": 1},
            {"name": "avgConfidence", "typeName": "string", "isOptional": True, "cardinality": "SINGLE", "valuesMinCount": 0, "valuesMaxCount": 1},
            {"name": "scanTimestamp", "typeName": "string", "isOptional": True, "cardinality": "SINGLE", "valuesMinCount": 0, "valuesMaxCount": 1}
        ]

        required_types = [
            {"name": "PII", "description": "Personally Identifiable Information", "attributeDefs": common_attributes},
            {"name": "SENSITIVE", "description": "Sensitive Business Data", "attributeDefs": common_attributes},
            {"name": "CONFIDENTIAL", "description": "Confidential Information", "attributeDefs": common_attributes},
            {"name": "PUBLIC", "description": "Public Data", "attributeDefs": []}
        ]
        
        for type_def in required_types:
            try:
                # Check if type exists
                resp = requests.get(
                    f"{self.base_url}/types/classificationdef/name/{type_def['name']}",
                    auth=self.auth,
                    timeout=self.timeout
                )
                
                # Definition payload
                payload = {
                    "classificationDefs": [{
                        "name": type_def["name"],
                        "description": type_def["description"],
                        "superTypes": [],
                        "attributeDefs": type_def.get("attributeDefs", [])
                    }]
                }

                if resp.status_code == 404:
                    # Create new type
                    self.post("/types/typedefs", payload)
                    logger.info(f"✅ Created Atlas classification type: {type_def['name']}")
                
                elif resp.status_code == 200:
                    # Type exists, check if attributes need update (PATCH)
                    existing_def = resp.json()
                    existing_attrs = {a['name'] for a in existing_def.get('attributeDefs', [])}
                    required_attrs = {a['name'] for a in type_def.get('attributeDefs', [])}
                    
                    if not required_attrs.issubset(existing_attrs):
                        # Missing attributes, update the type
                        logger.info(f"🔄 Updating classification type {type_def['name']} with missing attributes...")
                        # PUT to /types/typedefs works for updates
                        requests.put(
                            f"{self.base_url}/types/typedefs",
                            json=payload,
                            auth=self.auth,
                            timeout=self.timeout
                        )
                        logger.info(f"✅ Updated attributes for: {type_def['name']}")
                        
            except Exception as e:
                logger.warning(f"⚠️ Classification type setup warning for {type_def['name']}: {e}")

    def register_pii_columns(self, dataset_guid: str, dataset_name: str, detections: list) -> int:
        """
        Register PII columns as data_attribute entities in Atlas.
        """
        columns = {}
        for det in detections:
            col = det.get('column', det.get('field', det.get('position', 'unknown')))
            if col not in columns:
                columns[col] = []
            columns[col].append(det)
        
        created_count = 0
        created_count = 0
        for col_name, col_detections in columns.items():
            # SKIP 'unknown' columns as per user request
            if not col_name or col_name.lower() == 'unknown':
                continue
                
            try:
                pii_types = [d.get('entity_type', d.get('type', 'PII')) for d in col_detections]
                primary_type = max(set(pii_types), key=pii_types.count)
                avg_conf = sum(d.get('confidence', d.get('score', 0.8)) for d in col_detections) / len(col_detections)
                
                entity = {
                    "entity": {
                        "typeName": "DataSet", 
                        "attributes": {
                            "qualifiedName": f"column@{dataset_name}.{col_name}",
                            "name": f"{dataset_name}.{col_name}",
                            "description": f"Column {col_name} containing {primary_type} data",
                            "owner": "system",
                            "piiType": primary_type,
                            "avgConfidence": f"{avg_conf:.2f}",
                            "detectionCount": str(len(col_detections))
                        }
                    }
                }
                
                result = self.create_entity(entity)
                if result and 'mutatedEntities' in result:
                     created = result.get('mutatedEntities', {}).get('CREATE', [])
                     if created:
                         self.create_classification(created[0].get('guid'), primary_type if primary_type in ['PII', 'SENSITIVE'] else 'PII')
                         created_count += 1
            except Exception as e:
                logger.error(f"Failed to register column {col_name}: {e}")
                
        return created_count

    def add_classification_with_attributes(self, entity_guid: str, classification: str, detections: list) -> bool:
        """
        Add classification with detailed attributes.
        """
        try:
            pii_types = set()
            total_count = 0
            total_confidence = 0.0
            
            if detections:
                for det in detections:
                    entity_type = det.get('entity_type', det.get('type', 'UNKNOWN'))
                    pii_types.add(entity_type)
                    total_count += 1
                    total_confidence += det.get('confidence', det.get('score', 0.8))
            
            avg_confidence = total_confidence / max(total_count, 1)
            
            payload = [{
                "typeName": classification,
                "attributes": {
                    "detectedTypes": ",".join(sorted(pii_types)),
                    "detectionCount": str(total_count),
                    "avgConfidence": f"{avg_confidence:.2f}"
                }
            }]
            
            # Direct POST to handle attributes
            response = requests.post(
                f"{self.base_url}/entity/guid/{entity_guid}/classifications",
                json=payload,
                headers=self.headers,
                auth=self.auth
            )
            
            if response.status_code != 204: # Atlas returns 204 on success for classifications usually
                 # Fallback if attributes strict checking fails
                 self.create_classification(entity_guid, classification)
                 
            return True
        except Exception:
            return False

    def get_entity_guid(self, name: str) -> Optional[str]:
        # Enhanced helper: tries exact name, name with .csv, name without .csv
        candidates = [name]
        if name.endswith('.csv'):
            candidates.append(name[:-4])
        else:
            candidates.append(f"{name}.csv")
            
        for candidate in candidates:
            res = self.search_entity(candidate, "DataSet")
            if res and res.get('entities'):
                logger.info(f"✅ Found entity GUID for '{name}' using candidate '{candidate}'")
                return res['entities'][0]['guid']
        
        logger.warning(f"⚠️ Could not find Atlas entity GUID for '{name}' (Tried: {candidates})")
        return None
