Homebrew Packaging
==================

The Homebrew formula is available at https://github.com/Homebrew/homebrew-core/blob/master/Formula/azure-cli-2.rb.


Updating the formula
--------------------
1. Change the `url` in the formula to point to the new release (e.g. `azure-cli_packaged_0.1.5.tar.gz`).
2. Modify any patches as required (see below).
3. Run the formula verification commands (see below).
4. Submit a PR to https://github.com/Homebrew/homebrew-core.


Formula Verification
--------------------

```
$ brew install --build-from-source azure-cli-2
$ brew test azure-cli-2
$ brew audit --strict --online azure-cli-2
```


Patches
-------
The `patch_*` files in this directory are useful when creating the patches in the Homebrew formula.

Currently, two patches are applied:
1. The Homebrew install does not support `az component` so we patch this module with appropriate messages.
2. The CLI has a feature that checks PyPI for a command module if it's not installed and the user attempts to run it.
    This patch disables this as new components cannot be installed in the Homebrew install.

To create a new patch doing the following:
1. Modify the file in question (You can use the `patch_*` files in this directory for this).
2. Run git diff to get the patch. (e.g. `$ git diff src/command_modules/azure-cli-component/azure/cli/command_modules/component/custom.py`)
3. Publish the patch publicly and modify the formula to reference this patch.


More Information
----------------
https://github.com/Homebrew/homebrew-core/blob/master/CONTRIBUTING.md

https://github.com/Homebrew/brew/blob/master/docs/Formula-Cookbook.md

https://github.com/Homebrew/brew/blob/master/docs/Acceptable-Formulae.md
