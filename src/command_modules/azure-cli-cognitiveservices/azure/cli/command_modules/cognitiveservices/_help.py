# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps


helps['cognitiveservices'] = """
    type: group
    short-summary: Manage Azure Cognitive Services accounts.
"""

helps['cognitiveservices list'] = """
    type: command
    short-summary: List available Azure Cognitive Services accounts.
    examples:
        - name: List all the Cognitive Services accounts in a resource group.
          text: az cognitiveservices list -g MyResourceGroup
"""

helps['cognitiveservices account'] = """
    type: group
    short-summary: Manage Azure Cognitive Services accounts.
"""

helps['cognitiveservices account delete'] = """
    type: command
    short-summary: Delete an Azure Cognitive Services account.
"""

helps['cognitiveservices account create'] = """
    type: command
    short-summary: Create an Azure Cognitive Services account.
    examples:
        - name: Create an S0 face API Cognitive Services account in West Europe without confirmation required.
          text: az cognitiveservices create -n myresource -g myResourceGroup --kind Face --sku S0 -l WestEurope --yes
"""

helps['cognitiveservices account show'] = """
    type: command
    short-summary: Get the details of an Azure Cognitive Services account.
"""

helps['cognitiveservices account update'] = """
    type: command
    short-summary: Update the properties of an Azure Cognitive Services account.
"""

helps['cognitiveservices account list-skus'] = """
    type: command
    short-summary: List the SKUs avaiable for an Azure Cognitive Services account.
"""


helps['cognitiveservices account keys'] = """
    type: group
    short-summary: Manage the keys of an Azure Cognitive Services account.
"""

helps['cognitiveservices account keys regenerate'] = """
    type: command
    short-summary: Regenerate the keys of an Azure Cognitive Services account.
"""

helps['cognitiveservices account keys list'] = """
    type: command
    short-summary: List the keys of an Azure Cognitive Services account.
"""
