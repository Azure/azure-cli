# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from argcomplete.completers import FilesCompleter
from azure.mgmt.batch.models.batch_management_client_enums import \
    (AccountKeyType)
from azure.batch.models.batch_service_client_enums import \
    (ComputeNodeDeallocationOption)

from azure.cli.core.commands import \
    (register_cli_argument, CliArgumentType, register_extra_cli_argument)
from azure.cli.core.commands.parameters import \
    (tags_type, location_type, resource_group_name_type, ignore_type,
     get_resource_name_completion_list, enum_choice_list, file_type)

from azure.cli.command_modules.batch._validators import \
    (application_enabled, datetime_format, storage_account_id, application_package_reference_format,
     validate_pool_resize_parameters, metadata_item_format,
     certificate_reference_format, validate_json_file, validate_cert_file, keyvault_id,
     environment_setting_format, validate_cert_settings, resource_file_format, load_node_agent_skus)

from azure.cli.command_modules.batch._command_type import validate_client_parameters

# pylint: disable=line-too-long
# ARGUMENT DEFINITIONS

batch_name_type = CliArgumentType(help='Name of the Batch account.', options_list=('--account-name',), completer=get_resource_name_completion_list('Microsoft.Batch/batchAccounts'), id_part=None)

# PARAMETER REGISTRATIONS

register_cli_argument('batch', 'resource_group_name', resource_group_name_type, help='Name of the resource group', completer=None, validator=None)
register_cli_argument('batch account', 'account_name', batch_name_type, options_list=('--name', '-n'))
register_cli_argument('batch account create', 'location', location_type, help='The region in which to create the account.')
register_cli_argument('batch account create', 'tags', tags_type, help="Space separated tags in 'key[=value]' format.")
register_cli_argument('batch account create', 'storage_account', help='The storage account name or resource ID to be used for auto storage.', validator=storage_account_id)
register_cli_argument('batch account create', 'keyvault', help='The KeyVault name or resource ID to be used for an account with a pool allocation mode of \'User Subscription\'.', validator=keyvault_id)
register_cli_argument('batch account create', 'keyvault_url', ignore_type)
register_cli_argument('batch account set', 'tags', tags_type)
register_cli_argument('batch account set', 'storage_account', help='The storage account name or resource ID to be used for auto storage.', validator=storage_account_id)
register_cli_argument('batch account keys renew', 'key_name', **enum_choice_list(AccountKeyType))
register_cli_argument('batch account login', 'shared_key_auth', action='store_true', help='Using Shared Key authentication, if not specified, it will use Azure Active Directory authentication.')

register_cli_argument('batch application set', 'application_id', options_list=('--application-id',), help="The ID of the application.")
register_cli_argument('batch application set', 'allow_updates', options_list=('--allow-updates',), help="Specify to indicate whether packages within the application may be overwritten using the same version string. Specify either 'true' or 'false' to update the property.")
register_cli_argument('batch application create', 'allow_updates', options_list=('--allow-updates',), action="store_true", help="Specify to indicate whether packages within the application may be overwritten using the same version string. True if flag present.")
register_cli_argument('batch application package create', 'package_file', type=file_type, help='The path of the application package in zip format', completer=FilesCompleter())
register_cli_argument('batch application package create', 'application_id', options_list=('--application-id',), help="The ID of the application.")
register_cli_argument('batch application package create', 'version', options_list=('--version',), help="The version of the application.")
register_cli_argument('batch location quotas show', 'location_name', location_type, help='The region from which to display the Batch service quotas.')

for command in ['list', 'show', 'create', 'set', 'delete', 'package']:
    register_cli_argument('batch application {}'.format(command), 'account_name', batch_name_type, options_list=('--name', '-n'), validator=application_enabled)

# TODO: Refactor so the help text can be extracted automatically
register_cli_argument('batch pool resize', 'if_modified_since', help='The operation will be performed only if the resource has been modified since the specified timestamp.', type=datetime_format, arg_group='Pre-condition and Query')
register_cli_argument('batch pool resize', 'if_unmodified_since', help='The operation will not be performed only if the resource has been modified since the specified timestamp.', type=datetime_format, arg_group='Pre-condition and Query')
register_cli_argument('batch pool resize', 'if_match', help='The operation will be performed only if the resource\'s current ETag exactly matches the specified value.', arg_group='Pre-condition and Query')
register_cli_argument('batch pool resize', 'if_none_match', help='The operation will not be performed only if the resource\'s current ETag exactly matches the specified value.', arg_group='Pre-condition and Query')
register_cli_argument('batch pool resize', 'pool_id', help='The ID of the pool.')
register_cli_argument('batch pool resize', 'abort', action='store_true', help='Stop the pool resize operation.', validator=validate_pool_resize_parameters)
register_cli_argument('batch pool resize', 'node_deallocation_option', options_list=('--node-deallocation-option',), help='When nodes may be removed from the pool, if the pool size is decreasing.', **enum_choice_list(ComputeNodeDeallocationOption))

# TODO: Refactor so the help text can be extracted automatically
register_cli_argument('batch pool reset', 'json_file', type=file_type, help='The file containing pool update properties parameter specification in JSON format. If this parameter is specified, all \'Pool Update Properties Parameter Arguments\' are ignored.', validator=validate_json_file, completer=FilesCompleter())
register_cli_argument('batch pool reset', 'pool_id', help='The ID of the pool to update.')
register_cli_argument('batch pool reset', 'application_package_references', nargs='+', type=application_package_reference_format, arg_group='Pool')
register_cli_argument('batch pool reset', 'certificate_references', nargs='+', type=certificate_reference_format, arg_group='Pool')
register_cli_argument('batch pool reset', 'metadata', nargs='+', type=metadata_item_format, arg_group='Pool')
register_cli_argument('batch pool reset', 'start_task_command_line', arg_group='Pool: Start Task',
                      help='The command line of the start task. The command line does not run under a shell, and therefore cannot take advantage of shell features such as environment variable expansion. If you want to take advantage of such features, you should invoke the shell in the command line, for example using "cmd /c MyCommand" in Windows or "/bin/sh -c MyCommand" in Linux.')
register_cli_argument('batch pool reset', 'start_task_wait_for_success', action='store_true', arg_group='Pool: Start Task',
                      help='Whether the Batch service should wait for the start task to complete successfully (that is, to exit with exit code 0) before scheduling any tasks on the compute node. True if flag present, otherwise defaults to False.')
register_cli_argument('batch pool reset', 'start_task_max_task_retry_count', arg_group='Pool: Start Task',
                      help='The maximum number of times the task may be retried.')
register_cli_argument('batch pool reset', 'start_task_environment_settings', nargs='+', type=environment_setting_format, arg_group='Pool: Start Task',
                      help='A list of environment variable settings for the start task. Space separated values in \'key=value\' format.')

register_cli_argument('batch job list', 'filter', help=' An OData $filter clause.', arg_group='Pre-condition and Query')
register_cli_argument('batch job list', 'select', help=' An OData $select clause.', arg_group='Pre-condition and Query')
register_cli_argument('batch job list', 'expand', help=' An OData $expand clause.', arg_group='Pre-condition and Query')
register_cli_argument('batch job list', 'job_schedule_id', help='The ID of the job schedule from which you want to get a list of jobs. If omitted, lists all jobs in the account.')
for command in ['job create', 'job set', 'job reset', 'job-schedule create', 'job-schedule set', 'job-schedule reset']:
    register_cli_argument('batch {}'.format(command), 'pool_id', options_list=('--pool-id',), help='The id of an existing pool. All the tasks of the job will run on the specified pool.')

register_cli_argument('batch pool create', 'os_family', **enum_choice_list(['2', '3', '4', '5']))
register_cli_argument('batch pool create', 'auto_scale_formula', help='A formula for the desired number of compute nodes in the pool. The formula is checked for validity before the pool is created. If the formula is not valid, the Batch service rejects the request with detailed error information. For more information about specifying this formula, see https://azure.microsoft.com/documentation/articles/batch-automatic-scaling/.')
register_extra_cli_argument('batch pool create', 'image', completer=load_node_agent_skus, arg_group="Pool: Virtual Machine Configuration",
                            help="OS image URN in 'publisher:offer:sku[:version]' format. Version is optional and if omitted latest will be used.\n\tValues from 'az batch pool node-agent-skus list'.\n\tExample: 'MicrosoftWindowsServer:WindowsServer:2012-R2-Datacenter:latest'")

register_cli_argument('batch certificate', 'thumbprint', help='The certificate thumbprint.')
register_cli_argument('batch certificate show', 'thumbprint', help='The certificate thumbprint.', validator=validate_cert_settings)
register_cli_argument('batch certificate', 'password', help='The password to access the certificate\'s private key.')
register_cli_argument('batch certificate', 'certificate_file', type=file_type, help='The certificate file: cer file or pfx file.', validator=validate_cert_file, completer=FilesCompleter())
register_cli_argument('batch certificate delete', 'abort', action='store_true', help='Cancel the failed certificate deletion operation.')

register_cli_argument('batch task create', 'json_file', type=file_type, help='The file containing the task(s) to create in JSON format, if this parameter is specified, all other parameters are ignored.', validator=validate_json_file, completer=FilesCompleter())
register_cli_argument('batch task create', 'application_package_references', nargs='+', help='The space separated list of IDs specifying the application packages to be installed. Space separated application IDs with optional version in \'id[#version]\' format.', type=application_package_reference_format)
register_cli_argument('batch task create', 'job_id', help='The ID of the job containing the task.')
register_cli_argument('batch task create', 'task_id', help='The ID of the task.')
register_cli_argument('batch task create', 'command_line', help='The command line of the task. The command line does not run under a shell, and therefore cannot take advantage of shell features such as environment variable expansion. If you want to take advantage of such features, you should invoke the shell in the command line, for example using "cmd /c MyCommand" in Windows or "/bin/sh -c MyCommand" in Linux.')
register_cli_argument('batch task create', 'environment_settings', nargs='+', help='A list of environment variable settings for the task. Space separated values in \'key=value\' format.', type=environment_setting_format)
register_cli_argument('batch task create', 'resource_files', nargs='+', help='A list of files that the Batch service will download to the compute node before running the command line. Space separated resource references in filename=blobsource format.', type=resource_file_format)

for item in ['batch certificate delete', 'batch certificate create', 'batch pool resize', 'batch pool reset', 'batch job list', 'batch task create']:
    register_extra_cli_argument(item, 'account_name', arg_group='Batch Account',
                                validator=validate_client_parameters,
                                help='The Batch account name. Alternatively, set by environment variable: AZURE_BATCH_ACCOUNT')
    register_extra_cli_argument(item, 'account_key', arg_group='Batch Account',
                                help='The Batch account key. Alternatively, set by environment variable: AZURE_BATCH_ACCESS_KEY')
    register_extra_cli_argument(item, 'account_endpoint', arg_group='Batch Account',
                                help='Batch service endpoint. Alternatively, set by environment variable: AZURE_BATCH_ENDPOINT')
