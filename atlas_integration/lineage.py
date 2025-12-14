# atlas_integration/lineage.py

def create_process(name: str, input_guid: str, output_guid: str):
    return {
        "entity": {
            "typeName": "process",
            "attributes": {
                "name": name,
                "inputs": [{"guid": input_guid}],
                "outputs": [{"guid": output_guid}]
            }
        }
    }
