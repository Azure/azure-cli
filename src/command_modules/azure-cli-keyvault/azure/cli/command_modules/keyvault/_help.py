# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps


helps['keyvault'] = """
    type: group
    short-summary: Manage KeyVault keys, secrets, and certificates.
"""

helps['keyvault create'] = """
    type: command
    short-summary: Create a key vault.
    long-summary: Default permissions are created for the current user or service principal unless the `--no-self-perms` flag is specified.
"""

helps['keyvault delete'] = """
    type: command
    short-summary: Delete a key vault.
"""

helps['keyvault list'] = """
    type: command
    short-summary: List key vaults.
"""

helps['keyvault show'] = """
    type: command
    short-summary: Show details of a key vault.
"""

helps['keyvault update'] = """
    type: command
    short-summary: Update the properties of a key vault.
"""

helps['keyvault recover'] = """
    type: command
    short-summary: Recover a key vault.
    long-summary: Recovers a previously deleted key vault for which soft delete was enabled.
"""

helps['keyvault key'] = """
    type: group
    short-summary: Manage keys.
"""

helps['keyvault secret'] = """
    type: group
    short-summary: Manage secrets.
"""

helps['keyvault certificate'] = """
    type: group
    short-summary: Manage certificates.
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

helps['keyvault storage sas-definition'] = """
    type: group
    short-summary: Manage storage account SAS definitions.
"""

helps['keyvault storage sas-definition create'] = """
    type: command
    examples:
        - name: Add a sas-definition for an account sas-token
          text: |

            $sastoken = az storage account generate-sas --expiry 2020-01-01 --permissions rw \\
            --resource-types sco --services bfqt --https-only --account-name storageacct     \\
            --account-key 00000000

            az keyvault storage sas-definition create --vault-name vault --account-name storageacct   \\
            -n rwallserviceaccess --validity-period P2D --sas-type account --template-uri $sastoken
        - name: Add a sas-definition for a blob sas-token
          text: >

            $sastoken = az storage blob generate-sas --account-name storageacct --account-key 00000000 \\
            -c container1 -n blob1 --https-only --permissions rw

            $url = az storage blob url --account-name storageacct -c container1 -n blob1


            az keyvault storage sas-definition create --vault-name vault --account-name storageacct   \\
            -n rwblobaccess --validity-period P2D --sas-type service --template-uri $url?$sastoken
"""

helps['keyvault network-rule'] = """
    type: group
    short-summary: Manage vault network ACLs.
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

        For more details, see: https://docs.microsoft.com/en-us/rest/api/keyvault/certificates-and-policies
    examples:
        - name: Create a self-signed certificate with the default policy
          text: |
            az keyvault certificate create --vault-name vaultname -n cert1 \\
              -p "$(az keyvault certificate get-default-policy)"
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

            az keyvault certificate import --vault-name vaultname -n cert_file

            secrets=$(az keyvault secret list-versions --vault-name vaultname \\
              -n cert1 --query "[?attributes.enabled].id" -o tsv)

            vm_secrets=$(az vm secret format -s "$secrets")

            az vm create -g group-name -n vm-name --admin-username deploy  \\
              --image debian --secrets "$vm_secrets"
"""

helps['keyvault certificate pending'] = """
    type: group
    short-summary: Manage pending certificate creation operations.
"""

helps['keyvault certificate contact'] = """
    type: group
    short-summary: Manage contacts for certificate management.
"""

helps['keyvault certificate issuer'] = """
    type: group
    short-summary: Manage certificate issuer information.
"""

helps['keyvault certificate issuer admin'] = """
    type: group
    short-summary: Manage admin information for certificate issuers.
"""
