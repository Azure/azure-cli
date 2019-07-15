# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps


helps['cognitiveservices'] = """
    type: group
    short-summary: Manage Azure Cognitive Services accounts.
    long-summary: This article lists the Azure CLI commands for Azure Cognitive Services account and subscription management only. Refer to the documentation at https://docs.microsoft.com/azure/cognitive-services/ for individual services to learn how to use the APIs and supported SDKs.
"""

helps['cognitiveservices list'] = """
    type: command
    short-summary: Manage Azure Cognitive Services accounts.
    long-summary: This article lists the Azure CLI commands for Azure Cognitive Services account and subscription management only. Refer to the documentation at https://docs.microsoft.com/azure/cognitive-services/ for individual services to learn how to use the APIs and supported SDKs.
    examples:
        - name: List all the Cognitive Services accounts in a resource group.
          text: az cognitiveservices list -g MyResourceGroup
"""

helps['cognitiveservices account list'] = """
    type: command
    short-summary: Manage Azure Cognitive Services accounts.
    long-summary: This article lists the Azure CLI commands for Azure Cognitive Services account and subscription management only. Refer to the documentation at https://docs.microsoft.com/azure/cognitive-services/ for individual services to learn how to use the APIs and supported SDKs.
    examples:
        - name: List all the Cognitive Services accounts in a resource group.
          text: az cognitiveservices account list -g MyResourceGroup
"""

helps['cognitiveservices account'] = """
    type: group
    short-summary: Manage Azure Cognitive Services accounts.
    long-summary: This article lists the Azure CLI commands for Azure Cognitive Services account and subscription management only. Refer to the documentation at https://docs.microsoft.com/azure/cognitive-services/ for individual services to learn how to use the APIs and supported SDKs.
"""

helps['cognitiveservices account delete'] = """
    type: command
    short-summary: Manage Azure Cognitive Services accounts.
    long-summary: This article lists the Azure CLI commands for Azure Cognitive Services account and subscription management only. Refer to the documentation at https://docs.microsoft.com/azure/cognitive-services/ for individual services to learn how to use the APIs and supported SDKs.
    examples:
        - name: Delete account.
          text: az cognitiveservices account delete --name myresource-luis -g cognitive-services-resource-group
"""

helps['cognitiveservices account create'] = """
    type: command
    short-summary: Manage Azure Cognitive Services accounts.
    long-summary: This article lists the Azure CLI commands for Azure Cognitive Services account and subscription management only. Refer to the documentation at https://docs.microsoft.com/azure/cognitive-services/ for individual services to learn how to use the APIs and supported SDKs.
    parameters:
        - name: --kind
          populator-commands:
            - az cognitiveservices account list-kinds
        - name: --sku
          populator-commands:
            - az cognitiveservices account list-skus
    examples:
        - name: Create an S0 face API Cognitive Services account in West Europe without confirmation required.
          text: az cognitiveservices account create -n myresource -g myResourceGroup --kind Face --sku S0 -l WestEurope --yes
"""

helps['cognitiveservices account show'] = """
    type: command
    short-summary: Manage Azure Cognitive Services accounts.
    long-summary: This article lists the Azure CLI commands for Azure Cognitive Services account and subscription management only. Refer to the documentation at https://docs.microsoft.com/azure/cognitive-services/ for individual services to learn how to use the APIs and supported SDKs.
    examples:
        - name: Show account information.
          text: az cognitiveservices account show --name myresource --resource-group cognitive-services-resource-group
"""

helps['cognitiveservices account update'] = """
    type: command
    short-summary: Manage Azure Cognitive Services accounts.
    long-summary: This article lists the Azure CLI commands for Azure Cognitive Services account and subscription management only. Refer to the documentation at https://docs.microsoft.com/azure/cognitive-services/ for individual services to learn how to use the APIs and supported SDKs.
    parameters:
        - name: --sku
          populator-commands:
            - az cognitiveservices account list-skus
    examples:
        - name: Update sku and tags.
          text: az cognitiveservices account update --name myresource -g cognitive-services-resource-group --sku S0 --tags external-app=chatbot-HR azure-web-app-bot=HR-external azure-app-service=HR-external-app-service
"""

helps['cognitiveservices account list-skus'] = """
    type: command
    short-summary: Manage Azure Cognitive Services accounts.
    long-summary: This article lists the Azure CLI commands for Azure Cognitive Services account and subscription management only. Refer to the documentation at https://docs.microsoft.com/azure/cognitive-services/ for individual services to learn how to use the APIs and supported SDKs.
    parameters:
        - name: --name -n
          long-summary: |
              --kind and --location will be ignored when --name is specified.
              --resource-group is required when when --name is specified.
        - name: --resource-group -g
          long-summary: |
              --resource-group is used when when --name is specified. In other cases it will be ignored.
        - name: --kind
          populator-commands:
            - az cognitiveservices account list-kinds
    examples:
        - name: Show SKUs.
          text: az cognitiveservices account list-skus --kind Face --location westus
"""


helps['cognitiveservices account keys'] = """
    type: group
    short-summary: Manage Azure Cognitive Services accounts.
    long-summary: This article lists the Azure CLI commands for Azure Cognitive Services account and subscription management only. Refer to the documentation at https://docs.microsoft.com/azure/cognitive-services/ for individual services to learn how to use the APIs and supported SDKs.
"""

helps['cognitiveservices account keys regenerate'] = """
    type: command
    short-summary: Manage Azure Cognitive Services accounts.
    long-summary: This article lists the Azure CLI commands for Azure Cognitive Services account and subscription management only. Refer to the documentation at https://docs.microsoft.com/azure/cognitive-services/ for individual services to learn how to use the APIs and supported SDKs.
    examples:
        - name: Get new keys for resource.
          text: az cognitiveservices account keys regenerate --name myresource -g cognitive-services-resource-group --key-name key1
"""

helps['cognitiveservices account keys list'] = """
    type: command
    short-summary: Manage Azure Cognitive Services accounts.
    long-summary: This article lists the Azure CLI commands for Azure Cognitive Services account and subscription management only. Refer to the documentation at https://docs.microsoft.com/azure/cognitive-services/ for individual services to learn how to use the APIs and supported SDKs.
    examples:
        - name: Get current resource keys.
          text: az cognitiveservices account keys list --name myresource -g cognitive-services-resource-group
"""
