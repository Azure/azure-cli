# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# pylint: disable=line-too-long
def load_arguments(self, _):
    with self.argument_context('billing invoice list') as c:
        c.argument('generate_url', options_list=['--generate-download-url', '-d'], action='store_true', required=False, help='generate download url of the invoice')

    with self.argument_context('billing invoice show') as c:
        c.argument('name', options_list=['--name', '-n'], required=False, help='name of the invoice')

    with self.argument_context('billing period show') as c:
        c.argument('billing_period_name', options_list=['--name', '-n'], help='name of the billing period. Run the 'az billing period list' command to list the name of billing period')

    with self.argument_context('billing enrollment-account show') as c:
        c.argument('name', options_list=['--name', '-n'], help='name of the enrollment account')
