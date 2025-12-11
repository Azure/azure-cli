
source .venv/bin/activate

# Logout default account
export GITHUB_TOKEN=

if [[ $- == *i* ]]; then  # Interactive shell only
    # Check `repo` scope exists or not
    if gh auth status -a 2>/dev/null | grep "Token scopes: " | grep -q "repo"; then
        echo "You now have access to GitHub."
    else
        gh auth login -p https -w
    fi
fi

# Check `aaz-dev` is available or not
if ! command -v aaz-dev &> /dev/null; then
    GREEN="\033[0;32m"
    YELLOW="\033[0;33m"
    NC="\033[0m"  # no color

    set_or_add_remote() {
        local REPO=$1
        local REMOTE=$2
        local DIR="/workspaces/$REPO"
        local OWNER=$([ "$REMOTE" = "origin" ] && echo "$GITHUB_USER" || echo "Azure")
        local URL="https://github.com/$OWNER/$REPO.git"

        git -C "$DIR" remote get-url "$REMOTE" &>/dev/null || git -C "$DIR" remote add "$REMOTE" "$URL"
        git -C "$DIR" remote set-url "$REMOTE" "$URL"
    }

    setup_repo() {
        local REPO=$1
        local DIR="/workspaces/$REPO"

        echo
        gh repo fork "Azure/$REPO" --clone=false --default-branch-only

        if [ -d "$DIR" ]; then
            set_or_add_remote "$REPO" origin
            set_or_add_remote "$REPO" upstream
        else
            git clone "https://github.com/$GITHUB_USER/$REPO.git" --single-branch --no-tags
            set_or_add_remote "$REPO" upstream

            # Synchronize with upstream
            BRANCH=$(git -C "$DIR" remote show upstream | grep "HEAD branch" | awk '{print $NF}')
            git -C "$DIR" pull -r upstream "$BRANCH"
        fi
    }

    SECONDS=0

    echo
    uv pip install aaz-dev --link-mode=copy

    # `azdev` repositories
    setup_repo "azure-cli"
    setup_repo "azure-cli-extensions"

    azdev setup -c -r ./azure-cli-extensions

    # `aaz-dev` repositories
    setup_repo "aaz"
    setup_repo "azure-rest-api-specs"

    ELAPSED_TIME=$SECONDS

    echo -e "\n${YELLOW}Elapsed time: $((ELAPSED_TIME / 60))m $((ELAPSED_TIME % 60))s.${NC}"
    echo -e "\n${GREEN}Finished setup! Please launch the codegen tool via: aaz-dev run${NC}\n"
else
    echo -e "\nPlease launch the codegen tool via: aaz-dev run\n"
fi
