Creating a Packaged Release
===========================

This document provides instructions on creating a packaged release.

Throughout this document, `{VERSION}` refers to a semantic version for this packaged release (e.g. `0.2.3`).


1 - Create release archive
--------------------------

We create a `.tar.gz` containing the source code for the packaged release.  
This archive will be used as the basis for the Docker, Debian and Homebrew builds as they build from this source.

Clone the repo afresh:  
```
$ git clone https://github.com/azure/azure-cli
```

Run the script to create the release archive from the 'scripts' folder at the repo root:  
```
$ cd scripts
$ python -m automation.release.packaged --version {VERSION} --components azure-cli=VERSION ...
```

A full example:  
```
$ cat ~/cli-components.json
{
    "azure-cli": "2.0.1",
    "azure-cli-core": "2.0.1",
    "azure-cli-component": "2.0.0",
    "azure-cli-acs": "2.0.0"
}
$ python -m automation.release.packaged --version 0.2.3 -f ~/cli-components.json
```

OR

```
$ python -m automation.release.packaged --version 0.2.3 --components azure-cli=2.0.1 acs=2.0.1 appservice=0.1.1b6 batch=0.1.1b5 cloud=2.0.0 component=2.0.0 configure=2.0.1 container=0.1.1b4 core=2.0.1 documentdb=0.1.1b2 feedback=2.0.0 find=0.0.1b1 iot=0.1.1b3 keyvault=0.1.1b6 network=2.0.1 nspkg=2.0.0 profile=2.0.1 redis=0.1.1b3 resource=2.0.1 role=2.0.0 sql=0.1.1b6 storage=2.0.1 vm=2.0.1
```

2 - Upload release archive
--------------------------

The release archive should be uploaded to a storage account.

Upload the archive:
```
$ export AZURE_STORAGE_CONNECTION_STRING=$(az storage account show-connection-string  -g azure-cli-prod -n azurecliprod -otsv)
$ az storage blob upload -f azure-cli_packaged_{VERSION}.tar.gz -n azure-cli_packaged_{VERSION}.tar.gz -c releases
```

Get the URL for the uploaded archive:
```
$ az storage blob url -c releases -n azure-cli_packaged_{VERSION}.tar.gz
```

An example URL is `https://azurecliprod.blob.core.windows.net/releases/azure-cli_packaged_{VERSION}.tar.gz`.

Get the SHA256 checksum:
```
$ shasum -a 256 azure-cli_packaged_{VERSION}.tar.gz
```

3 - Build/Release for Debian, Docker, Homebrew
----------------------------------------------

Follow the instructions in the `debian`, `docker`, `windows` and `homebrew` subdirectories to create these releases.


4 - Modify HISTORY.md
---------------------

Modify the packaged release history with release notes on this release and create a PR for this change.


------------


Info on Patches
---------------
The `patch_*` files in the `patches` subdirectory are useful when creating the patches in the Homebrew formula.

Currently, two patches are applied:  
1. The packaged installs do not support `az component` so we patch this module with appropriate messages.  
2. The CLI has a feature that checks PyPI for a command module if it's not installed and the user attempts to run it. This patch disables this as components cannot be installed in packaged installs.  

