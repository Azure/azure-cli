# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['storage'] = """
type: group
short-summary: Manage Azure Cloud Storage resources.
"""

helps['storage account'] = """
type: group
short-summary: Manage storage accounts.
"""

helps['storage account check-name'] = """
type: command
short-summary: Check that the storage account name is valid and is not already in use.
"""

helps['storage account blob-inventory-policy'] = """
type: group
short-summary: Manage storage account Blob Inventory Policy.
"""

helps['storage account blob-inventory-policy create'] = """
type: command
short-summary: Create Blob Inventory Policy for storage account.
examples:
  - name: Create Blob Inventory Policy trough json file for storage account.
    text: az storage account blob-inventory-policy create -g myresourcegroup --account-name mystorageaccount --policy @policy.json
"""

helps['storage account blob-inventory-policy show'] = """
type: command
short-summary: Show Blob Inventory Policy properties associated with the specified storage account.
examples:
  - name: Show Blob Inventory Policy properties associated with the specified storage account without prompt.
    text: az storage account blob-inventory-policy show -g ResourceGroupName --account-name storageAccountName
"""

helps['storage account blob-inventory-policy update'] = """
type: command
short-summary: Update Blob Inventory Policy associated with the specified storage account.
examples:
  - name: Update Blob Inventory Policy associated with the specified storage account.
    text: az storage account blob-inventory-policy update -g ResourceGroupName --account-name storageAccountName --set "policy.rules[0].name=newname"
"""

helps['storage account blob-inventory-policy delete'] = """
type: command
short-summary: Delete Blob Inventory Policy associated with the specified storage account.
examples:
  - name: Delete Blob Inventory Policy associated with the specified storage account without prompt.
    text: az storage account blob-inventory-policy delete -g ResourceGroupName --account-name storageAccountName -y
"""

helps['storage account blob-service-properties'] = """
type: group
short-summary: Manage the properties of a storage account's blob service.
"""

helps['storage account blob-service-properties show'] = """
type: command
short-summary: Show the properties of a storage account's blob service.
long-summary: >
    Show the properties of a storage account's blob service, including
    properties for Storage Analytics and CORS (Cross-Origin Resource
    Sharing) rules.
examples:
  - name: Show the properties of the storage account 'mystorageaccount' in resource group 'MyResourceGroup'.
    text: az storage account blob-service-properties show -n mystorageaccount -g MyResourceGroup
"""

helps['storage account blob-service-properties update'] = """
type: command
short-summary: Update the properties of a storage account's blob service.
long-summary: >
    Update the properties of a storage account's blob service, including
    properties for Storage Analytics and CORS (Cross-Origin Resource
    Sharing) rules.
parameters:
  - name: --enable-change-feed
    short-summary: 'Indicate whether change feed event logging is enabled. If it is true, you enable the storage account to begin capturing changes. The default value is true. You can see more details in https://docs.microsoft.com/azure/storage/blobs/storage-blob-change-feed?tabs=azure-portal#register-by-using-azure-cli'
  - name: --enable-delete-retention
    short-summary: 'Indicate whether delete retention policy is enabled for the blob service.'
  - name: --delete-retention-days
    short-summary: 'Indicate the number of days that the deleted blob should be retained. The value must be in range [1,365]. It must be provided when `--enable-delete-retention` is true.'
examples:
  - name: Enable change feed and set change feed retention days to infinite for the storage account 'mystorageaccount' in resource group 'myresourcegroup'.
    text: az storage account blob-service-properties update --enable-change-feed true -n mystorageaccount -g myresourcegroup
  - name: Enable change feed and set change feed retention days to 100 for the storage account 'mystorageaccount' in resource group 'myresourcegroup'.
    text: az storage account blob-service-properties update --enable-change-feed --change-feed-days 100 -n mystorageaccount -g myresourcegroup
  - name: Disable change feed for the storage account 'mystorageaccount' in resource group 'myresourcegroup'.
    text: az storage account blob-service-properties update --enable-change-feed false -n mystorageaccount -g myresourcegroup
  - name: Enable delete retention policy and set delete retention days to 100 for the storage account 'mystorageaccount' in resource group 'myresourcegroup'.
    text: az storage account blob-service-properties update --enable-delete-retention true --delete-retention-days 100 -n mystorageaccount -g myresourcegroup
  - name: Enable versioning for the storage account 'mystorageaccount' in resource group 'myresourcegroup'.
    text: az storage account blob-service-properties update --enable-versioning -n mystorageaccount -g myresourcegroup
  - name: Set default version for incoming request for storage account 'mystorageaccount'.
    text: az storage account blob-service-properties update --default-service-version 2020-04-08 -n mystorageaccount -g myresourcegroup
"""

helps['storage account create'] = """
type: command
short-summary: Create a storage account.
long-summary: >
    The SKU of the storage account defaults to 'Standard_RAGRS'.
examples:
  - name: Create a storage account 'mystorageaccount' in resource group 'MyResourceGroup' in the West US region with locally redundant storage.
    text: az storage account create -n mystorageaccount -g MyResourceGroup -l westus --sku Standard_LRS
    unsupported-profiles: 2017-03-09-profile
  - name: Create a storage account 'mystorageaccount' in resource group 'MyResourceGroup' in the West US region with locally redundant storage.
    text: az storage account create -n mystorageaccount -g MyResourceGroup -l westus --account-type Standard_LRS
    supported-profiles: 2017-03-09-profile
  - name: Create a storage account 'mystorageaccount' in resource group 'MyResourceGroup' in the eastus2euap region with account-scoped encryption key enabled for Table Service.
    text: az storage account create -n mystorageaccount -g MyResourceGroup --kind StorageV2 -l eastus2euap -t Account
"""

helps['storage account delete'] = """
type: command
short-summary: Delete a storage account.
examples:
  - name: Delete a storage account using a resource ID.
    text: az storage account delete --ids /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Storage/storageAccounts/{StorageAccount}
  - name: Delete a storage account using an account name and resource group.
    text: az storage account delete -n MyStorageAccount -g MyResourceGroup
"""

helps['storage account encryption-scope'] = """
type: group
short-summary: Manage encryption scope for a storage account.
"""

helps['storage account encryption-scope create'] = """
type: command
short-summary: Create an encryption scope within storage account.
examples:
  - name: Create an encryption scope within storage account based on Micosoft.Storage key source.
    text: |
        az storage account encryption-scope create --name myencryption -s Microsoft.Storage --account-name mystorageaccount -g MyResourceGroup
  - name: Create an encryption scope within storage account based on Micosoft.KeyVault key source.
    text: |
        az storage account encryption-scope create --name myencryption -s Microsoft.KeyVault -u "https://vaultname.vault.azure.net/keys/keyname/1f7fa7edc99f4cdf82b5b5f32f2a50a7" --account-name mystorageaccount -g MyResourceGroup
  - name: Create an encryption scope within storage account. (autogenerated)
    text: |
        az storage account encryption-scope create --account-name mystorageaccount --key-source Microsoft.Storage --name myencryption --resource-group MyResourceGroup --subscription mysubscription
    crafted: true
"""

helps['storage account encryption-scope list'] = """
type: command
short-summary: List encryption scopes within storage account.
examples:
  - name: List encryption scopes within storage account.
    text: |
        az storage account encryption-scope list --account-name mystorageaccount -g MyResourceGroup
"""

helps['storage account encryption-scope show'] = """
type: command
short-summary: Show properties for specified encryption scope within storage account.
examples:
  - name: Show properties for specified encryption scope within storage account.
    text: |
        az storage account encryption-scope show --name myencryption --account-name mystorageaccount -g MyResourceGroup
"""

helps['storage account encryption-scope update'] = """
type: command
short-summary: Update properties for specified encryption scope within storage account.
examples:
  - name: Update an encryption scope key source to Micosoft.Storage.
    text: |
        az storage account encryption-scope update --name myencryption -s Microsoft.Storage --account-name mystorageaccount -g MyResourceGroup
  - name: Create an encryption scope within storage account based on Micosoft.KeyVault key source.
    text: |
        az storage account encryption-scope update --name myencryption -s Microsoft.KeyVault -u "https://vaultname.vault.azure.net/keys/keyname/1f7fa7edc99f4cdf82b5b5f32f2a50a7" --account-name mystorageaccount -g MyResourceGroup
  - name: Disable an encryption scope within storage account.
    text: |
        az storage account encryption-scope update --name myencryption --state Disabled --account-name mystorageaccount -g MyResourceGroup
  - name: Enable an encryption scope within storage account.
    text: |
        az storage account encryption-scope update --name myencryption --state Enabled --account-name mystorageaccount -g MyResourceGroup
"""

helps['storage account failover'] = """
type: command
short-summary: Failover request can be triggered for a storage account in case of availability issues.
long-summary: |
    The failover occurs from the storage account's primary cluster to secondary cluster for (RA-)GRS/GZRS accounts. The secondary
    cluster will become primary after failover. For more information, please refer to
    https://docs.microsoft.com/azure/storage/common/storage-disaster-recovery-guidance.
examples:
  - name: Failover a storage account.
    text: |
        az storage account failover -n mystorageaccount -g MyResourceGroup
  - name: Failover a storage account without waiting for complete.
    text: |
        az storage account failover -n mystorageaccount -g MyResourceGroup --no-wait
        az storage account show -n mystorageaccount --expand geoReplicationStats
"""

helps['storage account generate-sas'] = """
type: command
short-summary: Generate a shared access signature for the storage account.
parameters:
  - name: --services
    short-summary: 'The storage services the SAS is applicable for. Allowed values: (b)lob (f)ile (q)ueue (t)able. Can be combined.'
  - name: --resource-types
    short-summary: 'The resource types the SAS is applicable for. Allowed values: (s)ervice (c)ontainer (o)bject. Can be combined.'
  - name: --expiry
    short-summary: Specifies the UTC datetime (Y-m-d'T'H:M'Z') at which the SAS becomes invalid.
  - name: --start
    short-summary: Specifies the UTC datetime (Y-m-d'T'H:M'Z') at which the SAS becomes valid. Defaults to the time of the request.
  - name: --account-name
    short-summary: 'Storage account name. Must be used in conjunction with either storage account key or a SAS token. Environment Variable: AZURE_STORAGE_ACCOUNT'
examples:
  - name: Generate a sas token for the account that is valid for queue and table services on Linux.
    text: |
        end=`date -u -d "30 minutes" '+%Y-%m-%dT%H:%MZ'`
        az storage account generate-sas --permissions cdlruwap --account-name MyStorageAccount --services qt --resource-types sco --expiry $end -o tsv
  - name: Generate a sas token for the account that is valid for queue and table services on MacOS.
    text: |
        end=`date -v+30M '+%Y-%m-%dT%H:%MZ'`
        az storage account generate-sas --permissions cdlruwap --account-name MyStorageAccount --services qt --resource-types sco --expiry $end -o tsv
  - name: Generate a shared access signature for the account (autogenerated)
    text: |
        az storage account generate-sas --account-key 00000000 --account-name MyStorageAccount --expiry 2020-01-01 --https-only --permissions acuw --resource-types co --services bfqt
    crafted: true
"""

helps['storage account file-service-properties'] = """
type: group
short-summary: Manage the properties of file service in storage account.
"""

helps['storage account file-service-properties show'] = """
type: command
short-summary: Show the properties of file service in storage account.
long-summary: >
    Show the properties of file service in storage account.
examples:
  - name: Show the properties of file service in storage account.
    text: az storage account file-service-properties show -n mystorageaccount -g MyResourceGroup
"""

helps['storage account file-service-properties update'] = """
type: command
short-summary: Update the properties of file service in storage account.
long-summary: >
    Update the properties of file service in storage account.
examples:
  - name: Enable soft delete policy and set delete retention days to 100 for file service in storage account.
    text: az storage account file-service-properties update --enable-delete-retention true --delete-retention-days 100 -n mystorageaccount -g MyResourceGroup
  - name: Disable soft delete policy for file service.
    text: az storage account file-service-properties update --enable-delete-retention false -n mystorageaccount -g MyResourceGroup
  - name: Enable SMB Multichannel setting for file service.
    text: az storage account file-service-properties update --enable-smb-multichannel -n mystorageaccount -g MyResourceGroup
  - name: Disable SMB Multichannel setting for file service.
    text: az storage account file-service-properties update --enable-smb-multichannel false -n mystorageaccount -g MyResourceGroup
  - name: Set secured SMB setting for file service.
    text: >
        az storage account file-service-properties update --versions SMB2.1;SMB3.0;SMB3.1.1
        --auth-methods NTLMv2;Kerberos --kerb-ticket-encryption RC4-HMAC;AES-256
        --channel-encryption AES-CCM-128;AES-GCM-128;AES-GCM-256 -n mystorageaccount -g MyResourceGroup
"""

helps['storage account keys'] = """
type: group
short-summary: Manage storage account keys.
"""

helps['storage account keys list'] = """
type: command
short-summary: List the access keys or Kerberos keys (if active directory enabled) for a storage account.
examples:
  - name: List the access keys for a storage account.
    text: az storage account keys list -g MyResourceGroup -n MyStorageAccount
  - name: List the access keys and Kerberos keys (if active directory enabled) for a storage account.
    text: az storage account keys list -g MyResourceGroup -n MyStorageAccount --expand-key-type kerb
"""

helps['storage account keys renew'] = """
type: command
short-summary: Regenerate one of the access keys or Kerberos keys (if active directory enabled) for a storage account.
long-summary: >
    Kerberos key is generated per storage account for Azure Files identity based authentication either with
    Azure Active Directory Domain Service (Azure AD DS) or Active Directory Domain Service (AD DS). It is used as the
    password of the identity registered in the domain service that represents the storage account. Kerberos key does not
    provide access permission to perform any control or data plane read or write operations against the storage account.
examples:
  - name: Regenerate one of the access keys for a storage account.
    text: az storage account keys renew -g MyResourceGroup -n MyStorageAccount --key primary
  - name: Regenerate one of the Kerberos keys for a storage account.
    text: az storage account keys renew -g MyResourceGroup -n MyStorageAccount --key secondary --key-type kerb
"""


helps['storage account list'] = """
type: command
short-summary: List storage accounts.
examples:
  - name: List all storage accounts in a subscription.
    text: az storage account list
  - name: List all storage accounts in a resource group.
    text: az storage account list -g MyResourceGroup
"""

helps['storage account management-policy'] = """
type: group
short-summary: Manage storage account management policies.
"""

helps['storage account management-policy create'] = """
type: command
short-summary: Create the data policy rules associated with the specified storage account.
examples:
  - name: Create the data policy rules associated with the specified storage account. (autogenerated)
    text: |
        az storage account management-policy create --account-name myaccount --policy @policy.json --resource-group myresourcegroup
    crafted: true
"""

helps['storage account management-policy update'] = """
type: command
short-summary: Update the data policy rules associated with the specified storage account.
examples:
    - name: Update the data policy rules associated with the specified storage account.
      text: |
        az storage account management-policy update --account-name myaccount --resource-group myresourcegroup --set policy.rules[0].name=newname
"""

helps['storage account management-policy show'] = """
type: command
short-summary: Get the data policy rules associated with the specified storage account.
"""

helps['storage account management-policy delete'] = """
type: command
short-summary: Delete the data policy rules associated with the specified storage account.
"""

helps['storage account network-rule'] = """
type: group
short-summary: Manage network rules.
"""

helps['storage account network-rule add'] = """
type: command
short-summary: Add a network rule.
long-summary: >
    Rules can be created for an IPv4 address, address range (CIDR format), or a virtual network subnet.
examples:
  - name: Create a rule to allow a specific address-range.
    text: az storage account network-rule add -g myRg --account-name mystorageaccount --ip-address 23.45.1.0/24
  - name: Create a rule to allow access for a subnet.
    text: az storage account network-rule add -g myRg --account-name mystorageaccount --vnet-name myvnet --subnet mysubnet
  - name: Create a rule to allow access for a subnet in another resource group.
    text: az storage account network-rule add -g myRg --account-name mystorageaccount  --subnet $subnetId
"""

helps['storage account network-rule list'] = """
type: command
short-summary: List network rules.
examples:
  - name: List network rules. (autogenerated)
    text: |
        az storage account network-rule list --account-name MyAccount --resource-group MyResourceGroup
    crafted: true
"""

helps['storage account network-rule remove'] = """
type: command
short-summary: Remove a network rule.
examples:
  - name: Remove a network rule. (autogenerated)
    text: |
        az storage account network-rule remove --account-name MyAccount --resource-group MyResourceGroup --subnet MySubnetID
    crafted: true
  - name: Remove a network rule. (autogenerated)
    text: |
        az storage account network-rule remove --account-name MyAccount --ip-address 23.45.1.0/24 --resource-group MyResourceGroup
    crafted: true
"""

helps['storage account or-policy'] = """
type: group
short-summary: Manage storage account Object Replication Policy.
"""

helps['storage account or-policy create'] = """
type: command
short-summary: Create Object Replication Service Policy for storage account.
examples:
  - name: Create Object Replication Service Policy for storage account.
    text: az storage account or-policy create -g ResourceGroupName -n storageAccountName -d destAccountName -s srcAccountName --destination-container dcont --source-container scont
  - name: Create Object Replication Service Policy trough json file for storage account.
    text: az storage account or-policy create -g ResourceGroupName -n storageAccountName --policy @policy.json
  - name: Create Object Replication Service Policy to source storage account through policy associated with destination storage account.
    text: az storage account or-policy show -g ResourceGroupName -n destAccountName --policy-id "3496e652-4cea-4581-b2f7-c86b3971ba92" | az storage account or-policy create -g ResourceGroupName -n srcAccountName -p "@-"
"""

helps['storage account or-policy list'] = """
type: command
short-summary: List Object Replication Service Policies associated with the specified storage account.
examples:
  - name: List Object Replication Service Policies associated with the specified storage account.
    text: az storage account or-policy list -g ResourceGroupName -n StorageAccountName
"""

helps['storage account or-policy delete'] = """
type: command
short-summary: Delete specified Object Replication Service Policy associated with the specified storage account.
examples:
  - name: Delete Object Replication Service Policy associated with the specified storage account.
    text: az storage account or-policy delete -g ResourceGroupName -n StorageAccountName --policy-id "04344ea7-aa3c-4846-bfb9-e908e32d3bf8"
"""

helps['storage account or-policy show'] = """
type: command
short-summary: Show the properties of specified Object Replication Service Policy for storage account.
examples:
  - name: Show the properties of specified Object Replication Service Policy for storage account.
    text: az storage account or-policy show -g ResourceGroupName -n StorageAccountName --policy-id "04344ea7-aa3c-4846-bfb9-e908e32d3bf8"
"""

helps['storage account or-policy update'] = """
type: command
short-summary: Update Object Replication Service Policy properties for storage account.
examples:
  - name: Update source storage account in Object Replication Service Policy.
    text: az storage account or-policy update -g ResourceGroupName -n StorageAccountName --source-account newSourceAccount --policy-id "04344ea7-aa3c-4846-bfb9-e908e32d3bf8"
  - name: Update Object Replication Service Policy through json file.
    text: az storage account or-policy update -g ResourceGroupName -n StorageAccountName -p @policy.json
"""

helps['storage account or-policy rule'] = """
type: group
short-summary: Manage Object Replication Service Policy Rules.
"""

helps['storage account or-policy rule add'] = """
type: command
short-summary: Add rule to the specified Object Replication Service Policy.
examples:
  - name: Add rule to the specified Object Replication Service Policy.
    text: az storage account or-policy rule add -g ResourceGroupName -n StorageAccountName --policy-id "04344ea7-aa3c-4846-bfb9-e908e32d3bf8" -d destContainer -s srcContainer
"""

helps['storage account or-policy rule list'] = """
type: command
short-summary: List all the rules in the specified Object Replication Service Policy.
examples:
  - name: List all the rules in the specified Object Replication Service Policy.
    text: az storage account or-policy rule list -g ResourceGroupName -n StorageAccountName --policy-id "04344ea7-aa3c-4846-bfb9-e908e32d3bf8"
"""

helps['storage account or-policy rule remove'] = """
type: command
short-summary: Remove the specified rule from the specified Object Replication Service Policy.
examples:
  - name: Remove the specified rule from the specified Object Replication Service Policy.
    text: az storage account or-policy rule remove -g ResourceGroupName -n StorageAccountName --policy-id "04344ea7-aa3c-4846-bfb9-e908e32d3bf8" --rule-id "78746d86-d3b7-4397-a99c-0837e6741332"
"""

helps['storage account or-policy rule show'] = """
type: command
short-summary: Show the properties of specified rule in Object Replication Service Policy.
examples:
  - name: Show the properties of specified rule in Object Replication Service Policy.
    text: az storage account or-policy rule show -g ResourceGroupName -n StorageAccountName --policy-id "04344ea7-aa3c-4846-bfb9-e908e32d3bf8" --rule-id "78746d86-d3b7-4397-a99c-0837e6741332"
"""

helps['storage account or-policy rule update'] = """
type: command
short-summary: Update rule properties to Object Replication Service Policy.
examples:
  - name: Update rule properties to Object Replication Service Policy.
    text: az storage account or-policy rule update -g ResourceGroupName -n StorageAccountName --policy-id "04344ea7-aa3c-4846-bfb9-e908e32d3bf8" --rule-id "78746d86-d3b7-4397-a99c-0837e6741332" --prefix-match blobA blobB
"""

helps['storage account private-endpoint-connection'] = """
type: group
short-summary: Manage storage account private endpoint connection.
"""

helps['storage account private-endpoint-connection approve'] = """
type: command
short-summary: Approve a private endpoint connection request for storage account.
examples:
  - name: Approve a private endpoint connection request for storage account by ID.
    text: |
        az storage account private-endpoint-connection approve --id "/subscriptions/0000-0000-0000-0000/resourceGroups/MyResourceGroup/providers/Microsoft.Storage/storageAccounts/mystorageaccount/privateEndpointConnections/mystorageaccount.b56b5a95-0588-4f8b-b348-15db61590a6c"
  - name: Approve a private endpoint connection request for storage account by ID.
    text: |
        id = (az storage account show -n mystorageaccount --query "privateEndpointConnections[0].id")
        az storage account private-endpoint-connection approve --id $id
  - name: Approve a private endpoint connection request for storage account using account name and connection name.
    text: |
        az storage account private-endpoint-connection approve -g myRg --account-name mystorageaccount --name myconnection
  - name: Approve a private endpoint connection request for storage account using account name and connection name.
    text: |
        name = (az storage account show -n mystorageaccount --query "privateEndpointConnections[0].name")
        az storage account private-endpoint-connection approve -g myRg --account-name mystorageaccount --name $name
"""

helps['storage account private-endpoint-connection delete'] = """
type: command
short-summary: Delete a private endpoint connection request for storage account.
examples:
  - name: Delete a private endpoint connection request for storage account by ID.
    text: |
        az storage account private-endpoint-connection delete --id "/subscriptions/0000-0000-0000-0000/resourceGroups/MyResourceGroup/providers/Microsoft.Storage/storageAccounts/mystorageaccount/privateEndpointConnections/mystorageaccount.b56b5a95-0588-4f8b-b348-15db61590a6c"
  - name: Delete a private endpoint connection request for storage account by ID.
    text: |
        id = (az storage account show -n mystorageaccount --query "privateEndpointConnections[0].id")
        az storage account private-endpoint-connection delete --id $id
  - name: Delete a private endpoint connection request for storage account using account name and connection name.
    text: |
        az storage account private-endpoint-connection delete -g myRg --account-name mystorageaccount --name myconnection
  - name: Delete a private endpoint connection request for storage account using account name and connection name.
    text: |
        name = (az storage account show -n mystorageaccount --query "privateEndpointConnections[0].name")
        az storage account private-endpoint-connection delete -g myRg --account-name mystorageaccount --name $name
"""

helps['storage account private-endpoint-connection reject'] = """
type: command
short-summary: Reject a private endpoint connection request for storage account.
examples:
  - name: Reject a private endpoint connection request for storage account by ID.
    text: |
        az storage account private-endpoint-connection reject --id "/subscriptions/0000-0000-0000-0000/resourceGroups/MyResourceGroup/providers/Microsoft.Storage/storageAccounts/mystorageaccount/privateEndpointConnections/mystorageaccount.b56b5a95-0588-4f8b-b348-15db61590a6c"
  - name: Reject a private endpoint connection request for storage account by ID.
    text: |
        id = (az storage account show -n mystorageaccount --query "privateEndpointConnections[0].id")
        az storage account private-endpoint-connection reject --id $id
  - name: Reject a private endpoint connection request for storage account using account name and connection name.
    text: |
        az storage account private-endpoint-connection reject -g myRg --account-name mystorageaccount --name myconnection
  - name: Reject a private endpoint connection request for storage account using account name and connection name.
    text: |
        name = (az storage account show -n mystorageaccount --query "privateEndpointConnections[0].name")
        az storage account private-endpoint-connection reject -g myRg --account-name mystorageaccount --name $name
"""

helps['storage account private-endpoint-connection show'] = """
type: command
short-summary: Show details of a private endpoint connection request for storage account.
examples:
  - name: Show details of a private endpoint connection request for storage account by ID.
    text: |
        az storage account private-endpoint-connection show --id "/subscriptions/0000-0000-0000-0000/resourceGroups/MyResourceGroup/providers/Microsoft.Storage/storageAccounts/mystorageaccount/privateEndpointConnections/mystorageaccount.b56b5a95-0588-4f8b-b348-15db61590a6c"
  - name: Show details of a private endpoint connection request for storage account by ID.
    text: |
        id = (az storage account show -n mystorageaccount --query "privateEndpointConnections[0].id")
        az storage account private-endpoint-connection show --id $id
  - name: Show details of a private endpoint connection request for storage account using account name and connection name.
    text: |
        az storage account private-endpoint-connection show -g myRg --account-name mystorageaccount --name myconnection
  - name: Show details of a private endpoint connection request for storage account using account name and connection name.
    text: |
        name = (az storage account show -n mystorageaccount --query "privateEndpointConnections[0].name")
        az storage account private-endpoint-connection show -g myRg --account-name mystorageaccount --name $name
"""

helps['storage account private-link-resource'] = """
type: group
short-summary: Manage storage account private link resources.
"""

helps['storage account private-link-resource list'] = """
type: command
short-summary: Get the private link resources that need to be created for a storage account.
examples:
  - name: Get the private link resources that need to be created for a storage account.
    text: |
        az storage account private-link-resource list --account-name mystorageaccount -g MyResourceGroup
"""

helps['storage account revoke-delegation-keys'] = """
type: command
short-summary: Revoke all user delegation keys for a storage account.
examples:
  - name: Revoke all user delegation keys for a storage account by resource ID.
    text: az storage account revoke-delegation-keys --ids /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Storage/storageAccounts/{StorageAccount}
  - name: Revoke all user delegation keys for a storage account 'mystorageaccount' in resource group 'MyResourceGroup' in the West US region with locally redundant storage.
    text: az storage account revoke-delegation-keys -n mystorageaccount -g MyResourceGroup
"""

helps['storage account show'] = """
type: command
short-summary: Show storage account properties.
examples:
  - name: Show properties for a storage account by resource ID.
    text: az storage account show --ids /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Storage/storageAccounts/{StorageAccount}
  - name: Show properties for a storage account using an account name and resource group.
    text: az storage account show -g MyResourceGroup -n MyStorageAccount
"""

helps['storage account show-connection-string'] = """
type: command
short-summary: Get the connection string for a storage account.
examples:
  - name: Get a connection string for a storage account.
    text: az storage account show-connection-string -g MyResourceGroup -n MyStorageAccount
  - name: Get the connection string for a storage account. (autogenerated)
    text: |
        az storage account show-connection-string --name MyStorageAccount --resource-group MyResourceGroup --subscription MySubscription
    crafted: true
"""

helps['storage account show-usage'] = """
type: command
short-summary: Show the current count and limit of the storage accounts under the subscription.
examples:
  - name: Show the current count and limit of the storage accounts under the subscription. (autogenerated)
    text: |
        az storage account show-usage --location westus2
    crafted: true
"""

helps['storage account update'] = """
type: command
short-summary: Update the properties of a storage account.
examples:
  - name: Update the properties of a storage account. (autogenerated)
    text: |
        az storage account update --default-action Allow --name MyStorageAccount --resource-group MyResourceGroup
    crafted: true
"""

helps['storage account hns-migration'] = """
type: group
short-summary: Manage storage account migration to enable hierarchical namespace.
"""

helps['storage account hns-migration start'] = """
type: command
short-summary: Validate/Begin migrating a storage account to enable hierarchical namespace.
examples:
  - name: Validate migrating a storage account to enable hierarchical namespace.
    text: az storage account hns-migration start --type validation --name mystorageaccount --resource-group myresourcegroup
  - name: Begin migrating a storage account to enable hierarchical namespace.
    text: az storage account hns-migration start --type upgrade --name mystorageaccount --resource-group myresourcegroup
"""

helps['storage account hns-migration stop'] = """
type: command
short-summary: Stop the enabling hierarchical namespace migration of a storage account.
examples:
  - name: Stop the enabling hierarchical namespace migration of a storage account.
    text: az storage account hns-migration stop --name mystorageaccount --resource-group myresourcegroup
"""

helps['storage blob'] = """
type: group
short-summary: Manage object storage for unstructured data (blobs).
long-summary: >
    Please specify one of the following authentication parameters for your commands: --auth-mode, --account-key,
    --connection-string, --sas-token. You also can use corresponding environment variables to store your authentication
    credentials, e.g. AZURE_STORAGE_KEY, AZURE_STORAGE_CONNECTION_STRING and AZURE_STORAGE_SAS_TOKEN.
"""

helps['storage blob copy'] = """
type: group
short-summary: Manage blob copy operations. Use `az storage blob show` to check the status of the blobs.
"""

helps['storage blob copy start'] = """
type: command
short-summary: Copy a blob asynchronously. Use `az storage blob show` to check the status of the blobs.
parameters:
  - name: --source-uri -u
    type: string
    short-summary: >
        A URL of up to 2 KB in length that specifies an Azure file or blob.
        The value should be URL-encoded as it would appear in a request URI.
        If the source is in another account, the source must either be public
        or must be authenticated via a shared access signature. If the source
        is public, no authentication is required.
        Examples:
        `https://myaccount.blob.core.windows.net/mycontainer/myblob`,
        `https://myaccount.blob.core.windows.net/mycontainer/myblob?snapshot=<DateTime>`,
        `https://otheraccount.blob.core.windows.net/mycontainer/myblob?sastoken`
  - name: --destination-if-modified-since
    type: string
    short-summary: >
        A DateTime value. Azure expects the date value passed in to be UTC.
        If timezone is included, any non-UTC datetimes will be converted to UTC.
        If a date is passed in without timezone info, it is assumed to be UTC.
        Specify this conditional header to copy the blob only
        if the destination blob has been modified since the specified date/time.
        If the destination blob has not been modified, the Blob service returns
        status code 412 (Precondition Failed).
  - name: --destination-if-unmodified-since
    type: string
    short-summary: >
        A DateTime value. Azure expects the date value passed in to be UTC.
        If timezone is included, any non-UTC datetimes will be converted to UTC.
        If a date is passed in without timezone info, it is assumed to be UTC.
        Specify this conditional header to copy the blob only
        if the destination blob has not been modified since the specified
        date/time. If the destination blob has been modified, the Blob service
        returns status code 412 (Precondition Failed).
  - name: --source-if-modified-since
    type: string
    short-summary: >
        A DateTime value. Azure expects the date value passed in to be UTC.
        If timezone is included, any non-UTC datetimes will be converted to UTC.
        If a date is passed in without timezone info, it is assumed to be UTC.
        Specify this conditional header to copy the blob only if the source
        blob has been modified since the specified date/time.
  - name: --source-if-unmodified-since
    type: string
    short-summary: >
        A DateTime value. Azure expects the date value passed in to be UTC.
        If timezone is included, any non-UTC datetimes will be converted to UTC.
        If a date is passed in without timezone info, it is assumed to be UTC.
        Specify this conditional header to copy the blob only if the source blob
        has not been modified since the specified date/time.
examples:
  - name: Copy a blob asynchronously. Use `az storage blob show` to check the status of the blobs.
    text: |
        az storage blob copy start --account-key 00000000 --account-name MyAccount --destination-blob MyDestinationBlob --destination-container MyDestinationContainer --source-uri https://storage.blob.core.windows.net/photos
  - name: Copy a blob asynchronously. Use `az storage blob show` to check the status of the blobs.
    text: |
        az storage blob copy start --account-name MyAccount --destination-blob MyDestinationBlob --destination-container MyDestinationContainer --sas-token $sas --source-uri https://storage.blob.core.windows.net/photos
  - name: Copy a blob specific version
    text: |
        az storage blob copy start --account-name MyAccount --destination-blob MyDestinationBlob --destination-container MyDestinationContainer --source-uri https://my-account.blob.core.windows.net/my-container/my-blob?versionId=2022-03-21T18:28:44.4431011Z --auth-mode login
"""

helps['storage blob copy start-batch'] = """
type: command
short-summary: Copy multiple blobs to a blob container. Use `az storage blob show` to check the status of the blobs.
parameters:
  - name: --destination-container -c
    type: string
    short-summary: The blob container where the selected source files or blobs will be copied to.
  - name: --pattern
    type: string
    short-summary: The pattern used for globbing files or blobs in the source. The supported patterns are '*', '?', '[seq]', and '[!seq]'. For more information, please refer to https://docs.python.org/3.7/library/fnmatch.html.
    long-summary: When you use '*' in --pattern, it will match any character including the the directory separator '/'.
  - name: --dryrun
    type: bool
    short-summary: List the files or blobs to be uploaded. No actual data transfer will occur.
  - name: --source-account-name
    type: string
    short-summary: The source storage account from which the files or blobs are copied to the destination. If omitted, the source account is used.
  - name: --source-account-key
    type: string
    short-summary: The account key for the source storage account.
  - name: --source-container
    type: string
    short-summary: The source container from which blobs are copied.
  - name: --source-share
    type: string
    short-summary: The source share from which files are copied.
  - name: --source-uri
    type: string
    short-summary: A URI specifying a file share or blob container from which the files or blobs are copied.
    long-summary: If the source is in another account, the source must either be public or be authenticated by using a shared access signature.
  - name: --source-sas
    type: string
    short-summary: The shared access signature for the source storage account.
examples:
  - name: Copy multiple blobs to a blob container. Use `az storage blob show` to check the status of the blobs. (autogenerated)
    text: |
        az storage blob copy start-batch --account-key 00000000 --account-name MyAccount --destination-container MyDestinationContainer --source-account-key MySourceKey --source-account-name MySourceAccount --source-container MySourceContainer
    crafted: true
"""

helps['storage blob delete'] = """
type: command
short-summary: Mark a blob or snapshot for deletion.
long-summary: >
    The blob is marked for later deletion during garbage collection.  In order to delete a blob, all of its snapshots must also be deleted.
    Both can be removed at the same time.
examples:
  - name: Delete a blob.
    text: az storage blob delete -c mycontainer -n MyBlob
  - name: Delete a blob using login credentials.
    text: az storage blob delete -c mycontainer -n MyBlob --account-name mystorageaccount --auth-mode login
"""

helps['storage blob delete-batch'] = """
type: command
short-summary: Delete blobs from a blob container recursively.
parameters:
  - name: --source -s
    type: string
    short-summary: The blob container from where the files will be deleted.
    long-summary: The source can be the container URL or the container name. When the source is the container URL, the storage account name will be parsed from the URL.
  - name: --pattern
    type: string
    short-summary: The pattern used for globbing files or blobs in the source. The supported patterns are '*', '?', '[seq]', and '[!seq]'. For more information, please refer to https://docs.python.org/3.7/library/fnmatch.html.
    long-summary: When you use '*' in --pattern, it will match any character including the the directory separator '/'. You can also try "az storage remove" command with --include and --exclude with azure cli >= 2.0.70 to match multiple patterns.
  - name: --dryrun
    type: bool
    short-summary: Show the summary of the operations to be taken instead of actually deleting the file(s).
    long-summary: If this is specified, it will ignore all the Precondition Arguments that include --if-modified-since and --if-unmodified-since. So the file(s) will be deleted with the command without --dryrun may be different from the result list with --dryrun flag on.
  - name: --if-match
    type: string
    short-summary: An ETag value, or the wildcard character (*). Specify this header to perform the operation only if the resource's ETag matches the value specified.
  - name: --if-none-match
    type: string
    short-summary: An ETag value, or the wildcard character (*).
    long-summary: Specify this header to perform the operation only if the resource's ETag does not match the value specified. Specify the wildcard character (*) to perform the operation only if the resource does not exist, and fail the operation if it does exist.
examples:
  - name: Delete all blobs ending with ".py" in a container that have not been modified for 10 days.
    text: |
        date=`date -d "10 days ago" '+%Y-%m-%dT%H:%MZ'`
        az storage blob delete-batch -s mycontainer --account-name mystorageaccount --pattern *.py --if-unmodified-since $date --auth-mode login
  - name: Delete all the blobs in a directory named "dir" in a container named "mycontainer".
    text: |
        az storage blob delete-batch -s mycontainer --pattern dir/*
  - name: Delete the blobs with the format 'cli-2018-xx-xx.txt' or 'cli-2019-xx-xx.txt' in a container.
    text: |
        az storage blob delete-batch -s mycontainer --pattern cli-201[89]-??-??.txt
  - name: Delete all blobs with the format 'cli-201x-xx-xx.txt' except cli-2018-xx-xx.txt' and 'cli-2019-xx-xx.txt' in a container.
    text: |
        az storage blob delete-batch -s mycontainer --pattern cli-201[!89]-??-??.txt
"""

helps['storage blob download-batch'] = """
type: command
short-summary: Download blobs from a blob container recursively.
parameters:
  - name: --source -s
    type: string
    short-summary: The blob container from where the files will be downloaded.
    long-summary: The source can be the container URL or the container name. When the source is the container URL, the storage account name will be parsed from the URL.
  - name: --destination -d
    type: string
    short-summary: The existing destination folder for this download operation.
  - name: --pattern
    type: string
    short-summary: The pattern used for globbing files or blobs in the source. The supported patterns are '*', '?', '[seq]', and '[!seq]'. For more information, please refer to https://docs.python.org/3.7/library/fnmatch.html.
    long-summary: When you use '*' in --pattern, it will match any character including the the directory separator '/'.
  - name: --dryrun
    type: bool
    short-summary: Show the summary of the operations to be taken instead of actually downloading the file(s).
examples:
  - name: Download all blobs that end with .py
    text: |
        az storage blob download-batch -d . --pattern *.py -s mycontainer --account-name mystorageaccount --account-key 00000000
  - name: Download all blobs in a directory named "dir" from container named "mycontainer".
    text: |
        az storage blob download-batch -d . -s mycontainer --pattern dir/*
  - name: Download all blobs with the format 'cli-2018-xx-xx.txt' or 'cli-2019-xx-xx.txt' in container to current path.
    text: |
        az storage blob download-batch -d . -s mycontainer --pattern cli-201[89]-??-??.txt
  - name: Download all blobs with the format 'cli-201x-xx-xx.txt' except cli-2018-xx-xx.txt' and 'cli-2019-xx-xx.txt' in container to current path.
    text: |
        az storage blob download-batch -d . -s mycontainer --pattern cli-201[!89]-??-??.txt
"""

helps['storage blob exists'] = """
type: command
short-summary: Check for the existence of a blob in a container.
parameters:
  - name: --name -n
    short-summary: The blob name.
examples:
  - name: Check for the existence of a blob in a container. (autogenerated)
    text: |
        az storage blob exists --account-key 00000000 --account-name MyAccount --container-name mycontainer --name MyBlob
    crafted: true
"""

helps['storage blob generate-sas'] = """
type: command
short-summary: Generate a shared access signature for the blob.
examples:
  - name: Generate a sas token for a blob with read-only permissions.
    text: |
        end=`date -u -d "30 minutes" '+%Y-%m-%dT%H:%MZ'`
        az storage blob generate-sas -c myycontainer -n MyBlob --permissions r --expiry $end --https-only
  - name: Generate a sas token for a blob with ip range specified.
    text: |
        end=`date -u -d "30 minutes" '+%Y-%m-%dT%H:%MZ'`
        az storage blob generate-sas -c myycontainer -n MyBlob --ip "176.134.171.0-176.134.171.255" --permissions r --expiry $end --https-only
  - name: Generate a shared access signature for the blob. (autogenerated)
    text: |
        az storage blob generate-sas --account-key 00000000 --account-name MyStorageAccount --container-name mycontainer --expiry 2018-01-01T00:00:00Z --name MyBlob --permissions r
    crafted: true
"""

helps['storage blob incremental-copy'] = """
type: group
short-summary: Manage blob incremental copy operations.
"""

helps['storage blob incremental-copy start'] = """
type: command
short-summary: Copies an incremental copy of a blob asynchronously.
long-summary: This operation returns a copy operation properties object, including a copy ID you can use to check or abort the copy operation. The Blob service copies blobs on a best-effort basis. The source blob for an incremental copy operation must be a page blob. Call get_blob_properties on the destination blob to check the status of the copy operation. The final blob will be committed when the copy completes.
parameters:
  - name: --source-uri -u
    short-summary: >
        A URL of up to 2 KB in length that specifies an Azure page blob.
        The value should be URL-encoded as it would appear in a request URI.
        The copy source must be a snapshot and include a valid SAS token or be public.
        Example:
        `https://myaccount.blob.core.windows.net/mycontainer/myblob?snapshot=<DateTime>&sastoken`
examples:
  - name: Upload all files that end with .py unless blob exists and has been modified since given date.
    text: az storage blob incremental-copy start --source-container MySourceContainer --source-blob MyBlob --source-account-name MySourceAccount --source-account-key MySourceKey --source-snapshot MySnapshot --destination-container MyDestinationContainer --destination-blob MyDestinationBlob
  - name: Copies an incremental copy of a blob asynchronously. (autogenerated)
    text: |
        az storage blob incremental-copy start --account-key 00000000 --account-name MyAccount --destination-blob MyDestinationBlob --destination-container MyDestinationContainer --source-account-key MySourceKey --source-account-name MySourceAccount --source-blob MyBlob --source-container MySourceContainer --source-snapshot MySnapshot
    crafted: true
  - name: Copy an incremental copy of a blob asynchronously. (autogenerated)
    text: |
        az storage blob incremental-copy start --connection-string myconnectionstring --destination-blob mydestinationblob --destination-container MyDestinationContainer --source-uri https://storage.blob.core.windows.net/photos
    crafted: true
"""

helps['storage blob lease'] = """
type: group
short-summary: Manage storage blob leases.
"""

helps['storage blob lease acquire'] = """
type: command
short-summary: Request a new lease.
examples:
  - name: Request a new lease.
    text: az storage blob lease acquire -b myblob -c mycontainer --account-name mystorageaccount --account-key 0000-0000
"""

helps['storage blob lease renew'] = """
type: command
short-summary: Renew the lease.
examples:
  - name: Renew the lease.
    text: az storage blob lease renew -b myblob -c mycontainer --lease-id "32fe23cd-4779-4919-adb3-357e76c9b1bb" --account-name mystorageaccount --account-key 0000-0000
"""

helps['storage blob list'] = """
type: command
short-summary: List blobs in a given container.
examples:
  - name: List all storage blobs in a container whose names start with 'foo'; will match names such as 'foo', 'foobar', and 'foo/bar'
    text: az storage blob list -c mycontainer --prefix foo
"""

helps['storage blob metadata'] = """
type: group
short-summary: Manage blob metadata.
"""

helps['storage blob query'] = """
type: command
short-summary: Enable users to select/project on blob or blob snapshot data by providing simple query expressions.
examples:
  - name: Enable users to select/project on blob by providing simple query expressions.
    text: az storage blob query -c mycontainer -n myblob --query-expression "SELECT _2 from BlobStorage"
  - name: Enable users to select/project on blob by providing simple query expressions and save in target file.
    text: az storage blob query -c mycontainer -n myblob --query-expression "SELECT _2 from BlobStorage" --result-file result.csv
"""

helps['storage blob restore'] = """
type: command
short-summary: Restore blobs in the specified blob ranges.
examples:
  - name: Restore blobs in two specified blob ranges. For examples, (container1/blob1, container2/blob2) and (container2/blob3..container2/blob4).
    text: az storage blob restore --account-name mystorageaccount -g MyResourceGroup -t 2020-02-27T03:59:59Z -r container1/blob1 container2/blob2 -r container2/blob3 container2/blob4
  - name: Restore blobs in the specified blob ranges from account start to account end.
    text: az storage blob restore --account-name mystorageaccount -g MyResourceGroup -t 2020-02-27T03:59:59Z -r "" ""
  - name: Restore blobs in the specified blob range.
    text: |
        time=`date -u -d "30 minutes" '+%Y-%m-%dT%H:%MZ'`
        az storage blob restore --account-name mystorageaccount -g MyResourceGroup -t $time -r container0/blob1 container0/blob2
  - name: Restore blobs in the specified blob range without wait and query blob restore status with 'az storage account show'.
    text: |
        time=`date -u -d "30 minutes" '+%Y-%m-%dT%H:%MZ'`
        az storage blob restore --account-name mystorageaccount -g MyResourceGroup -t $time -r container0/blob1 container0/blob2 --no-wait
"""

helps['storage blob rewrite'] = """
type: command
short-summary:  Create a new Block Blob where the content of the blob is read from a given URL.
long-summary: The content of an existing blob is overwritten with the new blob.
examples:
  - name: Update encryption scope for existing blob.
    text: az storage blob rewrite --source-uri https://srcaccount.blob.core.windows.net/mycontainer/myblob?<sastoken> --encryption-scope newscope -c mycontainer -n myblob --account-name mystorageaccount --account-key 0000-0000
"""

helps['storage blob service-properties'] = """
type: group
short-summary: Manage storage blob service properties.
"""

helps['storage blob service-properties delete-policy'] = """
type: group
short-summary: Manage storage blob delete-policy service properties.
"""

helps['storage blob service-properties delete-policy show'] = """
type: command
short-summary: Show the storage blob delete-policy.
examples:
  - name: Show the storage blob delete-policy. (autogenerated)
    text: |
        az storage blob service-properties delete-policy show --account-name mystorageccount --account-key 00000000
    crafted: true
  - name: Show the storage blob delete-policy. (autogenerated)
    text: |
        az storage blob service-properties delete-policy show --account-name mystorageccount --auth-mode login
    crafted: true
"""

helps['storage blob service-properties delete-policy update'] = """
type: command
short-summary: Update the storage blob delete-policy.
examples:
  - name: Update the storage blob delete-policy. (autogenerated)
    text: |
        az storage blob service-properties delete-policy update --account-name mystorageccount --account-key 00000000 --days-retained 7 --enable true
    crafted: true
"""

helps['storage blob service-properties update'] = """
type: command
short-summary: Update storage blob service properties.
examples:
  - name: Update storage blob service properties. (autogenerated)
    text: |
        az storage blob service-properties update --404-document error.html --account-name mystorageccount --account-key 00000000 --index-document index.html --static-website true
    crafted: true
"""

helps['storage blob set-tier'] = """
type: command
short-summary: Set the block or page tiers on the blob.
parameters:
  - name: --type -t
    short-summary: The blob type
  - name: --tier
    short-summary: The tier value to set the blob to.
  - name: --timeout
    short-summary: The timeout parameter is expressed in seconds. This method may make multiple calls to the Azure service and the timeout will apply to each call individually.
long-summary: >
    For block blob this command only supports block blob on standard storage accounts.
    For page blob, this command only supports for page blobs on premium accounts.
examples:
  - name: Set the block or page tiers on the blob. (autogenerated)
    text: |
        az storage blob set-tier --account-key 00000000 --account-name MyAccount --container-name mycontainer --name MyBlob --tier P10
    crafted: true
"""

helps['storage blob immutability-policy'] = """
type: group
short-summary: Manage blob immutability policy.
"""

helps['storage blob immutability-policy set'] = """
type: command
short-summary: Set blob's immutability policy.
examples:
  - name: Set an unlocked immutability policy.
    text: az storage blob immutability-policy set --expiry-time 2021-09-07T08:00:00Z --policy-mode Unlocked -c mycontainer -n myblob --account-name mystorageaccount
  - name: Lock a immutability policy.
    text: az storage blob immutability-policy set --policy-mode Locked -c mycontainer -n myblob --account-name mystorageaccount
"""

helps['storage blob immutability-policy delete'] = """
type: command
short-summary: Delete blob's immutability policy.
examples:
  - name: Delete an unlocked immutability policy.
    text: az storage blob immutability-policy delete -c mycontainer -n myblob --account-name mystorageaccount --account-key 0000-0000
"""

helps['storage blob set-legal-hold'] = """
type: command
short-summary: Set blob legal hold.
examples:
  - name: Configure blob legal hold.
    text: az storage blob set-legal-hold --legal-hold -c mycontainer -n myblob --account-name mystorageaccount --account-key 0000-0000
  - name: Clear blob legal hold.
    text: az storage blob set-legal-hold --legal-hold false -c mycontainer -n myblob --account-name mystorageaccount --account-key 0000-0000
"""

helps['storage blob show'] = """
type: command
short-summary: Get the details of a blob.
examples:
  - name: Show all properties of a blob.
    text: az storage blob show -c mycontainer -n MyBlob
  - name: Get the details of a blob (autogenerated)
    text: |
        az storage blob show --account-name mystorageccount --account-key 00000000 --container-name mycontainer --name MyBlob
    crafted: true
"""

helps['storage blob sync'] = """
type: command
short-summary: Sync blobs recursively to a storage blob container.
examples:
  - name: Sync a single blob to a container.
    text: az storage blob sync -c mycontainer -s "path/to/file" -d NewBlob
  - name: Sync a directory to a container.
    text: az storage blob sync -c mycontainer --account-name mystorageccount --account-key 00000000 -s "path/to/directory"
"""

helps['storage blob upload'] = """
type: command
short-summary: Upload a file to a storage blob.
long-summary: Create a new blob from a file path, or updates the content of an existing blob with automatic chunking and progress notifications.
parameters:
  - name: --type -t
    short-summary: Default to 'page' for *.vhd files, or 'block' otherwise.
  - name: --maxsize-condition
    short-summary: The max length in bytes permitted for an append blob.
  - name: --validate-content
    short-summary: Specify that an MD5 hash shall be calculated for each chunk of the blob and verified by the service when the chunk has arrived.
examples:
  - name: Upload to a blob.
    text: az storage blob upload -f /path/to/file -c mycontainer -n MyBlob
  - name: Upload to a blob with blob sas url.
    text: az storage blob upload -f /path/to/file --blob-url https://mystorageaccount.blob.core.windows.net/mycontainer/myblob?sv=2019-02-02&st=2020-12-22T07%3A07%3A29Z&se=2020-12-23T07%3A07%3A29Z&sr=b&sp=racw&sig=redacted
  - name: Upload a file to a storage blob. (autogenerated)
    text: |
        az storage blob upload --account-name mystorageaccount --account-key 0000-0000 --container-name mycontainer --file /path/to/file --name myblob
    crafted: true
  - name: Upload a string to a blob.
    text: az storage blob upload --data "teststring" -c mycontainer -n myblob --account-name mystorageaccount --account-key 0000-0000
  - name: Upload to a through pipe.
    text: |
        echo $data | az storage blob upload --data @- -c mycontainer -n myblob --account-name mystorageaccount --account-key 0000-0000
"""

helps['storage blob upload-batch'] = """
type: command
short-summary: Upload files from a local directory to a blob container.
parameters:
  - name: --source -s
    type: string
    short-summary: The directory where the files to be uploaded are located.
  - name: --destination -d
    type: string
    short-summary: The blob container where the files will be uploaded.
    long-summary: The destination can be the container URL or the container name. When the destination is the container URL, the storage account name will be parsed from the URL.
  - name: --pattern
    type: string
    short-summary: The pattern used for globbing files or blobs in the source. The supported patterns are '*', '?', '[seq]', and '[!seq]'. For more information, please refer to https://docs.python.org/3.7/library/fnmatch.html.
    long-summary: When you use '*' in --pattern, it will match any character including the the directory separator '/'.
  - name: --dryrun
    type: bool
    short-summary: Show the summary of the operations to be taken instead of actually uploading the file(s).
  - name: --if-match
    type: string
    short-summary: An ETag value, or the wildcard character (*). Specify this header to perform the operation only if the resource's ETag matches the value specified.
  - name: --if-none-match
    type: string
    short-summary: An ETag value, or the wildcard character (*).
    long-summary: Specify this header to perform the operation only if the resource's ETag does not match the value specified. Specify the wildcard character (*) to perform the operation only if the resource does not exist, and fail the operation if it does exist.
  - name: --validate-content
    short-summary: Specifies that an MD5 hash shall be calculated for each chunk of the blob and verified by the service when the chunk has arrived.
  - name: --type -t
    short-summary: Defaults to 'page' for *.vhd files, or 'block' otherwise. The setting will override blob types for every file.
  - name: --maxsize-condition
    short-summary: The max length in bytes permitted for an append blob.
  - name: --lease-id
    short-summary: The active lease id for the blob
examples:
  - name: Upload all files that end with .py unless blob exists and has been modified since given date.
    text: |
        az storage blob upload-batch -d mycontainer --account-name mystorageaccount --account-key 00000000 -s <path-to-directory> --pattern *.py --if-unmodified-since 2018-08-27T20:51Z
  - name: Upload all files from local path directory to a container named "mycontainer".
    text: |
        az storage blob upload-batch -d mycontainer -s <path-to-directory>
  - name: Upload all files with the format 'cli-2018-xx-xx.txt' or 'cli-2019-xx-xx.txt' in local path directory.
    text: |
        az storage blob upload-batch -d mycontainer -s <path-to-directory> --pattern cli-201[89]-??-??.txt
  - name: Upload all files with the format 'cli-201x-xx-xx.txt' except cli-2018-xx-xx.txt' and 'cli-2019-xx-xx.txt' in a container.
    text: |
        az storage blob upload-batch -d mycontainer -s <path-to-directory> --pattern cli-201[!89]-??-??.txt
"""

helps['storage blob download'] = """
type: command
short-summary: Download a blob to a file path.
examples:
  - name: Download a blob.
    text: az storage blob download -f /path/to/file -c mycontainer -n MyBlob
"""

helps['storage blob url'] = """
type: command
short-summary: Create the url to access a blob.
examples:
  - name: Create the url to access a blob (autogenerated)
    text: |
        az storage blob url --connection-string $connectionString --container-name container1 --name blob1
    crafted: true
  - name: Create the url to access a blob (autogenerated)
    text: |
        az storage blob url --account-name storageacct --account-key 00000000 --container-name container1 --name blob1
    crafted: true
"""

helps['storage container-rm'] = """
type: group
short-summary: Manage Azure containers using the Microsoft.Storage resource provider.
"""

helps['storage container-rm create'] = """
type: command
short-summary: Create a new container under the specified storage account.
examples:
  - name: Create a new container under the specified storage account.
    text: az storage container-rm create --storage-account myaccount --name mycontainer
  - name: Create a new container with metadata and public-access as blob under the specified storage account(account id).
    text: az storage container-rm create --storage-account myaccountid --name mycontainer --public-access blob --metada key1=value1 key2=value2
"""

helps['storage container-rm delete'] = """
type: command
short-summary: Delete the specified container under its account.
examples:
  - name: Delete the specified container under its account.
    text: az storage container-rm delete --storage-account myAccount --name mycontainer
  - name: Delete the specified container under its account(account id).
    text: az storage container-rm delete --storage-account myaccountid --name mycontainer
  - name: Delete the specified container by resource id.
    text: az storage container-rm delete --ids mycontainerid
"""

helps['storage container-rm exists'] = """
type: command
short-summary: Check for the existence of a container.
examples:
  - name: Check for the existence of a container under the specified storage account.
    text: az storage container-rm exists --storage-account myaccount --name mycontainer
  - name: Check for the existence of a container under the specified storage account(account id).
    text: az storage container-rm exists --storage-account myaccountid --name mycontainer
  - name: Check for the existence of a container by resource id.
    text: az storage container-rm exists --ids mycontainerid
"""

helps['storage container-rm list'] = """
type: command
short-summary: List all containers under the specified storage account.
examples:
  - name: List all containers under the specified storage account.
    text: az storage container-rm list --storage-account myaccount
  - name: List all containers under the specified storage account(account id).
    text: az storage container-rm list --storage-account myaccountid
  - name: List all containers under the specified storage account, including deleted ones.
    text: az storage container-rm list --storage-account myaccount --include-deleted
"""

helps['storage container-rm migrate-vlw'] = """
type: command
short-summary: Migrate a blob container from container level WORM to object level immutability enabled container.
examples:
  - name: Migrate a blob container from container level WORM to object level immutability enabled container.
    text: az storage container-rm migrate-vlw -n mycontainer --storage-account myaccount -g myresourcegroup
  - name: Migrate a blob container from container level WORM to object level immutability enabled container without waiting.
    text: |
        az storage container-rm migrate-vlw -n mycontainer --storage-account myaccount -g myresourcegroup --no-wait
        az storage container-rm show -n mycontainer --storage-account myaccount -g myresourcegroup  --query immutableStorageWithVersioning.migrationState
"""

helps['storage container-rm show'] = """
type: command
short-summary: Show the properties for a specified container.
examples:
  - name: Show the properties for a container under the specified storage account.
    text: az storage container-rm show --storage-account myaccount --name mycontainer
  - name: Show the properties for a container under the specified storage account(account id).
    text: az storage container-rm show --storage-account myaccountid --name mycontainer
  - name: Show the properties for a container by resource id.
    text: az storage container-rm show --ids mycontainerid
"""

helps['storage container-rm update'] = """
type: command
short-summary: Update the properties for a container.
examples:
  - name: Update the public access level to 'blob' for a container under the specified storage account.
    text: az storage container-rm update --storage-account myaccount --name mycontainer --public-access blob
  - name: Update the metadata for a container under the specified storage account(account id).
    text: az storage container-rm update --storage-account myaccountid --name mycontainer --metadata newkey1=newvalue1 newkey2=newvalue2
  - name: Update the default encryption scope for a container by resource id.
    text: az storage container-rm update --ids mycontainerid --default-encryption-scope myencryptionscope
"""

helps['storage container'] = """
type: group
short-summary: Manage blob storage containers.
long-summary: >
    Please specify one of the following authentication parameters for your commands: --auth-mode, --account-key,
    --connection-string, --sas-token. You also can use corresponding environment variables to store your authentication
    credentials, e.g. AZURE_STORAGE_KEY, AZURE_STORAGE_CONNECTION_STRING and AZURE_STORAGE_SAS_TOKEN.
"""

helps['storage container create'] = """
type: command
short-summary: Create a container in a storage account.
long-summary: >
    By default, container data is private ("off") to the account owner. Use "blob" to allow public read access for blobs.
    Use "container" to allow public read and list access to the entire container.
    You can configure the --public-access using `az storage container set-permission -n CONTAINER_NAME --public-access blob/container/off`.
examples:
  - name: Create a storage container in a storage account.
    text: az storage container create -n mystoragecontainer
  - name: Create a storage container in a storage account and return an error if the container already exists.
    text: az storage container create -n mystoragecontainer --fail-on-exist
  - name: Create a storage container in a storage account and allow public read access for blobs.
    text: az storage container create -n mystoragecontainer --public-access blob
"""

helps['storage container delete'] = """
type: command
short-summary: Mark the specified container for deletion.
long-summary: >
    The container and any blobs contained within it are later deleted during garbage collection.
examples:
  - name: Marks the specified container for deletion. (autogenerated)
    text: |
        az storage container delete --account-key 00000000 --account-name MyAccount --name mycontainer
    crafted: true
"""

helps['storage container exists'] = """
type: command
short-summary: Check for the existence of a storage container.
examples:
  - name: Check for the existence of a storage container. (autogenerated)
    text: |
        az storage container exists --account-name mystorageccount --account-key 00000000 --name mycontainer
    crafted: true
"""

helps['storage container generate-sas'] = """
type: command
short-summary: Generate a SAS token for a storage container.
examples:
  - name: Generate a sas token for blob container and use it to upload a blob.
    text: |
        end=`date -u -d "30 minutes" '+%Y-%m-%dT%H:%MZ'`
        sas=`az storage container generate-sas -n mycontainer --https-only --permissions dlrw --expiry $end -o tsv`
        az storage blob upload -n MyBlob -c mycontainer -f file.txt --sas-token $sas
  - name: Generate a shared access signature for the container (autogenerated)
    text: |
        az storage container generate-sas --account-key 00000000 --account-name mystorageaccount --expiry 2020-01-01 --name mycontainer --permissions dlrw
    crafted: true
  - name: Generate a SAS token for a storage container. (autogenerated)
    text: |
        az storage container generate-sas --account-name mystorageaccount --as-user --auth-mode login --expiry 2020-01-01 --name container1 --permissions dlrw
    crafted: true
"""

helps['storage container show'] = """
type: command
short-summary: Return all user-defined metadata and system properties for the specified container.
"""

helps['storage container show-permission'] = """
type: command
short-summary: Get the permissions for the specified container.
"""

helps['storage container set-permission'] = """
type: command
short-summary: Set the permissions for the specified container.
"""

helps['storage container immutability-policy'] = """
type: group
short-summary: Manage container immutability policies.
"""

helps['storage container immutability-policy create'] = """
type: command
short-summary: Create or update an unlocked immutability policy.
"""

helps['storage container immutability-policy extend'] = """
type: command
short-summary: Extend the immutabilityPeriodSinceCreationInDays of a locked immutabilityPolicy.
"""

helps['storage container lease'] = """
type: group
short-summary: Manage blob storage container leases.
"""

helps['storage container lease acquire'] = """
type: command
short-summary: Request a new lease.
long-summary: If the container does not have an active lease, the Blob service creates a lease on the container and returns a new lease ID.
examples:
  - name: Request a new lease.
    text: az storage container lease acquire --container-name mycontainer --account-name mystorageaccount --account-key 0000-0000
"""

helps['storage container lease renew'] = """
type: command
short-summary: Renew the lease.
long-summary: The lease can be renewed if the lease ID specified matches that associated with the
        container. Note that the lease may be renewed even if it has expired as long as the
        container has not been leased again since the expiration of that lease. When you renew a
        lease, the lease duration clock resets.
examples:
  - name: Renew the lease.
    text: az storage container lease renew -c mycontainer --lease-id "32fe23cd-4779-4919-adb3-357e76c9b1bb" --account-name mystorageaccount --account-key 0000-0000
"""

helps['storage container lease break'] = """
type: command
short-summary: Break the lease, if the container has an active lease.
long-summary: Once a lease is broken, it cannot be renewed. Any authorized request can break the lease;
        the request is not required to specify a matching lease ID. When a lease is broken, the
        lease break period is allowed to elapse, during which time no lease operation except break
        and release can be performed on the container. When a lease is successfully broken, the
        response indicates the interval in seconds until a new lease can be acquired.
examples:
  - name: Break the lease.
    text: az storage container lease break -c mycontainer --lease-break-period 10 --account-name mystorageaccount --account-key 0000-0000
"""

helps['storage container lease change'] = """
type: command
short-summary: Change the lease ID of an active lease.
long-summary: A change must include the current lease ID and a new lease ID.
examples:
  - name: Change the lease.
    text: az storage container lease change -c mycontainer --lease-id "32fe23cd-4779-4919-adb3-357e76c9b1bb" --proposed-lease-id "sef2ef2d-4779-4919-adb3-357e76c9b1bb" --account-name mystorageaccount --account-key 0000-0000
"""

helps['storage container lease release'] = """
type: command
short-summary: Release the lease.
long-summary: The lease may be released if the lease_id specified matches that associated with the
        container. Releasing the lease allows another client to immediately acquire the lease for
        the container as soon as the release is complete.
examples:
  - name: Release the lease.
    text: az storage container lease release -c mycontainer --lease-id "32fe23cd-4779-4919-adb3-357e76c9b1bb" --account-name mystorageaccount --account-key 0000-0000
"""


helps['storage container legal-hold'] = """
type: group
short-summary: Manage container legal holds.
"""

helps['storage container legal-hold clear'] = """
type: command
short-summary: Clear legal hold tags.
examples:
  - name: Clear legal hold tags.
    text: |
        az storage container legal-hold clear --tags tag1 tag2 --container-name mycontainer --account-name mystorageccount -g MyResourceGroup
"""

helps['storage container legal-hold set'] = """
type: command
short-summary: Set legal hold tags.
examples:
  - name: Set legal hold tags.
    text: |
        az storage container legal-hold set --tags tag1 tag2 --container-name mycontainer --account-name mystorageccount -g MyResourceGroup
"""

helps['storage container legal-hold show'] = """
type: command
short-summary: Get the legal hold properties of a container.
examples:
  - name: Get the legal hold properties of a container. (autogenerated)
    text: |
        az storage container legal-hold show --account-name mystorageccount --container-name mycontainer
    crafted: true
"""

helps['storage container list'] = """
type: command
short-summary: List containers in a storage account.
examples:
  - name: List containers in a storage account.
    text: az storage container list
  - name: List soft deleted containers in a storage account.
    text: az storage container list --include-deleted
"""

helps['storage container metadata'] = """
type: group
short-summary: Manage container metadata.
"""

helps['storage container metadata show'] = """
type: command
short-summary: Return all user-defined metadata for the specified container.
"""

helps['storage container metadata update'] = """
type: command
short-summary: Set one or more user-defined name-value pairs for the specified container.
"""

helps['storage container policy'] = """
type: group
short-summary: Manage container stored access policies.
"""

helps['storage container restore'] = """
type: command
short-summary: Restore soft-deleted container.
long-summary:  Operation will only be successful if used within the specified number of days set in the delete retention policy.
examples:
  - name: List and restore soft-deleted container.
    text: |
          az storage container list --include-deleted
          az storage container restore -n deletedcontainer --deleted-version deletedversion
"""

helps['storage copy'] = """
type: command
short-summary: Copy files or directories to or from Azure storage.
examples:
  - name: Upload a single file to Azure Blob using url.
    text: az storage copy -s /path/to/file.txt -d https://[account].blob.core.windows.net/[container]/[path/to/blob]
  - name: Upload a single file to Azure Blob using account name and container name.
    text: az storage copy -s /path/to/file.txt --destination-account-name mystorageaccount --destination-container mycontainer
  - name: Upload a single file to Azure Blob with MD5 hash of the file content and save it as the blob's Content-MD5 property.
    text: az storage copy -s /path/to/file.txt -d https://[account].blob.core.windows.net/[container]/[path/to/blob] --put-md5
  - name: Upload an entire directory to Azure Blob using url.
    text: az storage copy -s /path/to/dir -d https://[account].blob.core.windows.net/[container]/[path/to/directory] --recursive
  - name: Upload an entire directory to Azure Blob using account name and container name.
    text: az storage copy -s /path/to/dir --destination-account-name mystorageaccount --destination-container mycontainer --recursive
  - name: Upload a set of files to Azure Blob using wildcards with url.
    text: az storage copy -s /path/*foo/*bar/*.pdf -d https://[account].blob.core.windows.net/[container]/[path/to/directory]
  - name: Upload a set of files to Azure Blob using wildcards with account name and container name.
    text: az storage copy -s /path/*foo/*bar/*.pdf --destination-account-name mystorageaccount --destination-container mycontainer
  - name: Upload files and directories to Azure Blob using wildcards with url.
    text: az storage copy -s /path/*foo/*bar* -d https://[account].blob.core.windows.net/[container]/[path/to/directory] --recursive
  - name: Upload files and directories to Azure Blob using wildcards with account name and container name.
    text: az storage copy -s /path/*foo/*bar* --destination-account-name mystorageaccount --destination-container mycontainer --recursive
  - name: Download a single file from Azure Blob using url, and you can also specify your storage account and container information as above.
    text: az storage copy -s https://[account].blob.core.windows.net/[container]/[path/to/blob] -d /path/to/file.txt
  - name: Download an entire directory from Azure Blob, and you can also specify your storage account and container information as above.
    text: az storage copy -s https://[account].blob.core.windows.net/[container]/[path/to/directory] -d /path/to/dir --recursive
  - name: Download a subset of containers within a storage account by using a wildcard symbol (*) in the container name, and you can also specify your storage account and container information as above.
    text: az storage copy -s https://[account].blob.core.windows.net/[container*name] -d /path/to/dir --recursive
  - name: Download a subset of files from Azure Blob. (Only jpg files and file names don't start with test will be included.)
    text: az storage copy -s https://[account].blob.core.windows.net/[container] --include-pattern "*.jpg" --exclude-pattern test* -d /path/to/dir --recursive
  - name: Copy a single blob to another blob, and you can also specify the storage account and container information of source and destination as above.
    text: az storage copy -s https://[srcaccount].blob.core.windows.net/[container]/[path/to/blob] -d https://[destaccount].blob.core.windows.net/[container]/[path/to/blob]
  - name: Copy an entire account data from blob account to another blob account, and you can also specify the storage account and container information of source and destination as above.
    text: az storage copy -s https://[srcaccount].blob.core.windows.net -d https://[destaccount].blob.core.windows.net --recursive
  - name: Copy a single object from S3 with access key to blob, and you can also specify your storage account and container information as above.
    text: az storage copy -s https://s3.amazonaws.com/[bucket]/[object] -d https://[destaccount].blob.core.windows.net/[container]/[path/to/blob]
  - name: Copy an entire directory from S3 with access key to blob virtual directory, and you can also specify your storage account and container information as above.
    text: az storage copy -s https://s3.amazonaws.com/[bucket]/[folder] -d https://[destaccount].blob.core.windows.net/[container]/[path/to/directory] --recursive
  - name: Copy all buckets in S3 service with access key to blob account, and you can also specify your storage account information as above.
    text: az storage copy -s https://s3.amazonaws.com/ -d https://[destaccount].blob.core.windows.net --recursive
  - name: Copy all buckets in a S3 region with access key to blob account, and you can also specify your storage account information as above.
    text: az storage copy -s https://s3-[region].amazonaws.com/ -d https://[destaccount].blob.core.windows.net --recursive
  - name: Upload a single file to Azure File Share using url.
    text: az storage copy -s /path/to/file.txt -d https://[account].file.core.windows.net/[share]/[path/to/file]
  - name: Upload a single file to Azure File Share using account name and share name.
    text: az storage copy -s /path/to/file.txt --destination-account-name mystorageaccount --destination-share myshare
  - name: Upload an entire directory to Azure File Share using url.
    text: az storage copy -s /path/to/dir -d https://[account].file.core.windows.net/[share]/[path/to/directory] --recursive
  - name: Upload an entire directory to Azure File Share using account name and container name.
    text: az storage copy -s /path/to/dir --destination-account-name mystorageaccount --destination-share myshare --recursive
  - name: Upload a set of files to Azure File Share using wildcards with account name and share name.
    text: az storage copy -s /path/*foo/*bar/*.pdf --destination-account-name mystorageaccount --destination-share myshare
  - name: Upload files and directories to Azure File Share using wildcards with url.
    text: az storage copy -s /path/*foo/*bar* -d https://[account].file.core.windows.net/[share]/[path/to/directory] --recursive
  - name: Upload files and directories to Azure File Share using wildcards with account name and share name.
    text: az storage copy -s /path/*foo/*bar* --destination-account-name mystorageaccount --destination-share myshare --recursive
  - name: Download a single file from Azure File Share using url, and you can also specify your storage account and share information as above.
    text: az storage copy -s https://[account].file.core.windows.net/[share]/[path/to/file] -d /path/to/file.txt
  - name: Download an entire directory from Azure File Share, and you can also specify your storage account and share information as above.
    text: az storage copy -s https://[account].file.core.windows.net/[share]/[path/to/directory] -d /path/to/dir --recursive
  - name: Download a set of files from Azure File Share using wildcards, and you can also specify your storage account and share information as above.
    text: az storage copy -s https://[account].file.core.windows.net/[share]/ --include-pattern foo* -d /path/to/dir --recursive
  - name: Upload a single file to Azure Blob using url with azcopy options pass-through.
    text: az storage copy -s /path/to/file.txt -d https://[account].blob.core.windows.net/[container]/[path/to/blob] -- --block-size-mb=0.25 --check-length
"""

helps['storage cors'] = """
type: group
short-summary: Manage storage service Cross-Origin Resource Sharing (CORS).
"""

helps['storage cors add'] = """
type: command
short-summary: Add a CORS rule to a storage account.
parameters:
  - name: --services
    short-summary: >
        The storage service(s) to add rules to. Allowed options are: (b)lob, (f)ile,
        (q)ueue, (t)able. Can be combined.
  - name: --max-age
    short-summary: The maximum number of seconds the client/browser should cache a preflight response.
  - name: --origins
    short-summary: Space-separated list of origin domains that will be allowed via CORS, or '*' to allow all domains.
  - name: --methods
    short-summary: Space-separated list of HTTP methods allowed to be executed by the origin.
  - name: --allowed-headers
    short-summary: Space-separated list of response headers allowed to be part of the cross-origin request.
  - name: --exposed-headers
    short-summary: Space-separated list of response headers to expose to CORS clients.
"""

helps['storage cors clear'] = """
type: command
short-summary: Remove all CORS rules from a storage account.
parameters:
  - name: --services
    short-summary: >
        The storage service(s) to remove rules from. Allowed options are: (b)lob, (f)ile,
        (q)ueue, (t)able. Can be combined.
examples:
  - name: Remove all CORS rules from a storage account. (autogenerated)
    text: |
        az storage cors clear --account-name MyAccount --services bfqt
    crafted: true
"""

helps['storage cors list'] = """
type: command
short-summary: List all CORS rules for a storage account.
parameters:
  - name: --services
    short-summary: >
        The storage service(s) to list rules for. Allowed options are: (b)lob, (f)ile,
        (q)ueue, (t)able. Can be combined.
examples:
  - name: List all CORS rules for a storage account. (autogenerated)
    text: |
        az storage cors list --account-key 00000000 --account-name mystorageaccount
    crafted: true
"""

helps['storage directory'] = """
type: group
short-summary: Manage file storage directories.
"""

helps['storage directory exists'] = """
type: command
short-summary: Check for the existence of a storage directory.
examples:
  - name: Check for the existence of a storage directory. (autogenerated)
    text: |
        az storage directory exists --account-key 00000000 --account-name MyAccount --name MyDirectory --share-name MyShare
    crafted: true
"""

helps['storage directory list'] = """
type: command
short-summary: List directories in a share.
examples:
  - name: List directories in a share. (autogenerated)
    text: |
        az storage directory list --account-key 00000000 --account-name MyAccount --share-name MyShare
    crafted: true
"""

helps['storage directory metadata'] = """
type: group
short-summary: Manage file storage directory metadata.
"""

helps['storage entity'] = """
type: group
short-summary: Manage table storage entities.
"""

helps['storage entity insert'] = """
type: command
short-summary: Insert an entity into a table.
parameters:
  - name: --table-name -t
    type: string
    short-summary: The name of the table to insert the entity into.
  - name: --entity -e
    type: list
    short-summary: Space-separated list of key=value pairs. Must contain a PartitionKey and a RowKey.
    long-summary: The PartitionKey and RowKey must be unique within the table, and may be up to 64Kb in size. If using an integer value as a key, convert it to a fixed-width string which can be canonically sorted. For example, convert the integer value 1 to the string value "0000001" to ensure proper sorting.
  - name: --if-exists
    type: string
    short-summary: Behavior when an entity already exists for the specified PartitionKey and RowKey.
examples:
  - name: Insert an entity into a table. (autogenerated)
    text: |
        az storage entity insert --connection-string $connectionString --entity PartitionKey=AAA RowKey=BBB Content=ASDF2 --if-exists fail --table-name MyTable
    crafted: true
"""

helps['storage entity merge'] = """
type: command
short-summary: Update an existing entity by merging the entity's properties.
"""

helps['storage entity replace'] = """
type: command
short-summary: Update an existing entity in a table.
"""

helps['storage entity query'] = """
type: command
short-summary: List entities which satisfy a query.
parameters:
  - name: --marker
    type: list
    short-summary: Space-separated list of key=value pairs. Must contain a nextpartitionkey and a nextrowkey.
    long-summary: This value can be retrieved from the next_marker field of a previous generator object if max_results was specified and that generator has finished enumerating results. If specified, this generator will begin returning results from the point where the previous generator stopped.
examples:
  - name: List entities which satisfy a query. (autogenerated)
    text: |
        az storage entity query --table-name MyTable
    crafted: true
"""

helps['storage entity delete'] = """
type: command
short-summary: Delete an existing entity in a table.
"""

helps['storage file'] = """
type: group
short-summary: Manage file shares that use the SMB 3.0 protocol.
"""

helps['storage file copy'] = """
type: group
short-summary: Manage file copy operations.
"""

helps['storage file copy start'] = """
type: command
short-summary: Copy a file asynchronously.
examples:
    - name: Copy a file asynchronously.
      text: |
        az storage file copy start --source-account-name srcaccount --source-account-key 00000000 --source-path <srcpath-to-file> --source-share srcshare --destination-path <destpath-to-file> --destination-share destshare --account-name destaccount --account-key 00000000
    - name: Copy a file asynchronously from source uri to destination storage account with sas token.
      text: |
        az storage file copy start --source-uri "https://srcaccount.file.core.windows.net/myshare/mydir/myfile?<sastoken>" --destination-path <destpath-to-file> --destination-share destshare --account-name destaccount --sas-token <destination-sas>
    - name: Copy a file asynchronously from file snapshot to destination storage account with sas token.
      text: |
        az storage file copy start --source-account-name srcaccount --source-account-key 00000000 --source-path <srcpath-to-file> --source-share srcshare --file-snapshot "2020-03-02T13:51:54.0000000Z" --destination-path <destpath-to-file> --destination-share destshare --account-name destaccount --sas-token <destination-sas>
"""

helps['storage file copy start-batch'] = """
type: command
short-summary: Copy multiple files or blobs to a file share.
parameters:
  - name: --destination-share
    type: string
    short-summary: The file share where the source data is copied to.
  - name: --destination-path
    type: string
    short-summary: The directory where the source data is copied to. If omitted, data is copied to the root directory.
  - name: --pattern
    type: string
    short-summary: The pattern used for globbing files and blobs. The supported patterns are '*', '?', '[seq]', and '[!seq]'. For more information, please refer to https://docs.python.org/3.7/library/fnmatch.html.
    long-summary: When you use '*' in --pattern, it will match any character including the the directory separator '/'.
  - name: --dryrun
    type: bool
    short-summary: List the files and blobs to be copied. No actual data transfer will occur.
  - name: --source-account-name
    type: string
    short-summary: The source storage account to copy the data from. If omitted, the destination account is used.
  - name: --source-account-key
    type: string
    short-summary: The account key for the source storage account. If omitted, the active login is used to determine the account key.
  - name: --source-container
    type: string
    short-summary: The source container blobs are copied from.
  - name: --source-share
    type: string
    short-summary: The source share files are copied from.
  - name: --source-uri
    type: string
    short-summary: A URI that specifies a the source file share or blob container.
    long-summary: If the source is in another account, the source must either be public or authenticated via a shared access signature.
  - name: --source-sas
    type: string
    short-summary: The shared access signature for the source storage account.
examples:
  - name: Copy all files in a file share to another storage account.
    text: |
        az storage file copy start-batch --source-account-name srcaccount --source-account-key 00000000 --source-share srcshare --destination-path <destpath-to-directory> --destination-share destshare --account-name destaccount --account-key 00000000
  - name: Copy all files in a file share to another storage account. with sas token.
    text: |
        az storage file copy start-batch --source-uri "https://srcaccount.file.core.windows.net/myshare?<sastoken>" --destination-path <destpath-to-directory> --destination-share destshare --account-name destaccount --sas-token <destination-sas>
"""

helps['storage file delete-batch'] = """
type: command
short-summary: Delete files from an Azure Storage File Share.
parameters:
  - name: --source -s
    type: string
    short-summary: The source of the file delete operation. The source can be the file share URL or the share name.
  - name: --pattern
    type: string
    short-summary: The pattern used for file globbing. The supported patterns are '*', '?', '[seq]', and '[!seq]'. For more information, please refer to https://docs.python.org/3.7/library/fnmatch.html.
    long-summary: When you use '*' in --pattern, it will match any character including the the directory separator '/'.
  - name: --dryrun
    type: bool
    short-summary: List the files and blobs to be deleted. No actual data deletion will occur.
examples:
  - name: Delete files from an Azure Storage File Share. (autogenerated)
    text: |
        az storage file delete-batch --account-key 00000000 --account-name MyAccount --source /path/to/file
    crafted: true
  - name: Delete files from an Azure Storage File Share. (autogenerated)
    text: |
        az storage file delete-batch --account-key 00000000 --account-name MyAccount --pattern *.py --source /path/to/file
    crafted: true
"""

helps['storage file download-batch'] = """
type: command
short-summary: Download files from an Azure Storage File Share to a local directory in a batch operation.
parameters:
  - name: --source -s
    type: string
    short-summary: The source of the file download operation. The source can be the file share URL or the share name.
  - name: --destination -d
    type: string
    short-summary: The local directory where the files are downloaded to. This directory must already exist.
  - name: --pattern
    type: string
    short-summary: The pattern used for file globbing. The supported patterns are '*', '?', '[seq]', and '[!seq]'. For more information, please refer to https://docs.python.org/3.7/library/fnmatch.html.
    long-summary: When you use '*' in --pattern, it will match any character including the the directory separator '/'.
  - name: --dryrun
    type: bool
    short-summary: List the files and blobs to be downloaded. No actual data transfer will occur.
  - name: --max-connections
    type: integer
    short-summary: The maximum number of parallel connections to use. Default value is 1.
  - name: --snapshot
    type: string
    short-summary: A string that represents the snapshot version, if applicable.
  - name: --validate-content
    type: bool
    short-summary: If set, calculates an MD5 hash for each range of the file for validation.
    long-summary: >
        The storage service checks the hash of the content that has arrived is identical to the hash that was sent.
        This is mostly valuable for detecting bitflips during transfer if using HTTP instead of HTTPS. This hash is not stored.
examples:
  - name: Download files from an Azure Storage File Share to a local directory in a batch operation. (autogenerated)
    text: |
        az storage file download-batch --account-key 00000000 --account-name MyAccount --destination . --no-progress --source /path/to/file
    crafted: true
"""

helps['storage file exists'] = """
type: command
short-summary: Check for the existence of a file.
examples:
  - name: Check for the existence of a file. (autogenerated)
    text: |
        az storage file exists --account-key 00000000 --account-name MyAccount --path path/file.txt --share-name MyShare
    crafted: true
  - name: Check for the existence of a file. (autogenerated)
    text: |
        az storage file exists --connection-string $connectionString --path path/file.txt --share-name MyShare
    crafted: true
"""

helps['storage file generate-sas'] = """
type: command
examples:
  - name: Generate a sas token for a file.
    text: |
        end=`date -u -d "30 minutes" '+%Y-%m-%dT%H:%MZ'`
        az storage file generate-sas -p path/file.txt -s MyShare --account-name MyStorageAccount --permissions rcdw --https-only --expiry $end
  - name: Generate a shared access signature for the file. (autogenerated)
    text: |
        az storage file generate-sas --account-name MyStorageAccount --expiry 2037-12-31T23:59:00Z --path path/file.txt --permissions rcdw --share-name MyShare --start 2019-01-01T12:20Z
    crafted: true
  - name: Generate a shared access signature for the file. (autogenerated)
    text: |
        az storage file generate-sas --account-key 00000000 --account-name mystorageaccount --expiry 2037-12-31T23:59:00Z --https-only --path path/file.txt --permissions rcdw --share-name myshare
    crafted: true
"""

helps['storage file list'] = """
type: command
short-summary: List files and directories in a share.
parameters:
  - name: --exclude-dir
    type: bool
    short-summary: List only files in the given share.
examples:
  - name: List files and directories in a share. (autogenerated)
    text: |
        az storage file list --share-name MyShare
    crafted: true
"""

helps['storage file metadata'] = """
type: group
short-summary: Manage file metadata.
"""

helps['storage file upload'] = """
type: command
short-summary: Upload a file to a share that uses the SMB 3.0 protocol.
long-summary: Creates or updates an Azure file from a source path with automatic chunking and progress notifications.
examples:
  - name: Upload to a local file to a share.
    text: az storage file upload -s MyShare --source /path/to/file
  - name: Upload a file to a share that uses the SMB 3.0 protocol. (autogenerated)
    text: |
        az storage file upload --account-key 00000000 --account-name MyStorageAccount --path path/file.txt --share-name MyShare --source /path/to/file
    crafted: true
"""

helps['storage file upload-batch'] = """
type: command
short-summary: Upload files from a local directory to an Azure Storage File Share in a batch operation.
parameters:
  - name: --source -s
    type: string
    short-summary: The directory to upload files from.
  - name: --destination -d
    type: string
    short-summary: The destination of the upload operation.
    long-summary: The destination can be the file share URL or the share name. When the destination is the share URL, the storage account name is parsed from the URL.
  - name: --destination-path
    type: string
    short-summary: The directory where the source data is copied to. If omitted, data is copied to the root directory.
  - name: --pattern
    type: string
    short-summary: The pattern used for file globbing. The supported patterns are '*', '?', '[seq]', and '[!seq]'. For more information, please refer to https://docs.python.org/3.7/library/fnmatch.html.
    long-summary: When you use '*' in --pattern, it will match any character including the the directory separator '/'.
  - name: --dryrun
    type: bool
    short-summary: List the files and blobs to be uploaded. No actual data transfer will occur.
  - name: --max-connections
    type: integer
    short-summary: The maximum number of parallel connections to use. Default value is 1.
  - name: --validate-content
    type: bool
    short-summary: If set, calculates an MD5 hash for each range of the file for validation.
    long-summary: >
        The storage service checks the hash of the content that has arrived is identical to the hash that was sent.
        This is mostly valuable for detecting bitflips during transfer if using HTTP instead of HTTPS. This hash is not stored.
examples:
  - name: Upload files from a local directory to an Azure Storage File Share in a batch operation.
    text: |
        az storage file upload-batch --destination myshare --source . --account-name myaccount --account-key 00000000
  - name: Upload files from a local directory to an Azure Storage File Share with url in a batch operation.
    text: |
        az storage file upload-batch --destination https://myaccount.file.core.windows.net/myshare --source . --account-key 00000000
"""

helps['storage file url'] = """
type: command
short-summary: Create the url to access a file.
examples:
  - name: Create the url to access a file. (autogenerated)
    text: |
        az storage file url --account-key 00000000 --account-name mystorageaccount --path path/file.txt --share-name myshare
    crafted: true
"""

helps['storage fs'] = """
type: group
short-summary: Manage file systems in Azure Data Lake Storage Gen2 account.
"""

helps['storage fs access'] = """
type: group
short-summary: Manage file system access and permissions for Azure Data Lake Storage Gen2 account.
"""

helps['storage fs access remove-recursive'] = """
type: command
short-summary: Remove the Access Control on a path and sub-paths in Azure Data Lake Storage Gen2 account.
parameters:
    - name: --acl
      short-summary: Remove POSIX access control rights on files and directories. The value is a comma-separated
        list of access control entries. Each access control entry (ACE) consists of a scope, a type, and a user or
        group identifier in the format "[scope:][type]:[id]".
examples:
    - name: Remove the Access Control on a path and sub-paths in Azure Data Lake Storage Gen2 account.
      text: az storage fs access remove-recursive --acl "default:user:21cd756e-e290-4a26-9547-93e8cc1a8923" -p dir -f myfilesystem --account-name myadlsaccount --account-key 0000-0000
"""

helps['storage fs access set'] = """
type: command
short-summary: Set the access control properties of a path(directory or file) in Azure Data Lake Storage Gen2 account.
parameters:
    - name: --acl
      short-summary: Invalid in conjunction with acl. POSIX access control rights on files and directories in the format "[scope:][type]:[id]:[permissions]". e.g. "user::rwx,group::r--,other::---,mask::rwx".
      long-summary: >
        The value is a comma-separated list of access control entries. Each access control entry (ACE) consists of a scope,
        a type, a user or group identifier, and permissions in the format "[scope:][type]:[id]:[permissions]".
        The scope must be "default" to indicate the ACE belongs to the default ACL for a directory;
        otherwise scope is implicit and the ACE belongs to the access ACL. There are four ACE types:
        "user" grants rights to the owner or a named user, "group" grants rights to the owning group
        or a named group, "mask" restricts rights granted to named users and the members of groups,
        and "other" grants rights to all users not found in any of the other entries.
        The user or group identifier is omitted for entries of type "mask" and "other".
        The user or group identifier is also omitted for the owner and owning group.
        For example, the following ACL grants read, write, and execute rights to the file owner an
        john.doe@contoso, the read right to the owning group, and nothing to everyone else:
        "user::rwx,user:john.doe@contoso:rwx,group::r--,other::---,mask::rwx".
        For more information, please refer to https://docs.microsoft.com/azure/storage/blobs/data-lake-storage-access-control.
    - name: --permissions
      short-summary: >
        Invalid in conjunction with acl. POSIX access permissions for the file owner, the file owning group, and others.
        Each class may be granted read(r), write(w), or execute(x) permission. Both symbolic (rwxrw-rw-) and 4-digit octal
        notation (e.g. 0766) are supported.'
    - name: --owner
      short-summary: >
        The owning user of the file or directory. The user Azure Active Directory object ID or user principal name to
        set as the owner. For more information, please refer to
        https://docs.microsoft.com/azure/storage/blobs/data-lake-storage-access-control#the-owning-user.
    - name: --group
      short-summary: >
        The owning group of the file or directory. The group Azure Active Directory object ID or user principal name to
        set as the owning group. For more information, please refer to
        https://docs.microsoft.com/azure/storage/blobs/data-lake-storage-access-control#changing-the-owning-group.
examples:
    - name: Set the access control list of a path.
      text: az storage fs access set --acl "user::rwx,group::r--,other::---" -p dir -f myfilesystem --account-name mystorageaccount --account-key 0000-0000
    - name: Set permissions of a path.
      text: az storage fs access set --permissions "rwxrwx---" -p dir -f myfilesystem --account-name mystorageaccount --account-key 0000-0000
    - name: Set owner of a path.
      text: az storage fs access set --owner example@microsoft.com -p dir -f myfilesystem --account-name mystorageaccount --account-key 0000-0000
    - name: Set owning group of a path.
      text: az storage fs access set --group 68390a19-a897-236b-b453-488abf67b4dc -p dir -f myfilesystem --account-name mystorageaccount --account-key 0000-0000
"""

helps['storage fs access set-recursive'] = """
type: command
short-summary: Set the Access Control on a path and sub-paths in Azure Data Lake Storage Gen2 account.
examples:
    - name: Set the Access Control on a path and sub-paths in Azure Data Lake Storage Gen2 account.
      text: az storage fs access set-recursive --acl "default:user:21cd756e-e290-4a26-9547-93e8cc1a8923:rwx" -p dir -f myfilesystem --account-name myadlsaccount --account-key 0000-0000
"""

helps['storage fs access show'] = """
type: command
short-summary: Show the access control properties of a path (directory or file) in Azure Data Lake Storage Gen2 account.
examples:
    - name: Show the access control properties of a path.
      text: az storage fs access show -p dir -f myfilesystem --account-name myadlsaccount --account-key 0000-0000
"""

helps['storage fs access update-recursive'] = """
type: command
short-summary: Modify the Access Control on a path and sub-paths in Azure Data Lake Storage Gen2 account.
examples:
    - name: Modify the Access Control on a path and sub-paths in Azure Data Lake Storage Gen2 account.
      text: az storage fs access update-recursive --acl "user::r-x" -p dir -f myfilesystem --account-name myadlsaccount --account-key 0000-0000
"""

helps['storage fs create'] = """
type: command
short-summary: Create file system for Azure Data Lake Storage Gen2 account.
examples:
  - name: Create file system for Azure Data Lake Storage Gen2 account.
    text: |
        az storage fs create -n fsname --account-name mystorageaccount --account-key 0000-0000
  - name: Create file system for Azure Data Lake Storage Gen2 account and enable public access.
    text: |
        az storage fs create -n fsname --public-access file --account-name mystorageaccount --account-key 0000-0000
  - name: Create file system for Azure Data Lake Storage Gen2 account. (autogenerated)
    text: |
        az storage fs create --account-name mystorageaccount --auth-mode login --name fsname
    crafted: true
"""

helps['storage fs delete'] = """
type: command
short-summary: Delete a file system in ADLS Gen2 account.
examples:
    - name: Delete a file system in ADLS Gen2 account.
      text: az storage fs delete -n myfilesystem --account-name myadlsaccount --account-key 0000-0000
"""

helps['storage fs exists'] = """
type: command
short-summary: Check for the existence of a file system in ADLS Gen2 account.
examples:
    - name: Check for the existence of a file system in ADLS Gen2 account.
      text: az storage fs exists -n myfilesystem --account-name myadlsaccount --account-key 0000-0000
"""

helps['storage fs generate-sas'] = """
type: command
short-summary: Generate a SAS token for file system in ADLS Gen2 account.
examples:
  - name: Generate a sas token for file system and use it to upload files.
    text: |
        end=`date -u -d "30 minutes" '+%Y-%m-%dT%H:%MZ'`
        az storage fs generate-sas -n myfilesystem --https-only --permissions dlrw --expiry $end -o tsv
"""

helps['storage fs list'] = """
type: command
short-summary: List file systems in ADLS Gen2 account.
examples:
    - name: List file systems in ADLS Gen2 account.
      text: az storage fs list --account-name myadlsaccount --account-key 0000-0000
"""

helps['storage fs show'] = """
type: command
short-summary: Show properties of file system in ADLS Gen2 account.
examples:
    - name: Show properties of file system in ADLS Gen2 account.
      text: az storage fs show -n myfilesystem --account-name myadlsaccount --account-key 0000-0000
    - name: Show properties of file system in ADLS Gen2 account. (autogenerated)
      text: |
          az storage fs show --account-name myadlsaccount --auth-mode login --name myfilesystem
      crafted: true
"""

helps['storage fs list-deleted-path'] = """
type: command
short-summary: List the deleted (file or directory) paths under the specified file system.
examples:
  - name: List the deleted (file or directory) paths under the specified file system..
    text: |
        az storage fs list-deleted-path -f myfilesystem --account-name mystorageccount --account-key 00000000
"""

helps['storage fs undelete-path'] = """
type: command
short-summary: Restore soft-deleted path.
long-summary: Operation will only be successful if used within the specified number of days set in the delete retention policy.
examples:
  - name: Restore soft-deleted path.
    text: |
        az storage fs undelete-path -f myfilesystem --deleted-path-name dir --deletion-id 0000 --account-name mystorageccount --account-key 00000000
"""

helps['storage fs service-properties'] = """
type: group
short-summary: Manage storage datalake service properties.
"""

helps['storage fs service-properties show'] = """
type: command
short-summary: Show the properties of a storage account's datalake service, including Azure Storage Analytics.
examples:
  - name: Show the properties of a storage account's datalake service
    text: |
        az storage fs service-properties show --account-name mystorageccount --account-key 00000000
"""

helps['storage fs service-properties update'] = """
type: command
short-summary: Update the properties of a storage account's datalake service, including Azure Storage Analytics.
examples:
  - name: Update the properties of a storage account's datalake service
    text: |
        az storage fs service-properties update --delete-retention --delete-retention-period 7 --account-name mystorageccount --account-key 00000000
"""

helps['storage fs directory'] = """
type: group
short-summary: Manage directories in Azure Data Lake Storage Gen2 account.
"""

helps['storage fs directory create'] = """
type: command
short-summary: Create a directory in ADLS Gen2 file system.
examples:
    - name: Create a directory in ADLS Gen2 file system.
      text: az storage fs directory create -n dir -f myfilesystem --account-name myadlsaccount --account-key 0000-0000
    - name: Create a directory in ADLS Gen2 file system through connection string.
      text: az storage fs directory create -n dir -f myfilesystem --connection-string myconnectionstring
"""

helps['storage fs directory delete'] = """
type: command
short-summary: Delete a directory in ADLS Gen2 file system.
examples:
    - name: Delete a directory in ADLS Gen2 file system.
      text: az storage fs directory delete -n dir -f myfilesystem --account-name myadlsaccount --account-key 0000-0000
    - name: Delete a directory in ADLS Gen2 file system. (autogenerated)
      text: |
          az storage fs directory delete --account-name myadlsaccount --auth-mode login --file-system myfilesystem --name dir --yes
      crafted: true
"""

helps['storage fs directory exists'] = """
type: command
short-summary: Check for the existence of a directory in ADLS Gen2 file system.
examples:
    - name: Check for the existence of a directory in ADLS Gen2 file system.
      text: az storage fs directory exists -n dir -f myfilesystem --account-name myadlsaccount --account-key 0000-0000
    - name: Check for the existence of a directory in ADLS Gen2 file system. (autogenerated)
      text: |
          az storage fs directory exists --account-name myadlsaccount --auth-mode login --file-system myfilesystem --name dir
      crafted: true
"""

helps['storage fs directory list'] = """
type: command
short-summary: List directories in ADLS Gen2 file system.
examples:
    - name: List directories in ADLS Gen2 file system.
      text: az storage fs directory list -f myfilesystem --account-name myadlsaccount --account-key 0000-0000
    - name: List directories in "dir/" for ADLS Gen2 file system.
      text: az storage fs directory list --path dir -f myfilesystem --account-name myadlsaccount --account-key 0000-0000
"""

helps['storage fs directory metadata'] = """
type: group
short-summary: Manage the metadata for directory in file system.
"""

helps['storage fs directory metadata show'] = """
type: command
short-summary: Return all user-defined metadata for the specified directory.
examples:
  - name: Return all user-defined metadata for the specified directory.
    text: az storage fs directory metadata show -n dir -f myfilesystem --account-name myadlsaccount --account-key 0000-0000
"""

helps['storage fs directory move'] = """
type: command
short-summary: Move a directory in ADLS Gen2 file system.
examples:
    - name: Move a directory a directory in ADLS Gen2 file system.
      text: az storage fs directory move --new-directory newfs/dir -n dir -f myfilesystem --account-name myadlsaccount --account-key 0000-0000
    - name: Move a directory in ADLS Gen2 file system. (autogenerated)
      text: |
          az storage fs directory move --account-name myadlsaccount --auth-mode login --file-system myfilesystem --name dir --new-directory newfs/dir
      crafted: true
"""

helps['storage fs directory show'] = """
type: command
short-summary: Show properties of a directory in ADLS Gen2 file system.
examples:
    - name: Show properties of a directory in ADLS Gen2 file system.
      text: az storage fs directory show -n dir -f myfilesystem --account-name myadlsaccount --account-key 0000-0000
    - name: Show properties of a subdirectory in ADLS Gen2 file system.
      text: az storage fs directory show -n dir/subdir -f myfilesystem --account-name myadlsaccount --account-key 0000-0000
    - name: Show properties of a directory in ADLS Gen2 file system. (autogenerated)
      text: |
          az storage fs directory show --account-name myadlsaccount --auth-mode login --file-system myfilesystem --name dir
      crafted: true
"""

helps['storage fs directory upload'] = """
    type: command
    short-summary: Upload files or subdirectories to a directory in ADLS Gen2 file system.
    examples:
        - name: Upload a single file to a storage blob directory.
          text: az storage fs directory upload -f myfilesystem --account-name mystorageaccount -s "path/to/file" -d directory
        - name: Upload a local directory to root directory in ADLS Gen2 file system.
          text: az storage fs directory upload -f myfilesystem --account-name mystorageaccount -s "path/to/directory" --recursive
        - name: Upload a local directory to a directory in ADLS Gen2 file system.
          text: az storage fs directory upload -f myfilesystem --account-name mystorageaccount -s "path/to/directory" -d directory --recursive
        - name: Upload a set of files in a local directory to a directory in ADLS Gen2 file system.
          text: az storage fs directory upload -f myfilesystem --account-name mystorageaccount -s "path/to/file*" -d directory --recursive
"""

helps['storage fs directory download'] = """
    type: command
    short-summary: Download files from the directory in ADLS Gen2 file system to a local file path.
    examples:
        - name: Download a single file in a directory in ADLS Gen2 file system.
          text: az storage fs directory download -f myfilesystem --account-name mystorageaccount -s "path/to/file" -d "<local-path>"
        - name: Download whole ADLS Gen2 file system.
          text: az storage fs directory download -f myfilesystem --account-name mystorageaccount  -d "<local-path>" --recursive
        - name: Download the entire directory in ADLS Gen2 file system.
          text: az storage fs directory download -f myfilesystem --account-name mystorageaccount -s SourceDirectoryPath -d "<local-path>" --recursive
        - name: Download an entire subdirectory in ADLS Gen2 file system.
          text: az storage fs directory download -f myfilesystem --account-name mystorageaccount -s "path/to/subdirectory" -d "<local-path>" --recursive
"""

helps['storage fs directory generate-sas'] = """
type: command
short-summary: Generate a SAS token for directory in ADLS Gen2 account.
examples:
  - name: Generate a sas token for directory and use it to upload files.
    text: |
        end=`date -u -d "30 minutes" '+%Y-%m-%dT%H:%MZ'`
        az storage fs directory generate-sas --name dir/ --file-system myfilesystem --https-only --permissions dlrw --expiry $end -o tsv
"""

helps['storage fs file'] = """
type: group
short-summary: Manage files in Azure Data Lake Storage Gen2 account.
"""

helps['storage fs file append'] = """
type: command
short-summary: Append content to a file in ADLS Gen2 file system.
examples:
  - name: Append content to a file in ADLS Gen2 file system.
    text: |
        az storage fs file append --content "test content test" -p dir/a.txt -f fsname --account-name myadlsaccount --account-key 0000-0000
"""

helps['storage fs file create'] = """
type: command
short-summary: Create a new file in ADLS Gen2 file system.
examples:
  - name: Create a new file in ADLS Gen2 file system.
    text: |
        az storage fs file create -p dir/a.txt -f fsname --account-name myadlsaccount --account-key 0000-0000
"""

helps['storage fs file delete'] = """
type: command
short-summary: Delete a file in ADLS Gen2 file system.
examples:
  - name: Delete a file in ADLS Gen2 file system.
    text: |
        az storage fs file delete -p dir/a.txt -f fsname --account-name myadlsaccount --account-key 0000-0000
"""

helps['storage fs file download'] = """
type: command
short-summary: Download a file from the specified path in ADLS Gen2 file system.
examples:
  - name: Download a file in ADLS Gen2 file system to current path.
    text: |
        az storage fs file download -p dir/a.txt -f fsname --account-name myadlsaccount --account-key 0000-0000
  - name: Download a file in ADLS Gen2 file system to a specified directory.
    text: |
        az storage fs file download -p dir/a.txt -d test/ -f fsname --account-name myadlsaccount --account-key 0000-0000
  - name: Download a file in ADLS Gen2 file system to a specified file path.
    text: |
        az storage fs file download -p dir/a.txt -d test/b.txt -f fsname --account-name myadlsaccount --account-key 0000-0000
"""

helps['storage fs file exists'] = """
type: command
short-summary: Check for the existence of a file in ADLS Gen2 file system.
examples:
  - name: Check for the existence of a file in ADLS Gen2 file system.
    text: |
        az storage fs file exists -p dir/a.txt -f fsname --account-name myadlsaccount --account-key 0000-0000
"""

helps['storage fs file list'] = """
type: command
short-summary: List files and directories in ADLS Gen2 file system.
examples:
  - name:  List files and directories in ADLS Gen2 file system.
    text: |
        az storage fs file list -f fsname --account-name myadlsaccount --account-key 0000-0000
  - name:  List files in ADLS Gen2 file system.
    text: |
        az storage fs file list --exclude-dir -f fsname --account-name myadlsaccount --account-key 0000-0000
  - name:  List files and directories in a specified path.
    text: |
        az storage fs file list --path dir -f fsname --account-name myadlsaccount --account-key 0000-0000
  - name:  List files and directories from a specific marker.
    text: |
        az storage fs file list --marker "VBaS6LvPufaqrTANTQvbmV3dHJ5FgAAAA==" -f fsname --account-name myadlsaccount --account-key 0000-0000
"""

helps['storage fs file metadata'] = """
type: group
short-summary: Manage the metadata for file in file system.
"""

helps['storage fs file metadata show'] = """
type: command
short-summary: Return all user-defined metadata for the specified file.
examples:
  - name: Return all user-defined metadata for the specified file.
    text: az storage fs file metadata show -p dir/a.txt -f fsname --account-name myadlsaccount --account-key 0000-0000
"""

helps['storage fs file move'] = """
type: command
short-summary: Move a file in ADLS Gen2 Account.
examples:
  - name:  Move a file in ADLS Gen2 Account.
    text: |
        az storage fs file move --new-path new-fs/new-dir/b.txt -p dir/a.txt -f fsname --account-name myadlsaccount --account-key 0000-0000
"""

helps['storage fs file show'] = """
type: command
short-summary: Show properties of file in ADLS Gen2 file system.
examples:
  - name:  Show properties of file in ADLS Gen2 file system.
    text: |
        az storage fs file show -p dir/a.txt -f fsname --account-name myadlsaccount --account-key 0000-0000
  - name: Show properties of file in ADLS Gen2 file system. (autogenerated)
    text: |
        az storage fs file show --account-name myadlsaccount --auth-mode login --file-system fsname --path dir/a.txt
    crafted: true
"""

helps['storage fs file upload'] = """
type: command
short-summary: Upload a file to a file path in ADLS Gen2 file system.
examples:
  - name:  Upload a file from local path to a file path in ADLS Gen2 file system.
    text: |
        az storage fs file upload --source a.txt -p dir/a.txt -f fsname --account-name myadlsaccount --account-key 0000-0000
"""

helps['storage fs metadata'] = """
type: group
short-summary: Manage the metadata for file system.
"""

helps['storage fs metadata show'] = """
type: command
short-summary: Return all user-defined metadata for the specified file system.
examples:
  - name: Return all user-defined metadata for the specified file system.
    text: az storage fs metadata show -n myfilesystem --account-name myadlsaccount --account-key 0000-0000
"""

helps['storage logging'] = """
type: group
short-summary: Manage storage service logging information.
"""

helps['storage logging off'] = """
type: command
short-summary: Turn off logging for a storage account.
parameters:
  - name: --services
    short-summary: 'The storage services from which to retrieve logging info: (b)lob (q)ueue (t)able. Can be combined.'
examples:
  - name: Turn off logging for a storage account.
    text: |
        az storage logging off --account-name MyAccount
"""

helps['storage logging show'] = """
type: command
short-summary: Show logging settings for a storage account.
parameters:
  - name: --services
    short-summary: 'The storage services from which to retrieve logging info: (b)lob (q)ueue (t)able. Can be combined.'
examples:
  - name: Show logging settings for a storage account. (autogenerated)
    text: |
        az storage logging show --account-name MyAccount --services qt
    crafted: true
"""

helps['storage logging update'] = """
type: command
short-summary: Update logging settings for a storage account.
parameters:
  - name: --services
    short-summary: 'The storage service(s) for which to update logging info: (b)lob (q)ueue (t)able. Can be combined.'
  - name: --log
    short-summary: 'The operations for which to enable logging: (r)ead (w)rite (d)elete. Can be combined.'
  - name: --retention
    short-summary: Number of days for which to retain logs. 0 to disable.
  - name: --version
    short-summary: Version of the logging schema.
"""

helps['storage message'] = """
type: group
short-summary: Manage queue storage messages.
long-summary: >
    Please specify one of the following authentication parameters for your commands: --auth-mode, --account-key,
    --connection-string, --sas-token. You also can use corresponding environment variables to store your authentication
    credentials, e.g. AZURE_STORAGE_KEY, AZURE_STORAGE_CONNECTION_STRING and AZURE_STORAGE_SAS_TOKEN.
"""

helps['storage metrics'] = """
type: group
short-summary: Manage storage service metrics.
"""

helps['storage metrics show'] = """
type: command
short-summary: Show metrics settings for a storage account.
parameters:
  - name: --services
    short-summary: 'The storage services from which to retrieve metrics info: (b)lob (q)ueue (t)able. Can be combined.'
  - name: --interval
    short-summary: Filter the set of metrics to retrieve by time interval
examples:
  - name: Show metrics settings for a storage account. (autogenerated)
    text: |
        az storage metrics show --account-key 00000000 --account-name MyAccount
    crafted: true
"""

helps['storage metrics update'] = """
type: command
short-summary: Update metrics settings for a storage account.
parameters:
  - name: --services
    short-summary: 'The storage services from which to retrieve metrics info: (b)lob (q)ueue (t)able. Can be combined.'
  - name: --hour
    short-summary: Update the hourly metrics
  - name: --minute
    short-summary: Update the by-minute metrics
  - name: --api
    short-summary: Specify whether to include API in metrics. Applies to both hour and minute metrics if both are specified. Must be specified if hour or minute metrics are enabled and being updated.
  - name: --retention
    short-summary: Number of days for which to retain metrics. 0 to disable. Applies to both hour and minute metrics if both are specified.
examples:
  - name: Update metrics settings for a storage account. (autogenerated)
    text: |
        az storage metrics update --account-name MyAccount --api true --hour true --minute true --retention 10 --services bfqt
    crafted: true
  - name: Update metrics settings for a storage account by connection string. (autogenerated)
    text: |
        az storage metrics update --api true --connection-string $connectionString --hour true --minute true --retention 10 --services bfqt
    crafted: true
"""

helps['storage queue'] = """
type: group
short-summary: Manage storage queues.
"""

helps['storage queue stats'] = """
    type: command
    short-summary: >
        Retrieve statistics related to replication for the Queue service.
        It is only available when read-access geo-redundant replication is enabled for the storage account.
    examples:
        - name: Show statistics related to replication for the Queue service.
          text: az storage queue stats --account-name mystorageaccount
"""

helps['storage queue exists'] = """
    type: command
    short-summary: Return a boolean indicating whether the queue exists.
    examples:
        - name: Check whether the queue exists.
          text: az storage queue exists -n myqueue --account-name mystorageaccount
"""

helps['storage queue generate-sas'] = """
    type: command
    short-summary: Generate a shared access signature for the queue.Use the returned signature with the sas_token parameter of QueueService.
    examples:
        - name: Generate a sas token for the queue with read-only permissions.
          text: |
              end=`date -u -d "30 minutes" '+%Y-%m-%dT%H:%MZ'`
              az storage queue generate-sas -n myqueue --account-name mystorageaccount --permissions r --expiry $end --https-only
        - name: Generate a sas token for the queue with ip range specified.
          text: |
              end=`date -u -d "30 minutes" '+%Y-%m-%dT%H:%MZ'`
              az storage queue generate-sas -n myqueue --account-name mystorageaccount --ip "176.134.171.0-176.134.171.255" --permissions r --expiry $end --https-only
"""

helps['storage queue create'] = """
    type: command
    short-summary:  Create a queue under the given account.
    examples:
        - name: Create a queue under the given account with metadata.
          text: az storage queue create -n myqueue --metadata key1=value1 key2=value2 --account-name mystorageaccount
"""

helps['storage queue delete'] = """
    type: command
    short-summary:  Delete the specified queue and any messages it contains.
    examples:
        - name: Delete the specified queue, throw an exception if the queue doesn't exist.
          text: az storage queue delete -n myqueue --fail-not-exist --account-name mystorageaccount
"""

helps['storage queue metadata show'] = """
    type: command
    short-summary:  Return all user-defined metadata for the specified queue.
    examples:
        - name: Return all user-defined metadata for the specified queue.
          text: az storage queue metadata show -n myqueue --account-name mystorageaccount
"""

helps['storage queue metadata update'] = """
    type: command
    short-summary:  Set user-defined metadata on the specified queue.
    examples:
        - name: Set user-defined metadata on the specified queue.
          text: az storage queue metadata update -n myqueue --metadata a=b c=d --account-name mystorageaccount
"""

helps['storage message put'] = """
    type: command
    short-summary:  Add a new message to the back of the message queue.
    examples:
        - name: Add a new message which will live one day.
          text: az storage message put -q myqueue --content mymessagecontent --time-to-live 86400 --account-name mystorageaccount
"""

helps['storage message peek'] = """
    type: command
    short-summary:  Retrieve one or more messages from the front of the queue, but do not alter the visibility of the message.
    examples:
        - name: Retrieve 5 messages from the front of the queue (do not alter the visibility of the message).
          text: az storage message peek -q myqueue --num-messages 5 --account-name mystorageaccount
"""

helps['storage message get'] = """
    type: command
    short-summary:  Retrieve one or more messages from the front of the queue.
    examples:
        - name: Retrieve one message from the front of the queue and reset the visibility timeout to 5 minutes later.
          text: az storage message get -q myqueue --visibility-timeout 300 --account-name mystorageaccount
"""

helps['storage message update'] = """
    type: command
    short-summary:  Update the visibility timeout of a message.
    examples:
        - name: Update the visibility timeout and content of a message.
          text: |
              az storage message update --id messageid --pop-receipt popreceiptreturned -q myqueue
              --visibility-timeout 3600 --content newmessagecontent --account-name mystorageaccount
"""

helps['storage message delete'] = """
    type: command
    short-summary:  Delete the specified message.
    examples:
        - name: Delete the specified message.
          text: az storage message delete --id messageid --pop-receipt popreceiptreturned -q myqueue --account-name mystorageaccount
"""

helps['storage message clear'] = """
    type: command
    short-summary:  Delete all messages from the specified queue.
    examples:
        - name: Delete all messages from the specified queue.
          text: az storage message clear -q myqueue --account-name mystorageaccount
"""

helps['storage queue list'] = """
type: command
short-summary: List queues in a storage account.
examples:
  - name: List queues whose names begin with 'myprefix' under the storage account 'mystorageaccount'(account name)
    text: az storage queue list --prefix myprefix --account-name mystorageaccount
"""

helps['storage queue metadata'] = """
type: group
short-summary: Manage the metadata for a storage queue.
"""

helps['storage queue policy'] = """
type: group
short-summary: Manage shared access policies for a storage queue.
"""

helps['storage remove'] = """
type: command
short-summary: Delete blobs or files from Azure Storage.
examples:
  - name: Remove a single blob.
    text: az storage remove -c mycontainer -n MyBlob
  - name: Remove an entire virtual directory.
    text: az storage remove -c mycontainer -n path/to/directory --recursive
  - name: Remove only the top blobs inside a virtual directory but not its sub-directories.
    text: az storage remove -c mycontainer --recursive
  - name: Remove all the blobs in a Storage Container.
    text: az storage remove -c mycontainer -n path/to/directory
  - name: Remove a subset of blobs in a virtual directory (For example, only jpg and pdf files, or if the blob name is "exactName" and file names don't start with "test").
    text: az storage remove -c mycontainer --include-path path/to/directory --include-pattern "*.jpg;*.pdf;exactName" --exclude-pattern "test*" --recursive
  - name: Remove an entire virtual directory but exclude certain blobs from the scope (For example, every blob that starts with foo or ends with bar).
    text: az storage remove -c mycontainer --include-path path/to/directory --exclude-pattern "foo*;*bar" --recursive
  - name: Remove a single file.
    text: az storage remove -s MyShare -p MyFile
  - name: Remove an entire directory.
    text: az storage remove -s MyShare -p path/to/directory --recursive
  - name: Remove all the files in a Storage File Share.
    text: az storage remove -s MyShare --recursive
"""

helps['storage share-rm'] = """
type: group
short-summary: Manage Azure file shares using the Microsoft.Storage resource provider.
"""

helps['storage share-rm create'] = """
type: command
short-summary: Create a new Azure file share under the specified storage account.
examples:
  - name: Create a new Azure file share 'myfileshare' with metadata and quota as 10 GB under the storage account 'mystorageaccount'(account name) in resource group 'MyResourceGroup'.
    text: az storage share-rm create -g MyResourceGroup --storage-account mystorageaccount --name myfileshare --quota 10 --metadata key1=value1 key2=value2
  - name: Create a new Azure file share 'myfileshare' with metadata and quota as 6000 GB under the storage account 'mystorageaccount'(account name) which enables large file share in resource group 'MyResourceGroup'.
    text: |
        az storage account update -g MyResourceGroup --name mystorageaccount --enable-large-file-share
        az storage share-rm create -g MyResourceGroup --storage-account mystorageaccount --name myfileshare --quota 6000 --metadata key1=value1 key2=value2
  - name: Create a new Azure file share 'myfileshare' with metadata and quota as 10 GB under the storage account 'mystorageaccount' (account id).
    text: az storage share-rm create --storage-account mystorageaccount --name myfileshare --quota 10 --metadata key1=value1 key2=value2
"""

helps['storage share-rm delete'] = """
type: command
short-summary: Delete the specified Azure file share or share snapshot.
long-summary: 'BREAKING CHANGE: Snapshot can not be deleted by default and we have added a new parameter to use if you want to include sanpshots for delete operation.'
examples:
  - name: Delete an Azure file share 'myfileshare' under the storage account 'mystorageaccount' (account name) in resource group 'MyResourceGroup'.
    text: az storage share-rm delete -g MyResourceGroup --storage-account mystorageaccount --name myfileshare
  - name: Delete an Azure file share 'myfileshare' under the storage account 'mystorageaccount' (account id).
    text: az storage share-rm delete --storage-account mystorageaccount --name myfileshare
  - name: Delete an Azure file share by resource id.
    text: az storage share-rm delete --ids file-share-id
  - name: Delete an Azure file share snapshot.
    text: az storage share-rm delete --ids file-share-id --snapshot "2021-03-25T05:29:56.0000000Z"
  - name: Delete an Azure file share and all its snapshots.
    text: az storage share-rm delete --include snapshots -g MyResourceGroup --storage-account mystorageaccount --name myfileshare
  - name: Delete an Azure file share and all its snapshots (leased/unleased).
    text: az storage share-rm delete --include leased-snapshots -g MyResourceGroup --storage-account mystorageaccount --name myfileshare
"""

helps['storage share-rm exists'] = """
type: command
short-summary: Check for the existence of an Azure file share.
examples:
  - name: Check for the existence of an Azure file share 'myfileshare' under the storage account 'mystorageaccount' (account name) in resource group 'MyResourceGroup'.
    text: az storage share-rm exists -g MyResourceGroup --storage-account mystorageaccount --name myfileshare
  - name: Check for the existence of an Azure file share 'myfileshare' under the storage account 'mystorageaccount' (account id).
    text: az storage share-rm exists --storage-account mystorageaccount --name myfileshare
  - name: Check for the existence of an Azure file share by resource id.
    text: az storage share-rm exists --ids file-share-id
"""

helps['storage share-rm list'] = """
type: command
short-summary: List the Azure file shares under the specified storage account.
examples:
  - name: List the Azure file shares under the storage account 'mystorageaccount' (account name) in resource group 'MyResourceGroup'.
    text: az storage share-rm list -g MyResourceGroup --storage-account mystorageaccount
  - name: List the Azure file shares under the storage account 'mystorageaccount' (account id).
    text: az storage share-rm list --storage-account mystorageaccount
  - name: List all file shares include deleted under the storage account 'mystorageaccount' .
    text: az storage share-rm list --storage-account mystorageaccount --include-deleted
  - name: List all file shares include its all snapshots under the storage account 'mystorageaccount' .
    text: az storage share-rm list --storage-account mystorageaccount --include-snapshot
  - name: List all file shares include its all snapshots and deleted file shares under the storage account 'mystorageaccount' .
    text: az storage share-rm list --storage-account mystorageaccount --include-deleted --include-snapshot
"""

helps['storage share-rm restore'] = """
type: command
short-summary: Restore a file share within a valid retention days if share soft delete is enabled.
examples:
  - name: Restore a file share within a valid retention days if share soft delete is enabled.
    text: az storage share-rm restore -n deletedshare --deleted-version 01D64EB9886F00C4 -g MyResourceGroup --storage-account mystorageaccount
  - name: Restore a file share within a valid retention days if share soft delete is enabled to a new name.
    text: az storage share-rm restore -n deletedshare --deleted-version 01D64EB9886F00C4 --restored-name newname -g MyResourceGroup --storage-account mystorageaccount
"""

helps['storage share-rm show'] = """
type: command
short-summary: Show the properties for a specified Azure file share or share snapshot.
examples:
  - name: Show the properties for an Azure file share 'myfileshare' under the storage account 'mystorageaccount' (account name) in resource group 'MyResourceGroup'.
    text: az storage share-rm show -g MyResourceGroup --storage-account mystorageaccount --name myfileshare
  - name: Show the properties for an Azure file share 'myfileshare' under the storage account 'mystorageaccount' (account id).
    text: az storage share-rm show --storage-account mystorageaccount --name myfileshare
  - name: Show the properties of an Azure file share by resource id.
    text: az storage share-rm show --ids file-share-id
  - name: Show the properties of an Azure file share snapshot
    text: az storage share-rm show --ids file-share-id --snapshot "2021-03-25T05:29:56.0000000Z"
"""

helps['storage share-rm stats'] = """
type: command
short-summary: Get the usage bytes of the data stored on the share.
examples:
  - name: Get the usage bytes of the data stored on the share.
    text: az storage share-rm stats -g MyResourceGroup --storage-account mystorageaccount --name myfileshare
"""

helps['storage share-rm update'] = """
type: command
short-summary: Update the properties for an Azure file share.
examples:
  - name: Update the properties for an Azure file share 'myfileshare' under the storage account 'mystorageaccount' (account name) in resource group 'MyResourceGroup'.
    text: az storage share-rm update -g MyResourceGroup --storage-account mystorageaccount --name myfileshare --quota 3 --metadata key1=value1 key2=value2
  - name: Update the properties for an Azure file share 'myfileshare' under the storage account 'mystorageaccount' (account id).
    text: az storage share-rm update --storage-account mystorageaccount --name myfileshare --quota 3 --metadata key1=value1 key2=value2
  - name: Update the properties for an Azure file shares by resource id.
    text: az storage share-rm update --ids file-share-id --quota 3 --metadata key1=value1 key2=value2
"""

helps['storage share-rm snapshot'] = """
type: command
short-summary: Create a snapshot of an existing share under the specified account.
examples:
  - name: Create a snapshot of an existing share under the specified account.
    text: az storage share-rm snapshot -g MyResourceGroup --storage-account mystorageaccount --name myfileshare
"""

helps['storage share'] = """
type: group
short-summary: Manage file shares.
"""

helps['storage share create'] = """
type: command
short-summary: Creates a new share under the specified account.
examples:
  - name: Creates a new share under the specified account. (autogenerated)
    text: |
        az storage share create --account-name MyAccount --name MyFileShare
    crafted: true
"""

helps['storage share exists'] = """
type: command
short-summary: Check for the existence of a file share.
examples:
  - name: Check for the existence of a file share. (autogenerated)
    text: |
        az storage share exists --account-key 00000000 --account-name MyAccount --name MyFileShare
    crafted: true
  - name: Check for the existence of a file share (autogenerated)
    text: |
        az storage share exists --connection-string $connectionString --name MyFileShare
    crafted: true
"""

helps['storage share generate-sas'] = """
type: command
short-summary: Generate a shared access signature for the share.
examples:
  - name: Generate a sas token for a fileshare and use it to upload a file.
    text: |
        end=`date -u -d "30 minutes" '+%Y-%m-%dT%H:%MZ'`
        sas=`az storage share generate-sas -n MyShare --account-name MyStorageAccount --https-only --permissions dlrw --expiry $end -o tsv`
        az storage file upload -s MyShare --account-name MyStorageAccount --source file.txt  --sas-token $sas
  - name: Generate a shared access signature for the share. (autogenerated)
    text: |
        az storage share generate-sas --account-key 00000000 --account-name MyStorageAccount --expiry 2037-12-31T23:59:00Z --name MyShare --permissions dlrw
    crafted: true
  - name: Generate a shared access signature for the share. (autogenerated)
    text: |
        az storage share generate-sas --connection-string $connectionString --expiry 2019-02-01T12:20Z --name MyShare --permissions dlrw
    crafted: true
"""

helps['storage share list'] = """
type: command
short-summary: List the file shares in a storage account.
"""

helps['storage share show'] = """
type: command
short-summary: Return all user-defined metadata and system properties for the specified share.
long-summary: The data returned does not include the shares's list of files or directories.
"""

helps['storage share delete'] = """
type: command
short-summary: Mark the specified share for deletion.
long-summary: If the share does not exist, the operation fails on the service. By default, the exception is swallowed by the client. To expose the exception, specify True for fail_not_exist.
"""

helps['storage share stats'] = """
type: command
short-summary: Get the approximate size of the data stored on the share, rounded up to the nearest gigabyte.
long-summary: Note that this value may not include all recently created or recently re-sized files.
"""

helps['storage share update'] = """
type: command
short-summary: Set service-defined properties for the specified share.
"""

helps['storage share metadata'] = """
type: group
short-summary: Manage the metadata of a file share.
"""

helps['storage share metadata show'] = """
type: command
short-summary: Return all user-defined metadata for the specified share.
"""

helps['storage share metadata update'] = """
type: command
short-summary: Set one or more user-defined name-value pairs for the specified share.
long-summary: Each call to this operation replaces all existing metadata attached to the share. To remove all metadata from the share, call this operation with no metadata dict.
"""

helps['storage share policy'] = """
type: group
short-summary: Manage shared access policies of a storage file share.
"""

helps['storage share url'] = """
type: command
short-summary: Create a URI to access a file share.
examples:
  - name: Create a URI to access a file share. (autogenerated)
    text: |
        az storage share url --account-key 00000000 --account-name MyAccount --name MyFileShare
    crafted: true
"""

helps['storage share list-handle'] = """
type: command
short-summary: List file handles of a file share.
examples:
  - name: List all file handles of a file share recursively.
    text: |
        az storage share list-handle --account-name MyAccount --name MyFileShare --recursive
  - name: List all file handles of a file directory recursively.
    text: |
        az storage share list-handle --account-name MyAccount --name MyFileShare --path 'dir1' --recursive
  - name: List all file handles of a file.
    text: |
        az storage share list-handle --account-name MyAccount --name MyFileShare --path 'dir1/test.txt'
"""

helps['storage share close-handle'] = """
type: command
short-summary: Close file handles of a file share.
examples:
  - name: Close all file handles of a file share recursively.
    text: |
        az storage share close-handle --account-name MyAccount --name MyFileShare --close-all --recursive
        az storage share close-handle --account-name MyAccount --name MyFileShare --handle-id "*" --recursive
  - name: Close all file handles of a file directory recursively.
    text: |
        az storage share close-handle --account-name MyAccount --name MyFileShare --path 'dir1' --close-all --recursive
  - name: Close all file handles of a file.
    text: |
        az storage share close-handle --account-name MyAccount --name MyFileShare --path 'dir1/test.txt' --close-all
  - name: Close file handle with a specific handle-id of a file.
    text: |
        az storage share close-handle --account-name MyAccount --name MyFileShare --path 'dir1/test.txt' --handle-id "id"
"""

helps['storage table'] = """
type: group
short-summary: Manage NoSQL key-value storage.
"""

helps['storage table create'] = """
type: command
short-summary: Create a new table in the storage account.
"""

helps['storage table delete'] = """
type: command
short-summary: Delete the specified table and any data it contains.
"""

helps['storage table exists'] = """
type: command
short-summary: Return a boolean indicating whether the table exists.
"""

helps['storage table generate-sas'] = """
type: command
short-summary: Generate a shared access signature for the table.
"""

helps['storage table list'] = """
type: command
short-summary: List tables in a storage account.
"""

helps['storage table policy'] = """
type: group
short-summary: Manage shared access policies of a storage table.
"""
