Homebrew Packaging
==============

This directory contains the Homebrew formula for the CLI.

```
brew create <url> --set-name azure-cli-2
brew edit azure-cli-2
brew install azure-cli-2
brew test azure-cli-2
```
For example url = https://github.com/Azure/azure-cli/archive/all-v0.1.0b11.tar.gz

Bottles:
```
brew install --build-bottle azure-cli-2
brew bottle azure-cli-2
```

After changing the formula, submit a PR to https://github.com/Homebrew/homebrew-core with the change.
