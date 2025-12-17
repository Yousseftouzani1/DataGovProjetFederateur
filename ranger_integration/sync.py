# ranger_integration/sync.py

from ranger_integration.client import RangerClient
from ranger_integration.tag_mapping import TAG_TO_POLICY
from ranger_integration.policies import (
    build_masking_policy,
    build_access_policy
)

def sync_policies_from_atlas_tags(
    dataset: str,
    table: str,
    columns_with_tags: dict
):
    """
    columns_with_tags = {
      "cin": ["PII"],
      "iban": ["SPI", "CRITICAL"]
    }
    """

    ranger = RangerClient()

    for column, tags in columns_with_tags.items():
        for tag in tags:

            rule = TAG_TO_POLICY.get(tag)
            if not rule:
                continue

            if "masking" in rule:
                policy = build_masking_policy(
                    policy_name=f"{column}-{tag}-mask",
                    database=dataset,
                    table=table,
                    columns=[column],
                    users=["data_labeler"],
                    mask_type=rule["masking"]
                )
                ranger.post("/policies", policy)

            if rule.get("access") == "DENY":
                policy = build_access_policy(
                    policy_name=f"{column}-{tag}-deny",
                    database=dataset,
                    table=table,
                    users=["annotator", "data_labeler"],
                    allow=False
                )
                ranger.post("/policies", policy)
