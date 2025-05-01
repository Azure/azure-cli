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
short-summary: "[Preview] Manage federated identity credentials under user assigned identities."
min_api: 2025-01-31-PREVIEW
"""

helps['identity federated-credential create'] = """
type: command
short-summary: "[Preview] Create a federated identity credential under an existing user assigned identity."
min_api: 2025-01-31-PREVIEW
examples:
  - name: Create a federated identity credential under a specific user assigned identity.
    text: |
        az identity federated-credential create --name myFicName --identity-name myIdentityName --resource-group myResourceGroup --issuer myIssuer --subject mySubject --audiences myAudiences
  - name: Create a federated identity credential with claims matching expressions.
    text: |
        az identity federated-credential create --name myFicName --identity-name myIdentityName --resource-group myResourceGroup --issuer https://tokens.githubusercontent.com --audiences api://AzureADTokenExchange --claims-matching-expression-value "claims['sub'] startswith 'repo:contoso-org/contoso-repo:ref:refs/heads'" --claims-matching-expression-version 1
"""

helps['identity federated-credential update'] = """
type: command
short-summary: "[Preview] Update a federated identity credential under an existing user assigned identity."
min_api: 2025-01-31-PREVIEW
examples:
  - name: Update a federated identity credential under a specific user assigned identity.
    text: |
        az identity federated-credential update --name myFicName --identity-name myIdentityName --resource-group myResourceGroup --issuer myIssuer --subject mySubject --audiences myAudiences
"""

helps['identity federated-credential delete'] = """
type: command
short-summary: "[Preview] Delete a federated identity credential under an existing user assigned identity."
min_api: 2025-01-31-PREVIEW
examples:
  - name: Delete a federated identity credential under a specific user assigned identity.
    text: |
        az identity federated-credential delete --name myFicName --identity-name myIdentityName --resource-group myResourceGroup
"""

helps['identity federated-credential show'] = """
type: command
short-summary: "[Preview] Show a federated identity credential under an existing user assigned identity."
min_api: 2025-01-31-PREVIEW
examples:
  - name: Show a federated identity credential under a specific user assigned identity.
    text: |
        az identity federated-credential show --name myFicName --identity-name myIdentityName --resource-group myResourceGroup
"""

helps['identity federated-credential list'] = """
type: command
short-summary: "[Preview] List all federated identity credentials under an existing user assigned identity."
min_api: 2025-01-31-PREVIEW
examples:
  - name: List all federated identity credentials under an existing user assigned identity.
    text: |
        az identity federated-credential list --identity-name myIdentityName --resource-group myResourceGroup
"""
