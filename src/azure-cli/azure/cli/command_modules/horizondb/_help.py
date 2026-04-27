# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import

# pylint: disable=line-too-long, too-many-lines


helps['horizondb'] = """
type: group
short-summary: Manage Azure HorizonDB.
"""


helps['horizondb show'] = """
type: command
short-summary: Show details of an Azure HorizonDB instance.
examples:
  - name: Show details of an Azure HorizonDB instance.
    text: az horizondb show --name examplecluster --resource-group exampleresourcegroup
"""