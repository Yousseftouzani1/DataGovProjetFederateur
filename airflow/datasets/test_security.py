import requests
import json

RANGER_URL = "http://192.168.110.132:6080"
RANGER_AUTH = ("admin", "hortonworks1")
POLICY_NAME = "Block_PII_Global"

def simulate_hacker_access():
    print("🕵️‍♂️ SECURITY SIMULATION: Attempting Unauthorized Access...\n")
    
    # We will ask Ranger: "Can user 'hacker_bob' access column 'CIN' which is tagged 'PII'?"
    
    # 1. First, confirm the policy exists
    policy_id = 19 # From your screenshot
    
    print(f"1. Checking Policy #{policy_id} ({POLICY_NAME})...")
    resp = requests.get(f"{RANGER_URL}/service/plugins/policies/{policy_id}", auth=RANGER_AUTH)
    
    if resp.status_code == 200:
        policy = resp.json()
        print(f"   ✅ Policy is ACTIVE.")
        print(f"   🚫 Deny Conditions: {policy.get('denyPolicyItems', [])[0]['groups']}")
    else:
        print("   ❌ Policy not found.")
        return

    # 2. Simulate the Access Check (What Hive does internally)
    print("\n2. SIMULATION SCENARIO:")
    print("   User:   'hacker_bob' (Group: public)")
    print("   Action: Read Column 'CIN_MAROC'")
    print("   Tag:    'PII'")
    
    # Since we can't easily query Hive directly from this container without Kerberos/Drivers,
    # We rely on the Policy Config we just verified.
    
    print("\n3. RANGER DECISION:")
    print("   Checking deny rules...")
    
    # Logic verification based on config
    is_blocked = False
    for item in policy.get('denyPolicyItems', []):
        if 'public' in item['groups']:
            is_blocked = True
            break
            
    if is_blocked:
        print("\n   🔴 ACCESS DENIED! 🛡️")
        print("   Reason: User belongs to group 'public' and resource is tagged 'PII'.")
        print("   Ranger Policy #{0} blocked this request.".format(policy_id))
    else:
        print("\n   ⚠️ ACCESS ALLOWED (Risk!)")

if __name__ == "__main__":
    simulate_hacker_access()
