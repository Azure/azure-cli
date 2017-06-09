Bundled Installer Packaging
===========================


Updating the Debian package
---------------------------

On a build machine (e.g. new Ubuntu 14.04 VM), run the build script.
Requires both Python 2 and Python 3 (as we package for both).

For example:

First copy the build scripts onto the build machine.
```
> ~/build-bundle.py; editor ~/build-bundle.py
> ~/installer; editor ~/installer
```

Then execute it with the appropriate environment variable values.
```
export CLI_VERSION=0.2.10 \
  && export CLI_DOWNLOAD_SHA256=be72ddb0983b3466e868602e68e4d3bf67379fbe080bdaa6aa321c03f9bcce48 \
  && python ~/build-bundle.py
```

Now you have built the package, upload the package to the storage account.


Verification
------------

```
tmp_dir=$(mktemp -d)
tar -xvzf azure-cli_bundle.tar.gz
azure-cli_bundle_*/installer --install-dir $(mktemp -d) --bin-dir $(mktemp -d)
az --version
```

Upload the bundled installer archive
------------------------------------

The archive should be uploaded to a storage account.

Upload the archive:
```
export AZURE_STORAGE_CONNECTION_STRING=$(az storage account show-connection-string  -g azure-cli-prod -n azurecliprod -otsv)
az storage blob upload -f azure-cli_bundle_{VERSION}.tar.gz -n azure-cli_bundle_{VERSION}.tar.gz -c bundled
```

Get the URL for the uploaded archive:
```
az storage blob url -c bundled -n azure-cli_bundle_{VERSION}.tar.gz
```

An example URL is `https://azurecliprod.blob.core.windows.net/bundled/azure-cli_bundle_{VERSION}.tar.gz`.

Get the SHA256 checksum (if needed):
```
shasum -a 256 azure-cli_bundle_{VERSION}.tar.gz
```

Using the Bundled Installer
===========================
Where does this install fit in with everything else?
----------------------------------------------------
- It behaves similarly to the interactive script except it’s reproducible, scriptable (non-interactive), configurable and doesn’t rely on PyPI (can be run offline).
- It’s ideal as part of a CI/production build system.
- It makes it simpler to install on other Linux distros (e.g. RHEL).
- More info at #3376
 
Prerequisites
-------------
- Linux or macOS
- Python 2.7+ or Python 3.5+
 
Installing
----------
```
curl -L https://aka.ms/InstallAzureCliBundled -o azure-cli_bundle.tar.gz
tar -xvzf azure-cli_bundle.tar.gz
azure-cli_bundle_*/installer
```

After the install, it prints out exactly how to add az to path and set up tab completion:
```
-- The executable is available at '/root/bin/az'.
-- Tip: Add the executable to your path: e.g. 'export PATH=$PATH:/root/bin'.
-- Tip: Enable tab completion: e.g. 'source /root/lib/azure-cli/az.completion'
-- Done.
 ```

For installer help:
```
$ azure-cli_bundle_*/installer --help
usage: installer [-h] [--install-dir INSTALL_DIR] [--bin-dir BIN_DIR]
                 [--overwrite-install-dir] [--override-python-version-check]
                 [--override-native-check]
 
optional arguments:
  -h, --help            show this help message and exit
  --install-dir INSTALL_DIR, -i INSTALL_DIR
                        <snippet-removed> (default: /root/lib/azure-
                        cli)
  --bin-dir BIN_DIR, -b BIN_DIR
                        <snippet-removed> (default: /root/bin)
```

Running with a different python
-------------------------------
The above instructions run with your default ‘python’. You can use a different python for the installation.
```
<path-to-python> azure-cli_bundle_*/installer
```
 
Viewing all available versions
------------------------------
The install link above will always point to latest.

Older versions are available here:

https://azurecliprod.blob.core.windows.net/bundled?restype=container&comp=list
 
Upgrading
---------
Download the new bundle and run the installer again; you’ll be given the option to reinstall over a previous directory.
 
Uninstalling
------------
```
rm -r ~/lib/azure-cli
rm ~/bin/az
```
