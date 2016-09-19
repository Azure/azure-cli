#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps #pylint: disable=unused-import

#pylint: disable=line-too-long
helps['login'] = """
            examples:
                - name: login interactively (work for all user account types)
                  text: >
                    az login
                - name: login with user name and password(doesn't work with two-factor authentication enabled accounts or Microsoft accounts, like live id)
                  text: >
                    az login -u johndoe@contoso.com -p VerySecret
                - name: login with service principal
                  text: >
                    az login --service-principal -u http://azure-cli-2016-08-05-14-31-15 -p VerySecret --tenant contoso.onmicrosoft.com
            """

helps['account'] = """
    type: group
    short-summary: Manages stored and default subscriptions
"""