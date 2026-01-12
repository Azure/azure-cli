# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum
from argcomplete.completers import FilesCompleter

from knack.arguments import CLIArgumentType

from azure.mgmt.batch.models import (
    AccountKeyType,
    KeySource,
    PublicNetworkAccessType,
    ResourceIdentityType,
    EndpointAccessDefaultAction)
from azure.batch.models import (
    CachingType,
    BatchNodeDeallocationOption,
    StorageAccountType)

from azure.cli.core.commands.parameters import (
    file_type,
    get_enum_type,
    get_location_type,
    get_resource_name_completion_list,
    get_three_state_flag,
    resource_group_name_type,
    tags_type)

from azure.cli.command_modules.batch._completers import load_supported_images
from azure.cli.command_modules.batch._validators import (
    application_enabled,
    batch_application_package_reference_format,
    datetime_format,
    disk_encryption_configuration_format,
    environment_setting_format,
    keyvault_id,
    metadata_item_format,
    resource_file_format,
    duration_format,
    storage_account_id,
    validate_client_parameters,
    validate_json_file,
    validate_pool_resize_parameters)


class NetworkProfile(Enum):
    BatchAccount = "BatchAccount"
    NodeManagement = "NodeManagement"


profile_param_type = CLIArgumentType(
    help="Network profile to set.",
    arg_type=get_enum_type(NetworkProfile))


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
        c.argument('public_network_access', help="The network access type for accessing Azure Batch account. Values can either be enabled or disabled.", arg_type=get_enum_type(PublicNetworkAccessType))
        c.argument('encryption_key_source', help='Part of the encryption configuration for the Batch account. Type of the key source. Can be either Microsoft.Batch or Microsoft.KeyVault', arg_type=get_enum_type(KeySource))
        c.argument('encryption_key_identifier', help='Part of the encryption configuration for the Batch account. '
                                                     'Full path to the versioned secret. Example https://mykeyvault.vault.azure.net/keys/testkey/6e34a81fef704045975661e297a4c053.')
        c.argument('identity_type', help="The type of identity used for the Batch account. Possible values include: 'SystemAssigned', 'None'.", arg_type=get_enum_type(ResourceIdentityType), deprecate_info=c.deprecate(hide=True))
        c.argument('mi_user_assigned', help='Resource ID of the user assigned identity for the batch services account.', arg_group='Identity')
        c.argument('mi_system_assigned', help='Set the system managed identity on the batch services account.', arg_group='Identity')
        c.ignore('keyvault_url')

    with self.argument_context('batch account set') as c:
        c.argument('tags', tags_type)
        c.argument('storage_account', help='The storage account name or resource ID to be used for auto storage.', validator=storage_account_id)
        c.argument('encryption_key_source', help='Part of the encryption configuration for the Batch account. Type of the key source. Can be either Microsoft.Batch or Microsoft.KeyVault')
        c.argument('public_network_access', help="The network access type for accessing Azure Batch account. Values can either be enabled or disabled.", arg_type=get_enum_type(PublicNetworkAccessType))
        c.argument('encryption_key_identifier', help='Part of the encryption configuration for the Batch account. Full path to the versioned secret. Example https://mykeyvault.vault.azure.net/keys/testkey/6e34a81fef704045975661e297a4c053.')
        c.argument('identity_type', help="The type of identity used for the Batch account. Possible values include: 'SystemAssigned', 'None'.", arg_type=get_enum_type(ResourceIdentityType), deprecate_info=c.deprecate(hide=True))

    with self.argument_context('batch account identity assign') as c:
        c.argument('resource_group_name', resource_group_name_type, help='Name of the resource group. If not specified will display currently set account.')
        c.argument('account_name', batch_name_type, options_list=('--name', '-n'), help='Name of the batch account to show. If not specified will display currently set account.')
        c.argument('mi_system_assigned', options_list=['--system-assigned'], action='store_true',
                   arg_group='Managed Identity', help='Provide this flag to use system assigned identity for batch accounts. '
                   'Check out help for more examples')
        c.argument('mi_user_assigned', options_list=['--user-assigned'],
                   arg_group='Managed Identity', help='User Assigned Identity ids to be used for batch account. '
                   'Check out help for more examples')

    with self.argument_context('batch account identity remove') as c:
        c.argument('resource_group_name', resource_group_name_type, help='Name of the resource group. If not specified will display currently set account.')
        c.argument('account_name', batch_name_type, options_list=('--name', '-n'), help='Name of the batch account to show. If not specified will display currently set account.')
        c.argument('mi_system_assigned', options_list=['--system-assigned'], action='store_true',
                   arg_group='Managed Identity', help='Provide this flag to use system assigned identity for batch accounts. '
                   'Check out help for more examples')
        c.argument('mi_user_assigned', options_list=['--user-assigned'], nargs='*',
                   arg_group='Managed Identity', help='User Assigned Identity ids to be used for batch account. '
                   'Check out help for more examples')

    with self.argument_context('batch account identity show') as c:
        c.argument('resource_group_name', resource_group_name_type, help='Name of the resource group. If not specified will display currently set account.')
        c.argument('account_name', batch_name_type, options_list=('--name', '-n'), help='Name of the batch account to show. If not specified will display currently set account.')

    with self.argument_context('batch account network-profile show') as c:
        c.argument('resource_group_name', resource_group_name_type, help='Name of the resource group. If not specified will display currently set account.')
        c.argument('account_name', batch_name_type, options_list=('--name', '-n'), help='Name of the batch account to show. If not specified will display currently set account.')

    with self.argument_context('batch account network-profile set') as c:
        c.argument('resource_group_name', resource_group_name_type, help='Name of the resource group. If not specified will display currently set account.')
        c.argument('account_name', batch_name_type, options_list=('--name', '-n'), help='Name of the batch account to show. If not specified will display currently set account.')
        c.argument('profile', arg_type=profile_param_type)
        c.argument('default_action', help="Default action for endpoint access. It is only applicable when publicNetworkAccess is enabled. Possible values include: 'Allow', 'Deny'", arg_type=get_enum_type(EndpointAccessDefaultAction))

    with self.argument_context('batch account network-profile network-rule list') as c:
        c.argument('resource_group_name', resource_group_name_type, help='Name of the resource group. If not specified will display currently set account.')
        c.argument('account_name', batch_name_type, options_list=('--name', '-n'), help='Name of the batch account to show. If not specified will display currently set account.')

    with self.argument_context('batch account network-profile network-rule add') as c:
        c.argument('resource_group_name', resource_group_name_type, help='Name of the resource group. If not specified will display currently set account.')
        c.argument('account_name', batch_name_type, options_list=('--name', '-n'), help='Name of the batch account to show. If not specified will display currently set account.')
        c.argument('profile', arg_type=profile_param_type)
        c.argument('ip_address', help='IPv4 address or CIDR range.')

    with self.argument_context('batch account network-profile network-rule delete') as c:
        c.argument('resource_group_name', resource_group_name_type, help='Name of the resource group. If not specified will display currently set account.')
        c.argument('account_name', batch_name_type, options_list=('--name', '-n'), help='Name of the batch account to show. If not specified will display currently set account.')
        c.argument('profile', arg_type=profile_param_type)
        c.argument('ip_address', help='IPv4 address or CIDR range.')

    with self.argument_context('batch account keys renew') as c:
        c.argument('resource_group_name', resource_group_name_type,
                   help='Name of the resource group. If not specified will display currently set account.',
                   required=False)
        c.argument('account_name', batch_name_type, options_list=('--name', '-n'),
                   help='Name of the batch account to show. If not specified will display currently set account.',
                   required=False)
        c.argument('key_name', arg_type=get_enum_type(AccountKeyType), help='Name of the batch account key.')

    with self.argument_context('batch account login') as c:
        c.argument('shared_key_auth', action='store_true', help='Using Shared Key authentication, if not specified, it will use Azure Active Directory authentication.')
        c.argument('show', action='store_true', help='Display the credential information for the Batch account.')

    with self.argument_context('batch application set') as c:
        c.argument('application_name', help="The name of the application.")
        c.argument('allow_updates', help="Specify to indicate whether packages within the application may be overwritten using the same version string. Specify either 'true' or 'false' to update the property.")
        c.argument('default_version', help="Specify which package to use if a client requests the application but does not specify a version.")
        c.argument('display_name', help="Specify the display name for the application.")

    with self.argument_context('batch application create') as c:
        c.argument('allow_updates', options_list=('--allow-updates',), action="store_true", help="Specify to indicate whether packages within the application may be overwritten using the same version string. True if flag present.")

    for command in ['create', 'activate']:
        with self.argument_context(f'batch application package {command}') as c:
            c.argument('package_file', type=file_type, help='The path of the application package in zip format', completer=FilesCompleter())
            c.argument('application_name', help="The name of the application.")
            c.argument('version_name', help="The version name of the application.")
            c.argument('f_ormat', options_list=('--format',), help="The format of the application package binary file.")

    with self.argument_context('batch location quotas show') as c:
        c.argument('location_name', get_location_type(self.cli_ctx), help='The region for which to display the Batch service quotas.')

    with self.argument_context('batch location list-skus') as c:
        c.argument('location_name', get_location_type(self.cli_ctx), help='The region for which to display the available Batch VM SKUs.')

    for command in ['list', 'show', 'create', 'set', 'delete', 'package']:
        with self.argument_context(f'batch application {command}') as c:
            c.argument('account_name', batch_name_type, options_list=('--name', '-n'), validator=application_enabled)

    # TODO: Refactor so the help text can be extracted automatically
    with self.argument_context('batch pool resize') as c:
        c.argument('if_modified_since', help='The operation will be performed only if the resource has been modified since the specified timestamp.', type=datetime_format, arg_group='Pre-condition and Query')
        c.argument('if_unmodified_since', help='The operation will not be performed only if the resource has been modified since the specified timestamp.', type=datetime_format, arg_group='Pre-condition and Query')
        c.argument('if_match', help='The operation will be performed only if the resource\'s current ETag exactly matches the specified value.', arg_group='Pre-condition and Query')
        c.argument('if_none_match', help='The operation will not be performed only if the resource\'s current ETag exactly matches the specified value.', arg_group='Pre-condition and Query')
        c.argument('pool_id', help='The ID of the pool.')
        c.argument('abort', action='store_true', help='Stop the pool resize operation.', validator=validate_pool_resize_parameters)
        c.argument('node_deallocation_option', options_list=('--node-deallocation-option',), help='When nodes may be removed from the pool, if the pool size is decreasing.', arg_type=get_enum_type(BatchNodeDeallocationOption))
        c.argument('resize_timeout', type=duration_format, help='The default value is 15 minutes. The minimum value is 5 minutes. '
                                                                'If you specify a value less than 5 minutes, the Batch service '
                                                                'returns an error; if you are calling the REST API directly, the '
                                                                'HTTP status code is 400 (Bad Request). ISO-8601 duration format')
        c.argument('target_dedicated_nodes', help='The desired number of dedicated Compute Nodes in the Pool.')
        c.argument('target_low_priority_nodes', help='The desired number of Spot/Low-priority Compute Nodes in the Pool.')

    # TODO: Refactor so the help text can be extracted automatically
    with self.argument_context('batch pool reset') as c:
        c.argument('json_file', type=file_type, help='The file containing pool update properties parameter specification in JSON(formatted to match REST API request body). If this parameter is specified, all \'Pool Update Properties Parameter Arguments\' are ignored.', validator=validate_json_file, completer=FilesCompleter())
        c.argument('pool_id', help='The ID of the pool to update.')
        c.argument('application_package_references', nargs='+', type=batch_application_package_reference_format, arg_group='Pool', help='Required. The list replaces any existing Application Package '
                                                                                                                                        'references on the Pool. Changes to Application Package '
                                                                                                                                        'references affect all new Compute Nodes joining the Pool, '
                                                                                                                                        'but do not affect Compute Nodes that are already in the Pool '
                                                                                                                                        'until they are rebooted or reimaged. There is a maximum of '
                                                                                                                                        '10 Application Package references on any given Pool. If '
                                                                                                                                        'omitted, or if you specify an empty collection, any existing '
                                                                                                                                        'Application Packages references are removed from the Pool. A '
                                                                                                                                        'maximum of 10 references may be specified on a given Pool.')
        c.argument('metadata', nargs='+', type=metadata_item_format, arg_group='Pool', help='Required. This list replaces any existing metadata'
                                                                                            'configured on the Pool. If omitted, or if you specify an'
                                                                                            'empty collection, any existing metadata is removed from the'
                                                                                            'Pool.')
        c.argument('start_task_command_line', arg_group='Pool: Start Task',
                   help='The command line of the start task. The command line does not run under a shell, and therefore cannot take advantage of shell features such as environment variable expansion. If you want to take advantage of such features, you should invoke the shell in the command line, for example using "cmd /c MyCommand" in Windows or "/bin/sh -c MyCommand" in Linux.')
        c.argument('start_task_wait_for_success', action='store_true', arg_group='Pool: Start Task',
                   help='Whether the Batch service should wait for the start task to complete successfully (that is, to exit with exit code 0) before scheduling any tasks on the compute node. True if flag present, otherwise defaults to False.')
        c.argument('start_task_max_task_retry_count', arg_group='Pool: Start Task',
                   help='The maximum number of times the task may be retried.')
        c.argument('start_task_resource_files', nargs='+', type=resource_file_format, arg_group='Pool: Start Task',
                   help='A list of files that the Batch service will download to the '
                        'Compute Node before running the command line. Files listed under this element are '
                        'located in the Task\'s working directory. Space-separated '
                        'resource references in filename=httpurl format.')
        c.argument('start_task_environment_settings', nargs='+', type=environment_setting_format, arg_group='Pool: Start Task',
                   help='A list of environment variable settings for the start task. Space-separated values in \'key=value\' format.')

    with self.argument_context('batch pool autoscale enable') as c:
        c.extra('auto_scale_formula',
                help='The formula for the desired number of Compute Nodes in the Pool. '
                     'The formula is checked for validity before it is applied to the Pool. '
                     'If the formula is not valid, the Batch service rejects the request with detailed error information. '
                     'For more information about specifying this formula, see Automatically scale Compute Nodes in an Azure Batch Pool '
                     '(https://learn.microsoft.com/azure/batch/batch-automatic-scaling).')
        c.extra('auto_scale_evaluation_interval',
                help='The time interval at which to automatically adjust the Pool size according to the autoscale formula. '
                     'The default value is 15 minutes. The minimum and maximum value are 5 minutes and 168 hours respectively. '
                     'If you specify a value less than 5 minutes or greater than 168 hours, the Batch service rejects the request '
                     'with an invalid property value error; if you are calling the REST API directly, the HTTP status code is 400 (Bad Request). '
                     'If you specify a new interval, then the existing autoscale evaluation schedule will be stopped and a new autoscale evaluation '
                     'schedule will be started, with its starting time being the time when this request was issued.')

    with self.argument_context('batch private-endpoint-connection show') as c:
        c.argument('private_endpoint_connection_name', options_list=['--name', '-n'],
                   help='The private endpoint connection name. This must be unique within the account.')

    with self.argument_context('batch private-link-resource show') as c:
        c.argument('private_link_resource_name', options_list=['--name', '-n'],
                   help='The private link resource name. This must be unique within the account.')

    for command in [
        'pool delete', 'pool show', 'pool set', 'pool autoscale enable',
        'job delete', 'job show', 'job reset', 'job set', 'job disable', 'job enable', 'job stop',
        'job-schedule delete', 'job-schedule show', 'job-schedule reset', 'job-schedule set',
        'job-schedule disable', 'job-schedule enable', 'job-schedule stop',
        'task delete', 'task show', 'task stop', 'task reactivate',
        'node delete'
    ]:
        with self.argument_context(f'batch {command}') as c:
            c.extra('if_match', arg_group='Pre-condition and Query',
                    help='An ETag value associated with the version of the resource known to the client. '
                         'The operation will be performed only if the resource\'s current ETag on the service '
                         'exactly matches the value specified by the client.')
            c.extra('if_modified_since', arg_group='Pre-condition and Query', type=datetime_format,
                    help='A timestamp indicating the last modified time of the resource known to the client. '
                         'The operation will be performed only if the resource on the service has been modified '
                         'since the specified time.',)
            c.extra('if_none_match', arg_group='Pre-condition and Query',
                    help='An ETag value associated with the version of the resource known to the client. '
                         'The operation will be performed only if the resource\'s current ETag on the service '
                         'does not match the value specified by the client.')
            c.extra('if_unmodified_since', arg_group='Pre-condition and Query', type=datetime_format,
                    help='A timestamp indicating the last modified time of the resource known to the client. '
                         'The operation will be performed only if the resource on the service has been modified '
                         'since the specified time.')

    for command in ['pool node-counts list', 'pool supported-images list', 'job list', 'pool list', 'job-schedule list', 'task list', 'job prep-release-status list', 'node list', 'node file list', 'task file list', 'pool usage-metrics list']:
        with self.argument_context(f'batch {command}') as c:
            c.extra('filter', arg_group='Pre-condition and Query', help='An OData $filter clause. For more information on constructing this filter,'
                                                                        'see https://learn.microsoft.com/rest/api/batchservice/odata-filters-in-batch.')

    for command in ['job list', 'pool list', 'job-schedule list', 'task list', 'job show', 'pool show', 'task show', 'job-schedule show']:
        with self.argument_context(f'batch {command}') as c:
            c.extra('select', nargs='+', help='An OData $select clause.', arg_group='Pre-condition and Query')
            c.extra('expand', nargs='+', help='An OData $expand clause.', arg_group='Pre-condition and Query')

    with self.argument_context('batch job list') as c:
        c.argument('job_schedule_id', help='The ID of the job schedule from which you want to get a list of jobs. If omitted, lists all jobs in the account.')

    for command in ['node list', 'node show', 'job prep-release-status list', 'task subtask list']:
        with self.argument_context(f'batch {command}') as c:
            c.extra('select', nargs='+', help='An OData $select clause.', arg_group='Pre-condition and Query')

    with self.argument_context('batch job stop') as c:
        c.extra('reason', options_list=['--terminate-reason'], help='Termination reason. The text you want to appear as the job\'s TerminateReason. The default is \'UserTerminate\'.')

    for command in ['node file delete', 'task file delete']:
        with self.argument_context(f'batch {command}') as c:
            c.extra('recursive', arg_type=get_three_state_flag(),
                    help='Whether to delete children of a directory. If the filePath parameter '
                    'represents a directory instead of a file, you can set recursive to true to delete the '
                    'directory and all of the files and subdirectories in it. If recursive is false '
                    'then the directory must be empty or deletion will fail. Default value is None.')

    with self.argument_context('batch node file list') as c:
        c.extra('recursive', arg_type=get_three_state_flag(), help='Whether to list children of a directory.')

    with self.argument_context('batch task reset') as c:
        c.argument('if_modified_since', help='The operation will be performed only if the resource has been modified since the specified timestamp.', type=datetime_format, arg_group='Pre-condition and Query')
        c.argument('if_unmodified_since', help='The operation will not be performed only if the resource has been modified since the specified timestamp.', type=datetime_format, arg_group='Pre-condition and Query')
        c.argument('if_match', help='The operation will be performed only if the resource\'s current ETag exactly matches the specified value.', arg_group='Pre-condition and Query')
        c.argument('if_none_match', help='The operation will not be performed only if the resource\'s current ETag exactly matches the specified value.', arg_group='Pre-condition and Query')
        c.argument('job_id', help='The ID of the Job containing the Task.', required=True)
        c.argument('task_id', help='The ID of the Task to update.', required=True)
        c.argument('json_file', type=file_type, help='The file containing pool update properties parameter specification in JSON(formatted to match REST API request body). If this parameter is specified, all \'Pool Update Properties Parameter Arguments\' are ignored.', validator=validate_json_file, completer=FilesCompleter())
        c.argument('max_task_retry_count', arg_group='Constraints',
                   help='The maximum number of times the Task may be retried. The Batch service '
                        'retries a Task if its exit code is nonzero. Note that this value '
                        'specifically controls the number of retries for the Task executable due '
                        'to a nonzero exit code. The Batch service will try the Task once, and '
                        'may then retry up to this limit. For example, if the maximum retry '
                        'count is 3, Batch tries the Task up to 4 times (one initial try and 3 '
                        'retries). If the maximum retry count is 0, the Batch service does not '
                        'retry the Task after the first attempt. If the maximum retry count is '
                        '-1, the Batch service retries the Task without limit, however this is '
                        'not recommended for a start task or any task. The default value is 0 '
                        '(no retries).')
        c.argument('max_wall_clock_time', type=duration_format, arg_group='Constraints',
                   help='If this is not specified, there is no time limit on how long the Task '
                        'may run. Expected format is an ISO-8601 duration.')
        c.argument('retention_time', type=duration_format, arg_group='Constraints',
                   help='The default is 7 days, i.e. the Task directory will be retained for 7 '
                        'days unless the Compute Node is removed or the Job is deleted. Expected '
                        'format is an ISO-8601 duration.')

    with self.argument_context('batch pool usage-metrics list') as c:
        c.extra('endtime', options_list=['--end-time'], arg_group='Pre-condition and Query',
                help='The latest time from which to include metrics. This must be at least two '
                     'hours before the current time. If not specified this defaults to the end '
                     'time of the last aggregation interval currently available.')
        c.extra('starttime', options_list=['--start-time'], arg_group='Pre-condition and Query',
                help='The earliest time from which to include metrics. This must be at least two '
                     'and a half hours before the current time. If not specified this defaults to '
                     'the start time of the last aggregation interval currently available.')

    with self.argument_context('batch task file list') as c:
        c.extra('recursive', arg_type=get_three_state_flag(),
                help='Whether to list children of the Task directory. This parameter can be '
                'used in combination with the filter parameter to list specific type of files.')

    for command in ['node file download', 'task file download']:
        with self.argument_context(f'batch {command}') as c:
            c.extra('end_range', arg_group='Pre-condition and Query',
                    help='The byte range to be retrieved. If not set the file will be retrieved to the end.')
            c.extra('start_range', arg_group='Pre-condition and Query',
                    help='The byte range to be retrieved. If not set the file will be retrieved from the beginning.')

    for command in ['node file download', 'node file show', 'task file show', 'task file download']:
        with self.argument_context(f'batch {command}') as c:
            c.extra('if_modified_since', arg_group='Pre-condition and Query', type=datetime_format,
                    help='A timestamp indicating the last modified time of the resource known to the client. '
                         'The operation will be performed only if the resource on the service has been modified '
                         'since the specified time.',)
            c.extra('if_unmodified_since', arg_group='Pre-condition and Query', type=datetime_format,
                    help='A timestamp indicating the last modified time of the resource known to the client. '
                         'The operation will be performed only if the resource on the service has been modified '
                         'since the specified time.')

    with self.argument_context('batch pool create') as c:
        c.argument('json_file', help='The file containing pool create properties parameter specification in JSON(formatted to match REST API request body). If this parameter is specified, all \'Pool Create Properties Parameter Arguments\' are ignored.  See https://learn.microsoft.com/rest/api/batchservice/pool/add?tabs=HTTP#request-body')
        c.argument('enable_accelerated_networking', arg_type=get_three_state_flag(), options_list=['--accelerated-networking'], arg_group="Pool: Network Configuration",
                   help='Whether this pool should enable accelerated networking. Accelerated networking enables single root I/O virtualization (SR-IOV) to a VM, which may lead to improved networking performance. For more details, see: https://learn.microsoft.com/azure/virtual-network/accelerated-networking-overview. Set true to enable.')
        c.argument('caching',
                   options_list=('--os-disk-caching'),
                   arg_type=get_enum_type(CachingType),
                   arg_group="Pool: OS Disk",
                   help="Specify the caching requirements. Possible values are: None, ReadOnly, ReadWrite. The default values are: None for Standard storage. ReadOnly for Premium storage.")
        c.argument('storage_account_type',
                   arg_group="Pool: OS Disk",
                   arg_type=get_enum_type(StorageAccountType),
                   help="The storage account type for managed disk")
        c.argument('disk_size_g_b',
                   options_list=('--os-disk-size'),
                   arg_group="Pool: OS Disk",
                   help="The initial disk size in GB when creating new OS disk.")
        c.argument('write_accelerator_enabled', arg_type=get_three_state_flag(),
                   options_list=('--enable-write-accel'),
                   arg_group="Pool: OS Disk",
                   help="Specify whether writeAccelerator should be enabled or disabled on the disk.")
        c.argument('encryption_at_host', arg_type=get_three_state_flag(),
                   arg_group='Pool: Security Profile',
                   help='This property can be used by user in the request to enable or disable the Host Encryption for the virtual machine or virtual machine scale set. This will enable the encryption for all the disks including Resource/Temp disk at host itself. The default behavior is: The Encryption at host will be disabled unless this property is set to true for the resource.')
        c.argument('security_type',
                   arg_group='Pool: Security Profile',
                   help='Specify the SecurityType of the virtual machine. It has to be set to any specified value to enable UefiSettings. The default behavior is: UefiSettings will not be enabled unless this property is set.')
        c.argument('secure_boot_enabled', arg_type=get_three_state_flag(),
                   options_list=('--enable-secure-boot'),
                   arg_group='Pool: Security Profile',
                   help='Enable secure boot')
        c.argument('v_tpm_enabled', arg_type=get_three_state_flag(),
                   options_list=('--enable-vtpm'),
                   arg_group='Pool: Security Profile',
                   help='Enable vTPM')
        c.argument('disable_automatic_rollback', options_list=['--disable-auto-rollback'], arg_type=get_three_state_flag())
        c.argument('enable_automatic_os_upgrade', options_list=['--enable-auto-os-upgrade'], arg_type=get_three_state_flag())
        c.argument('os_rolling_upgrade_deferral', options_list=['--defer-os-rolling-upgrade'], arg_type=get_three_state_flag())
        c.argument('use_rolling_upgrade_policy', arg_type=get_three_state_flag())
        c.extra('disk_encryption_targets',
                arg_group="Pool: Virtual Machine Configuration",
                help='A space separated list of DiskEncryptionTargets. current possible values include OsDisk and TemporaryDisk.', type=disk_encryption_configuration_format)
        c.extra('image', completer=load_supported_images, arg_group="Pool: Virtual Machine Configuration",
                help="OS image reference. This can be either 'publisher:offer:sku[:version]' format, or a fully qualified ARM image id of the form '/subscriptions/{subscriptionId}/resourceGroups/{resourceGroup}/providers/Microsoft.Compute/images/{imageName}'. If 'publisher:offer:sku[:version]' format, version is optional and if omitted latest will be used. Valid values can be retrieved via 'az batch pool supported-images list'. For example: 'MicrosoftWindowsServer:WindowsServer:2012-R2-Datacenter:latest'")
        c.argument('mode', options_list=['--upgrade-policy-mode'], help='The mode of the pool OS upgrade.')
        c.argument('enable_cross_zone_upgrade', arg_type=get_three_state_flag())
        c.argument('prioritize_unhealthy_instances', arg_type=get_three_state_flag())
        c.argument('rollback_failed_instances_on_policy_breach', arg_type=get_three_state_flag())

    with self.argument_context('batch task create') as c:
        c.argument('json_file', type=file_type, help='The file containing the task(s) to create in JSON(formatted to match REST API request body). When submitting multiple tasks, accepts either an array of tasks or a TaskAddCollectionParamater. If this parameter is specified, all other parameters are ignored.', validator=validate_json_file, completer=FilesCompleter())
        c.argument('application_package_references', nargs='+', help='The space-separated list of IDs specifying the application packages to be installed. Space-separated application IDs with optional version in \'id[#version]\' format.', type=batch_application_package_reference_format)
        c.argument('job_id', help='The ID of the job containing the task.')
        c.argument('task_id', help='The ID of the task.')
        c.argument('command_line', help='The command line of the task. The command line does not run under a shell, and therefore cannot take advantage of shell features such as environment variable expansion. If you want to take advantage of such features, you should invoke the shell in the command line, for example using "cmd /c MyCommand" in Windows or "/bin/sh -c MyCommand" in Linux.')
        c.argument('environment_settings', nargs='+', help='A list of environment variable settings for the task. Space-separated values in \'key=value\' format.', type=environment_setting_format)
        c.argument('resource_files', nargs='+', help='A list of files that the Batch service will download to the compute node before running the command line. Space-separated resource references in filename=httpurl format, with httpurl being any HTTP url with public access or a SAS url with read access.', type=resource_file_format)
        c.argument('affinity_id', help='Required. You can pass the affinityId of a Node to indicate '
                                       'that this Task needs to run on that Compute Node. Note that '
                                       'this is just a soft affinity. If the target Compute Node is '
                                       'busy or unavailable at the time the Task is scheduled, then '
                                       'the Task will be scheduled elsewhere.')
        c.argument('max_task_retry_count', help='The maximum number of times the Task may be retried. The '
                                                'Batch service retries a Task if its exit code is nonzero. '
                                                'Note that this value specifically controls the number of '
                                                'retries for the Task executable due to a nonzero exit code. '
                                                'The Batch service will try the Task once, and may then retry '
                                                'up to this limit. For example, if the maximum retry count is '
                                                '3, Batch tries the Task up to 4 times (one initial try and 3 '
                                                'retries). If the maximum retry count is 0, the Batch service '
                                                'does not retry the Task after the first attempt. If the '
                                                'maximum retry count is -1, the Batch service retries the Task '
                                                'without limit, however this is not recommended for a start '
                                                'task or any task. The default value is 0 (no retries).')
        c.argument('max_wall_clock_time', type=duration_format, help='If this is not specified, there is no time limit on how long '
                                                                     'the Task may run.')
        c.argument('retention_time', type=duration_format, help='The default is 7 days, i.e. the Task directory will be '
                                                                'retained for 7 days unless the Compute Node is removed or the '
                                                                'Job is deleted.')

    for item in ['batch pool resize', 'batch pool reset', 'batch job list', 'batch task create', 'batch task reset']:
        with self.argument_context(item) as c:
            c.extra('account_name', arg_group='Batch Account', validator=validate_client_parameters,
                    help='The Batch account name. Only needed Alternatively, set by environment variable: AZURE_BATCH_ACCOUNT')
            c.extra('account_key', arg_group='Batch Account',
                    help='The Batch account key. Alternatively, set by environment variable: AZURE_BATCH_ACCESS_KEY')
            c.extra('account_endpoint', arg_group='Batch Account',
                    help='Batch service endpoint. Alternatively, set by environment variable: AZURE_BATCH_ENDPOINT')
