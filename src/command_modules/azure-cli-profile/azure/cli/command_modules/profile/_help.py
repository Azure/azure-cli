# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from knack.help_files import helps  # pylint: disable=unused-import

helps['login'] = """
    type: command
    short-summary: Log in to Azure.
    examples:
        - name: Log in interactively.
          text: >
            az login
        - name: Log in with user name and password. This doesn't work with Microsoft accounts or accounts that have two-factor authentication enabled.
          text: >
            az login -u johndoe@contoso.com -p VerySecret
        - name: Log in with a service principal using client secret.
          text: >
            az login --service-principal -u http://azure-cli-2016-08-05-14-31-15 -p VerySecret --tenant contoso.onmicrosoft.com
        - name: Log in with a service principal using client certificate.
          text: >
            az login --service-principal -u http://azure-cli-2016-08-05-14-31-15 -p ~/mycertfile.pem --tenant contoso.onmicrosoft.com
        - name: Log in using a VM's system assigned identity
          text: >
            az login --identity
        - name: Log in using a VM's user assigned identity. Client or object ids of the service identity also work
          text: >
            az login --identity -u /subscriptions/<subscriptionId>/resourcegroups/myRG/providers/Microsoft.ManagedIdentity/userAssignedIdentities/myID
    """

helps['account'] = """
    type: group
    short-summary: Manage Azure subscription information.
"""

helps['account clear'] = """
    type: command
    short-summary: Clear all subscriptions from the CLI's local cache.
    long-summary: To clear the current subscription, use 'az logout'.
"""

helps['account list'] = """
    type: command
    short-summary: Get a list of subscriptions for the logged in account.
"""

helps['account list-locations'] = """
    type: command
    short-summary: List supported regions for the current subscription.
"""

helps['account show'] = """
    type: command
    short-summary: Get the details of a subscription.
    long-summary: If no subscription is specified, shows the current subscription.
"""

helps['account set'] = """
    type: command
    short-summary: Set a subscription to be the current active subscription.
"""

helps['account show'] = """
    type: command
    short-summary: Get the details of a subscription.
    long-summary: If the subscription isn't specified, shows the details of the default subscription.
"""

helps['account get-access-token'] = """
    type: command
    short-summary: Get a token for utilities to access Azure.
    long-summary: >
        The token will be valid for at least 5 minutes with the maximum at 60 minutes.
        If the subscription argument isn't specified, the current account is used.
"""
