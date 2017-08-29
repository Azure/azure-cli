Homebrew Packaging
==================


Updating the formula
--------------------
1. Change the `url` in the formula to point to the new release (e.g. `azure-cli_packaged_2.0.14.tar.gz`).
2. Modify any checksums as required.
3. Run the formula verification commands (see below).
4. Submit a PR to https://github.com/Homebrew/homebrew-core.


Verification
------------

```
$ brew install --build-from-source ./azure-cli.rb
$ brew test azure-cli
$ brew audit --strict --online azure-cli
```

More Information
----------------
https://github.com/Homebrew/homebrew-core/blob/master/CONTRIBUTING.md

https://github.com/Homebrew/brew/blob/master/docs/Formula-Cookbook.md

https://github.com/Homebrew/brew/blob/master/docs/Acceptable-Formulae.md
