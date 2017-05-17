Bundled Installer Packaging
===========================


Updating the Debian package
---------------------------

On a build machine (e.g. new Ubuntu 14.04 VM), run the build script.

For example:

First copy the build scripts onto the build machine.
```
$ > ~/build-bundle.py; editor ~/build-bundle.py
$ > ~/installer; editor ~/installer
```

Then execute it with the appropriate environment variable values.
```
$ export CLI_VERSION=0.2.8 \
    && export CLI_DOWNLOAD_SHA256=dfe1902e5f0ea14f38b2c1137b71c4d7daa2f0b27869eaf868fc3dfbdb3a366a \
    && python ~/build-bundle.py
```

Now you have built the package, upload the package to the storage account.


Verification
------------

```
$ tmp_dir=$(mktemp -d)
$ tar -xvzf azure-cli_bundle.tar.gz -C $tmp_dir
$ $tmp_dir/*/installer
$ az --version
```

Upload the bundled installer archive
------------------------------------

The archive should be uploaded to a storage account.

Upload the archive:
```
$ export AZURE_STORAGE_CONNECTION_STRING=$(az storage account show-connection-string  -g azure-cli-prod -n azurecliprod -otsv)
$ az storage blob upload -f azure-cli_bundle_{VERSION}.tar.gz -n azure-cli_bundle_{VERSION}.tar.gz -c bundled
```

Get the URL for the uploaded archive:
```
$ az storage blob url -c bundled -n azure-cli_bundle_{VERSION}.tar.gz
```

An example URL is `https://azurecliprod.blob.core.windows.net/bundled/azure-cli_bundle_{VERSION}.tar.gz`.

Get the SHA256 checksum:
```
$ shasum -a 256 azure-cli_bundle_{VERSION}.tar.gz
```
