
source .venv/bin/activate

# Logout default account
export GITHUB_TOKEN=

# Check `repo` scope exists or not
if gh auth status -a 2>/dev/null | grep "Token scopes: " | grep -q "repo"; then
    echo "You now have access to GitHub."
else
    gh auth login -p https -w
fi

# Check `aaz-dev` is available or not
if ! command -v aaz-dev &> /dev/null; then
    GREEN="\033[0;32m"
    YELLOW="\033[0;33m"
    NC="\033[0m"  # no color

    set_or_add_remote() {
        local REMOTE_NAME=$1
        local REMOTE_URL=$2
        local REPO_PATH="/workspaces/$REPO_NAME"

        git -C "$REPO_PATH" remote get-url "$REMOTE_NAME" &>/dev/null || git -C "$REPO_PATH" remote add "$REMOTE_NAME" "$REMOTE_URL"
        git -C "$REPO_PATH" remote set-url "$REMOTE_NAME" "$REMOTE_URL"
    }

    setup_repo() {
        local DIR_NAME="$1"
        local DIR_PATH="/workspaces/$DIR_NAME"
        local REPO="Azure/$DIR_NAME"

        if [ -d "$DIR_PATH" ]; then
            echo -e "\n${YELLOW}($DIR_NAME) Pulling the latest changes from upstream...${NC}"
            gh repo fork "$REPO" --clone=false
        else
            echo -e "\n${GREEN}($DIR_NAME) Forking and cloning the repository...${NC}"
            gh repo fork "$REPO" --clone -- --depth=1
        fi

        # `git` doesn't work well with private repository
        if [ "$(gh repo view "$REPO" --json visibility --jq '.visibility')" == "PRIVATE" ]; then
            cd "$DIR_PATH"
            gh repo sync --source "$REPO"
            cd /workspaces
        else
            DEFAULT_BRANCH=$(git -C "$DIR_PATH" remote show upstream | grep "HEAD branch" | awk '{print $NF}')
            git -C "$DIR_PATH" pull -r upstream "$DEFAULT_BRANCH"
        fi
    }

    echo -e "\n${GREEN}Welcome to the dev environment setup wizard.${NC}\n"

    SECONDS=0

    REPO_NAME=$(basename "$GITHUB_REPOSITORY")
    set_or_add_remote origin "https://github.com/$GITHUB_USER/$REPO_NAME.git"
    set_or_add_remote upstream "https://github.com/Azure/$REPO_NAME.git"

    uv pip install aaz-dev

    # `azdev` repositories
    setup_repo "azure-cli"
    setup_repo "azure-cli-extensions"

    azdev setup -c -r ./azure-cli-extensions

    # `aaz-dev` repositories
    setup_repo "aaz"
    setup_repo "azure-rest-api-specs"
    setup_repo "azure-rest-api-specs-pr"

    ELAPSED_TIME=$SECONDS
    echo -e "\n${YELLOW}Elapsed time: $((ELAPSED_TIME / 60))m $((ELAPSED_TIME % 60))s.${NC}"
    echo -e "\n${GREEN}Finished setup! Please launch the codegen tool via:${NC}"
    echo -e "${GREEN}aaz-dev run -c azure-cli -e azure-cli-extensions -s azure-rest-api-specs -a aaz${NC}\n"
fi
