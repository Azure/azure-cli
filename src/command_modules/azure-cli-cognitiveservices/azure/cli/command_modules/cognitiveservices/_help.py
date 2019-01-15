# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["cognitiveservices account keys list"] = """
"type": |-
    command
"short-summary": |-
    Manage Azure Cognitive Services accounts.
"long-summary": |-
    This article lists the Azure CLI commands for Azure Cognitive Services account and subscription management only. Refer to the documentation at https://docs.microsoft.com/azure/cognitive-services/ for individual services to learn how to use the APIs and supported SDKs.
"examples":
-   "name": |-
        List the keys of an Azure Cognitive Services account.
    "text": |-
        az cognitiveservices account keys list --name myresource --resource-group cognitive-services-resource-group
"""

helps["cognitiveservices list"] = """
"type": |-
    command
"short-summary": |-
    Manage Azure Cognitive Services accounts.
"long-summary": |-
    This article lists the Azure CLI commands for Azure Cognitive Services account and subscription management only. Refer to the documentation at https://docs.microsoft.com/azure/cognitive-services/ for individual services to learn how to use the APIs and supported SDKs.
"""

helps["cognitiveservices"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Cognitive Services accounts.
"long-summary": |-
    This article lists the Azure CLI commands for Azure Cognitive Services account and subscription management only. Refer to the documentation at https://docs.microsoft.com/azure/cognitive-services/ for individual services to learn how to use the APIs and supported SDKs.
"""

helps["cognitiveservices account update"] = """
"type": |-
    command
"short-summary": |-
    Manage Azure Cognitive Services accounts.
"long-summary": |-
    This article lists the Azure CLI commands for Azure Cognitive Services account and subscription management only. Refer to the documentation at https://docs.microsoft.com/azure/cognitive-services/ for individual services to learn how to use the APIs and supported SDKs.
"parameters":
-   "name": |-
        --sku
    "populator-commands":
    - |-
        az cognitiveservices account list-skus
"""

helps["cognitiveservices account create"] = """
"type": |-
    command
"short-summary": |-
    Manage Azure Cognitive Services accounts.
"long-summary": |-
    This article lists the Azure CLI commands for Azure Cognitive Services account and subscription management only. Refer to the documentation at https://docs.microsoft.com/azure/cognitive-services/ for individual services to learn how to use the APIs and supported SDKs.
"parameters":
-   "name": |-
        --kind
    "populator-commands":
    - |-
        az cognitiveservices account list-kinds
-   "name": |-
        --sku
    "populator-commands":
    - |-
        az cognitiveservices account list-skus
"examples":
-   "name": |-
        Create an Azure Cognitive Services account.
    "text": "az cognitiveservices account create --sku S0 --location WestEurope --name\
        \ myresource --kind Face --resource-group myResourceGroup --yes "
"""

helps["cognitiveservices account list"] = """
"type": |-
    command
"short-summary": |-
    Manage Azure Cognitive Services accounts.
"long-summary": |-
    This article lists the Azure CLI commands for Azure Cognitive Services account and subscription management only. Refer to the documentation at https://docs.microsoft.com/azure/cognitive-services/ for individual services to learn how to use the APIs and supported SDKs.
"""

helps["cognitiveservices account list-skus"] = """
"type": |-
    command
"short-summary": |-
    Manage Azure Cognitive Services accounts.
"long-summary": |-
    This article lists the Azure CLI commands for Azure Cognitive Services account and subscription management only. Refer to the documentation at https://docs.microsoft.com/azure/cognitive-services/ for individual services to learn how to use the APIs and supported SDKs.
"parameters":
-   "name": |-
        --name -n
    "long-summary": |
        --kind and --location will be ignored when --name is specified.
        --resource-group is required when when --name is specified.
-   "name": |-
        --resource-group -g
    "long-summary": |
        --resource-group is used when when --name is specified. In other cases it will be ignored.
-   "name": |-
        --kind
    "populator-commands":
    - |-
        az cognitiveservices account list-kinds
"""

helps["cognitiveservices account delete"] = """
"type": |-
    command
"short-summary": |-
    Manage Azure Cognitive Services accounts.
"long-summary": |-
    This article lists the Azure CLI commands for Azure Cognitive Services account and subscription management only. Refer to the documentation at https://docs.microsoft.com/azure/cognitive-services/ for individual services to learn how to use the APIs and supported SDKs.
"""

helps["cognitiveservices account keys"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Cognitive Services accounts.
"long-summary": |-
    This article lists the Azure CLI commands for Azure Cognitive Services account and subscription management only. Refer to the documentation at https://docs.microsoft.com/azure/cognitive-services/ for individual services to learn how to use the APIs and supported SDKs.
"""

helps["cognitiveservices account"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Cognitive Services accounts.
"long-summary": |-
    This article lists the Azure CLI commands for Azure Cognitive Services account and subscription management only. Refer to the documentation at https://docs.microsoft.com/azure/cognitive-services/ for individual services to learn how to use the APIs and supported SDKs.
"""

helps["cognitiveservices account show"] = """
"type": |-
    command
"short-summary": |-
    Manage Azure Cognitive Services accounts.
"long-summary": |-
    This article lists the Azure CLI commands for Azure Cognitive Services account and subscription management only. Refer to the documentation at https://docs.microsoft.com/azure/cognitive-services/ for individual services to learn how to use the APIs and supported SDKs.
"""

helps["cognitiveservices account keys regenerate"] = """
"type": |-
    command
"short-summary": |-
    Manage Azure Cognitive Services accounts.
"long-summary": |-
    This article lists the Azure CLI commands for Azure Cognitive Services account and subscription management only. Refer to the documentation at https://docs.microsoft.com/azure/cognitive-services/ for individual services to learn how to use the APIs and supported SDKs.
"""

