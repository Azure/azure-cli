import requests
from base64 import b64encode

targets = [
    "/subscriptions/{}/providers/microsoft.cdn/cdnwebapplicationfirewallmanagedrulesets",
    "/subscriptions/{}/resourcegroups/{}/providers/microsoft.cdn/cdnwebapplicationfirewallpolicies",
    "/subscriptions/{}/resourcegroups/{}/providers/microsoft.cdn/cdnwebapplicationfirewallpolicies/{}",
]

for rid in targets:
    encoded = b64encode(rid.encode()).decode()
    r = requests.get(f"http://127.0.0.1:5000/AAZ/Specs/Resources/mgmt-plane/{encoded}")
    print(f"{rid}")
    if r.status_code == 200:
        data = r.json()
        print(f"  aaz versions: {data.get('versions', [])}")
    else:
        print(f"  aaz: NOT FOUND")

    # Check swagger versions
    r2 = requests.get("http://127.0.0.1:5000/Swagger/Specs/mgmt-plane/cdn/ResourceProviders/Microsoft.Cdn")
    rp = r2.json()
    for res in rp["resources"]:
        if res["id"] == rid:
            versions = [v["version"] for v in res["versions"]]
            print(f"  swagger versions: {versions}")
            break
    print()
