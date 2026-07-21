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

  - name: Create an identity with regional assignment restrictions.
    text: |
        az identity create --name MyIdentity --resource-group MyResourceGroup --isolation-scope Regional
"""

helps['identity update'] = """
type: command
short-summary: Update an identity.
examples:
  - name: Update an identity to restrict assignment within an Azure region.
    text: |
        az identity update --name MyIdentity --resource-group MyResourceGroup --isolation-scope Regional
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
