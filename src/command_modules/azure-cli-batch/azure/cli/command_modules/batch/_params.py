# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from argcomplete.completers import FilesCompleter
from azure.mgmt.batch.models.batch_management_client_enums import \
    (AccountKeyType)

from azure.cli.core.commands import \
    (register_cli_argument, CliArgumentType, register_extra_cli_argument)
from azure.cli.core.commands.parameters import \
    (tags_type, location_type, resource_group_name_type,
     get_resource_name_completion_list, enum_choice_list, file_type)

from ._validators import \
    (application_enabled, datetime_format, storage_account_id, application_package_reference_format)

# pylint: disable=line-too-long
# ARGUMENT DEFINITIONS

batch_name_type = CliArgumentType(help='Name of the Batch account.', options_list=('--account-name',), completer=get_resource_name_completion_list('Microsoft.Batch/batchAccounts'), id_part=None)

# PARAMETER REGISTRATIONS

register_cli_argument('batch', 'resource_group_name', resource_group_name_type, completer=None, validator=None)
register_cli_argument('batch account', 'account_name', batch_name_type, options_list=('--name', '-n'))
register_cli_argument('batch account create', 'location', location_type)
register_cli_argument('batch account create', 'tags', tags_type)
register_extra_cli_argument('batch account create', 'storage_account_name', help='The storage account name to be used for auto storage account.', validator=storage_account_id)
register_cli_argument('batch account set', 'tags', tags_type)
register_extra_cli_argument('batch account set', 'storage_account_name', help='The storage account name to be used for auto storage account.', validator=storage_account_id)
register_cli_argument('batch account keys renew', 'key_name', **enum_choice_list(AccountKeyType))
register_cli_argument('batch application', 'account_name', batch_name_type, options_list=('--name', '-n'), validator=application_enabled)
register_cli_argument('batch application package create', 'package_file', type=file_type, help='The path of the application package in zip format', completer=FilesCompleter())
register_cli_argument('batch location quotas show', 'location_name', location_type)

for command in ['list', 'show', 'create', 'set', 'delete', 'package']:
    register_cli_argument('batch application {}'.format(command), 'account_name', batch_name_type, options_list=('--name', '-n'), validator=application_enabled)

register_cli_argument('batch pool resize', 'if_modified_since', help='Specify this header to perform the operation only if the resource has been modified since the specified date/time.', type=datetime_format, arg_group='Pre-condition')
register_cli_argument('batch pool resize', 'if_unmodified_since', help='Specify this header to perform the operation only if the resource has not been modified since the specified date/time.', type=datetime_format, arg_group='Pre-condition')
register_cli_argument('batch pool resize', 'if_match', help='An ETag is specified. Specify this header to perform the operation only if the resource\'s ETag is an exact match as specified', arg_group='Pre-condition')
register_cli_argument('batch pool resize', 'if_none_match', help='An ETag is specified. Specify this header to perform the operation only if the resource\'s ETag does not match the specified ETag.', arg_group='Pre-condition')
register_cli_argument('batch pool resize', 'pool_id', help='The ID of the pool.')
register_cli_argument('batch pool resize', 'abort', action='store_true', help='Stop the pool resize operation.')

register_cli_argument('batch job list', 'filter', help=' An OData $filter clause.', arg_group='OData')
register_cli_argument('batch job list', 'select', help=' An OData $select clause.', arg_group='OData')
register_cli_argument('batch job list', 'expand', help=' An OData $expand clause.', arg_group='OData')
register_cli_argument('batch job list', 'job_schedule_id', help='The ID of the job schedule from which you want to get a list of jobs.')

register_cli_argument('batch certificate', 'thumbprint', help='The certificate thumbprint.')
register_cli_argument('batch certificate', 'thumbprint_algorithm', help='The certificate thumbprint algorithm.')
register_cli_argument('batch certificate', 'password', help='The password to access the certificate\'s private key.')
register_cli_argument('batch certificate', 'cert_file', help='The certificate file: cer file or pfx file.', completer=FilesCompleter())
register_cli_argument('batch certificate delete', 'abort', action='store_true', help='Cancel the certificate deletion operation.')

register_cli_argument('batch task add', 'json_file', help='The file containing the task(s) to create in JSON format, if this parameter is specified, all other parameters are ignored.', completer=FilesCompleter())
register_cli_argument('batch task add', 'application_package_references', nargs='+', help='The space separated list of ids specifying the application packages to be installed.', type=application_package_reference_format)
register_cli_argument('batch task add', 'job_id', help='The ID of the job containing the task.')
register_cli_argument('batch task add', 'task_id', help='The ID of the task.')
