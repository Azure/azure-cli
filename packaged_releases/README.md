Creating a Packaged Release
===========================

This document provides instructions on creating a packaged release.

Throughout this document, `{VERSION}` refers to a semantic version for this packaged release (e.g. `0.1.5`).


1 - Assemble module source code
-------------------------------

To assemble the source code, visit [Releases](https://github.com/Azure/azure-cli/releases) and download the source code for each component (and version) that should be part of the packaged release.  

Use the downloaded source code to create a directory with the structure outlined below.

Make a directory with name `azure-cli_packaged_{VERSION}`:
```
$ mkdir azure-cli_packaged_{VERSION}
```

**IMPORTANT** - The builds expect a certain folder structure.  
Expected folder structure inside of `azure-cli_packaged_{VERSION}`:
```
.
|-- az.completion
|-- src
|   |-- azure-cli
|       |-- setup.py
|       `-- etc...
|   |-- azure-cli-core
|       |-- setup.py
|       `-- etc...
|   |-- azure-cli-nspkg
|       |-- setup.py
|       `-- etc...
|   |-- command_modules
|       |-- <MODULE_NAME>
|           |-- setup.py
|           `-- etc...
```

(A script may be available in the future to make this step more straightforward.)

Notes:  
- Only the packages that will be in the CLI should be included here; leave out 'optional' components unless there's a specific reason to include any extra components.
- Make sure the versions of components don't include the `+dev` suffix. Remove these if this is the case.

APPLY ANY PATCHES:  
Modify the file in question in the directory created from  (You can use the `patch_*` files in `patches` subdirectory for this).  


2 - Create release archive
--------------------------

We create a `.tar.gz` containing the source code for the packaged release.  
This archive will be used as the basis for the Docker, Debian and Homebrew builds as they build from this source.

The archive should have the following name `azure-cli_packaged_{VERSION}.tar.gz`.

Archive the assembled source code from above:
```
$ tar -cvzf azure-cli_packaged_{VERSION}.tar.gz azure-cli_packaged_{VERSION}/
```


3 - Upload release archive
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

4 - Build/Release for Debian, Docker, Homebrew
----------------------------------------------

Follow the instructions in the `debian`, `docker` and `homebrew` subdirectories to create these releases.


5 - Modify HISTORY.md
---------------------

Modify the packaged release history with release notes on this release and create a PR for this change.


------------


Info on Patches
---------------
The `patch_*` files in the `patches` subdirectory are useful when creating the patches in the Homebrew formula.

Currently, two patches are applied:  
1. The packaged installs do not support `az component` so we patch this module with appropriate messages.  
2. The CLI has a feature that checks PyPI for a command module if it's not installed and the user attempts to run it. This patch disables this as components cannot be installed in packaged installs.  

