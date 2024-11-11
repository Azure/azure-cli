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

# Fetch upstream/dev branch
echo "\033[0;32mFetching upstream/dev branch...\033[0m"
git fetch upstream dev
if [ $? -ne 0 ]; then
    echo "\033[0;31mError: Failed to fetch upstream/dev branch. Please run 'git remote add upstream https://github.com/Azure/azure-cli.git' first.\033[0m"
    exit 1
fi

# Check if current branch needs rebasing
echo "\033[0;32mChecking if branch needs rebasing...\033[0m"
MERGE_BASE=$(git merge-base HEAD upstream/dev)
UPSTREAM_HEAD=$(git rev-parse upstream/dev)

if [ "$MERGE_BASE" != "$UPSTREAM_HEAD" ]; then
    read -p "Your branch is not up to date with upstream/dev. Do you want to rebase? (Y/N) " response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        git rebase upstream/dev
        if [ $? -ne 0 ]; then
            echo "\033[0;31mError: Rebase failed. Please resolve conflicts manually.\033[0m"
            exit 1
        fi
        echo "\033[0;32mRunning azdev setup -c $AZURE_CLI_FOLDER\033[0m"
        azdev setup -c "$AZURE_CLI_FOLDER"
    else
        echo "\033[0;33mContinuing without rebase...\033[0m"
    fi
fi

# get the current branch name
currentBranch=$(git branch --show-current)

# Run command azdev lint
echo "\033[0;32mRunning azdev lint...\033[0m"
azdev linter --repo ./ --src $currentBranch --tgt upstream/dev
if [ $? -ne 0 ]; then
    echo "\033[0;31mError: azdev lint check failed.\033[0m"
    exit 1
fi

# Run command azdev style
echo "\033[0;32mRunning azdev style...\033[0m"
azdev style --repo ./ --src $currentBranch --tgt upstream/dev
if [ $? -ne 0 ]; then
    error_msg=$(azdev style --repo ./ --src $currentBranch --tgt upstream/dev 2>&1)
    if echo "$error_msg" | grep -q "No modules"; then
        echo "\033[0;32mPre-push hook passed.\033[0m"
        exit 0
    fi
    echo "\033[0;31mError: azdev style check failed.\033[0m"
    exit 1
fi

# Run command azdev test
echo "\033[0;32mRunning azdev test...\033[0m"
azdev test --repo ./ --src $currentBranch --tgt upstream/dev
if [ $? -ne 0 ]; then
    echo "\033[0;31mError: azdev test check failed.\033[0m"
    exit 1
fi

echo "\033[0;32mPre-push hook passed.\033[0m"
exit 0

