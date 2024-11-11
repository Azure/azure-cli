#!/bin/bash

echo "\033[0;32mRunning pre-push hook in bash ...\033[0m"

# run azdev_active script and save its output
SCRIPT_PATH="$(dirname "$0")/azdev_active.sh"
. "$SCRIPT_PATH"
if [ $? -ne 0 ]; then
    exit 1
fi

# Check if azure-cli is installed in editable mode
PIP_SHOW_OUTPUT=$(pip show azure-cli 2>&1)
if echo "$PIP_SHOW_OUTPUT" | grep -q "Editable project location:"; then
    EDITABLE_LOCATION=$(echo "$PIP_SHOW_OUTPUT" | grep "Editable project location:" | sed 's/Editable project location: //')
    # get the parent of parent directory of the editable location
    AZURE_CLI_FOLDER=$(dirname "$(dirname "$EDITABLE_LOCATION")")
else
    echo "\033[0;31mError: azure-cli is not installed in editable mode. Please install it in editable mode using `azdev setup`.\033[0m"
    exit 1
fi

# Get extension repo paths and join them with spaces
EXTENSIONS=$(azdev extension repo list -o tsv | tr '\n' ' ')

# Fetch upstream/dev branch
echo "\033[0;32mFetching upstream/dev branch...\033[0m"
git fetch upstream dev
if [ $? -ne 0 ]; then
    echo "\033[0;31mError: Failed to fetch upstream/dev branch. Please run 'git remote add upstream https://github.com/Azure/azure-cli.git' first.\033[0m"
    exit 1
fi

# Check if current branch needs rebasing
MERGE_BASE=$(git merge-base HEAD upstream/dev)
UPSTREAM_HEAD=$(git rev-parse upstream/dev)

if [ "$MERGE_BASE" != "$UPSTREAM_HEAD" ]; then
    echo ""
    echo "\033[1;33mYour branch is not up to date with upstream/dev. Please run the following commands to rebase and setup:\033[0m"
    echo "\033[1;33m+++++++++++++++++++++++++++++++++++++++++++++++++++++++\033[0m"
    echo "\033[1;33mgit rebase upstream/dev\033[0m"
    
    # Get extension repo paths
    EXTENSIONS=$(azdev extension repo list -o tsv | tr '\n' ' ')
    if [ -n "$EXTENSIONS" ]; then
        echo "\033[1;33mazdev setup -c $AZURE_CLI_FOLDER -r $EXTENSIONS\033[0m"
    else
        echo "\033[1;33mazdev setup -c $AZURE_CLI_FOLDER\033[0m"
    fi
    echo "\033[1;33m+++++++++++++++++++++++++++++++++++++++++++++++++++++++\033[0m"
    echo ""
    echo "\033[1;33mYou have 5 seconds to stop the push (Ctrl+C)...\033[0m"
    
    for i in {5..1}; do
        echo -ne "\r\033[1;33mTime remaining: $i seconds...\033[0m"
        sleep 1
    done
    echo -e "\r\033[1;33mContinuing without rebase...\033[0m"
fi

# get the current branch name
currentBranch=$(git branch --show-current)

# Run command azdev lint
echo "\033[0;32mRunning azdev lint...\033[0m"
azdev linter --repo ./ --src $currentBranch --tgt $MERGE_BASE
if [ $? -ne 0 ]; then
    echo "\033[0;31mError: azdev lint check failed.\033[0m"
    exit 1
fi

# Run command azdev style
echo "\033[0;32mRunning azdev style...\033[0m"
azdev style --repo ./ --src $currentBranch --tgt $MERGE_BASE
if [ $? -ne 0 ]; then
    error_msg=$(azdev style --repo ./ --src $currentBranch --tgt $MERGE_BASE 2>&1)
    if echo "$error_msg" | grep -q "No modules"; then
        echo "\033[0;32mPre-push hook passed.\033[0m"
        exit 0
    fi
    echo "\033[0;31mError: azdev style check failed.\033[0m"
    exit 1
fi

# Run command azdev test
echo "\033[0;32mRunning azdev test...\033[0m"
azdev test --repo ./ --src $currentBranch --tgt $MERGE_BASE
if [ $? -ne 0 ]; then
    echo "\033[0;31mError: azdev test check failed.\033[0m"
    exit 1
fi

echo "\033[0;32mPre-push hook passed.\033[0m"
exit 0

