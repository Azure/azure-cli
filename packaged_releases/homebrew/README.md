Homebrew Packaging
==================


Updating the formula
--------------------
1. Change the `url` in the formula to point to the new release (e.g. `azure-cli_packaged_0.1.5.tar.gz`).
2. Modify any checksums as required.
3. Run the formula verification commands (see below).
4. Submit a PR to https://github.com/Homebrew/homebrew-core.


Verification
------------

```
$ brew create https://azurecliprod.blob.core.windows.net/releases/azure-cli_packaged_${CLI_VERSION}.tar.gz --set-name azure-cli-2
$ brew install --build-from-source azure-cli-2
$ brew test azure-cli-2
$ brew audit --strict --online azure-cli-2
```

More Information
----------------
https://github.com/Homebrew/homebrew-core/blob/master/CONTRIBUTING.md

https://github.com/Homebrew/brew/blob/master/docs/Formula-Cookbook.md

https://github.com/Homebrew/brew/blob/master/docs/Acceptable-Formulae.md
