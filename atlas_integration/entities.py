# atlas_integration/entities.py

from atlas_integration.config import ATLAS_METADATA

def create_data_source(name: str):
    return {
        "entity": {
            "typeName": "data_source",
            "attributes": {
                "qualifiedName": f"mongo::{name}",
                "name": name,
                "owner": ATLAS_METADATA["OWNER"]
            }
        }
    }

def create_dataset(name: str, domain: str):
    return {
        "entity": {
            "typeName": "dataset",
            "attributes": {
                "qualifiedName": f"dataset::{name}",
                "name": name,
                "domain": domain,
                "owner": ATLAS_METADATA["OWNER"]
            }
        }
    }

def create_data_attribute(dataset: str, attribute: str):
    return {
        "entity": {
            "typeName": "data_attribute",
            "attributes": {
                "qualifiedName": f"{dataset}::{attribute}",
                "name": attribute,
                "dataType": "string"
            }
        }
    }
