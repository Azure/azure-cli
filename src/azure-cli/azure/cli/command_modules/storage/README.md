# Azure CLI Storage Command Module #

### How to use ###
Install Azure CLI in one of the following ways:
1. [Public Released Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest)
2. [Try Features before Release](https://github.com/Azure/azure-cli/blob/dev/doc/try_new_features_before_release.md)


### Included Features
Use the below CLI command to see all commands/groups in storage command group
```
az storage -h
```

#### Manage Encryption Scope:
Manage encryption scope associated with a storage account.
```
az storage account encryptipn-scope -h
```

*Examples:*
##### Create an encryption scope in a storage account based on Microsoft.Storage key source
```
az storage account encryption-scope create \
    -n myencryption \
    -s Micrsoft.Storage \
    --account-name mystorageaccount \
    -g MyResourceGroup
```

##### Show the properties of specified encryption scope in a storage account.
```
az storage account encryption-scope show \
    -n myencryption \
    --account-name mystorageaccount \
    -g MyResourceGroup
```

#### List all encryption scopes in a storage account.
```
az storage account encryption-scope show \
    --account-name mystorageaccount \
    -g MyResourceGroup
```

#### Update key source of specified encryption scope in a storage account.
```
az storage account encryption-scope update \
    -n myencryption \
    -s Micrsoft.KeyVault \
    -u "https://vaultname.vault.azure.net/keys/keyname/1f7fa7edc99f4cdf82b5b5f32f2a50a7" \
    --account-name mystorageaccount \
    -g MyResourceGoup
```

