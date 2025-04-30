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
min_api: 2025-01-31-PREVIEW
"""

helps['identity federated-credential create'] = """
type: command
min_api: 2025-01-31-PREVIEW
short-summary: Create a federated identity credential under an existing user assigned identity.
"""

helps['identity federated-credential update'] = """
min_api: 2025-01-31-PREVIEW
type: command
short-summary: Update a federated identity credential under an existing user assigned identity.
"""

helps['identity federated-credential delete'] = """
min_api: 2025-01-31-PREVIEW
type: command
short-summary: Delete a federated identity credential under an existing user assigned identity.
"""

helps['identity federated-credential show'] = """
min_api: 2025-01-31-PREVIEW
type: command
short-summary: Show a federated identity credential under an existing user assigned identity.
"""

helps['identity federated-credential list'] = """
min_api: 2025-01-31-PREVIEW
type: command
short-summary: List all federated identity credentials under an existing user assigned identity.
"""
