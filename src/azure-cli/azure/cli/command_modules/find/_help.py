# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['find'] = """
type: command
short-summary: I'm an AI robot, my advice is based on our Azure documentation as well as the usage patterns of Azure CLI and Azure ARM users. Using me improves Azure products and documentation.
examples:
  - name: Give me any Azure CLI group and I’ll show the most popular commands within the group.
    text: |
        az find "az storage"
  - name: Give me any Azure CLI command and I’ll show the most popular parameters and subcommands.
    text: |
        az find "az monitor activity-log list"
  - name: You can also enter a search term, and I'll try to help find the best commands.
    text: |
        az find "arm template"
"""
