# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-lines

from knack.help_files import helps

helps['identity'] = """
    type: group
    short-summary: Managed Identities
    long-summary: These commands are in preview and under development. Reference and support levels are not guaranteed, and these commands might be changed or removed in the future.
"""

helps['identity create'] = """
    type: command
    short-summary: Create a user assigned managed identity.
    long-summary: You can create a user assigned managed identity to use across multiple Azure resources.
    examples:
      - name: Create a user assigned managed identity.
        text: |
            az identity create --name MyIdentity --resource-group MyResourceGroup
"""

helps['identity list'] = """
    type: command
    short-summary: List user assigned managed identities.
"""

helps['identity list-operations'] = """
    type: command
    short-summary: List operations for managed identities.
"""

helps['identity list-resources'] = """
    type: command
    short-summary: List resources associated with a managed identity.
"""

helps['identity federated-credential'] = """
    type: group
    short-summary: Manage federated identity credentials for user assigned managed identities.
    long-summary: These commands are in preview and use API version 2025-01-31-PREVIEW.
"""

helps['identity federated-credential create'] = """
    type: command
    short-summary: Create a federated identity credential under an existing user assigned identity.
    examples:
      - name: Create a federated identity credential under a specific user assigned identity.
        text: |
            az identity federated-credential create --name myFicName --identity-name myIdentityName --resource-group myResourceGroup --issuer myIssuer --subject mySubject --audiences myAudiences
      - name: Create a federated identity credential with claims matching expression for GitHub
        text: |
            az identity federated-credential create --name myFicName --identity-name myIdentityName --resource-group myResourceGroup --issuer https://token.actions.githubusercontent.com --audiences api://AzureADTokenExchange --claims-matching-expression-value "claims['sub'] startswith 'repo:contoso-org/contoso-repo:ref:refs/heads'" --claims-matching-expression-version 1
"""

helps['identity federated-credential update'] = """
    type: command
    short-summary: Update a federated identity credential under an existing user assigned identity.
    examples:
      - name: Update a federated identity credential under a specific user assigned identity.
        text: |
            az identity federated-credential update --name myFicName --identity-name myIdentityName --resource-group myResourceGroup --issuer myIssuer --subject mySubject --audiences myAudiences
      - name: Update a federated identity credential with claims matching expression for GitHub
        text: |
            az identity federated-credential update --name myFicName --identity-name myIdentityName --resource-group myResourceGroup --issuer https://token.actions.githubusercontent.com --audiences api://AzureADTokenExchange --claims-matching-expression-value "claims['sub'] startswith 'repo:contoso-org/contoso-repo:ref:refs/heads'" --claims-matching-expression-version 1
"""

helps['identity federated-credential delete'] = """
    type: command
    short-summary: Delete a federated identity credential.
    examples:
      - name: Delete a federated identity credential under a user assigned managed identity.
        text: |
            az identity federated-credential delete --name myFicName --identity-name myIdentityName --resource-group myResourceGroup
"""

helps['identity federated-credential show'] = """
    type: command
    short-summary: Show details of a federated identity credential.
    examples:
      - name: Show details of a federated identity credential under a user assigned managed identity.
        text: |
            az identity federated-credential show --name myFicName --identity-name myIdentityName --resource-group myResourceGroup
"""

helps['identity show'] = """
    type: command
    short-summary: Show details of a user assigned managed identity.
    examples:
      - name: Show details of a user assigned managed identity.
        text: |
            az identity show --name myIdentity --resource-group myResourceGroup
"""

helps['identity delete'] = """
    type: command
    short-summary: Delete a user assigned managed identity.
    examples:
      - name: Delete a user assigned managed identity.
        text: |
            az identity delete --name myIdentity --resource-group myResourceGroup
"""

helps['identity federated-credential list'] = """
    type: command
    short-summary: List all federated identity credentials under an existing user assigned identity.
    examples:
      - name: List all federated identity credentials under an existing user assigned identity.
        text: |
            az identity federated-credential list --identity-name myIdentityName --resource-group myResourceGroup
"""
