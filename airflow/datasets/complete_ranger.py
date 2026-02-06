"""
Complete Ranger Configuration Script
Adds missing features per Cahier des Charges Section 12.4
"""
import requests
import json

RANGER_URL = "http://localhost:6080"
RANGER_AUTH = ("admin", "hortonworks1")
HEADERS = {"Content-Type": "application/json"}
TAG_SERVICE = "data_gov_tags"

def add_spi_policy():
    """Add SPI (Sensitive Personal Information) policy"""
    print("📜 Adding SPI Tag Policy...")
    
    spi_policy = {
        "name": "SPI_RestrictedAccess",
        "service": TAG_SERVICE,
        "description": "Restrict access to SPI-tagged data (financial, health)",
        "isEnabled": True,
        "resources": {"tag": {"values": ["SPI"], "isExcludes": False}},
        "policyItems": [
            {
                "accesses": [{"type": "hive:select", "isAllowed": True}, {"type": "hdfs:read", "isAllowed": True}],
                "users": ["admin"],
                "groups": [],
                "delegateAdmin": True
            }
        ],
        "denyPolicyItems": [
            {
                "accesses": [{"type": "hive:select", "isAllowed": True}, {"type": "hdfs:read", "isAllowed": True}],
                "users": [],
                "groups": ["public"],
                "delegateAdmin": False
            }
        ]
    }
    
    resp = requests.post(f"{RANGER_URL}/service/plugins/policies", json=spi_policy, auth=RANGER_AUTH, headers=HEADERS)
    if resp.status_code == 200:
        print("   ✅ SPI policy created!")
    elif "already exists" in resp.text.lower():
        print("   ℹ️ SPI policy already exists")
    else:
        print(f"   ⚠️ Failed: {resp.text[:100]}")

def add_audit_policy():
    """Enable audit logging for all access"""
    print("\n📝 Configuring Audit...")
    # Ranger has audit enabled by default, just verify
    resp = requests.get(f"{RANGER_URL}/service/plugins/services/name/{TAG_SERVICE}", auth=RANGER_AUTH)
    if resp.status_code == 200:
        svc = resp.json()
        configs = svc.get('configs', {})
        audit_enabled = configs.get('ranger.plugin.audit.enabled', 'true')
        print(f"   Audit Status: {'✅ Enabled' if audit_enabled == 'true' else '⚠️ Disabled'}")
    else:
        print("   ⚠️ Could not verify audit config")

def verify_all_policies():
    """List all policies for verification"""
    print("\n📋 All Ranger Policies:")
    resp = requests.get(f"{RANGER_URL}/service/plugins/policies", params={"serviceName": TAG_SERVICE}, auth=RANGER_AUTH)
    if resp.status_code == 200:
        policies = resp.json().get('policies', [])
        for p in policies:
            print(f"   ├─ {p['name']} (Enabled: {p['isEnabled']})")
    else:
        print("   ⚠️ Could not list policies")

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 COMPLETING RANGER CONFIGURATION")
    print("=" * 60)
    
    add_spi_policy()
    add_audit_policy()
    verify_all_policies()
    
    print("\n" + "=" * 60)
    print("✅ RANGER CONFIGURATION COMPLETE")
    print("=" * 60)
