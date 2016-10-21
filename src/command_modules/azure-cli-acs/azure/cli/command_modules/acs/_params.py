#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.commands import register_cli_argument
from azure.cli.core.commands.parameters import (
    name_type,
    resource_group_name_type)

register_cli_argument('acs dcos browse', 'name', name_type)
register_cli_argument('acs dcos browse', 'resource_group_name', resource_group_name_type)
