# Git Hooks for Azure CLI Extension Development

## Setup

Please run the following command to enable the hooks.

```bash
azdev setup -c {azure_cli_repo_path} -r {azure_cli_extension_repo_path}

# if you install azdev which version is less than 0.1.84, you need to run the following command to enable the hooks
git config --local core.hooksPath .githooks
```

## Usage

Every time you git commit or git push, please make sure you have activated the python environment and completed the azdev setup.

If you want to skip the verification, you can add `--no-verify` to the git command.

## Note

### pre-commit

The pre-commit hook (`pre-commit.ps1`) performs the following checks:

1. Verifies that azdev is active in your current environment
2. Runs `azdev scan` on all staged files to detect potential secrets
3. If any secrets are detected, the commit will be blocked
   - You can use `azdev mask` to remove secrets before committing
   - Alternatively, use `git commit --no-verify` to bypass the check

### pre-push

The pre-push hooks (`pre-push.sh` for bash and `pre-push.ps1` for PowerShell) perform several quality checks:

1. Verifies that azdev is active in your current environment
2. Confirms azure-cli is installed in editable mode
3. Checks if your branch needs rebasing against upstream/dev
   - If rebasing is needed, displays instructions and provides a 5-second window to cancel
4. Runs the following quality checks on changed files:
   - `azdev lint`: Checks for linting issues
   - `azdev style`: Verifies code style compliance
   - `azdev test`: Runs tests for modified code
5. If any check fails, the push will be blocked
   - Use `git push --no-verify` to bypass these checks (not recommended)

The hooks support both Windows (PowerShell) and Unix-like systems (Bash), automatically using the appropriate script for your environment.
