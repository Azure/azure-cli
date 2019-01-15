# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["keyvault"] = """
"type": |-
    group
"short-summary": |-
    Manage KeyVault keys, secrets, and certificates.
"""

helps["keyvault certificate issuer"] = """
"type": |-
    group
"short-summary": |-
    Manage certificate issuer information.
"""

helps["keyvault certificate pending"] = """
"type": |-
    group
"short-summary": |-
    Manage pending certificate creation operations.
"""

helps["keyvault certificate contact"] = """
"type": |-
    group
"short-summary": |-
    Manage contacts for certificate management.
"""

helps["keyvault certificate get-default-policy"] = """
"type": |-
    command
"short-summary": |-
    Get the default policy for self-signed certificates.
"long-summary": |
    This default policy can be used in conjunction with `az keyvault create` to create a self-signed certificate.
    The default policy can also be used as a starting point to create derivative policies.

    For more details, see: https://docs.microsoft.com/en-us/rest/api/keyvault/certificates-and-policies
"""

helps["keyvault secret"] = """
"type": |-
    group
"short-summary": |-
    Manage secrets.
"""

helps["keyvault storage sas-definition"] = """
"type": |-
    group
"short-summary": |-
    Manage storage account SAS definitions.
"""

helps["keyvault list"] = """
"type": |-
    command
"short-summary": |-
    List key vaults.
"""

helps["keyvault certificate download"] = """
"type": |-
    command
"short-summary": |-
    Download the public portion of a Key Vault certificate.
"long-summary": |-
    The certificate formatted as either PEM or DER. PEM is the default.
"""

helps["keyvault create"] = """
"type": |-
    command
"short-summary": |-
    Create a key vault.
"long-summary": |-
    Default permissions are created for the current user or service principal unless the `--no-self-perms` flag is specified.
"examples":
-   "name": |-
        Create a key vault.
    "text": |-
        az keyvault create --resource-group MyResourceGroup --location westus2 --name MyKeyVault
"""

helps["keyvault certificate create"] = """
"type": |-
    command
"short-summary": |-
    Create a Key Vault certificate.
"long-summary": |-
    Certificates can be used as a secrets for provisioned virtual machines.
"examples":
-   "name": |-
        Create a Key Vault certificate.
    "text": |-
        az keyvault certificate create --disabled false --policy <policy> --vault-name MyVault --name MyCertificate
"""

helps["keyvault recover"] = """
"type": |-
    command
"short-summary": |-
    Recover a key vault.
"long-summary": |-
    Recovers a previously deleted key vault for which soft delete was enabled.
"""

helps["keyvault key"] = """
"type": |-
    group
"short-summary": |-
    Manage keys.
"""

helps["keyvault network-rule"] = """
"type": |-
    group
"short-summary": |-
    Manage vault network ACLs.
"""

helps["keyvault certificate issuer admin"] = """
"type": |-
    group
"short-summary": |-
    Manage admin information for certificate issuers.
"""

helps["keyvault storage"] = """
"type": |-
    group
"short-summary": |-
    Manage storage accounts.
"""

helps["keyvault update"] = """
"type": |-
    command
"short-summary": |-
    Update the properties of a key vault.
"""

helps["keyvault storage sas-definition create"] = """
"type": |-
    command
"""

helps["keyvault show"] = """
"type": |-
    command
"short-summary": |-
    Show details of a key vault.
"examples":
-   "name": |-
        Show details of a key vault.
    "text": |-
        az keyvault show --name MyKeyVault
"""

helps["keyvault certificate import"] = """
"type": |-
    command
"short-summary": |-
    Import a certificate into KeyVault.
"long-summary": |-
    Certificates can also be used as a secrets in provisioned virtual machines.
"""

helps["keyvault certificate"] = """
"type": |-
    group
"short-summary": |-
    Manage certificates.
"""

helps["keyvault storage add"] = """
"type": |-
    command
"""

helps["keyvault delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a key vault.
"""

