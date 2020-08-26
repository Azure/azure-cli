# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['keyvault'] = """
type: group
short-summary: Manage KeyVault keys, secrets, and certificates.
"""

helps['keyvault certificate'] = """
type: group
short-summary: Manage certificates.
"""

helps['keyvault certificate contact'] = """
type: group
short-summary: Manage contacts for certificate management.
"""

helps['keyvault certificate create'] = """
type: command
short-summary: Create a Key Vault certificate.
long-summary: Certificates can be used as a secrets for provisioned virtual machines.
examples:
  - name: Create a self-signed certificate with the default policy and add it to a virtual machine.
    text: |
        az keyvault certificate create --vault-name vaultname -n cert1 \\
          -p "$(az keyvault certificate get-default-policy)"

        secrets=$(az keyvault secret list-versions --vault-name vaultname \\
          -n cert1 --query "[?attributes.enabled].id" -o tsv)

        vm_secrets=$(az vm secret format -s "$secrets")

        az vm create -g group-name -n vm-name --admin-username deploy  \\
          --image debian --secrets "$vm_secrets"
"""

helps['keyvault certificate download'] = """
type: command
short-summary: Download the public portion of a Key Vault certificate.
long-summary: The certificate formatted as either PEM or DER. PEM is the default.
examples:
  - name: Download a certificate as PEM and check its fingerprint in openssl.
    text: |
        az keyvault certificate download --vault-name vault -n cert-name -f cert.pem && \\
        openssl x509 -in cert.pem -inform PEM  -noout -sha1 -fingerprint
  - name: Download a certificate as DER and check its fingerprint in openssl.
    text: |
        az keyvault certificate download --vault-name vault -n cert-name -f cert.crt -e DER && \\
        openssl x509 -in cert.crt -inform DER  -noout -sha1 -fingerprint
"""

helps['keyvault certificate get-default-policy'] = """
type: command
short-summary: Get the default policy for self-signed certificates.
long-summary: |
    This default policy can be used in conjunction with `az keyvault create` to create a self-signed certificate.
    The default policy can also be used as a starting point to create derivative policies.

    For more details, see: https://docs.microsoft.com/azure/key-vault/certificates/about-certificates#certificate-policy
examples:
  - name: Create a self-signed certificate with the default policy
    text: |
        az keyvault certificate create --vault-name vaultname -n cert1 \\
          -p "$(az keyvault certificate get-default-policy)"
"""

helps['keyvault certificate import'] = """
type: command
short-summary: Import a certificate into KeyVault.
long-summary: Certificates can also be used as a secrets in provisioned virtual machines.
examples:
  - name: Create a service principal with a certificate, add the certificate to Key Vault and provision a VM with that certificate.
    text: |
        service_principal=$(az ad sp create-for-rbac --create-cert)

        cert_file=$(echo $service_principal | jq .fileWithCertAndPrivateKey -r)

        az keyvault create -g my-group -n vaultname

        az keyvault certificate import --vault-name vaultname -n cert_name -f cert_file

        secrets=$(az keyvault secret list-versions --vault-name vaultname \\
          -n cert1 --query "[?attributes.enabled].id" -o tsv)

        vm_secrets=$(az vm secret format -s "$secrets")

        az vm create -g group-name -n vm-name --admin-username deploy  \\
          --image debian --secrets "$vm_secrets"
"""

helps['keyvault certificate issuer'] = """
type: group
short-summary: Manage certificate issuer information.
"""

helps['keyvault certificate issuer admin'] = """
type: group
short-summary: Manage admin information for certificate issuers.
"""

helps['keyvault certificate pending'] = """
type: group
short-summary: Manage pending certificate creation operations.
"""

helps['keyvault create'] = """
type: command
short-summary: Create a key vault.
long-summary: If `--enable-rbac-authorization` is not specified, then default permissions are created for the current user or service principal unless the `--no-self-perms` flag is specified.
examples:

  - name: Create a key vault with network ACLs specified (use --network-acls to specify IP and VNet rules by using a JSON string).
    text: |
        az keyvault create --location westus2 --name MyKeyVault --resource-group MyResourceGroup --network-acls "{\\"ip\\": [\\"1.2.3.4\\", \\"2.3.4.0/24\\"], \\"vnet\\": [\\"vnet_name_1/subnet_name1\\", \\"vnet_name_2/subnet_name2\\", \\"/subscriptions/000000-0000-0000/resourceGroups/MyResourceGroup/providers/Microsoft.Network/virtualNetworks/MyVNet/subnets/MySubnet\\"]}"

  - name: Create a key vault with network ACLs specified (use --network-acls to specify IP and VNet rules by using a JSON file).
    text: |
        az keyvault create --location westus2 --name MyKeyVault --resource-group MyResourceGroup --network-acls network-acls-example.json

  - name: Create a key vault with network ACLs specified (use --network-acls-ips to specify IP rules).
    text: |
        az keyvault create --location westus2 --name MyKeyVault --resource-group MyResourceGroup --network-acls-ips 3.4.5.0/24 4.5.6.0/24

  - name: Create a key vault with network ACLs specified (use --network-acls-vnets to specify VNet rules).
    text: |
        az keyvault create --location westus2 --name MyKeyVault --resource-group MyResourceGroup --network-acls-vnets vnet_name_2/subnet_name_2 vnet_name_3/subnet_name_3 /subscriptions/000000-0000-0000/resourceGroups/MyResourceGroup/providers/Microsoft.Network/virtualNetworks/vnet_name_4/subnets/subnet_name_4

  - name: Create a key vault with network ACLs specified (use --network-acls, --network-acls-ips and --network-acls-vnets together, redundant rules will be removed, finally there will be 4 IP rules and 3 VNet rules).
    text: |
        az keyvault create --location westus2 --name MyKeyVault --resource-group MyResourceGroup --network-acls "{\\"ip\\": [\\"1.2.3.4\\", \\"2.3.4.0/24\\"], \\"vnet\\": [\\"vnet_name_1/subnet_name1\\", \\"vnet_name_2/subnet_name2\\"]}" --network-acls-ips 3.4.5.0/24 4.5.6.0/24 --network-acls-vnets vnet_name_2/subnet_name_2 vnet_name_3/subnet_name_3 /subscriptions/000000-0000-0000/resourceGroups/MyResourceGroup/providers/Microsoft.Network/virtualNetworks/vnet_name_4/subnets/subnet_name_4
  - name: Create a key vault. (autogenerated)
    text: |
        az keyvault create --location westus2 --name MyKeyVault --resource-group MyResourceGroup
    crafted: true
"""

helps['keyvault delete'] = """
type: command
short-summary: Delete a key vault.
examples:
  - name: Delete a key vault. (autogenerated)
    text: |
        az keyvault delete --name MyKeyVault --resource-group MyResourceGroup
    crafted: true
"""

helps['keyvault key'] = """
type: group
short-summary: Manage keys.
"""

helps['keyvault key download'] = """
type: command
short-summary: Downloads the public part of a stored key.
examples:
  - name: Save the key with PEM encoding
    text: |
        az keyvault key download --vault-name MyKeyVault -n MyKey -e PEM -f mykey.pem
  - name: Save the key with DER encoding
    text: |
        az keyvault key download --vault-name MyKeyVault -n MyKey -e DER -f mykey.der
"""

helps['keyvault list'] = """
type: command
short-summary: List key vaults.
"""

helps['keyvault network-rule'] = """
type: group
short-summary: Manage vault network ACLs.
"""

helps['keyvault network-rule wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the vault is met.
examples:
  - name: Pause CLI until the network ACLs are updated.
    text: |
        az keyvault network-rule wait --name MyVault --updated
"""

helps['keyvault private-endpoint-connection'] = """
type: group
short-summary: Manage vault private endpoint connections.
"""

helps['keyvault private-endpoint-connection approve'] = """
type: command
short-summary: Approve a private endpoint connection request for a Key Vault.
examples:
  - name: Approve a private endpoint connection request for a Key Vault by ID.
    text: |
        az keyvault private-endpoint-connection approve --id "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/myrg/providers/Microsoft.KeyVault/vaults/mykv/privateEndpointConnections/mykv.00000000-0000-0000-0000-000000000000"
  - name: Approve a private endpoint connection request for a Key Vault by ID.
    text: |
        id = (az keyvault show -n mykv --query "privateEndpointConnections[0].id")
        az keyvault private-endpoint-connection approve --id $id
  - name: Approve a private endpoint connection request for a Key Vault using vault name and connection name.
    text: |
        az keyvault private-endpoint-connection approve -g myrg --vault-name mykv --name myconnection
  - name: Approve a private endpoint connection request for a Key Vault using vault name and connection name.
    text: |
        name = (az keyvault show -n mykv --query "privateEndpointConnections[0].name")
        az keyvault private-endpoint-connection approve -g myrg --vault-name mykv --name $name
"""

helps['keyvault private-endpoint-connection reject'] = """
type: command
short-summary: Reject a private endpoint connection request for a Key Vault.
examples:
  - name: Reject a private endpoint connection request for a Key Vault by ID.
    text: |
        az keyvault private-endpoint-connection reject --id "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/myrg/providers/Microsoft.KeyVault/vaults/mykv/privateEndpointConnections/mykv.00000000-0000-0000-0000-000000000000"
  - name: Reject a private endpoint connection request for a Key Vault by ID.
    text: |
        id = (az keyvault show -n mykv --query "privateEndpointConnections[0].id")
        az keyvault private-endpoint-connection reject --id $id
  - name: Reject a private endpoint connection request for a Key Vault using vault name and connection name.
    text: |
        az keyvault private-endpoint-connection reject -g myrg --vault-name mykv --name myconnection
  - name: Reject a private endpoint connection request for a Key Vault using vault name and connection name.
    text: |
        name = (az keyvault show -n mykv --query "privateEndpointConnections[0].name")
        az keyvault private-endpoint-connection reject -g myrg --vault-name mystorageaccount --name $name
"""

helps['keyvault private-endpoint-connection delete'] = """
type: command
short-summary: Delete the specified private endpoint connection associated with a Key Vault.
examples:
  - name: Delete a private endpoint connection request for a Key Vault by ID.
    text: |
        az keyvault private-endpoint-connection delete --id "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/myrg/providers/Microsoft.KeyVault/vaults/mykv/privateEndpointConnections/mykv.00000000-0000-0000-0000-000000000000"
  - name: Delete a private endpoint connection request for a Key Vault by ID.
    text: |
        id = (az keyvault show -n mykv --query "privateEndpointConnections[0].id")
        az keyvault private-endpoint-connection delete --id $id
  - name: Delete a private endpoint connection request for a Key Vault using account name and connection name.
    text: |
        az keyvault private-endpoint-connection delete -g myrg --vault-name mykv --name myconnection
  - name: Delete a private endpoint connection request for a Key Vault using account name and connection name.
    text: |
        name = (az keyvault show -n mykv --query "privateEndpointConnections[0].name")
        az keyvault private-endpoint-connection delete -g myrg --vault-name mykv --name $name
"""

helps['keyvault private-endpoint-connection show'] = """
type: command
short-summary: Show details of a private endpoint connection associated with a Key Vault.
examples:
  - name: Show details of a private endpoint connection request for a Key Vault by ID.
    text: |
        az keyvault private-endpoint-connection show --id "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/myrg/providers/Microsoft.KeyVault/vaults/mykv/privateEndpointConnections/mykv.00000000-0000-0000-0000-000000000000"
  - name: Show details of a private endpoint connection request for a Key Vault by ID.
    text: |
        id = (az keyvault show -n mykv --query "privateEndpointConnections[0].id")
        az keyvault private-endpoint-connection show --id $id
  - name: Show details of a private endpoint connection request for a Key Vault using vault name and connection name.
    text: |
        az keyvault private-endpoint-connection show -g myrg --vault-name mykv --name myconnection
  - name: Show details of a private endpoint connection request for a Key Vault using vault name and connection name.
    text: |
        name = (az keyvault show -n mykv --query "privateEndpointConnections[0].name")
        az keyvault private-endpoint-connection show -g myrg --vault-name mykv --name $name
"""

helps['keyvault private-endpoint-connection wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the private endpoint connection is met.
examples:
  - name: Pause CLI until the private endpoint connection is approved/rejected by ID.
    text: |
        az keyvault private-endpoint-connection wait --id "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/myrg/providers/Microsoft.KeyVault/vaults/mykv/privateEndpointConnections/mykv.00000000-0000-0000-0000-000000000000" --created
  - name: Pause CLI until the private endpoint connection is approved/rejected using vault name and connection name.
    text: |
        az keyvault private-endpoint-connection wait -g myrg --vault-name mykv --name myconnection --created
"""

helps['keyvault private-link-resource'] = """
type: group
short-summary: Manage vault private link resources.
"""

helps['keyvault private-link-resource list'] = """
type: command
short-summary: List the private link resources supported for a Key Vault.
examples:
  - name: Get the private link resources that need to be created for a Key Vault.
    text: |
        az keyvault private-link-resource list --vault-name mykv
"""

helps['keyvault recover'] = """
type: command
short-summary: Recover a key vault.
long-summary: Recovers a previously deleted key vault for which soft delete was enabled.
examples:
  - name: Recover a key vault. (autogenerated)
    text: |
        az keyvault recover --location westus2 --name MyKeyVault --resource-group MyResourceGroup
    crafted: true
"""

helps['keyvault secret'] = """
type: group
short-summary: Manage secrets.
"""

helps['keyvault secret set'] = """
type: command
short-summary: Create a secret (if one doesn't exist) or update a secret in a KeyVault.
"""

helps['keyvault show'] = """
type: command
short-summary: Show details of a key vault.
examples:
  - name: Show details of a key vault. (autogenerated)
    text: |
        az keyvault show --name MyKeyVault
    crafted: true
"""

helps['keyvault storage'] = """
type: group
short-summary: Manage storage accounts.
"""

helps['keyvault storage add'] = """
type: command
examples:
  - name: Create a storage account and setup a vault to manage its keys
    text: |
        $id = az storage account create -g resourcegroup -n storageacct --query id

        # assign the Azure Key Vault service the "Storage Account Key Operator Service Role" role.
        az role assignment create --role "Storage Account Key Operator Service Role" --scope $id \\
        --assignee cfa8b339-82a2-471a-a3c9-0fc0be7a4093

        az keyvault storage add --vault-name vault -n storageacct --active-key-name key1    \\
        --auto-regenerate-key --regeneration-period P90D  --resource-id $id
"""

helps['keyvault storage remove'] = """
type: command
short-summary: Remove a Key Vault managed Azure Storage Account and all associated SAS definitions. This operation requires the storage/delete permission.
examples:
  - name: Remove a Key Vault managed Azure Storage Account and all associated SAS definitions (autogenerated)
    text: |
        az keyvault storage remove --name MyStorageAccount --vault-name MyVault
    crafted: true
"""

helps['keyvault storage sas-definition'] = """
type: group
short-summary: Manage storage account SAS definitions.
"""

helps['keyvault storage sas-definition create'] = """
type: command
examples:
  - name: Add a sas-definition for an account sas-token
    text: |4
        $sastoken = az storage account generate-sas --expiry 2020-01-01 --permissions rw --resource-types sco --services bfqt --https-only --account-name storageacct --account-key 00000000

        az keyvault storage sas-definition create --vault-name vault --account-name storageacct -n rwallserviceaccess --validity-period P2D --sas-type account --template-uri $sastoken
  - name: Add a sas-definition for a blob sas-token
    text: >4
        $sastoken = az storage blob generate-sas --account-name storageacct --account-key 00000000 -c container1 -n blob1 --https-only --permissions rw

        $url = az storage blob url --account-name storageacct -c container1 -n blob1

        az keyvault storage sas-definition create --vault-name vault --account-name storageacct -n rwblobaccess --validity-period P2D --sas-type service --template-uri $url?$sastoken
  - name: Add a sas-definition for a container sas-token
    text: >4
        $sastoken = az storage container generate-sas --account-name storageacct --account-key 00000000 -n container1 --https-only --permissions rw

        $url = "https://{storage-account-name}.blob.core.windows.net/{container-name}"  # The prefix of your blob url

        az keyvault storage sas-definition create --vault-name vault --account-name storageacct -n rwcontaineraccess --validity-period P2D --sas-type service --template-uri $url?$sastoken
"""

helps['keyvault update'] = """
type: command
short-summary: Update the properties of a key vault.
examples:
  - name: Update the properties of a key vault. (autogenerated)
    text: |
        az keyvault update --enabled-for-disk-encryption true --name MyKeyVault --resource-group MyResourceGroup
    crafted: true
"""

helps['keyvault wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the vault is met.
examples:
  - name: Pause CLI until the vault is created.
    text: |
        az keyvault wait --name MyVault --created
"""
