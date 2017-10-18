Debian Packaging
================

Updating the Debian package
---------------------------

On a build machine (e.g. new Ubuntu 14.04 VM), run the build script.

For example:
```
git clone https://github.com/azure/azure-cli
cd azure-cli
export CLI_VERSION=2.0.9 \
  && export BUILD_ARTIFACT_DIR=$(mktemp -d)\
  && build_scripts/debian/build.sh $(pwd)
```

Note: The paths above have to be full paths, not relative otherwise the build will fail.

Now you have built the package, upload the package to the apt repository.


Verification
------------

```
sudo dpkg -i azure-cli_${CLI_VERSION}-1_all.deb
az
az --version
```
