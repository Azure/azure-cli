# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import register_cli_argument

# pylint: disable=line-too-long
register_cli_argument('configure', 'settings', nargs='+', help="space separated 'name=value' pairs for new configurations")
