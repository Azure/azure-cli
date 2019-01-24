# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps['find'] = """
    type: command
    short-summary: I'm an AI robot, my advice is based on our Azure documentation as well as the usage patterns of Azure CLI and Azure ARM users. Using me improves Azure products and documentation.
    examples:
        - name: Give me any Azure CLI command or group and I’ll show the most popular commands and parameters.
          text: |
            az find 'az [group]'           : az find 'az storage'
            az find 'az [group] [command]' : az find 'az monitor activity-log list'
        - name: You can also enter a search term, and I'll try to help find the best commands.
          text: |
            az find '[query]' : az find 'arm template'
"""
