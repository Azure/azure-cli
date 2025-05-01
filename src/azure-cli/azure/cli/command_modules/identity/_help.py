# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps['identity'] = """
type: group
short-summary: Managed Identities
"""

helps['identity create'] = """
type: command
short-summary: Create an identity.
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

helps['identity show'] = """
type: command
short-summary: Show the details of a managed identity.
"""

helps['identity delete'] = """
type: command
short-summary: Delete a managed identity.
"""

helps['identity federated-credential'] = """
type: group
short-summary: [Preview] Manage federated credentials under managed identities.
"""

helps['identity federated-credential create'] = """
type: command
short-summary: [Preview] Create a federated credential.
parameters:
  - name: --name -n
    type: string
    short-summary: Name of the federated credential.
    long-summary: Must start with a letter or number, and can contain letters, numbers, underscores, and hyphens. Length must be between 3-120 characters.
  - name: --identity-name
    type: string
    short-summary: Name of the managed identity.
  - name: --issuer 
    type: string
    short-summary: The URL of the issuer to be trusted.
    long-summary: For GitHub Actions, use 'https://token.actions.githubusercontent.com'
  - name: --subject
    type: string
    short-summary: The identifier of the external identity.
    long-summary: Cannot be used with claims-matching-expression-* parameters.
  - name: --audiences
    type: array
    short-summary: List of audiences that can appear in the issued token.
examples:
  - name: Create a federated identity credential with subject matching
    text: |
        az identity federated-credential create -g MyResourceGroup --identity-name MyIdentity -n MyFicName \\
            --issuer https://token.actions.githubusercontent.com \\
            --subject "system:serviceaccount:ns:svcaccount" \\
            --audiences api://AzureADTokenExchange
"""

helps['identity federated-credential update'] = """
type: command
short-summary: [Preview] Update a federated credential.
"""

helps['identity federated-credential delete'] = """
type: command
short-summary: [Preview] Delete a federated credential.
examples:
  - name: Delete a federated credential
    text: az identity federated-credential delete -g MyResourceGroup --identity-name MyIdentity -n MyFicName
"""

helps['identity federated-credential show'] = """
type: command
short-summary: [Preview] Show details of a federated credential.
"""

helps['identity federated-credential list'] = """
type: command
short-summary: [Preview] List all federated credentials for a managed identity.
"""
