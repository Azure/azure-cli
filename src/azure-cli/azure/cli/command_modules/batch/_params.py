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
    ComputeNodeDeallocationOption,
    NodeCommunicationMode,
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
    application_package_reference_format,
    certificate_reference_format,
    datetime_format,
    disk_encryption_configuration_format,
    environment_setting_format,
    keyvault_id,
    metadata_item_format,
    resource_file_format,
    resource_tag_format,
    storage_account_id,
    validate_cert_file,
    validate_cert_settings,
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

    with self.argument_context('batch private-endpoint-connection show') as c:
        c.argument('private_endpoint_connection_name', options_list=['--name', '-n'],
                   help='The private endpoint connection name. This must be unique within the account.')

    with self.argument_context('batch private-link-resource show') as c:
        c.argument('private_link_resource_name', options_list=['--name', '-n'],
                   help='The private link resource name. This must be unique within the account.')

    with self.argument_context('batch job list') as c:
        c.argument('filter', help=' An OData $filter clause.', arg_group='Pre-condition and Query')
        c.argument('select', help=' An OData $select clause.', arg_group='Pre-condition and Query')
        c.argument('expand', help=' An OData $expand clause.', arg_group='Pre-condition and Query')
        c.argument('job_schedule_id', help='The ID of the job schedule from which you want to get a list of jobs. If omitted, lists all jobs in the account.')

    for command in ['job create', 'job set', 'job reset', 'job-schedule create', 'job-schedule set', 'job-schedule reset']:
        with self.argument_context(f'batch {command}') as c:
            c.argument('pool_id', options_list=('--pool-id',), help='The id of an existing pool. All the tasks of the job will run on the specified pool.')

    with self.argument_context('batch pool create') as c:
        c.argument('json_file', help='The file containing pool create properties parameter specification in JSON(formatted to match REST API request body). If this parameter is specified, all \'Pool Create Properties Parameter Arguments\' are ignored.  See https://docs.microsoft.com/en-us/rest/api/batchservice/pool/add?tabs=HTTP#request-body')
        c.argument('os_family', arg_type=get_enum_type(['2', '3', '4', '5', '6']))
        c.argument('auto_scale_formula', help='A formula for the desired number of compute nodes in the pool. The formula is checked for validity before the pool is created. If the formula is not valid, the Batch service rejects the request with detailed error information. For more information about specifying this formula, see https://azure.microsoft.com/documentation/articles/batch-automatic-scaling/.')
        c.extra('resource_tags', arg_group='Pool', type=resource_tag_format, help="User is able to specify resource tags for the pool. Any resource created for the pool will then also be tagged by the same resource tags")
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
        c.extra('disk_encryption_targets',
                arg_group="Pool: Virtual Machine Configuration",
                help='A space separated list of DiskEncryptionTargets. current possible values include OsDisk and TemporaryDisk.', type=disk_encryption_configuration_format)
        c.extra('image', completer=load_supported_images, arg_group="Pool: Virtual Machine Configuration",
                help="OS image reference. This can be either 'publisher:offer:sku[:version]' format, or a fully qualified ARM image id of the form '/subscriptions/{subscriptionId}/resourceGroups/{resourceGroup}/providers/Microsoft.Compute/images/{imageName}'. If 'publisher:offer:sku[:version]' format, version is optional and if omitted latest will be used. Valid values can be retrieved via 'az batch pool supported-images list'. For example: 'MicrosoftWindowsServer:WindowsServer:2012-R2-Datacenter:latest'")
        c.argument('caching',
                   options_list=('--os-disk-caching'),
                   arg_type=get_enum_type(CachingType),
                   arg_group="Pool: OS Disk",
                   help="Specify the caching requirements. Possible values are: None, ReadOnly, ReadWrite. The default values are: None for Standard storage. ReadOnly for Premium storage.")
        c.argument('storage_account_type',
                   arg_group="Pool: OS Disk",
                   arg_type=get_enum_type(StorageAccountType),
                   help="The storage account type for managed disk")
        c.argument('disk_size_gb',
                   options_list=('--os-disk-size'),
                   arg_group="Pool: OS Disk",
                   help="The initial disk size in GB when creating new OS disk.")
        c.argument('write_accelerator_enabled', arg_type=get_three_state_flag(),
                   options_list=('--enable-write-accel'),
                   arg_group="Pool: OS Disk",
                   help="Specify whether writeAccelerator should be enabled or disabled on the disk.")
        c.argument('target_node_communication_mode', options_list=['--target-communication'],
                   help="The desired node communication mode for the pool. If this element is present, it replaces the existing targetNodeCommunicationMode configured on the Pool. If omitted, any existing metadata is left unchanged.",
                   arg_type=get_enum_type(NodeCommunicationMode))
        c.extra('enable_accelerated_networking', arg_type=get_three_state_flag(), options_list=['--accelerated-networking'], arg_group="Pool: Network Configuration",
                help='Whether this pool should enable accelerated networking. Accelerated networking enables single root I/O virtualization (SR-IOV) to a VM, which may lead to improved networking performance. For more details, see: https://learn.microsoft.com/azure/virtual- network/accelerated-networking-overview. Set true to enable.')
        c.argument('mode', options_list=['--upgrade-policy-mode'], help='The mode of the pool OS upgrade.')
        c.argument('disable_automatic_rollback', options_list=['--disable-auto-rollback'], arg_type=get_three_state_flag())
        c.argument('enable_automatic_os_upgrade', options_list=['--enable-auto-os-upgrade'], arg_type=get_three_state_flag())
        c.argument('os_rolling_upgrade_deferral', options_list=['--defer-os-rolling-upgrade'], arg_type=get_three_state_flag())
        c.argument('use_rolling_upgrade_policy', arg_type=get_three_state_flag())
        c.argument('enable_cross_zone_upgrade', arg_type=get_three_state_flag())
        c.argument('prioritize_unhealthy_instances', arg_type=get_three_state_flag())
        c.argument('rollback_failed_instances_on_policy_breach', arg_type=get_three_state_flag())

    with self.argument_context('batch pool set') as c:
        c.argument('target_node_communication_mode', options_list=['--target-communication'],
                   help="The desired node communication mode for the pool. If this element is present, it replaces the existing targetNodeCommunicationMode configured on the Pool. If omitted, any existing metadata is left unchanged.",
                   arg_type=get_enum_type(NodeCommunicationMode))

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
        c.argument('resource_files', nargs='+', help='A list of files that the Batch service will download to the compute node before running the command line. Space-separated resource references in filename=httpurl format, with httpurl being any HTTP url with public access or a SAS url with read access.', type=resource_file_format)

    for item in ['batch certificate delete', 'batch certificate create', 'batch pool resize', 'batch pool reset', 'batch job list', 'batch task create']:
        with self.argument_context(item) as c:
            c.extra('account_name', arg_group='Batch Account', validator=validate_client_parameters,
                    help='The Batch account name. Alternatively, set by environment variable: AZURE_BATCH_ACCOUNT')
            c.extra('account_key', arg_group='Batch Account',
                    help='The Batch account key. Alternatively, set by environment variable: AZURE_BATCH_ACCESS_KEY')
            c.extra('account_endpoint', arg_group='Batch Account',
                    help='Batch service endpoint. Alternatively, set by environment variable: AZURE_BATCH_ENDPOINT')
