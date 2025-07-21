#!/bin/bash
set -euo pipefail

echo "======================================"
echo " Azure CLI Devcontainer Setup Started "
echo "======================================"

# -----------------------------
# Remove existing virtual environments
# -----------------------------
VENV_DIRS=(
    "$HOME/.venv"
    "/workspaces/.venv"
)
for VENV in "${VENV_DIRS[@]}"; do
    if [ -d "$VENV" ]; then
        echo "Removing existing virtual environment at $VENV..."
        rm -rf "$VENV"
    fi
done

# -----------------------------
# GitHub authentication
# -----------------------------
export GITHUB_TOKEN=${GITHUB_TOKEN:-}
export GITHUB_USER=$(gh api user --jq .login 2>/dev/null || echo "")

if [ -z "$GITHUB_USER" ]; then
    echo "No GitHub user detected, running gh auth login..."
    gh auth login -p https -w
    export GITHUB_USER=$(gh api user --jq .login || echo "unknown")
fi
echo "Using GitHub user: $GITHUB_USER"

# -----------------------------
# Install aaz-dev
# -----------------------------
pip install --upgrade pip
pip install --no-cache-dir aaz-dev

# -----------------------------
# Repo paths
# -----------------------------
export AZDEV_CLI_PATH="/workspaces/azure-cli"
export CLI_PATH="/workspaces/azure-cli"
export CLI_EXTENSION_PATH="/workspaces-src/azure-cli-extensions"
export AAZ_PATH="/workspaces-src/aaz"
export SWAGGER_PATH="/workspaces-src/azure-rest-api-specs"

# -----------------------------
# Ensure /workspaces-src exists
# -----------------------------
mkdir -p /workspaces-src

# -----------------------------
# Clone repos only if they don't exist
# -----------------------------
OTHER_REPOS=("azure-cli-extensions" "aaz" "azure-rest-api-specs")

for REPO in "${OTHER_REPOS[@]}"; do
    DIR="/workspaces-src/$REPO"
    if [ -d "$DIR/.git" ]; then
        echo "$REPO already exists, skipping clone."
    else
        echo "Cloning $REPO..."
        gh repo fork "Azure/$REPO" --clone=false --default-branch-only
        git clone "https://github.com/$GITHUB_USER/$REPO.git" "$DIR" --single-branch --no-tags
        git -C "$DIR" remote add upstream "https://github.com/Azure/$REPO.git"
        git -C "$DIR" pull -r upstream main || true
    fi
done

# -----------------------------
# Install aaz-flow using uv (no separate venv)
# -----------------------------
echo "Installing aaz-flow and dependencies using uv..."
cd "/workspaces/azure-cli/tools/aaz-flow"
sudo uv pip install -e . --system
cd -

# -----------------------------
# Final setup
# -----------------------------
echo "Running azdev setup..."
python3 -m venv /workspaces-src/.azdev-env
source /workspaces-src/.azdev-env/bin/activate
pip install --upgrade pip
pip install azdev
azdev setup -c /workspaces/azure-cli -r /workspaces-src/azure-cli-extensions