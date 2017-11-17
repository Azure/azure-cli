#!/usr/bin/env bash

set -e

pip install -e ./tools

echo "Scan license"
azdev verify license

echo "Documentation Map"
azdev verify document-map

echo "Verify readme history"
python -m automation.tests.verify_readme_history

echo "Verify package versions"
python -m automation.tests.verify_package_versions

