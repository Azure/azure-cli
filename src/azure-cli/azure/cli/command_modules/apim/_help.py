# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import


helps['apim'] = """
    type: group
    short-summary: Commands to manage Azure API Management service instance.
"""

helps['apim create'] = """
    type: command
    short-summary: Create an API Management service instance.

examples:
  - name: Create a Developer tier API Management instance
    text: az aks create -g MyResourceGroup -n MyManagedCluster --ssh-key-value /path/to/publickey
    text: az apim create --name MyApim -g MyResourceGroup -l eastus --sku Developer --publisher-email email@mydomain.com --enable-client-certificate true
"""

helps['apim list'] = """
    type: command
    short-summary: List API Management service instances.
"""

helps['apim delete'] = """
    type: command
    short-summary: Delete an API Management service instance.
"""

helps['apim show'] = """
    type: command
    short-summary: Show details of an APIM instance.
"""

helps['apim update'] = """
    type: command
    short-summary: Update an API Management serviceaz  instance.
"""

helps['apim api list'] = """
    type: command
    short-summary: List all API's for a service instance.
"""

helps['apim backup'] = """
    type: command
    short-summary: Creates a backup of the API Management service to the given Azure
        Storage Account. This is long running operation and could take several
        minutes to complete.
"""

