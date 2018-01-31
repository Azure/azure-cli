#!/usr/bin/env bash

set -e

pip install -e ./tools

echo "Scan license"
azdev verify license

echo "Documentation Map"
azdev verify document-map

echo "Verify readme history"
python -m automation.tests.verify_readme_history

# Only verify package version or PRs to Azure/azure-cli (not other forks)
if [ $TRAVIS_EVENT_TYPE == "pull_request" ] && [ $TRAVIS_REPO_SLUG == "Azure/azure-cli" ]; then
    echo "Verify package versions"
    python -m automation.tests.verify_package_versions
fi

