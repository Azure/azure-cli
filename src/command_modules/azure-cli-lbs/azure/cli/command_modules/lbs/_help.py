# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps['lbs'] = """
    type: group
    short-summary: Manage Azure Location Based Services accounts.
"""

helps['lbs account'] = """
    type: group
    short-summary: Commands to manage Azure Location Based Services accounts.
"""

helps['lbs account key'] = """
    type: group
    short-summary: Commands to manage Azure Location Based Services account keys.
"""

helps['lbs account show'] = """
    type: command
    short-summary: Show a Location Based Services account.
"""

helps['lbs account list'] = """
    type: command
    short-summary: Show all Location Based Services accounts in a Subscription or in a Resource Group.
"""

helps['lbs account create'] = """
    type: command
    short-summary: Create a Location Based Services account.
    long-summary: |
        Create a Location Based Services account. A Location Based Services account holds the keys which allow access to the Location Based Services REST APIs.
"""

helps['lbs account delete'] = """
    type: command
    short-summary: Delete a Location Based Services account.
"""

helps['lbs account key list'] = """
    type: command
    short-summary: List the keys to use with the Location Based Services APIs.
    long-summary: |
        List the keys to use with the Location Based Services APIs. A key is used to authenticate and authorize access to the Location Based Services REST APIs. Only one key is needed at a time; two are given to provide seamless key regeneration.
"""

helps['lbs account key regenerate'] = """
    type: command
    short-summary: Regenerate either the primary or secondary key for use with the Location Based Services APIs.
    long-summary: |
        Regenerate either the primary or secondary key for use with the Location Based Services APIs. The old key will stop working immediately.
"""
