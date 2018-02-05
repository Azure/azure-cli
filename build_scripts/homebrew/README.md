Homebrew Packaging
==================


Updating the formula
--------------------
1. Change the `url` in the formula to point to the new release and change the `sha256` value also.
2. Update the resources list in the formula (see below).
3. Run the formula verification commands (see below).
4. Submit a PR to https://github.com/Homebrew/homebrew-core.


Updating the resources list
---------------------------
```
# Create a new virtual environment first
pip install azure-cli homebrew-pypi-poet; poet -r azure-cli
```

Verification
------------

```
brew install --build-from-source azure-cli.rb
brew test azure-cli.rb
brew audit --strict --online azure-cli.rb
```

More Information
----------------
https://github.com/Homebrew/homebrew-core/blob/master/CONTRIBUTING.md

https://github.com/Homebrew/brew/blob/master/docs/Formula-Cookbook.md

https://github.com/Homebrew/brew/blob/master/docs/Acceptable-Formulae.md
