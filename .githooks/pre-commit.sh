#!/bin/bash
echo "\033[0;32mRunning pre-commit hook in bash ...\033[0m"

# run azdev_active script
SCRIPT_PATH="$(dirname "$0")/azdev_active.sh"
. "$SCRIPT_PATH"
if [ $? -ne 0 ]; then
    exit 1
fi

# Run command azdev scan
echo "\033[0;32mRunning azdev scan...\033[0m"

if git rev-parse --verify HEAD >/dev/null 2>&1
then
	echo "Using HEAD as the previous commit"
	against=HEAD
else
	echo "Using empty tree object as the previous commit"
	against=$(git hash-object -t tree /dev/null)
fi
has_secrets=0
for FILE in `git diff --cached --name-only --diff-filter=AM $against` ; do
    # Check if the file contains secrets
    detected=$(azdev scan -f "$FILE" | python -c "import sys, json; print(json.load(sys.stdin)['secrets_detected'])")
    if [ "$detected" = "True" ]; then
      echo "\033[0;31mDetected secrets from $FILE, You can run 'azdev mask' to remove secrets before commit.\033[0m"
      has_secrets=1
    fi
done

if [ $has_secrets -eq 1 ]; then
    echo "\033[0;31mSecret detected. If you want to skip that, run add '--no-verify' in the end of 'git commit' command.\033[0m"
    exit 1
fi

echo "\033[0;32mPre-commit hook passed.\033[0m"
exit 0
