import requests

RANGER_URL = "http://192.168.110.132:6080"
RANGER_AUTH = ("admin", "hortonworks1")

print("=" * 60)
print("RANGER POLICY VERIFICATION - All Roles")
print("=" * 60)

resp = requests.get(f"{RANGER_URL}/service/plugins/policies", params={"serviceName": "data_gov_tags"}, auth=RANGER_AUTH)
policies = resp.json().get("policies", [])

print(f"\nTotal Policies: {len(policies)}\n")

for p in policies:
    name = p.get("name", "Unknown")
    enabled = p.get("isEnabled", False)
    
    users_allow = []
    users_deny = []
    
    for item in p.get("policyItems", []):
        users_allow.extend(item.get("users", []))
        
    for item in p.get("denyPolicyItems", []):
        users_deny.extend(item.get("users", []))
        for g in item.get("groups", []):
            users_deny.append(f"@{g}")
    
    print(f"Policy: {name}")
    print(f"  Enabled: {enabled}")
    print(f"  Allow: {users_allow if users_allow else 'None'}")
    print(f"  Deny: {users_deny if users_deny else 'None'}")
    print()

print("=" * 60)
print("SIMULATION: Who Can Access PII?")
print("=" * 60)

# Simple logic simulation
roles = {
    "admin": "ALLOWED (explicit allow)",
    "steward1": "ALLOWED (explicit allow)", 
    "annotator1": "ALLOWED + MASKED",
    "labeler1": "DENIED (explicit deny)",
    "hacker_bob": "DENIED (public group deny)"
}

for user, expected in roles.items():
    print(f"  {user}: {expected}")
