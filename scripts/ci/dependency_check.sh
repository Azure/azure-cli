#!/usr/bin/env bash

set -ev

REPO_ROOT="$(dirname ${BASH_SOURCE[0]})/../.."

# Upgrade pip to the latest version
python -m pip install --upgrade pip

# Uninstall any cruft that can poison the rest of the checks in this script.
pip freeze > baseline_deps.txt
pip uninstall -y -r baseline_deps.txt || true
pip list
pip check
rm baseline_deps.txt

# Install everything from our repository first.
if [[ "${CLI_CG_REPORT:-}" == [Tt][Rr][Uu][Ee] ]]; then
    python "${REPO_ROOT}/scripts/ci/install_with_cg_report.py"
else
    ${REPO_ROOT}/scripts/install_full.sh
fi

pip check

python -m azure.cli --version

python -m azure.cli self-test
