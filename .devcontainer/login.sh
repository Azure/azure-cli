
source .venv/bin/activate

# Logout default account
export GITHUB_TOKEN=

# Check `repo` scope exists or not
if gh auth status -a 2>/dev/null | grep "Token scopes: " | grep -q "repo"; then
    echo "You now have access to GitHub."
else
    gh auth login -p https -w
fi
