#!/bin/bash

printf "\033[0;32mRunning pre-push hook in bash ...\033[0m\n"

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
    printf "\033[0;31mError: azure-cli is not installed in editable mode. Please install it in editable mode using `azdev setup`.\033[0m\n"
    exit 1
fi

# Get extension repo paths and join them with spaces
EXTENSIONS=$(azdev extension repo list -o tsv | tr '\n' ' ')

# Fetch upstream/dev branch
printf "\033[0;32mFetching upstream/dev branch...\033[0m\n"
git fetch upstream dev
if [ $? -ne 0 ]; then
    printf "\033[0;31mError: Failed to fetch upstream/dev branch. Please run 'git remote add upstream https://github.com/Azure/azure-cli.git' first.\033[0m\n"
    exit 1
fi

# Check if current branch needs rebasing
MERGE_BASE=$(git merge-base HEAD upstream/dev)
UPSTREAM_HEAD=$(git rev-parse upstream/dev)

if [ "$MERGE_BASE" != "$UPSTREAM_HEAD" ]; then
    printf "\n"
    printf "\033[1;33mYour branch is not up to date with upstream/dev. Please run the following commands to rebase and setup:\033[0m\n"
    printf "\033[1;33m+++++++++++++++++++++++++++++++++++++++++++++++++++++++\033[0m\n"
    printf "\033[1;33mgit rebase upstream/dev\033[0m\n"
    
    # Get extension repo paths
    EXTENSIONS=$(azdev extension repo list -o tsv | tr '\n' ' ')
    if [ -n "$EXTENSIONS" ]; then
        printf "\033[1;33mazdev setup -c %s -r %s\033[0m\n" "$AZURE_CLI_FOLDER" "$EXTENSIONS"
    else
        printf "\033[1;33mazdev setup -c %s\033[0m\n" "$AZURE_CLI_FOLDER"
    fi
    printf "\033[1;33m+++++++++++++++++++++++++++++++++++++++++++++++++++++++\033[0m\n"
    printf "\n"
    printf "\033[1;33mYou have 5 seconds to stop the push (Ctrl+C)...\033[0m\n"
    
    # Using a C-style for loop instead of seq
    i=5
    while [ $i -ge 1 ]; do
        printf "\r\033[K\033[1;33mTime remaining: %d seconds...\033[0m" $i
        sleep 1
        i=$((i-1))
    done
    printf "\r\033[K\033[1;33mContinuing without rebase...\033[0m\n"
fi

# get the current branch name
CURRENT_BRANCH=$(git branch --show-current)

# Run command azdev lint
printf "\033[0;32mRunning azdev lint...\033[0m\n"
azdev linter --min-severity medium --repo ./ --src $CURRENT_BRANCH --tgt $MERGE_BASE
if [ $? -ne 0 ]; then
    printf "\033[0;31mError: azdev lint check failed.\033[0m\n"
    exit 1
fi

# Run command azdev style
printf "\033[0;32mRunning azdev style...\033[0m\n"
azdev style --repo ./ --src $CURRENT_BRANCH --tgt $MERGE_BASE
if [ $? -ne 0 ]; then
    error_msg=$(azdev style --repo ./ --src $CURRENT_BRANCH --tgt $MERGE_BASE 2>&1)
    if echo "$error_msg" | grep -q "No modules"; then
        printf "\033[0;32mPre-push hook passed.\033[0m\n"
        exit 0
    fi
    printf "\033[0;31mError: azdev style check failed.\033[0m\n"
    exit 1
fi

# Run command azdev test
printf "\033[0;32mRunning azdev test...\033[0m\n"
azdev test --repo ./ --src $CURRENT_BRANCH --tgt $MERGE_BASE --discover --no-exitfirst --xml-path test_results.xml 2>/dev/null
if [ $? -ne 0 ]; then
    printf "\033[0;31mError: azdev test check failed.\033[0m\n"
    exit 1
else
    # remove the test_results.xml file
    rm -f test_results.xml
fi

printf "\033[0;32mPre-push hook passed.\033[0m\n"

if [ "$MERGE_BASE" != "$UPSTREAM_HEAD" ]; then
    printf "\n"
    printf "\033[1;33mYour branch is not up to date with upstream/dev. Please run the following commands to rebase and setup:\033[0m\n"
    printf "\033[1;33m+++++++++++++++++++++++++++++++++++++++++++++++++++++++\033[0m\n"
    printf "\033[1;33mgit rebase upstream/dev\033[0m\n"
    
    # Get extension repo paths
    EXTENSIONS=$(azdev extension repo list -o tsv | tr '\n' ' ')
    if [ -n "$EXTENSIONS" ]; then
        printf "\033[1;33mazdev setup -c %s -r %s\033[0m\n" "$AZURE_CLI_FOLDER" "$EXTENSIONS"
    else
        printf "\033[1;33mazdev setup -c %s\033[0m\n" "$AZURE_CLI_FOLDER"
    fi
    printf "\033[1;33m+++++++++++++++++++++++++++++++++++++++++++++++++++++++\033[0m\n"
fi
exit 0

