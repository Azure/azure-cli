# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from argcomplete.completers import FilesCompleter, DirectoriesCompleter
from azure.mgmt.batch.models.batch_management_client_enums import \
    (AccountKeyType)

from azure.batch.models.batch_service_client_enums import \
    (ComputeNodeDeallocationOption)

from azure.cli.core.commands import \
    (register_cli_argument, CliArgumentType, register_extra_cli_argument)
from azure.cli.core.commands.parameters import \
    (tags_type, location_type, resource_group_name_type,
     get_resource_name_completion_list, enum_choice_list, file_type)

from ._validators import \
    (application_enabled, datetime_type, validate_metadata, storage_account_id)

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

#register_cli_argument('batch', 'if_modified_since', help='Specify this header to perform the operation only if the resource has been modified since the specified date/time.', type=datetime_type, arg_group='Pre-condition')
#register_cli_argument('batch', 'if_unmodified_since', help='Specify this header to perform the operation only if the resource has not been modified since the specified date/time.', type=datetime_type, arg_group='Pre-condition')
#register_cli_argument('batch', 'if_match', help='An ETag is specified. Specify this header to perform the operation only if the resource\'s ETag is an exact match as specified', arg_group='Pre-condition')
#register_cli_argument('batch', 'if_none_match', help='An ETag is specified. Specify this header to perform the operation only if the resource\'s ETag does not match the specified ETag.', arg_group='Pre-condition')

#register_cli_argument('batch', 'filter', help=' An OData $filter clause.', arg_group='OData')
#register_cli_argument('batch', 'select', help=' An OData $select clause.', arg_group='OData')
#register_cli_argument('batch', 'expand', help=' An OData $expand clause.', arg_group='OData')

#register_cli_argument('batch', 'json_file', help='The file containing the object to create in JSON format, if this parameter is specified, all other parameters are ignored.', completer=FilesCompleter())
#register_cli_argument('batch', 'metadata', nargs='+', help='Metadata in space-separated key=value pairs. The Batch service does not assign any meaning to metadata; it is solely for the use of user code.', validator=validate_metadata)
#register_cli_argument('batch', 'certificate_references', nargs='+', help='The space separated list of thumbprints specifying the certificates to be installed on each compute node in the pool.')
#register_cli_argument('batch', 'application_package_references', nargs='+', help='The space separated list of ids specifying the application packages to be installed.')
#register_cli_argument('batch', 'abort', action='store_true', help='Cancel the current operation.')

#register_cli_argument('batch', 'thumbprint', help='The certificate thumbprint.')
#register_cli_argument('batch', 'thumbprint_algorithm', help='The certificate thumbprint algorithm.')

#register_cli_argument('batch certificate', 'password', help='The password to access the certificate\'s private key.')
#register_cli_argument('batch certificate', 'cert_file', help='The certificate file: cer file or pfx file.', completer=FilesCompleter())

#register_cli_argument('batch pool', 'pool_id', help='The ID of the pool.')
#register_cli_argument('batch pool', 'node_agent_sku_id', help='The SKU of the Batch node agent to be provisioned on compute nodes in the pool.')
#register_cli_argument('batch pool', 'image_publisher', help='The publisher of the Azure Virtual Machines Marketplace image.')
#register_cli_argument('batch pool', 'image_offer', help='The offer type of the Azure Virtual Machines Marketplace image.')
#register_cli_argument('batch pool', 'image_sku', help='The SKU of the Azure Virtual Machines Marketplace image.')
#register_cli_argument('batch pool', 'os_family', help='The Azure Guest OS family to be installed on the virtual machines in the pool.')
#register_cli_argument('batch pool', 'start_task_cmd', help='The command line of the start task.')
#register_cli_argument('batch pool', 'node_deallocation_option', **enum_choice_list(ComputeNodeDeallocationOption))

#register_cli_argument('batch job', 'pool_id', help='The ID of an existing pool.')
#register_cli_argument('batch job', 'job_id', help='The ID of the job.')
#register_cli_argument('batch job list', 'job_schedule_id', help='The ID of the job schedule from which you want to get a list of jobs.')

#register_cli_argument('batch job-schedule', 'pool_id', help='The ID of an existing pool.')
#register_cli_argument('batch job-schedule', 'job_schedule_id', help='The ID of the job schedule.')
#register_cli_argument('batch job-schedule', 'priority', help='The priority of jobs created under this schedule.')

#register_cli_argument('batch task', 'job_id', help='The ID of the job containing the task.')
#register_cli_argument('batch task', 'task_id', help='The ID of the task.')

#register_cli_argument('batch', 'start_range', help='The start position of byte range to be retreved.')
#register_cli_argument('batch', 'end_range', help='The end position of byte range to be retreved.')
#register_cli_argument('batch', 'destination_path', help='The path to the destination file or directory.', completer=DirectoriesCompleter())
