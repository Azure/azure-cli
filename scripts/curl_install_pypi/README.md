Curl Install Script Information
==============

The scripts in this directory are used for installing through curl and they point to the packages on PyPI.

curl https://azurecliprod.blob.core.windows.net/install | bash

To update these scripts, submit a PR and request a member of the team to upload the scripts to the storage account.

Uploading the script:
```
$ export AZURE_STORAGE_CONNECTION_STRING=$(az storage account show-connection-string -g <RG> -n <NAME> -otsv)
$ az storage blob upload -c '$root' -n install.py -f scripts/curl_install_pypi/install.py 
$ az storage blob upload -c '$root' -n install -f scripts/curl_install_pypi/install 
```
