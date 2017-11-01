# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps['find'] = """
    type: command
    short-summary: Find Azure CLI commands.
    examples:
      - name: Search for commands containing 'vm' or 'secret'
        text: >
            az find -q vm secret
"""
