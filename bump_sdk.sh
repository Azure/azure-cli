#!/usr/bin/env bash
#
# Automate SDK version bump for the ACS (Azure Kubernetes Service) module.
#
# Usage:
#   bash bump_sdk.sh \
#       --old-sdk-version 41.0.0 \
#       --new-sdk-version 42.0.0 \
#       --old-api-version 2026-01-01 \
#       --new-api-version 2026-02-01
#
# With --dry-run to preview changes without modifying files:
#   bash bump_sdk.sh \
#       --old-sdk-version 41.0.0 \
#       --new-sdk-version 42.0.0 \
#       --old-api-version 2026-01-01 \
#       --new-api-version 2026-02-01 \
#       --dry-run
#
# With --run-tests to run acs tests in replay mode after bumping:
#   bash bump_sdk.sh \
#       --old-sdk-version 41.0.0 \
#       --new-sdk-version 42.0.0 \
#       --old-api-version 2026-01-01 \
#       --new-api-version 2026-02-01 \
#       --run-tests

set -euo pipefail

# ── Self-relocate to /tmp so git checkout doesn't break the running script ──
ORIG_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
if [[ "${_BUMP_SDK_RELOCATED:-}" != "1" ]]; then
    TMP_SCRIPT="$(mktemp /tmp/bump_sdk.XXXXXX.sh)"
    cp "$ORIG_SCRIPT" "$TMP_SCRIPT"
    chmod +x "$TMP_SCRIPT"
    export _BUMP_SDK_RELOCATED=1
    export _BUMP_SDK_ORIG_SCRIPT="$ORIG_SCRIPT"
    exec bash "$TMP_SCRIPT" "$@"
fi

# Running from /tmp now — resolve repo root from the original script path
SCRIPT_DIR="$(cd "$(dirname "$_BUMP_SDK_ORIG_SCRIPT")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../../../../" && pwd)"
SCRIPT_REL_PATH="${_BUMP_SDK_ORIG_SCRIPT#"$REPO_ROOT"/}"

# ── Defaults ──
OLD_SDK_VERSION=""
NEW_SDK_VERSION=""
OLD_API_VERSION=""
NEW_API_VERSION=""
BRANCH_NAME=""
DRY_RUN=false
RUN_TESTS=false

# ── Parse arguments ──
usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Required:
  --old-sdk-version VERSION   Current azure-mgmt-containerservice version (e.g. 41.0.0)
  --new-sdk-version VERSION   New azure-mgmt-containerservice version (e.g. 42.0.0)
  --old-api-version VERSION   Current API version in recordings (e.g. 2026-01-01)
  --new-api-version VERSION   New API version for recordings (e.g. 2026-02-01)

Optional:
  --branch-name NAME          Git branch name (default: bump-acs-sdk-<new-sdk-version>)
  --dry-run                   Preview changes without modifying any files
  --run-tests                 Set up azdev and run acs tests in replay mode after bumping
  -h, --help                  Show this help message
EOF
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --old-sdk-version)  OLD_SDK_VERSION="$2"; shift 2 ;;
        --new-sdk-version)  NEW_SDK_VERSION="$2"; shift 2 ;;
        --old-api-version)  OLD_API_VERSION="$2"; shift 2 ;;
        --new-api-version)  NEW_API_VERSION="$2"; shift 2 ;;
        --branch-name)      BRANCH_NAME="$2"; shift 2 ;;
        --dry-run)          DRY_RUN=true; shift ;;
        --run-tests)        RUN_TESTS=true; shift ;;
        -h|--help)          usage ;;
        *)                  echo "[ERROR] Unknown option: $1"; usage ;;
    esac
done

# Validate required arguments
for var_name in OLD_SDK_VERSION NEW_SDK_VERSION OLD_API_VERSION NEW_API_VERSION; do
    if [[ -z "${!var_name}" ]]; then
        echo "[ERROR] Missing required argument: --$(echo "$var_name" | tr '_' '-' | tr '[:upper:]' '[:lower:]')"
        usage
    fi
done

# Validate api-version format (YYYY-MM-DD)
for api_ver in "$OLD_API_VERSION" "$NEW_API_VERSION"; do
    if ! [[ "$api_ver" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        echo "[ERROR] Invalid API version format: $api_ver (expected YYYY-MM-DD)"
        exit 1
    fi
done

# Default branch name
if [[ -z "$BRANCH_NAME" ]]; then
    BRANCH_NAME="bump-acs-sdk-${NEW_SDK_VERSION}"
fi

# ── Paths ──
SETUP_PY="$REPO_ROOT/src/azure-cli/setup.py"
REQ_DIR="$REPO_ROOT/src/azure-cli"
RECORDINGS_DIR="$REPO_ROOT/src/azure-cli/azure/cli/command_modules/acs/tests/latest/recordings"

echo "Repository root: $REPO_ROOT"
if $DRY_RUN; then
    echo "=== DRY RUN MODE ==="
    echo
fi

# ── Detect sed in-place flag (macOS vs GNU) ──
if sed --version >/dev/null 2>&1; then
    # GNU sed
    SED_INPLACE=(sed -i)
else
    # macOS BSD sed
    SED_INPLACE=(sed -i '')
fi

# ── Step 0: Prepare git branch ──
echo "--- Step 0: Prepare git branch ---"
if $DRY_RUN; then
    echo "[DRY-RUN] Would run the following git commands:"
    echo "  git checkout dev"
    echo "  git pull origin dev"
    echo "  git checkout -b $BRANCH_NAME"
else
    echo "  Switching to dev branch..."
    git -C "$REPO_ROOT" checkout dev
    echo "  Pulling latest dev..."
    git -C "$REPO_ROOT" pull origin dev
    echo "  Creating new branch: $BRANCH_NAME"
    git -C "$REPO_ROOT" checkout -b "$BRANCH_NAME"
    echo "[OK] On new branch: $BRANCH_NAME"

    # Hide the script from git so it doesn't appear in the branch
    EXCLUDE_FILE="$REPO_ROOT/.git/info/exclude"
    if ! grep -qF "$SCRIPT_REL_PATH" "$EXCLUDE_FILE" 2>/dev/null; then
        echo "$SCRIPT_REL_PATH" >> "$EXCLUDE_FILE"
        echo "  Added $SCRIPT_REL_PATH to .git/info/exclude"
    fi
fi

# ── Step 1: Update setup.py ──
echo
echo "--- Step 1: Update setup.py ---"
OLD_SDK_PATTERN="azure-mgmt-containerservice~=${OLD_SDK_VERSION}"
NEW_SDK_PATTERN="azure-mgmt-containerservice~=${NEW_SDK_VERSION}"

if ! grep -q "$OLD_SDK_PATTERN" "$SETUP_PY"; then
    echo "[WARN] setup.py: Could not find '$OLD_SDK_PATTERN'"
elif $DRY_RUN; then
    echo "[DRY-RUN] setup.py: '$OLD_SDK_PATTERN' -> '$NEW_SDK_PATTERN'"
else
    "${SED_INPLACE[@]}" "s|${OLD_SDK_PATTERN}|${NEW_SDK_PATTERN}|g" "$SETUP_PY"
    echo "[OK] setup.py: '$OLD_SDK_PATTERN' -> '$NEW_SDK_PATTERN'"
fi

# ── Step 2: Update requirements.py3.*.txt ──
echo
echo "--- Step 2: Update requirements.py3.*.txt ---"
OLD_REQ_PATTERN="azure-mgmt-containerservice==${OLD_SDK_VERSION}"
NEW_REQ_PATTERN="azure-mgmt-containerservice==${NEW_SDK_VERSION}"

req_found=false
for req_file in "$REQ_DIR"/requirements.py3.*.txt; do
    [[ -f "$req_file" ]] || continue
    req_found=true
    rel_path="${req_file#"$REPO_ROOT"/}"

    if ! grep -q "$OLD_REQ_PATTERN" "$req_file"; then
        echo "[WARN] $rel_path: Could not find '$OLD_REQ_PATTERN'"
        continue
    fi

    if $DRY_RUN; then
        echo "[DRY-RUN] $rel_path: '$OLD_REQ_PATTERN' -> '$NEW_REQ_PATTERN'"
    else
        "${SED_INPLACE[@]}" "s|${OLD_REQ_PATTERN}|${NEW_REQ_PATTERN}|g" "$req_file"
        echo "[OK] $rel_path: '$OLD_REQ_PATTERN' -> '$NEW_REQ_PATTERN'"
    fi
done

if ! $req_found; then
    echo "[WARN] No requirements.py3.*.txt files found"
fi

# ── Step 3: Replace API version in recordings ──
echo
echo "--- Step 3: Replace API version in recordings ---"

if [[ ! -d "$RECORDINGS_DIR" ]]; then
    echo "[WARN] Recordings directory not found: $RECORDINGS_DIR"
else
    total_files=0
    total_replacements=0

    for rec_file in "$RECORDINGS_DIR"/*.yaml; do
        [[ -f "$rec_file" ]] || continue
        count=$(grep -c "$OLD_API_VERSION" "$rec_file" 2>/dev/null || true)

        if [[ "$count" -eq 0 ]]; then
            continue
        fi

        total_files=$((total_files + 1))
        total_replacements=$((total_replacements + count))
        rel_path="${rec_file#"$REPO_ROOT"/}"

        if $DRY_RUN; then
            echo "[DRY-RUN] $rel_path: $count replacement(s)"
        else
            "${SED_INPLACE[@]}" "s|${OLD_API_VERSION}|${NEW_API_VERSION}|g" "$rec_file"
            echo "[OK] $rel_path: $count replacement(s)"
        fi
    done

    if $DRY_RUN; then
        label="Would replace"
    else
        label="Replaced"
    fi
    echo
    echo "$label $OLD_API_VERSION -> $NEW_API_VERSION in $total_files file(s), $total_replacements occurrence(s) total."
fi

# ── Step 4: Run local tests in replay mode (optional) ──
if $RUN_TESTS; then
    echo
    echo "--- Step 4: Run local tests in replay mode ---"

    if $DRY_RUN; then
        echo "[DRY-RUN] Would run the following commands:"
        echo "  azdev setup -c $REPO_ROOT"
        echo "  azdev extension remove aks-preview  (may fail, ignored)"
        echo "  az extension remove -n aks-preview   (may fail, ignored)"
        echo "  az aks fake                          (force refresh command index)"
        echo "  azdev test acs"
    else
        # 4a. Set up azdev with local CLI repo
        echo "  [4a] Setting up azdev..."
        azdev setup -c "$REPO_ROOT"

        # 4b. Remove aks-preview extension (may fail if not installed — that's fine)
        echo "  [4b] Removing aks-preview extension (best-effort)..."
        azdev extension remove aks-preview || true
        az extension remove -n aks-preview || true

        # 4c. Force refresh command index
        echo "  [4c] Refreshing command index..."
        az aks fake || true

        # 4d. Run acs tests in replay mode
        echo "  [4d] Running acs tests (replay mode)..."
        if ! azdev test acs; then
            echo "[ERROR] azdev test acs failed"
            echo
            echo "Done (with test failures)."
            exit 1
        fi

        echo "[OK] All acs tests passed."
    fi
fi

# ── Cleanup: remove script from working tree so the branch is clean ──
if ! $DRY_RUN && [[ -f "$_BUMP_SDK_ORIG_SCRIPT" ]]; then
    rm -f "$_BUMP_SDK_ORIG_SCRIPT"
    echo "Cleaned up: removed $SCRIPT_REL_PATH from working tree"
fi

# Remove the temp copy
rm -f "${BASH_SOURCE[0]}" 2>/dev/null || true

echo
echo "Done!"
