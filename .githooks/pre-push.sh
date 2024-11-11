#!/bin/bash

echo "\033[0;32mRunning pre-push hook in bash ...\033[0m"

# run azdev_active script
SCRIPT_PATH="$(dirname "$0")/azdev_active.sh"
. "$SCRIPT_PATH"
if [ $? -ne 0 ]; then
    exit 1
fi

# Fetch upstream/dev branch
echo "\033[0;32mFetching upstream/dev branch...\033[0m"
git fetch upstream dev
if [ $? -ne 0 ]; then
    echo "\033[0;31mError: Failed to fetch upstream/dev branch. Please run 'git remote add upstream https://github.com/Azure/azure-cli.git' first.\033[0m"
    exit 1
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

