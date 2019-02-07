#!/usr/bin/env bash

set -exv

pip install -e ./tools

echo "Scan license"
azdev verify license

echo "Documentation Map"
azdev verify document-map

echo "Verify readme history"
python -m automation.tests.verify_readme_history

# Only verify package version or PRs to Azure/azure-cli (not other forks)
# if [ $TRAVIS_EVENT_TYPE == "pull_request" ] && [ $TRAVIS_REPO_SLUG == "Azure/azure-cli" ]; then
#     echo "Verify package versions"
#    latestCliReleaseTag=$(git describe --tags `git rev-list --tags='azure-cli-*' --max-count=1`)
#    latestCliReleaseDir=$(mktemp -d)
#    echo "Latest CLI release tag $latestCliReleaseTag"
#    git clone -c advice.detachedHead=False https://github.com/$TRAVIS_REPO_SLUG --branch $latestCliReleaseTag $latestCliReleaseDir
#    python -m automation.tests.verify_package_versions --base-repo $latestCliReleaseDir --base-tag $latestCliReleaseTag
# fi

