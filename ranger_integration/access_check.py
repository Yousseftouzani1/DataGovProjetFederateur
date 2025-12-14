# ranger_integration/access_check.py

def check_access_decision(user_role: str, tags: list) -> dict:
    """
    Simule la décision Ranger (en pratique Ranger Plugin)
    """

    if "CRITICAL" in tags and user_role != "admin":
        return {"allow": False}

    if "SPI" in tags and user_role not in ["admin", "data_steward"]:
        return {"allow": True, "mask": "HASH"}

    if "PII" in tags:
        return {"allow": True, "mask": "MASK"}

    return {"allow": True, "mask": None}
