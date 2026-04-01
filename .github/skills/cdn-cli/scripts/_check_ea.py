import requests

r = requests.get("http://127.0.0.1:5000/Swagger/Specs/mgmt-plane/cdn/ResourceProviders/Microsoft.Cdn")
for res in r.json()["resources"]:
    if "edgeaction" in res["id"]:
        for v in res["versions"]:
            if v["version"] == "2025-09-01-preview":
                print(f"{res['id']}")
                print(f"  file: {v['file']}")
                break
