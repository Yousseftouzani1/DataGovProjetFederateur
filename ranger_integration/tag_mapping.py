# ranger_integration/tag_mapping.py

TAG_TO_POLICY = {
    "PII": {
        "masking": "MASK"
    },
    "SPI": {
        "masking": "HASH"
    },
    "CRITICAL": {
        "access": "DENY"
    }
}
