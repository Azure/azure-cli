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
EXTENSIONS=$(azdev extension repo list -o tsv | tr '\n' ' ' | sed 's/ $//')

# Detect the remote pointing to Azure/azure-cli
UPSTREAM_REMOTE=$(git remote -v | grep -i "Azure/azure-cli" | grep "(fetch)" | head -1 | awk '{print $1}')
if [ -z "$UPSTREAM_REMOTE" ]; then
    printf "\033[0;31mError: No remote found pointing to Azure/azure-cli. Please run 'git remote add upstream https://github.com/Azure/azure-cli.git' first.\033[0m\n"
    exit 1
fi
printf "\033[0;36mUsing remote: %s\033[0m\n" "$UPSTREAM_REMOTE"

# Fetch remote dev branch
printf "\033[0;32mFetching %s/dev branch...\033[0m\n" "$UPSTREAM_REMOTE"
git fetch "$UPSTREAM_REMOTE" dev
if [ $? -ne 0 ]; then
    printf "\033[0;31mError: Failed to fetch %s/dev branch.\033[0m\n" "$UPSTREAM_REMOTE"
    exit 1
fi

# Check if current branch needs rebasing
MERGE_BASE=$(git merge-base HEAD "$UPSTREAM_REMOTE/dev")
UPSTREAM_HEAD=$(git rev-parse "$UPSTREAM_REMOTE/dev")
printf "\033[0;36mInitial mergeBase: %s\033[0m\n" "$MERGE_BASE"

if [ "$MERGE_BASE" != "$UPSTREAM_HEAD" ]; then
    printf "\n"
    printf "\033[1;33mYour branch is not up to date with %s/dev.\033[0m\n" "$UPSTREAM_REMOTE"
    printf "\033[1;33mWould you like to automatically rebase and setup? [Y/n]\033[0m\n"

    read -r INPUT < /dev/tty
    if [ "$INPUT" = "Y" ] || [ "$INPUT" = "y" ]; then
        printf "\033[0;32mRebasing with %s/dev...\033[0m\n" "$UPSTREAM_REMOTE"
        git rebase "$UPSTREAM_REMOTE/dev"
        if [ $? -ne 0 ]; then
            printf "\033[0;31mRebase failed. Please resolve conflicts and try again.\033[0m\n"
            exit 1
        fi
        printf "\033[0;32mRebase completed successfully.\033[0m\n"
        MERGE_BASE=$(git merge-base HEAD "$UPSTREAM_REMOTE/dev")
        printf "\033[0;36mUpdated mergeBase: %s\033[0m\n" "$MERGE_BASE"

        printf "\033[0;32mRunning azdev setup...\033[0m\n"
        if [ -n "$EXTENSIONS" ]; then
            azdev setup -c "$AZURE_CLI_FOLDER" -r "$EXTENSIONS"
        else
            azdev setup -c "$AZURE_CLI_FOLDER"
        fi
        if [ $? -ne 0 ]; then
            printf "\033[0;31mazdev setup failed. Please check your environment.\033[0m\n"
            exit 1
        fi
        printf "\033[0;32mSetup completed successfully.\033[0m\n"
    elif [ "$INPUT" = "N" ] || [ "$INPUT" = "n" ]; then
        printf "\r\033[K\033[1;33mSkipping rebase and setup. Continue push...\033[0m\n"
    else
        printf "\033[0;31mInvalid input. Aborting push...\033[0m\n"
        exit 1
    fi
fi

# Get the current branch name
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
    # Remove the test_results.xml file
    rm -f test_results.xml
fi

printf "\033[0;32mPre-push hook passed.\033[0m\n"
exit 0

