#!/usr/bin/env bash
# Reproduces the credential encryption warning that Linux users see when the system keyring is
# unreachable, which is the case on headless machines, in containers and in Cloud Shell.
#
# D-Bus is pointed at a socket that does not exist, so libsecret cannot be reached and the CLI
# falls back to storing credentials in plaintext. The warning is emitted at sign-in only, so it
# appears once for 'az login' and not at all for the commands that follow.
#
# Everything runs against a throwaway AZURE_CONFIG_DIR in a subshell, so the real ~/.azure and
# the surrounding shell are left untouched.
#
# Usage:
#   scripts/repro_encryption_warning.sh                   # uses ~/.azure-cli-livetest-sp.json
#   scripts/repro_encryption_warning.sh --no-login        # no credentials needed
#   scripts/repro_encryption_warning.sh --show-keyring    # what az has stored, metadata only
#   scripts/repro_encryption_warning.sh --verify-keyring  # real login, keyring reachable
#
# --verify-keyring is the positive control: it leaves D-Bus alone, so encryption succeeds and
# the credentials really are written to libsecret. It runs against the REAL profile, not a
# sandbox, so it overwrites both the libsecret items and ~/.azure with the test service
# principal. Recover with 'az login'. Pass --yes to skip the confirmation prompt.

set -euo pipefail

UNREACHABLE_DBUS='unix:path=/nonexistent'
SP_FILE="${AZ_LIVETEST_SP_FILE:-$HOME/.azure-cli-livetest-sp.json}"
CONFIG_DIR="${AZURE_CONFIG_DIR:-$HOME/.azure}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Prefer the repo's virtualenv over whatever az happens to be on PATH, so the code under test is
# the code in this working tree.
if [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
    AZ=("$REPO_ROOT/.venv/bin/python" -m azure.cli)
elif command -v az >/dev/null 2>&1; then
    AZ=(az)
else
    echo "error: no .venv in $REPO_ROOT and no az on PATH" >&2
    exit 1
fi

# A plain interpreter for the libsecret probes, which must run even when AZ is the packaged 'az'.
if [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
    PY="$REPO_ROOT/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PY=python3
else
    PY=''
fi

if [[ "$(uname -s)" != "Linux" ]]; then
    echo "error: only Linux uses libsecret. macOS Keychain and Windows DPAPI cannot be made" >&2
    echo "       unreachable through an environment variable." >&2
    exit 1
fi

count_warnings() {
    grep -c 'Encryption is unavailable' || true
}

run_step() {
    local label="$1"; shift
    echo
    echo "=============================================================================="
    echo "  $label"
    echo "=============================================================================="
    local output
    output="$("$@" 2>&1 >/dev/null || true)"
    [[ -n "$output" ]] && echo "$output"
    echo "------------------------------------------------------------------------------"
    echo "  warnings: $(printf '%s\n' "$output" | count_warnings)"
}

# Reads the CLI's libsecret items. Secrets are never printed: 'meta' and 'snapshot' do not even
# load them, and 'verify' compares them in memory and reports only match/MISMATCH.
keyring_py() {
    if [[ -z "$PY" ]]; then
        echo "error: no python interpreter available for the libsecret probe" >&2
        return 1
    fi
    "$PY" - "$@" <<'PYEOF'
import json
import os
import sys
from hmac import compare_digest

try:
    import gi
    gi.require_version("Secret", "1")
    from gi.repository import Secret
except Exception as exc:  # noqa: BLE001 - any import failure means the probe cannot run
    sys.exit("error: libsecret bindings unavailable (%s).\n"
             "       Install them with 'sudo apt install gir1.2-secret-1 python3-gi'." % exc)

# Must match LIBSECRET_SCHEMA_NAME and the 'type' attribute in
# src/azure-cli-core/azure/cli/core/auth/persistence.py
SCHEMA_NAME = "Microsoft Azure CLI"
TOKEN_CACHE = "Token cache"
SECRET_STORE = "Secret store"


def fetch(load_secrets):
    flags = Secret.SearchFlags.ALL | Secret.SearchFlags.UNLOCK
    if load_secrets:
        flags |= Secret.SearchFlags.LOAD_SECRETS
    try:
        service = Secret.Service.get_sync(Secret.ServiceFlags.OPEN_SESSION, None)
        items = service.search_sync(None, {"xdg:schema": SCHEMA_NAME}, flags, None)
    except Exception as exc:  # noqa: BLE001 - no bus, locked keyring, no collection
        sys.exit("error: cannot reach the keyring (%s)." % exc)

    found = {}
    for item in items:
        value = item.get_secret() if load_secrets else None
        found[dict(item.get_attributes()).get("type", "(no type)")] = {
            "created": item.get_created(),
            "modified": item.get_modified(),
            "text": value.get_text() if value else None,
        }
    return found


def stamp(epoch):
    import datetime
    return datetime.datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M:%S")


def cmd_meta():
    found = fetch(load_secrets=False)
    if not found:
        print("  (no items under schema %r)" % SCHEMA_NAME)
        return
    for name in sorted(found):
        entry = found[name]
        print("  %-14s created %s   modified %s"
              % (name, stamp(entry["created"]), stamp(entry["modified"])))


def cmd_snapshot(path):
    found = fetch(load_secrets=False)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({k: v["modified"] for k, v in found.items()}, handle)


def cmd_compare(before_path, after_path):
    with open(before_path, encoding="utf-8") as handle:
        before = json.load(handle)
    with open(after_path, encoding="utf-8") as handle:
        after = json.load(handle)
    for name in sorted(set(before) | set(after)):
        was, now = before.get(name), after.get(name)
        if was is None:
            print("  %-14s CREATED  at %s" % (name, stamp(now)))
        elif now is None:
            print("  %-14s REMOVED" % name)
        elif was != now:
            print("  %-14s CONTENT CHANGED  %s -> %s" % (name, stamp(was), stamp(now)))
        else:
            print("  %-14s content unchanged  (still %s)" % (name, stamp(was)))
    # gnome-keyring leaves 'modified' alone when a save rewrites an identical value, so an
    # unchanged timestamp means the content did not change, not that nothing was written.


def cmd_poison():
    """Overwrite both items with placeholders, so a later match cannot be stale data."""
    for name, payload in ((SECRET_STORE, "[]"), (TOKEN_CACHE, "{}")):
        schema = Secret.Schema.new(SCHEMA_NAME, Secret.SchemaFlags.NONE,
                                   {"type": Secret.SchemaAttributeType.STRING})
        ok = Secret.password_store_sync(schema, {"type": name}, None, "", payload, None)
        print("  %-14s %s" % (name, "replaced with a placeholder" if ok else "COULD NOT WRITE"))


def cmd_verify():
    # The credential file path arrives through the environment, so no secret ever reaches argv.
    with open(os.environ["AZ_SP_FILE_PATH"], encoding="utf-8") as handle:
        expected = json.load(handle)

    found = fetch(load_secrets=True)
    failures = 0

    entry = found.get(SECRET_STORE)
    if entry is None or entry["text"] is None:
        print("  secret store   ABSENT   (nothing stored in the keyring)")
        failures += 1
    else:
        stored = json.loads(entry["text"])
        match = next((e for e in stored if e.get("client_id") == expected["appId"]), None)
        if match is None:
            print("  client_id      MISMATCH (%d entr%s, none for this service principal)"
                  % (len(stored), "y" if len(stored) == 1 else "ies"))
            failures += 1
        else:
            print("  client_id      match")
            for label, stored_key, expected_key in (("tenant", "tenant", "tenant"),
                                                    ("client_secret", "client_secret", "password")):
                ok = compare_digest(str(match.get(stored_key, "")), str(expected[expected_key]))
                print("  %-14s %s" % (label, "match" if ok else "MISMATCH"))
                failures += 0 if ok else 1

    entry = found.get(TOKEN_CACHE)
    if entry is None or entry["text"] is None:
        print("  token cache    ABSENT")
        failures += 1
    else:
        cache = json.loads(entry["text"])
        counts = {k: len(v) for k, v in cache.items() if isinstance(v, dict) and v}
        print("  token cache    present  (%s)"
              % (", ".join("%s x%d" % kv for kv in sorted(counts.items())) or "empty"))
        if not counts.get("AccessToken"):
            print("  AccessToken    ABSENT")
            failures += 1

    sys.exit(1 if failures else 0)


COMMANDS = {"meta": cmd_meta, "snapshot": cmd_snapshot, "compare": cmd_compare,
            "poison": cmd_poison, "verify": cmd_verify}
COMMANDS[sys.argv[1]](*sys.argv[2:])
PYEOF
}

require_keyring_reachable() {
    if [[ -z "${DBUS_SESSION_BUS_ADDRESS:-}" ]]; then
        echo "error: DBUS_SESSION_BUS_ADDRESS is not set, so there is no keyring to inspect." >&2
        echo "       This mode needs a real desktop session with an unlocked login keyring." >&2
        exit 1
    fi
    if [[ "$DBUS_SESSION_BUS_ADDRESS" == "$UNREACHABLE_DBUS" ]]; then
        echo "error: DBUS_SESSION_BUS_ADDRESS still points at the unreachable socket used by the" >&2
        echo "       fallback repro. This mode must run against the real bus." >&2
        exit 1
    fi
}

# Exports SP, PW and TEN for the live login paths.
load_sp_creds() {
    if [[ ! -f "$SP_FILE" ]]; then
        echo "error: $SP_FILE not found." >&2
        echo "       Create it with 'az ad sp create-for-rbac', set AZ_LIVETEST_SP_FILE to point at" >&2
        echo "       another file, or run with --no-login to skip authentication entirely." >&2
        exit 1
    fi
    eval "$(python3 -c "
import json
c = json.load(open('$SP_FILE'))
print(f\"SP={c['appId']}\nPW={c['password']}\nTEN={c['tenant']}\")")"
}

if [[ "${1:-}" == "--no-login" ]]; then
    # Builds both persistences directly, then runs the sign-in check that emits the warning.
    echo "Building the token cache and the secret store with the keyring unreachable."
    probe_dir="$(mktemp -d)"
    trap 'rm -rf "$probe_dir"' EXIT

    output="$(DBUS_SESSION_BUS_ADDRESS="$UNREACHABLE_DBUS" "${AZ[0]}" -c "
from azure.cli.core.auth.persistence import (load_persisted_token_cache, load_secret_store,
                                             warn_if_encryption_unavailable)
load_secret_store('$probe_dir/service_principal_entries', True)
load_persisted_token_cache('$probe_dir/msal_token_cache', True)
warn_if_encryption_unavailable()" 2>&1 || true)"

    echo
    echo "$output"
    echo "------------------------------------------------------------------------------"
    echo "  warnings: $(printf '%s\n' "$output" | count_warnings)"
    echo
    echo "Expected 1: both persistences fall back, but the sign-in check warns only once."
    exit 0
fi

if [[ "${1:-}" == "--show-keyring" ]]; then
    require_keyring_reachable
    echo "=============================================================================="
    echo "  Azure CLI items currently in the keyring (metadata only)"
    echo "=============================================================================="
    keyring_py meta
    echo
    echo "Nothing above is credential material: only the item type and its timestamps."
    exit 0
fi

if [[ "${1:-}" == "--verify-keyring" ]]; then
    require_keyring_reachable
    load_sp_creds

    if [[ "${2:-}" != "--yes" ]]; then
        echo "This signs in for real, against the real profile at $CONFIG_DIR, with the keyring"
        echo "reachable. It overwrites both the libsecret items and the profile with this service"
        echo "principal. Whatever you are signed in as now is replaced and needs 'az login'."
        read -r -p "Continue? [y/N] " reply
        [[ "$reply" == [yY] ]] || { echo "Aborted."; exit 1; }
    fi

    work_dir="$(mktemp -d)"
    trap 'rm -rf "$work_dir"' EXIT

    echo "Config dir: $CONFIG_DIR (the real profile, not a sandbox)"
    echo "D-Bus:      $DBUS_SESSION_BUS_ADDRESS (keyring reachable)"

    # Encryption is the default. Pin it for this process only, so the run does not depend on
    # inherited config and the user's config file is left alone.
    export AZURE_CORE_ENCRYPT_TOKEN_CACHE=true

    echo
    echo "=============================================================================="
    echo "  Keyring before"
    echo "=============================================================================="
    keyring_py meta
    echo
    echo "  Replacing the payloads, so a post-login match cannot be leftover data:"
    keyring_py poison
    keyring_py snapshot "$work_dir/before.json"

    run_step "az login --service-principal" \
        "${AZ[@]}" login --service-principal -u "$SP" -p "$PW" --tenant "$TEN" -o none

    echo
    echo "=============================================================================="
    echo "  Where the credentials ended up"
    echo "=============================================================================="
    ls -l "$CONFIG_DIR"/msal_token_cache.* "$CONFIG_DIR"/service_principal_entries.* 2>/dev/null || true
    echo
    echo ".sig means the payload went to the keyring. A .json here would mean the fallback ran."
    echo "A stale .json alongside a .sig is leftover from an earlier plaintext run."

    keyring_py snapshot "$work_dir/after.json"
    echo
    echo "=============================================================================="
    echo "  Keyring after"
    echo "=============================================================================="
    keyring_py compare "$work_dir/before.json" "$work_dir/after.json"

    echo
    echo "=============================================================================="
    echo "  Does the keyring hold the credential we just signed in with?"
    echo "=============================================================================="
    export AZ_SP_FILE_PATH="$SP_FILE"
    if keyring_py verify; then
        echo
        echo "PASS: encryption was available, and the stored payload is this service principal."
        exit 0
    fi
    echo
    echo "FAIL: the keyring does not hold what this run signed in with." >&2
    exit 1
fi

load_sp_creds

# Throwaway config dir so the real ~/.azure keeps its encrypted credentials.
export AZURE_CONFIG_DIR
AZURE_CONFIG_DIR="$(mktemp -d)"
export DBUS_SESSION_BUS_ADDRESS="$UNREACHABLE_DBUS"
trap 'rm -rf "$AZURE_CONFIG_DIR"' EXIT

echo "Config dir: $AZURE_CONFIG_DIR (removed on exit)"
echo "D-Bus:      $UNREACHABLE_DBUS (keyring unreachable)"

run_step "az login --service-principal" \
    "${AZ[@]}" login --service-principal -u "$SP" -p "$PW" --tenant "$TEN" -o none
run_step "az group list" "${AZ[@]}" group list -o none
run_step "az group list" "${AZ[@]}" group list -o none
run_step "az account get-access-token" "${AZ[@]}" account get-access-token -o none

echo
echo "=============================================================================="
echo "  Where the credentials ended up"
echo "=============================================================================="
ls -l "$AZURE_CONFIG_DIR"/msal_token_cache.* "$AZURE_CONFIG_DIR"/service_principal_entries.* 2>/dev/null || true
echo
echo ".json means plaintext on disk. .sig would mean the payload went to the keyring."
echo
echo "Only 'az login' warns, once. The commands that follow stay quiet, because the warning is"
echo "checked at sign-in instead of on every command."
