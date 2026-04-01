"""
Auto-select swagger resources for aaz-dev workspace.
Creates a workspace named by API version with all CDN/AFD resources auto-selected.
Resources with existing AAZ command models (inheritance) are auto-selected.

Usage:
    python auto_select_resources.py --version VERSION [--dry-run]

Examples:
    # Create workspace cdn-2025-09-01-preview with all resources
    python auto_select_resources.py --version 2025-09-01-preview

    # Dry run to see what would be selected
    python auto_select_resources.py --version 2025-09-01-preview --dry-run
"""

import argparse
import sys
from base64 import b64encode

import requests

BASE_URL = "http://127.0.0.1:5000"
PLANE = "mgmt-plane"
MOD_NAMES = "cdn"
RP_NAME = "Microsoft.Cdn"

# Resources to exclude (separated to their own swagger modules)
EXCLUDE_PATTERNS = [
    "edgeaction",
]




def b64(s):
    return b64encode(s.encode()).decode()


def get_existing_workspaces():
    """Get set of existing workspace names."""
    r = requests.get(f"{BASE_URL}/AAZ/Editor/Workspaces")
    r.raise_for_status()
    return {ws["name"] for ws in r.json()}


def get_rp_resources():
    """Get all resources from CDN swagger spec."""
    r = requests.get(f"{BASE_URL}/Swagger/Specs/{PLANE}/{MOD_NAMES}/ResourceProviders/{RP_NAME}")
    r.raise_for_status()
    return r.json()["resources"]


def get_aaz_resource(resource_id):
    """Check if a resource has existing command models in AAZ."""
    encoded = b64(resource_id)
    r = requests.get(f"{BASE_URL}/AAZ/Specs/Resources/{PLANE}/{encoded}")
    if r.status_code == 200:
        return r.json()
    return None


def create_workspace(name):
    """Create a new workspace."""
    payload = {
        "name": name,
        "plane": PLANE,
        "modNames": MOD_NAMES,
        "resourceProvider": RP_NAME,
        "source": "OpenAPI",
    }
    r = requests.post(f"{BASE_URL}/AAZ/Editor/Workspaces", json=payload)
    r.raise_for_status()
    return r.json()


def add_resources_to_workspace(ws_name, version, resources):
    """Add swagger resources to workspace via AddSwagger endpoint.

    Groups resources by version and sends one request per version.
    Each resource can optionally have an aaz_version for inheritance.
    """
    # Group resources by their chosen version
    by_version = {}
    for r in resources:
        v = r["version"]
        by_version.setdefault(v, []).append(r)

    for ver, res_list in by_version.items():
        payload_resources = []
        for r in res_list:
            entry = {"id": r["id"]}
            # If there's an existing aaz version, set it for inheritance
            if r.get("aaz_version"):
                entry["options"] = {"aaz_version": r["aaz_version"]}
            payload_resources.append(entry)

        payload = {
            "module": MOD_NAMES,
            "version": ver,
            "resources": payload_resources,
        }
        r = requests.post(
            f"{BASE_URL}/AAZ/Editor/Workspaces/{ws_name}/CommandTree/Nodes/aaz/AddSwagger",
            json=payload,
        )
        r.raise_for_status()

    return True


def select_resources(target_version=None):
    """
    Analyze all CDN resources, classify as cdn/afd, and select the best version.

    Strategy:
    1. Only select resources that have existing AAZ command models (inheritance)
    2. If target_version specified and resource has it -> use target_version
    3. Otherwise use the latest inherited version
    4. New resources without AAZ history are skipped (add manually in Web UI)
    """
    all_resources = get_rp_resources()
    selected = []
    skipped = []

    for res in all_resources:
        res_id = res["id"]
        available_versions = [v["version"] for v in res["versions"]]

        # Skip excluded resources
        if any(pat in res_id.lower() for pat in EXCLUDE_PATTERNS):
            skipped.append({
                "id": res_id,
                "versions": available_versions[-3:] if available_versions else [],
                "has_aaz": False,
                "reason": "excluded",
            })
            continue

        # Check AAZ for existing command models
        aaz_data = get_aaz_resource(res_id)
        aaz_versions = aaz_data.get("versions", []) if aaz_data else []

        chosen_version = None
        inherit_from = None
        reason = ""

        if aaz_versions:
            aaz_latest = aaz_versions[-1]

            if target_version and target_version in available_versions:
                chosen_version = target_version
                inherit_from = aaz_latest
                reason = f"target version (aaz has: {aaz_latest or 'none'})"
            else:
                for v in reversed(available_versions):
                    if v in aaz_versions:
                        chosen_version = v
                        inherit_from = v
                        reason = "inherited from aaz"
                        break
                if not chosen_version and aaz_versions:
                    chosen_version = aaz_latest
                    inherit_from = aaz_latest
                    reason = "aaz latest"


        if chosen_version:
            entry = {
                "id": res_id,
                "version": chosen_version,
                "reason": reason,
            }
            if inherit_from:
                entry["aaz_version"] = inherit_from
            selected.append(entry)
        else:
            skipped.append({
                "id": res_id,
                "versions": available_versions[-3:] if available_versions else [],
                "has_aaz": bool(aaz_versions),
            })

    return selected, skipped


def main():
    parser = argparse.ArgumentParser(description="Auto-select CDN swagger resources for aaz-dev workspace")
    parser.add_argument("--version", "-v", required=True, help="Target API version (e.g. 2025-09-01-preview)")
    parser.add_argument("--dry-run", action="store_true", help="Only show what would be selected")
    args = parser.parse_args()

    ws_name = f"cdn-{args.version}"

    print(f"Analyzing CDN resources for version {args.version}...")
    print(f"  Workspace: {ws_name}")

    selected, skipped = select_resources(target_version=args.version)

    print(f"\n=== SELECTED: {len(selected)} resources ===")
    for r in selected:
        print(f"  [+] {r['id']}")
        print(f"      version: {r['version']}  ({r['reason']})")

    print(f"\n=== SKIPPED: {len(skipped)} resources ===")
    for r in skipped:
        print(f"  [-] {r['id']}")
        print(f"      versions: {r['versions']}  aaz: {r['has_aaz']}")

    if args.dry_run:
        print("\n(dry run - no changes made)")
        return

    if not selected:
        print("\nNo resources to add.")
        return

    existing = get_existing_workspaces()
    if ws_name in existing:
        print(f"\nWorkspace '{ws_name}' already exists, skipping.")
        return

    print(f"\nCreating workspace '{ws_name}'...")
    ws = create_workspace(ws_name)
    print(f"  Created: {ws['url']}")

    print(f"  Adding {len(selected)} resources...")
    try:
        add_resources_to_workspace(ws_name, args.version, selected)
        print(f"  Done!")
    except requests.exceptions.HTTPError as e:
        print(f"  Error: {e.response.status_code} - {e.response.text[:500]}")

    print(f"\nOpen http://127.0.0.1:5000 to view and edit the workspace.")


if __name__ == "__main__":
    main()
