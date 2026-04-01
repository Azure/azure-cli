import requests
from base64 import b64encode

# Check if webagents has AAZ command models
res_ids = [
    "/subscriptions/{}/providers/microsoft.cdn/webagents",
    "/subscriptions/{}/resourcegroups/{}/providers/microsoft.cdn/webagents",
    "/subscriptions/{}/resourcegroups/{}/providers/microsoft.cdn/webagents/{}",
]
for rid in res_ids:
    encoded = b64encode(rid.encode()).decode()
    r = requests.get(f"http://127.0.0.1:5000/AAZ/Specs/Resources/mgmt-plane/{encoded}")
    print(f"{rid}")
    print(f"  aaz: {r.status_code == 200}")
    if r.status_code == 200:
        print(f"  versions: {r.json().get('versions', [])}")

# Check swagger versions
r = requests.get("http://127.0.0.1:5000/Swagger/Specs/mgmt-plane/cdn/ResourceProviders/Microsoft.Cdn")
rp = r.json()
for res in rp["resources"]:
    if "webagent" in res["id"] or "agent" in res["id"]:
        versions = [v["version"] for v in res["versions"]]
        print(f"\n{res['id']}")
        print(f"  swagger versions: {versions}")
