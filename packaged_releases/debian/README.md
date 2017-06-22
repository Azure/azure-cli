Debian Packaging
================

Updating the Debian package
---------------------------

On a build machine (e.g. new Ubuntu 14.04 VM), run the build script.

For example:

First copy the build scripts onto the build machine.
```
> ~/debian_build.sh; editor ~/debian_build.sh
> ~/debian_dir_creator.sh; editor ~/debian_dir_creator.sh
chmod +x ~/debian_build.sh ~/debian_dir_creator.sh
```

Then execute it with the appropriate environment variable values.
```
export CLI_VERSION=2.0.9 \
  && export CLI_DOWNLOAD_SHA256=ea4868b31a9d0b0e0a40ba7ff18100aea92175f4d3115fe9948064cc3677fcfb \
  && ~/debian_build.sh ~/debian_dir_creator.sh
```

Now you have built the package, upload the package to the apt repository.


Verification
------------

```
sudo dpkg -i azure-cli_${CLI_VERSION}-1_all.deb
az
az --version
```
