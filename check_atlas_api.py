import requests

def check_atlas():
    url = "http://192.168.110.132:21000/api/atlas/v2/search/basic?query=ENSIAS"
    auth = ("admin", "ensias2025")
    try:
        r = requests.get(url, auth=auth)
        data = r.json()
        entities = data.get("entities", [])
        print(f"Entities found: {len(entities)}")
        for e in entities:
            print(f" - Name: {e.get('attributes', {}).get('name')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_atlas()
