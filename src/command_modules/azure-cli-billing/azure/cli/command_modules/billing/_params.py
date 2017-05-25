# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import register_cli_argument

register_cli_argument('billing invoice list', 'generate_url', options_list=('--generate-download-url', '-d'), action='store_true', required=False, help='generate download url of the invoice')
register_cli_argument('billing invoice show', 'name', options_list=('--name', '-n'), required=False, help='name of the invoice')
register_cli_argument('billing period show', 'billing_period_name', options_list=('--name', '-n'), help='name of the billing period')
