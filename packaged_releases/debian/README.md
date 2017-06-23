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
  && export CLI_DOWNLOAD_SHA256=e74150b2db2975e8b17710eb7ef270ded16e6a8c27f77929544533f6b4c33b76 \
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
