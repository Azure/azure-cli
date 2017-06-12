# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliArgumentType, register_cli_argument


query = CliArgumentType(
    options_list=('--search-query', '-q'),
    help='Query text to find.',
    nargs='+'
)

register_cli_argument('find', 'criteria', query)
