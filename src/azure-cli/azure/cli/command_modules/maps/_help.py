# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps['maps'] = """
    type: group
    short-summary: Manage Azure Maps.
"""

helps['maps account'] = """
    type: group
    short-summary: Manage Azure Maps accounts.
"""

helps['maps account keys'] = """
    type: group
    short-summary: Manage Azure Maps account keys.
"""

helps['maps account show'] = """
    type: command
    short-summary: Show the details of a maps account.
"""

helps['maps account list'] = """
    type: command
    short-summary: Show all maps accounts in a subscription or in a resource group.
"""

helps['maps account create'] = """
    type: command
    short-summary: Create a maps account.
    parameters:
        - name: --accept-tos
          short-summary: Accept the Terms of Service, and do not prompt for confirmation.
          long-summary: |
              By creating an Azure Maps account, you agree that you have read and agree to the
              License (https://azure.microsoft.com/en-us/support/legal/) and
              Privacy Statement (https://privacy.microsoft.com/en-us/privacystatement).

"""

helps['maps account update'] = """
    type: command
    short-summary: Update the properties of a maps account.
"""

helps['maps account delete'] = """
    type: command
    short-summary: Delete a maps account.
"""

helps['maps account keys list'] = """
    type: command
    short-summary: List the keys to use with the Maps APIs.
    long-summary: |
        A key is used to authenticate and authorize access to the Maps REST APIs. Only one key is needed at a time; two are given to provide seamless key regeneration.
"""

helps['maps account keys renew'] = """
    type: command
    short-summary: Renew either the primary or secondary key for use with the Maps APIs.
    long-summary: |
        This command immediately invalidates old API keys. Only the renewed keys can be used to connect to maps.
"""
