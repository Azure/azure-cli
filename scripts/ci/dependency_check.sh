#!/usr/bin/env bash

set -ev

REPO_ROOT="$(dirname ${BASH_SOURCE[0]})/../.."

# Uninstall any cruft that can poison the rest of the checks in this script.
pip freeze > baseline_deps.txt
pip uninstall -y -r baseline_deps.txt || true
pip list
pip check
rm baseline_deps.txt

# Install everything from our repository first.
${REPO_ROOT}/scripts/install_full.sh

pip check

python -m azure.cli --version

python -m azure.cli self-test
