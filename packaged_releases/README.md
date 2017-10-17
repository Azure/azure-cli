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
cd scripts
python -m automation.release.packaged --version {VERSION} --components azure-cli=VERSION ...
```

A full example:  
```
cat ~/cli-components.json
{
    "azure-cli": "2.0.1",
    "azure-cli-core": "2.0.1",
    "azure-cli-component": "2.0.0",
    "azure-cli-acs": "2.0.0"
}
python -m automation.release.packaged --version 0.2.3 -f ~/cli-components.json
```

OR

```
python -m automation.release.packaged --version 2.0.9 --components azure-cli=2.0.9 azure-cli-acr=2.0.7 azure-cli-acs=2.0.9 azure-cli-appservice=0.1.9 azure-cli-batch=3.0.2 azure-cli-billing=0.1.2 azure-cli-cdn=0.0.5 azure-cli-cloud=2.0.5 azure-cli-cognitiveservices=0.1.5 azure-cli-command_modules-nspkg=2.0.0 azure-cli-component=2.0.6 azure-cli-configure=2.0.9 azure-cli-consumption=0.1.2 azure-cli-core=2.0.10 azure-cli-cosmosdb=0.1.9 azure-cli-dla=0.0.9 azure-cli-dls=0.0.9 azure-cli-feedback=2.0.5 azure-cli-find=0.2.5 azure-cli-interactive=0.3.5 azure-cli-iot=0.1.8 azure-cli-keyvault=2.0.7 azure-cli-lab=0.0.7 azure-cli-monitor=0.0.7 azure-cli-network=2.0.9 azure-cli-nspkg=3.0.0 azure-cli-profile=2.0.7 azure-cli-rdbms=0.0.4 azure-cli-redis=0.2.6 azure-cli-resource=2.0.9 azure-cli-role=2.0.7 azure-cli-sql=2.0.6 azure-cli-storage=2.0.9 azure-cli-vm=2.0.9
```

2 - Upload release archive
--------------------------

The release archive should be uploaded to a storage account.

Upload the archive:
```
export AZURE_STORAGE_CONNECTION_STRING=$(az storage account show-connection-string  -g azure-cli-prod -n azurecliprod -otsv)
az storage blob upload -f azure-cli_packaged_{VERSION}.tar.gz -n azure-cli_packaged_{VERSION}.tar.gz -c releases
```

Get the URL for the uploaded archive:
```
az storage blob url -c releases -n azure-cli_packaged_{VERSION}.tar.gz
```

An example URL is `https://azurecliprod.blob.core.windows.net/releases/azure-cli_packaged_{VERSION}.tar.gz`.

Get the SHA256 checksum:
```
shasum -a 256 azure-cli_packaged_{VERSION}.tar.gz
```

3 - Build/Release for Debian, Docker, Windows, RPM, Homebrew
------------------------------------------------------------

Follow the instructions in the `debian`, `docker`, `windows`, `rpm` and `homebrew` subdirectories to create these releases.


4 - Modify HISTORY.md
---------------------

Modify the packaged release history with release notes on this release and create a PR for this change.
