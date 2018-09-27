# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from argcomplete.completers import FilesCompleter

from knack.arguments import CLIArgumentType

from azure.mgmt.batch.models import AccountKeyType
from azure.batch.models import ComputeNodeDeallocationOption

from azure.cli.core.commands.parameters import \
    (tags_type, get_location_type, resource_group_name_type,
     get_resource_name_completion_list, file_type, get_enum_type)

from azure.cli.command_modules.batch._completers import load_node_agent_skus
from azure.cli.command_modules.batch._validators import \
    (application_enabled, datetime_format, storage_account_id, metadata_item_format,
     application_package_reference_format, validate_pool_resize_parameters,
     certificate_reference_format, validate_json_file, validate_cert_file, keyvault_id,
     environment_setting_format, validate_cert_settings, resource_file_format,
     validate_client_parameters)


# pylint: disable=line-too-long, too-many-statements
def load_arguments(self, _):
    batch_name_type = CLIArgumentType(
        help='Name of the Batch account.',
        options_list=('--account-name',),
        completer=get_resource_name_completion_list('Microsoft.Batch/batchAccounts'),
        id_part=None)

    with self.argument_context('batch') as c:
        c.argument('resource_group_name', resource_group_name_type, help='Name of the resource group', completer=None, validator=None, required=True)

    with self.argument_context('batch account') as c:
        c.argument('account_name', batch_name_type, options_list=('--name', '-n'))

    with self.argument_context('batch account show') as c:
        c.argument('resource_group_name', resource_group_name_type, help='Name of the resource group. If not specified will display currently set account.', required=False)
        c.argument('account_name', batch_name_type, options_list=('--name', '-n'), help='Name of the batch account to show. If not specified will display currently set account.', required=False)

    with self.argument_context('batch account list') as c:
        c.argument('resource_group_name', resource_group_name_type, help='Name of the resource group', required=False)

    with self.argument_context('batch account create') as c:
        c.argument('location', get_location_type(self.cli_ctx), help='The region in which to create the account.')
        c.argument('tags', tags_type, help="Space-separated tags in 'key[=value]' format.")
        c.argument('storage_account', help='The storage account name or resource ID to be used for auto storage.', validator=storage_account_id)
        c.argument('keyvault', help='The KeyVault name or resource ID to be used for an account with a pool allocation mode of \'User Subscription\'.', validator=keyvault_id)
        c.ignore('keyvault_url')

    with self.argument_context('batch account set') as c:
        c.argument('tags', tags_type)
        c.argument('storage_account', help='The storage account name or resource ID to be used for auto storage.', validator=storage_account_id)

    with self.argument_context('batch account keys renew') as c:
        c.argument('key_name', arg_type=get_enum_type(AccountKeyType))

    with self.argument_context('batch account login') as c:
        c.argument('shared_key_auth', action='store_true', help='Using Shared Key authentication, if not specified, it will use Azure Active Directory authentication.')
        c.argument('show', action='store_true', help='Display the credential information for the Batch account.')

    with self.argument_context('batch application set') as c:
        c.argument('application_id', options_list=('--application-id',), help="The ID of the application.")
        c.argument('allow_updates', options_list=('--allow-updates',), help="Specify to indicate whether packages within the application may be overwritten using the same version string. Specify either 'true' or 'false' to update the property.")

    with self.argument_context('batch application create') as c:
        c.argument('allow_updates', options_list=('--allow-updates',), action="store_true", help="Specify to indicate whether packages within the application may be overwritten using the same version string. True if flag present.")

    with self.argument_context('batch application package create') as c:
        c.argument('package_file', type=file_type, help='The path of the application package in zip format', completer=FilesCompleter())
        c.argument('application_id', options_list=('--application-id',), help="The ID of the application.")
        c.argument('version', options_list=('--version',), help="The version of the application.")

    with self.argument_context('batch location quotas show') as c:
        c.argument('location_name', get_location_type(self.cli_ctx), help='The region from which to display the Batch service quotas.')

    for command in ['list', 'show', 'create', 'set', 'delete', 'package']:
        with self.argument_context('batch application {}'.format(command)) as c:
            c.argument('account_name', batch_name_type, options_list=('--name', '-n'), validator=application_enabled)

    # TODO: Refactor so the help text can be extracted automatically
    with self.argument_context('batch pool resize') as c:
        c.argument('if_modified_since', help='The operation will be performed only if the resource has been modified since the specified timestamp.', type=datetime_format, arg_group='Pre-condition and Query')
        c.argument('if_unmodified_since', help='The operation will not be performed only if the resource has been modified since the specified timestamp.', type=datetime_format, arg_group='Pre-condition and Query')
        c.argument('if_match', help='The operation will be performed only if the resource\'s current ETag exactly matches the specified value.', arg_group='Pre-condition and Query')
        c.argument('if_none_match', help='The operation will not be performed only if the resource\'s current ETag exactly matches the specified value.', arg_group='Pre-condition and Query')
        c.argument('pool_id', help='The ID of the pool.')
        c.argument('abort', action='store_true', help='Stop the pool resize operation.', validator=validate_pool_resize_parameters)
        c.argument('node_deallocation_option', options_list=('--node-deallocation-option',), help='When nodes may be removed from the pool, if the pool size is decreasing.', arg_type=get_enum_type(ComputeNodeDeallocationOption))

    # TODO: Refactor so the help text can be extracted automatically
    with self.argument_context('batch pool reset') as c:
        c.argument('json_file', type=file_type, help='The file containing pool update properties parameter specification in JSON(formatted to match REST API request body). If this parameter is specified, all \'Pool Update Properties Parameter Arguments\' are ignored.', validator=validate_json_file, completer=FilesCompleter())
        c.argument('pool_id', help='The ID of the pool to update.')
        c.argument('application_package_references', nargs='+', type=application_package_reference_format, arg_group='Pool')
        c.argument('certificate_references', nargs='+', type=certificate_reference_format, arg_group='Pool')
        c.argument('metadata', nargs='+', type=metadata_item_format, arg_group='Pool')
        c.argument('start_task_command_line', arg_group='Pool: Start Task',
                   help='The command line of the start task. The command line does not run under a shell, and therefore cannot take advantage of shell features such as environment variable expansion. If you want to take advantage of such features, you should invoke the shell in the command line, for example using "cmd /c MyCommand" in Windows or "/bin/sh -c MyCommand" in Linux.')
        c.argument('start_task_wait_for_success', action='store_true', arg_group='Pool: Start Task',
                   help='Whether the Batch service should wait for the start task to complete successfully (that is, to exit with exit code 0) before scheduling any tasks on the compute node. True if flag present, otherwise defaults to False.')
        c.argument('start_task_max_task_retry_count', arg_group='Pool: Start Task',
                   help='The maximum number of times the task may be retried.')
        c.argument('start_task_environment_settings', nargs='+', type=environment_setting_format, arg_group='Pool: Start Task',
                   help='A list of environment variable settings for the start task. Space-separated values in \'key=value\' format.')

    with self.argument_context('batch job list') as c:
        c.argument('filter', help=' An OData $filter clause.', arg_group='Pre-condition and Query')
        c.argument('select', help=' An OData $select clause.', arg_group='Pre-condition and Query')
        c.argument('expand', help=' An OData $expand clause.', arg_group='Pre-condition and Query')
        c.argument('job_schedule_id', help='The ID of the job schedule from which you want to get a list of jobs. If omitted, lists all jobs in the account.')

    for command in ['job create', 'job set', 'job reset', 'job-schedule create', 'job-schedule set', 'job-schedule reset']:
        with self.argument_context('batch {}'.format(command)) as c:
            c.argument('pool_id', options_list=('--pool-id',), help='The id of an existing pool. All the tasks of the job will run on the specified pool.')

    with self.argument_context('batch pool create') as c:
        c.argument('os_family', arg_type=get_enum_type(['2', '3', '4', '5']))
        c.argument('auto_scale_formula', help='A formula for the desired number of compute nodes in the pool. The formula is checked for validity before the pool is created. If the formula is not valid, the Batch service rejects the request with detailed error information. For more information about specifying this formula, see https://azure.microsoft.com/documentation/articles/batch-automatic-scaling/.')
        c.extra('image', completer=load_node_agent_skus, arg_group="Pool: Virtual Machine Configuration",
                help="OS image reference. This can be either 'publisher:offer:sku[:version]' format, or a fully qualified ARM image id of the form '/subscriptions/{subscriptionId}/resourceGroups/{resourceGroup}/providers/Microsoft.Compute/images/{imageName}'. If 'publisher:offer:sku[:version]' format, version is optional and if omitted latest will be used. Valid values can be retrieved via 'az batch pool node-agent-skus list'. For example: 'MicrosoftWindowsServer:WindowsServer:2012-R2-Datacenter:latest'")

    with self.argument_context('batch certificate') as c:
        c.argument('thumbprint', help='The certificate thumbprint.')
        c.argument('password', help='The password to access the certificate\'s private key.')
        c.argument('certificate_file', type=file_type, help='The certificate file: cer file or pfx file.', validator=validate_cert_file, completer=FilesCompleter())
        c.argument('abort', action='store_true', help='Cancel the failed certificate deletion operation.')

    with self.argument_context('batch certificate show') as c:
        c.argument('thumbprint', help='The certificate thumbprint.', validator=validate_cert_settings)

    with self.argument_context('batch task create') as c:
        c.argument('json_file', type=file_type, help='The file containing the task(s) to create in JSON(formatted to match REST API request body). When submitting multiple tasks, accepts either an array of tasks or a TaskAddCollectionParamater. If this parameter is specified, all other parameters are ignored.', validator=validate_json_file, completer=FilesCompleter())
        c.argument('application_package_references', nargs='+', help='The space-separated list of IDs specifying the application packages to be installed. Space-separated application IDs with optional version in \'id[#version]\' format.', type=application_package_reference_format)
        c.argument('job_id', help='The ID of the job containing the task.')
        c.argument('task_id', help='The ID of the task.')
        c.argument('command_line', help='The command line of the task. The command line does not run under a shell, and therefore cannot take advantage of shell features such as environment variable expansion. If you want to take advantage of such features, you should invoke the shell in the command line, for example using "cmd /c MyCommand" in Windows or "/bin/sh -c MyCommand" in Linux.')
        c.argument('environment_settings', nargs='+', help='A list of environment variable settings for the task. Space-separated values in \'key=value\' format.', type=environment_setting_format)
        c.argument('resource_files', nargs='+', help='A list of files that the Batch service will download to the compute node before running the command line. Space-separated resource references in filename=blobsource format.', type=resource_file_format)

    for item in ['batch certificate delete', 'batch certificate create', 'batch pool resize', 'batch pool reset', 'batch job list', 'batch task create']:
        with self.argument_context(item) as c:
            c.extra('account_name', arg_group='Batch Account', validator=validate_client_parameters,
                    help='The Batch account name. Alternatively, set by environment variable: AZURE_BATCH_ACCOUNT')
            c.extra('account_key', arg_group='Batch Account',
                    help='The Batch account key. Alternatively, set by environment variable: AZURE_BATCH_ACCESS_KEY')
            c.extra('account_endpoint', arg_group='Batch Account',
                    help='Batch service endpoint. Alternatively, set by environment variable: AZURE_BATCH_ENDPOINT')
