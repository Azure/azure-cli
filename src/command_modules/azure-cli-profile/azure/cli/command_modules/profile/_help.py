# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["account set"] = """
"type": |-
    command
"short-summary": |-
    Set a subscription to be the current active subscription.
"examples":
-   "name": |-
        Set a subscription to be the current active subscription.
    "text": |-
        az account set --subscription MySubscription
"""

helps["login"] = """
"type": |-
    command
"short-summary": |-
    Log in to Azure.
"""

helps["account list-locations"] = """
"type": |-
    command
"short-summary": |-
    List supported regions for the current subscription.
"""

helps["account"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure subscription information.
"""

helps["account show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a subscription.
"long-summary": |-
    If the subscription isn't specified, shows the details of the default subscription.
"""

helps["account list"] = """
"type": |-
    command
"short-summary": |-
    Get a list of subscriptions for the logged in account.
"""

helps["account clear"] = """
"type": |-
    command
"short-summary": |-
    Clear all subscriptions from the CLI's local cache.
"long-summary": |-
    To clear the current subscription, use 'az logout'.
"""

helps["self-test"] = """
"type": |-
    command
"short-summary": |-
    Runs a self-test of the CLI.
"""

helps["account get-access-token"] = """
"type": |-
    command
"short-summary": |-
    Get a token for utilities to access Azure.
"long-summary": |
    The token will be valid for at least 5 minutes with the maximum at 60 minutes. If the subscription argument isn't specified, the current account is used.
"""

