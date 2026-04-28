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


helps['horizondb create'] = """
type: command
short-summary: Create a new Azure HorizonDB cluster.
examples:
  - name: Create a new HorizonDB cluster.
    text: az horizondb create --name examplecluster --resource-group exampleresourcegroup --location centralus --admin-user myadmin --admin-password examplepassword --version 17 --v-cores 4 --replica-count 3
  - name: Create a HorizonDB cluster with zone placement policy.
    text: az horizondb create --name examplecluster --resource-group exampleresourcegroup --location centralus --admin-user myadmin --admin-password examplepassword --version 17 --v-cores 4 --replica-count 3 --zone-placement-policy Strict
"""


helps['horizondb delete'] = """
type: command
short-summary: Delete an Azure HorizonDB cluster.
examples:
  - name: Delete an Azure HorizonDB cluster.
    text: az horizondb delete --name examplecluster --resource-group exampleresourcegroup
"""


helps['horizondb show'] = """
type: command
short-summary: Show details of an Azure HorizonDB cluster.
examples:
  - name: Show details of an Azure HorizonDB cluster.
    text: az horizondb show --name examplecluster --resource-group exampleresourcegroup
"""
