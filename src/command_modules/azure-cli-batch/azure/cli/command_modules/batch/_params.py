# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from argcomplete.completers import FilesCompleter
from azure.mgmt.batch.models.batch_management_client_enums import \
    (AccountKeyType)

from azure.cli.core.commands import \
    (register_cli_argument, CliArgumentType)
from azure.cli.core.commands.parameters import \
    (tags_type, location_type, resource_group_name_type,
     get_resource_name_completion_list, enum_choice_list)

from ._validators import \
    (application_enabled)

# pylint: disable=line-too-long
# ARGUMENT DEFINITIONS

batch_name_type = CliArgumentType(help='Name of the Batch account.', options_list=('--account_name',), completer=get_resource_name_completion_list('Microsoft.Batch/batchAccounts'), id_part=None)


# PARAMETER REGISTRATIONS

register_cli_argument('batch', 'account_name', batch_name_type, options_list=('--name', '-n'))
register_cli_argument('batch', 'resource_group_name', resource_group_name_type, completer=None, validator=None)
register_cli_argument('batch account create', 'location', location_type)
register_cli_argument('batch account create', 'tags', tags_type)
register_cli_argument('batch account set', 'tags', tags_type)
register_cli_argument('batch account keys renew', 'key_name', **enum_choice_list(AccountKeyType))
register_cli_argument('batch application', 'account_name', batch_name_type, options_list=('--name', '-n'), validator=application_enabled)
register_cli_argument('batch application package create', 'package_file', help='The path of the application package in zip format', completer=FilesCompleter())
register_cli_argument('batch location quotas show', 'location_name', location_type)
