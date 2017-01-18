Debian Packaging
================

Updating the Debian package
---------------------------

Firstly, in `debian_dir_creator.sh`, modify debian/changelog with the new release information.
Create a PR for this change so it is tracked in the repo for next time.

Next, on a build machine (e.g. new Ubuntu 14.04 VM), run the build script.

For example:

First copy the build scripts onto the build machine.
```
$ > debian_build.sh; editor debian_build.sh
$ > debian_dir_creator.sh; editor debian_dir_creator.sh
$ chmod +x debian_build.sh debian_dir_creator.sh
```

Then execute it with the appropriate environment variable values.
```
$ export CLI_VERSION=0.1.6 \
    && export CLI_DOWNLOAD_SHA256=bb4bd4694e044bf416941e3afdc505bde7d049bac2e66c8b3fe44c9cb3b57ff8 \
    && export CLI_PATCH1_SHA256=d61ef29ace9bbdfef9a25dfbb1f475225bbca174263c8f863ee70f87d0a78bbe \
    && export CLI_PATCH2_SHA256=4b97507cb73b405c6fb2d701eb52ffa72ce547f791097fccadffc491ad6ae194 \
    && ./debian_build.sh ./debian_dir_creator.sh
```

Now you have built the package, upload the package to the apt repository.


Verification
------------

```
$ sudo dpkg -i azure-cli_${CLI_VERSION}-1_all.deb
$ az
$ az --version
```
