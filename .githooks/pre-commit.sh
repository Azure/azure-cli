#!/bin/bash
printf "\033[0;32mRunning pre-commit hook in bash ...\033[0m\n"

# run azdev_active script
SCRIPT_PATH="$(dirname "$0")/azdev_active.sh"
. "$SCRIPT_PATH"
if [ $? -ne 0 ]; then
    exit 1
fi

# Run command azdev scan
printf "\033[0;32mRunning azdev scan...\033[0m\n"

if git rev-parse --verify HEAD >/dev/null 2>&1
then
    printf "Using HEAD as the previous commit\n"
    against=HEAD
else
    printf "Using an empty tree object as the previous commit\n"
    against=$(git hash-object -t tree /dev/null)
fi
has_secrets=0
for FILE in `git diff --cached --name-only --diff-filter=AM $against` ; do
    # Check if the file contains secrets
    detected=$(azdev scan -f "$FILE" --continue-on-failure | python -c "import sys, json; print(json.load(sys.stdin)['secrets_detected'])")
    if [ "$detected" = "True" ]; then
      printf "\033[0;31mDetected secrets from %s, Please run the following command to mask it:\033[0m\n" "$FILE"
      printf "\033[0;31m+++++++++++++++++++++++++++++++++++++++++++++++++++++++\033[0m\n"
      printf "\033[0;31mazdev mask -f %s\033[0m\n" "$FILE"
      printf "\033[0;31m+++++++++++++++++++++++++++++++++++++++++++++++++++++++\033[0m\n"
      has_secrets=1
    fi
done

if [ $has_secrets -eq 1 ]; then
    printf "\033[0;31mSecret detected. If you want to skip that, run add '--no-verify' in the end of 'git commit' command.\033[0m\n"
    exit 1
fi

printf "\033[0;32mPre-commit hook passed.\033[0m\n"
exit 0
