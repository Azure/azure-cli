# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.cli.core.help_files import helps  # pylint: disable=unused-import

helps['login'] = """
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
            """

helps['account'] = """
    type: group
    short-summary: Manage subscriptions.
"""

helps['account clear'] = """
    type: command
    short-summary: Clear all subscriptions from the CLI's local cache.
    long-summary: To clear the current subscription, use 'az logout'.
"""

helps['account list'] = """
    type: command
    short-summary: Get a list of subscriptions for the account.
"""

helps['account list-locations'] = """
    type: command
    short-summary: List supported regions of the current subscription.
"""

helps['account show'] = """
    type: command
    short-summary: Show the details of a subscription.
    long-summary: If no subscription is specified, shows the current subscription.
"""

helps['account set'] = """
    type: command
    short-summary: Set a subscription as the current subscription.
"""

helps['account show'] = """
    type: command
    short-summary: Show the details of a subscription.
    long-summary: If the subscription isn't specified, shows the details of the default subscription.
"""

helps['account get-access-token'] = """
    type: command
    long-summary: provides the token for trusted utils to access your Azure subscriptions. The token will be valid for at least 5 minutes with the maximum at 60 minutes. If the subscription argument isn't specified, the current account is used.
"""
