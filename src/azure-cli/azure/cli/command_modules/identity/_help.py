# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-lines

from knack.help_files import helps

helps['identity'] = """
type: group
short-summary: Managed Identities
"""

helps['identity create'] = """
type: command
short-summary: Create Identities.
examples:
  - name: Create an identity.
    text: |
        az identity create --name MyIdentity --resource-group MyResourceGroup
"""

helps['identity list'] = """
type: command
short-summary: List Managed Identities.
"""

helps['identity list-operations'] = """
type: command
short-summary: List available operations for the Managed Identity provider.
"""

helps['identity list-resources'] = """
type: command
short-summary: List the associated resources for the identity.
"""

helps['identity federated-credential'] = """
type: group
short-summary: Manage federated identity credentials under user assigned identities.
long-summary: |
    Federated identity credentials enable user-assigned managed identities to be authenticated using external identity providers.
    Credentials can be configured using either a subject identifier or a claims matching expression for more complex token validation scenarios.
"""

helps['identity federated-credential create'] = """
type: command
short-summary: Create a federated identity credential under an existing user assigned identity.
examples:
  - name: Create a federated identity credential using subject identifier
    text: |
        az identity federated-credential create --fed-name $ficId --name $uaId --resource-group $rg --issuer 'https://aks.azure.com/issuerGUID' --subject 'system:serviceaccount:ns:svcaccount' --audiences 'api://AzureADTokenExchange'
  - name: Create a federated identity credential using claims matching expression (long form)
    text: |
        az identity federated-credential create --fed-name $ficId --name $uaId --resource-group $rg --issuer 'https://aks.azure.com/issuerGUID' --cme-value "claims['sub'] startswith 'repo:contoso-org/contoso-repo:ref:refs/heads/'" --cme-version 1 --audiences 'api://AzureADTokenExchange'
  - name: Create a federated identity credential using claims matching expression (short form)
    text: |
        az identity federated-credential create -f $ficId --name $uaId --resource-group $rg --issuer 'https://aks.azure.com/issuerGUID' -v "claims['sub'] startswith 'repo:contoso-org/contoso-repo:ref:refs/heads/'" -e 1 --audiences 'api://AzureADTokenExchange'
"""

helps['identity federated-credential update'] = """
type: command
short-summary: Update a federated identity credential under an existing user assigned identity.
examples:
  - name: Update a federated identity credential using subject identifier
    text: |
        az identity federated-credential update --fed-name $ficId --name $uaId --resource-group $rg --issuer 'https://aks.azure.com/issuerGUID' --subject 'system:serviceaccount:ns:svcaccount' --audiences 'api://AzureADTokenExchange'
  - name: Update a federated identity credential using claims matching expression (long form)
    text: |
        az identity federated-credential update --fed-name $ficId --name $uaId --resource-group $rg --issuer 'https://aks.azure.com/issuerGUID' --cme-value "claims['sub'] startswith 'repo:contoso-org/contoso-repo:ref:refs/heads/'" --cme-version 1 --audiences 'api://AzureADTokenExchange'
  - name: Update a federated identity credential using claims matching expression (short form)
    text: |
        az identity federated-credential update -f $ficId --name $uaId --resource-group $rg --issuer 'https://aks.azure.com/issuerGUID' -v "claims['sub'] startswith 'repo:contoso-org/contoso-repo:ref:refs/heads/'" -e 1 --audiences 'api://AzureADTokenExchange'
"""

helps['identity federated-credential delete'] = """
type: command
short-summary: Delete a federated identity credential under an existing user assigned identity.
examples:
  - name: Delete a federated identity credential using long form
    text: |
        az identity federated-credential delete --fed-name myFicName --name myIdentityName --resource-group myResourceGroup
  - name: Delete a federated identity credential using short form
    text: |
        az identity federated-credential delete -f myFicName --name myIdentityName --resource-group myResourceGroup
"""

helps['identity federated-credential show'] = """
type: command
short-summary: Show a federated identity credential under an existing user assigned identity.
examples:
  - name: Show a federated identity credential using long form
    text: |
        az identity federated-credential show --fed-name myFicName --name myIdentityName --resource-group myResourceGroup
  - name: Show a federated identity credential using short form
    text: |
        az identity federated-credential show -f myFicName --name myIdentityName --resource-group myResourceGroup
"""

helps['identity federated-credential list'] = """
type: command
short-summary: List all federated identity credentials under an existing user assigned identity.
examples:
  - name: List all federated identity credentials under an existing user assigned identity.
    text: |
        az identity federated-credential list --name myIdentityName --resource-group myResourceGroup
"""
