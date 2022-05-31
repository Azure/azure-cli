# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.profiles import ResourceType
from azure.cli.core.commands.validators import get_default_location_from_resource_group
from azure.cli.core.commands.parameters import (tags_type, file_type, get_location_type,
                                                get_enum_type, get_three_state_flag, edge_zone_type)
from azure.cli.core.local_context import LocalContextAttribute, LocalContextAction, ALL

from ._validators import (get_datetime_type, validate_metadata, get_permission_validator, get_permission_help_string,
                          validate_entity, validate_select, validate_blob_type,
                          validate_included_datasets_validator, validate_custom_domain, validate_hns_migration_type,
                          validate_container_public_access,
                          add_progress_callback, process_resource_group,
                          storage_account_key_options, process_file_download_namespace, process_metric_update_namespace,
                          get_char_options_validator, validate_bypass, validate_encryption_source, validate_marker,
                          validate_storage_data_plane_list, validate_azcopy_upload_destination_url,
                          validate_azcopy_remove_arguments, as_user_validator, parse_storage_account,
                          validate_delete_retention_days, validate_container_delete_retention_days,
                          validate_file_delete_retention_days, validator_change_feed_retention_days,
                          validate_fs_public_access, validate_logging_version, validate_or_policy, validate_policy,
                          get_api_version_type, blob_download_file_path_validator, blob_tier_validator, validate_subnet,
                          validate_immutability_arguments, validate_blob_name_for_upload, validate_share_close_handle,
                          blob_tier_validator_track2, services_type_v2, resource_type_type_v2)


def load_arguments(self, _):  # pylint: disable=too-many-locals, too-many-statements, too-many-lines, too-many-branches, line-too-long
    from argcomplete.completers import FilesCompleter

    from knack.arguments import ignore_type, CLIArgumentType

    from azure.cli.core.commands.parameters import get_resource_name_completion_list

    from .sdkutil import get_table_data_type
    from .completers import get_storage_name_completion_list

    t_base_blob_service = self.get_sdk('blob.baseblobservice#BaseBlobService')
    t_file_service = self.get_sdk('file#FileService')
    t_share_service = self.get_sdk('_share_service_client#ShareServiceClient',
                                   resource_type=ResourceType.DATA_STORAGE_FILESHARE)
    t_queue_service = self.get_sdk('_queue_service_client#QueueServiceClient',
                                   resource_type=ResourceType.DATA_STORAGE_QUEUE)
    t_table_service = get_table_data_type(self.cli_ctx, 'table', 'TableService')

    storage_account_type = CLIArgumentType(options_list='--storage-account',
                                           help='The name or ID of the storage account.',
                                           validator=parse_storage_account, id_part='name')

    acct_name_type = CLIArgumentType(options_list=['--account-name', '-n'], help='The storage account name.',
                                     id_part='name',
                                     completer=get_resource_name_completion_list('Microsoft.Storage/storageAccounts'),
                                     local_context_attribute=LocalContextAttribute(
                                         name='storage_account_name', actions=[LocalContextAction.GET]))
    blob_name_type = CLIArgumentType(options_list=['--blob-name', '-b'], help='The blob name.',
                                     completer=get_storage_name_completion_list(t_base_blob_service, 'list_blobs',
                                                                                parent='container_name'))

    container_name_type = CLIArgumentType(options_list=['--container-name', '-c'], help='The container name.',
                                          completer=get_storage_name_completion_list(t_base_blob_service,
                                                                                     'list_containers'))
    directory_type = CLIArgumentType(options_list=['--directory-name', '-d'], help='The directory name.',
                                     completer=get_storage_name_completion_list(t_file_service,
                                                                                'list_directories_and_files',
                                                                                parent='share_name'))
    file_name_type = CLIArgumentType(options_list=['--file-name', '-f'],
                                     completer=get_storage_name_completion_list(t_file_service,
                                                                                'list_directories_and_files',
                                                                                parent='share_name'))
    share_name_type = CLIArgumentType(options_list=['--share-name', '-s'], help='The file share name.',
                                      completer=get_storage_name_completion_list(t_share_service, 'list_shares'))
    table_name_type = CLIArgumentType(options_list=['--table-name', '-t'], help='The table name.',
                                      completer=get_storage_name_completion_list(t_table_service, 'list_tables'))
    queue_name_type = CLIArgumentType(options_list=['--queue-name', '-q'], help='The queue name.',
                                      completer=get_storage_name_completion_list(t_queue_service, 'list_queues'))
    progress_type = CLIArgumentType(help='Include this flag to disable progress reporting for the command.',
                                    action='store_true', validator=add_progress_callback)
    large_file_share_type = CLIArgumentType(
        action='store_true', min_api='2019-04-01',
        help='Enable the capability to support large file shares with more than 5 TiB capacity for storage account.'
             'Once the property is enabled, the feature cannot be disabled. Currently only supported for LRS and '
             'ZRS replication types, hence account conversions to geo-redundant accounts would not be possible. '
             'For more information, please refer to https://go.microsoft.com/fwlink/?linkid=2086047.')
    adds_type = CLIArgumentType(arg_type=get_three_state_flag(), min_api='2019-04-01',
                                arg_group='Azure Files Identity Based Authentication',
                                help='Enable Azure Files Active Directory Domain Service Authentication for '
                                     'storage account. When --enable-files-adds is set to true, Azure Active '
                                     'Directory Properties arguments must be provided.')
    aadds_type = CLIArgumentType(arg_type=get_three_state_flag(), min_api='2018-11-01',
                                 arg_group='Azure Files Identity Based Authentication',
                                 help='Enable Azure Active Directory Domain Services authentication for Azure Files')
    domain_name_type = CLIArgumentType(min_api='2019-04-01', arg_group="Azure Active Directory Properties",
                                       help="Specify the primary domain that the AD DNS server is authoritative for. "
                                            "Required when --enable-files-adds is set to True")
    net_bios_domain_name_type = CLIArgumentType(min_api='2019-04-01', arg_group="Azure Active Directory Properties",
                                                help="Specify the NetBIOS domain name. "
                                                     "Required when --enable-files-adds is set to True")
    forest_name_type = CLIArgumentType(min_api='2019-04-01', arg_group="Azure Active Directory Properties",
                                       help="Specify the Active Directory forest to get. "
                                            "Required when --enable-files-adds is set to True")
    domain_guid_type = CLIArgumentType(min_api='2019-04-01', arg_group="Azure Active Directory Properties",
                                       help="Specify the domain GUID. Required when --enable-files-adds is set to True")
    domain_sid_type = CLIArgumentType(min_api='2019-04-01', arg_group="Azure Active Directory Properties",
                                      help="Specify the security identifier (SID). Required when --enable-files-adds "
                                           "is set to True")
    azure_storage_sid_type = CLIArgumentType(min_api='2019-04-01', arg_group="Azure Active Directory Properties",
                                             help="Specify the security identifier (SID) for Azure Storage. "
                                                  "Required when --enable-files-adds is set to True")
    sam_account_name_type = CLIArgumentType(min_api='2021-08-01', arg_group="Azure Active Directory Properties",
                                            help="Specify the Active Directory SAMAccountName for Azure Storage.")
    t_account_type = self.get_models('ActiveDirectoryPropertiesAccountType', resource_type=ResourceType.MGMT_STORAGE)
    account_type_type = CLIArgumentType(min_api='2021-08-01', arg_group="Azure Active Directory Properties",
                                        arg_type=get_enum_type(t_account_type),
                                        help="Specify the Active Directory account type for Azure Storage.")
    exclude_pattern_type = CLIArgumentType(arg_group='Additional Flags', help='Exclude these files where the name '
                                           'matches the pattern list. For example: *.jpg;*.pdf;exactName. This '
                                           'option supports wildcard characters (*)')
    include_pattern_type = CLIArgumentType(arg_group='Additional Flags', help='Include only these files where the name '
                                           'matches the pattern list. For example: *.jpg;*.pdf;exactName. This '
                                           'option supports wildcard characters (*)')
    exclude_path_type = CLIArgumentType(arg_group='Additional Flags', help='Exclude these paths. This option does not '
                                        'support wildcard characters (*). Checks relative path prefix. For example: '
                                        'myFolder;myFolder/subDirName/file.pdf.')
    include_path_type = CLIArgumentType(arg_group='Additional Flags', help='Include only these paths. This option does '
                                        'not support wildcard characters (*). Checks relative path prefix. For example:'
                                        'myFolder;myFolder/subDirName/file.pdf')
    recursive_type = CLIArgumentType(options_list=['--recursive', '-r'], action='store_true',
                                     help='Look into sub-directories recursively.')
    sas_help = 'The permissions the SAS grants. Allowed values: {}. Do not use if a stored access policy is ' \
               'referenced with --id that specifies this value. Can be combined.'
    t_routing_choice = self.get_models('RoutingChoice', resource_type=ResourceType.MGMT_STORAGE)
    routing_choice_type = CLIArgumentType(
        arg_group='Routing Preference', arg_type=get_enum_type(t_routing_choice),
        help='Routing Choice defines the kind of network routing opted by the user.',
        min_api='2019-06-01')
    publish_microsoft_endpoints_type = CLIArgumentType(
        arg_group='Routing Preference', arg_type=get_three_state_flag(), min_api='2019-06-01',
        help='A boolean flag which indicates whether microsoft routing storage endpoints are to be published.')
    publish_internet_endpoints_type = CLIArgumentType(
        arg_group='Routing Preference', arg_type=get_three_state_flag(), min_api='2019-06-01',
        help='A boolean flag which indicates whether internet routing storage endpoints are to be published.')

    umask_type = CLIArgumentType(
        help='When creating a file or directory and the parent folder does not have a default ACL, the umask restricts '
             'the permissions of the file or directory to be created. The resulting permission is given by p & ^u, '
             'where p is the permission and u is the umask. For more information, please refer to '
             'https://docs.microsoft.com/azure/storage/blobs/data-lake-storage-access-control#umask.')
    permissions_type = CLIArgumentType(
        help='POSIX access permissions for the file owner, the file owning group, and others. Each class may be '
             'granted read, write, or execute permission. The sticky bit is also supported. Both symbolic (rwxrw-rw-) '
             'and 4-digit octal notation (e.g. 0766) are supported. For more information, please refer to https://'
             'docs.microsoft.com/azure/storage/blobs/data-lake-storage-access-control#levels-of-permission.')

    timeout_type = CLIArgumentType(
        help='Request timeout in seconds. Applies to each call to the service.', type=int
    )

    marker_type = CLIArgumentType(
        help='A string value that identifies the portion of the list of containers to be '
             'returned with the next listing operation. The operation returns the NextMarker value within '
             'the response body if the listing operation did not return all containers remaining to be listed '
             'with the current page. If specified, this generator will begin returning results from the point '
             'where the previous generator stopped.')

    num_results_type = CLIArgumentType(
        default=5000, validator=validate_storage_data_plane_list,
        help='Specify the maximum number to return. If the request does not specify '
        'num_results, or specifies a value greater than 5000, the server will return up to 5000 items. Note that '
        'if the listing operation crosses a partition boundary, then the service will return a continuation token '
        'for retrieving the remaining of the results. Provide "*" to return all.'
    )

    if_modified_since_type = CLIArgumentType(
        help='Commence only if modified since supplied UTC datetime (Y-m-d\'T\'H:M\'Z\')',
        type=get_datetime_type(False))
    if_unmodified_since_type = CLIArgumentType(
        help='Commence only if unmodified since supplied UTC datetime (Y-m-d\'T\'H:M\'Z\')',
        type=get_datetime_type(False))

    allow_shared_key_access_type = CLIArgumentType(
        arg_type=get_three_state_flag(), options_list=['--allow-shared-key-access', '-k'], min_api='2019-04-01',
        help='Indicate whether the storage account permits requests to be authorized with the account access key via '
             'Shared Key. If false, then all requests, including shared access signatures, must be authorized with '
             'Azure Active Directory (Azure AD). The default value is null, which is equivalent to true.')

    sas_expiration_period_type = CLIArgumentType(
        options_list=['--sas-expiration-period', '--sas-exp'], min_api='2021-02-01',
        help='Expiration period of the SAS Policy assigned to the storage account, DD.HH:MM:SS.'
    )

    key_expiration_period_in_days_type = CLIArgumentType(
        options_list=['--key-expiration-period-in-days', '--key-exp-days'], min_api='2021-02-01', type=int,
        help='Expiration period in days of the Key Policy assigned to the storage account'
    )

    allow_cross_tenant_replication_type = CLIArgumentType(
        arg_type=get_three_state_flag(), options_list=['--allow-cross-tenant-replication', '-r'], min_api='2021-04-01',
        help='Allow or disallow cross AAD tenant object replication. The default interpretation is true for this '
        'property.')

    t_share_permission = self.get_models('DefaultSharePermission', resource_type=ResourceType.MGMT_STORAGE)

    default_share_permission_type = CLIArgumentType(
        options_list=['--default-share-permission', '-d'],
        arg_type=get_enum_type(t_share_permission),
        min_api='2020-08-01-preview',
        arg_group='Azure Files Identity Based Authentication',
        help='Default share permission for users using Kerberos authentication if RBAC role is not assigned.')

    t_blob_tier = self.get_sdk('_generated.models._azure_blob_storage_enums#AccessTierOptional',
                               resource_type=ResourceType.DATA_STORAGE_BLOB)
    t_rehydrate_priority = self.get_sdk('_generated.models._azure_blob_storage_enums#RehydratePriority',
                                        resource_type=ResourceType.DATA_STORAGE_BLOB)
    tier_type = CLIArgumentType(
        arg_type=get_enum_type(t_blob_tier), min_api='2019-02-02',
        help='The tier value to set the blob to. For page blob, the tier correlates to the size of the blob '
             'and number of allowed IOPS. Possible values are P10, P15, P20, P30, P4, P40, P50, P6, P60, P70, P80 '
             'and this is only applicable to page blobs on premium storage accounts; For block blob, possible '
             'values are Archive, Cool and Hot. This is only applicable to block blobs on standard storage accounts.'
    )
    rehydrate_priority_type = CLIArgumentType(
        arg_type=get_enum_type(t_rehydrate_priority), options_list=('--rehydrate-priority', '-r'),
        min_api='2019-02-02',
        help='Indicate the priority with which to rehydrate an archived blob.')

    action_type = CLIArgumentType(
        help='The action of virtual network rule. Possible value is Allow.'
    )

    immutability_period_since_creation_in_days_type = CLIArgumentType(
        options_list=['--immutability-period-in-days', '--immutability-period'], min_api='2021-06-01',
        help='The immutability period for the blobs in the container since the policy creation, in days.'
    )

    account_immutability_policy_state_enum = self.get_sdk(
        'models._storage_management_client_enums#AccountImmutabilityPolicyState',
        resource_type=ResourceType.MGMT_STORAGE)
    immutability_policy_state_type = CLIArgumentType(
        arg_type=get_enum_type(account_immutability_policy_state_enum),
        options_list='--immutability-state', min_api='2021-06-01',
        help='Defines the mode of the policy. Disabled state disables the policy, '
        'Unlocked state allows increase and decrease of immutability retention time '
        'and also allows toggling allow-protected-append-write property, '
        'Locked state only allows the increase of the immutability retention time. '
        'A policy can only be created in a Disabled or Unlocked state and can be toggled between the '
        'two states. Only a policy in an Unlocked state can transition to a Locked state which cannot '
        'be reverted.')

    public_network_access_enum = self.get_sdk('models._storage_management_client_enums#PublicNetworkAccess',
                                              resource_type=ResourceType.MGMT_STORAGE)

    version_id_type = CLIArgumentType(
        help='An optional blob version ID. This parameter is only for versioning enabled account. ',
        min_api='2019-12-12', is_preview=True
    )

    with self.argument_context('storage') as c:
        c.argument('container_name', container_name_type)
        c.argument('directory_name', directory_type)
        c.argument('share_name', share_name_type)
        c.argument('table_name', table_name_type)
        c.argument('retry_wait', options_list=('--retry-interval',))
        c.ignore('progress_callback')
        c.argument('metadata', nargs='+',
                   help='Metadata in space-separated key=value pairs. This overwrites any existing metadata.',
                   validator=validate_metadata)
        c.argument('timeout', help='Request timeout in seconds. Applies to each call to the service.', type=int)

    with self.argument_context('storage', arg_group='Precondition') as c:
        c.argument('if_modified_since', if_modified_since_type)
        c.argument('if_unmodified_since', if_unmodified_since_type)
        c.argument('if_match')
        c.argument('if_none_match')

    for item in ['delete', 'show', 'update', 'show-connection-string', 'keys', 'network-rule', 'revoke-delegation-keys', 'failover', 'hns-migration']:  # pylint: disable=line-too-long
        with self.argument_context('storage account {}'.format(item)) as c:
            c.argument('account_name', acct_name_type, options_list=['--name', '-n'])
            c.argument('resource_group_name', required=False, validator=process_resource_group)

    with self.argument_context('storage account blob-inventory-policy') as c:
        c.ignore('blob_inventory_policy_name')
        c.argument('resource_group_name', required=False, validator=process_resource_group)
        c.argument('account_name',
                   help='The name of the storage account within the specified resource group. Storage account names '
                        'must be between 3 and 24 characters in length and use numbers and lower-case letters only.')

    with self.argument_context('storage account blob-inventory-policy create') as c:
        c.argument('policy', type=file_type, completer=FilesCompleter(),
                   help='The Storage Account Blob Inventory Policy, string in JSON format or json file path. See more '
                   'details in https://docs.microsoft.com/azure/storage/blobs/blob-inventory#inventory-policy.')

    with self.argument_context('storage account check-name') as c:
        c.argument('name', options_list=['--name', '-n'],
                   help='The name of the storage account within the specified resource group')

    with self.argument_context('storage account delete') as c:
        c.argument('account_name', acct_name_type, options_list=['--name', '-n'], local_context_attribute=None)

    with self.argument_context('storage account create', resource_type=ResourceType.MGMT_STORAGE) as c:
        t_account_type, t_sku_name, t_kind, t_tls_version = \
            self.get_models('AccountType', 'SkuName', 'Kind', 'MinimumTlsVersion',
                            resource_type=ResourceType.MGMT_STORAGE)
        t_identity_type = self.get_models('IdentityType', resource_type=ResourceType.MGMT_STORAGE)
        c.register_common_storage_account_options()
        c.argument('location', get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)
        c.argument('account_type', help='The storage account type', arg_type=get_enum_type(t_account_type))
        c.argument('account_name', acct_name_type, options_list=['--name', '-n'], completer=None,
                   local_context_attribute=LocalContextAttribute(
                       name='storage_account_name', actions=[LocalContextAction.SET], scopes=[ALL]))
        c.argument('kind', help='Indicate the type of storage account.',
                   arg_type=get_enum_type(t_kind),
                   default='StorageV2' if self.cli_ctx.cloud.profile == 'latest' else 'Storage')
        c.argument('https_only', arg_type=get_three_state_flag(), min_api='2019-04-01',
                   help='Allow https traffic only to storage service if set to true. The default value is true.')
        c.argument('https_only', arg_type=get_three_state_flag(), max_api='2018-11-01',
                   help='Allow https traffic only to storage service if set to true. The default value is false.')
        c.argument('tags', tags_type)
        c.argument('custom_domain', help='User domain assigned to the storage account. Name is the CNAME source.')
        c.argument('sku', help='The storage account SKU.', arg_type=get_enum_type(t_sku_name, default='standard_ragrs'))
        c.argument('enable_files_aadds', aadds_type)
        c.argument('enable_files_adds', adds_type)
        c.argument('enable_large_file_share', arg_type=large_file_share_type)
        c.argument('domain_name', domain_name_type)
        c.argument('net_bios_domain_name', net_bios_domain_name_type)
        c.argument('forest_name', forest_name_type)
        c.argument('domain_guid', domain_guid_type)
        c.argument('domain_sid', domain_sid_type)
        c.argument('azure_storage_sid', azure_storage_sid_type)
        c.argument('sam_account_name', sam_account_name_type)
        c.argument('account_type', account_type_type)
        c.argument('enable_hierarchical_namespace', arg_type=get_three_state_flag(),
                   options_list=['--enable-hierarchical-namespace', '--hns',
                                 c.deprecate(target='--hierarchical-namespace', redirect='--hns', hide=True)],
                   help=" Allow the blob service to exhibit filesystem semantics. This property can be enabled only "
                   "when storage account kind is StorageV2.",
                   min_api='2018-02-01')
        c.argument('encryption_key_type_for_table', arg_type=get_enum_type(['Account', 'Service']),
                   help='Set the encryption key type for Table service. "Account": Table will be encrypted '
                        'with account-scoped encryption key. "Service": Table will always be encrypted with '
                        'service-scoped keys. Currently the default encryption key type is "Service".',
                   min_api='2019-06-01', options_list=['--encryption-key-type-for-table', '-t'])
        c.argument('encryption_key_type_for_queue', arg_type=get_enum_type(['Account', 'Service']),
                   help='Set the encryption key type for Queue service. "Account": Queue will be encrypted '
                        'with account-scoped encryption key. "Service": Queue will always be encrypted with '
                        'service-scoped keys. Currently the default encryption key type is "Service".',
                   min_api='2019-06-01', options_list=['--encryption-key-type-for-queue', '-q'])
        c.argument('routing_choice', routing_choice_type)
        c.argument('publish_microsoft_endpoints', publish_microsoft_endpoints_type)
        c.argument('publish_internet_endpoints', publish_internet_endpoints_type)
        c.argument('require_infrastructure_encryption', options_list=['--require-infrastructure-encryption', '-i'],
                   arg_type=get_three_state_flag(),
                   help='A boolean indicating whether or not the service applies a secondary layer of encryption with '
                   'platform managed keys for data at rest.')
        c.argument('allow_blob_public_access', arg_type=get_three_state_flag(), min_api='2019-04-01',
                   help='Allow or disallow public access to all blobs or containers in the storage account. '
                   'The default value for this property is null, which is equivalent to true. When true, containers '
                   'in the account may be configured for public access. Note that setting this property to true does '
                   'not enable anonymous access to any data in the account. The additional step of configuring the '
                   'public access setting for a container is required to enable anonymous access.')
        c.argument('min_tls_version', arg_type=get_enum_type(t_tls_version),
                   help='The minimum TLS version to be permitted on requests to storage. '
                        'The default interpretation is TLS 1.0 for this property')
        c.argument('allow_shared_key_access', allow_shared_key_access_type)
        c.argument('edge_zone', edge_zone_type, min_api='2020-08-01-preview')
        c.argument('identity_type', arg_type=get_enum_type(t_identity_type), arg_group='Identity',
                   help='The identity type.')
        c.argument('user_identity_id', arg_group='Identity',
                   help='The key is the ARM resource identifier of the identity. Only 1 User Assigned identity is '
                   'permitted here.')
        c.argument('key_expiration_period_in_days', key_expiration_period_in_days_type, is_preview=True)
        c.argument('sas_expiration_period', sas_expiration_period_type, is_preview=True)
        c.argument('allow_cross_tenant_replication', allow_cross_tenant_replication_type)
        c.argument('default_share_permission', default_share_permission_type)
        c.argument('enable_nfs_v3', arg_type=get_three_state_flag(), is_preview=True, min_api='2021-01-01',
                   help='NFS 3.0 protocol support enabled if sets to true.')
        c.argument('enable_alw', arg_type=get_three_state_flag(), min_api='2021-06-01',
                   help='The account level immutability property. The property is immutable and can only be set to true'
                        ' at the account creation time. When set to true, it enables object level immutability for all '
                        'the containers in the account by default.',
                   arg_group='Account Level Immutability',
                   validator=validate_immutability_arguments)
        c.argument('immutability_period_since_creation_in_days',
                   arg_type=immutability_period_since_creation_in_days_type,
                   arg_group='Account Level Immutability',
                   validator=validate_immutability_arguments)
        c.argument('immutability_policy_state', arg_type=immutability_policy_state_type,
                   arg_group='Account Level Immutability',
                   validator=validate_immutability_arguments)
        c.argument('allow_protected_append_writes', arg_type=get_three_state_flag(),
                   options_list=['--allow-protected-append-writes', '--allow-append', '-w'],
                   min_api='2021-06-01',
                   help='This property can only be changed for disabled and unlocked time-based retention policies. '
                        'When enabled, new blocks can be written to an append blob while maintaining immutability '
                        'protection and compliance. Only new blocks can be added and any existing blocks cannot be '
                        'modified or deleted.',
                   arg_group='Account Level Immutability',
                   validator=validate_immutability_arguments)
        c.argument('public_network_access', arg_type=get_enum_type(public_network_access_enum), min_api='2021-06-01',
                   help='Enable or disable public network access to the storage account. '
                        'Possible values include: `Enabled` or `Disabled`.')

    with self.argument_context('storage account private-endpoint-connection',
                               resource_type=ResourceType.MGMT_STORAGE) as c:
        c.argument('private_endpoint_connection_name', options_list=['--name', '-n'],
                   help='The name of the private endpoint connection associated with the Storage Account.')
    for item in ['approve', 'reject', 'show', 'delete']:
        with self.argument_context('storage account private-endpoint-connection {}'.format(item),
                                   resource_type=ResourceType.MGMT_STORAGE) as c:
            c.argument('private_endpoint_connection_name', options_list=['--name', '-n'], required=False,
                       help='The name of the private endpoint connection associated with the Storage Account.')
            c.extra('connection_id', options_list=['--id'],
                    help='The ID of the private endpoint connection associated with the Storage Account. You can get '
                    'it using `az storage account show`.')
            c.argument('account_name', help='The storage account name.', required=False)
            c.argument('resource_group_name', help='The resource group name of specified storage account.',
                       required=False)
            c.argument('description', help='Comments for {} operation.'.format(item))

    with self.argument_context('storage account update', resource_type=ResourceType.MGMT_STORAGE) as c:
        t_tls_version = self.get_models('MinimumTlsVersion', resource_type=ResourceType.MGMT_STORAGE)
        t_identity_type = self.get_models('IdentityType', resource_type=ResourceType.MGMT_STORAGE)
        c.register_common_storage_account_options()
        c.argument('sku', arg_type=get_enum_type(t_sku_name),
                   help='Note that the SKU name cannot be updated to Standard_ZRS, Premium_LRS or Premium_ZRS, '
                   'nor can accounts of those SKU names be updated to any other value')
        c.argument('custom_domain',
                   help='User domain assigned to the storage account. Name is the CNAME source. Use "" to clear '
                        'existing value.',
                   validator=validate_custom_domain)
        c.argument('use_subdomain', help='Specify whether to use indirect CNAME validation.',
                   arg_type=get_enum_type(['true', 'false']))
        c.argument('tags', tags_type, default=None)
        c.argument('enable_files_aadds', aadds_type)
        c.argument('enable_files_adds', adds_type)
        c.argument('enable_large_file_share', arg_type=large_file_share_type)
        c.argument('domain_name', domain_name_type)
        c.argument('net_bios_domain_name', net_bios_domain_name_type)
        c.argument('forest_name', forest_name_type)
        c.argument('domain_guid', domain_guid_type)
        c.argument('domain_sid', domain_sid_type)
        c.argument('azure_storage_sid', azure_storage_sid_type)
        c.argument('sam_account_name', sam_account_name_type)
        c.argument('account_type', account_type_type)
        c.argument('routing_choice', routing_choice_type)
        c.argument('publish_microsoft_endpoints', publish_microsoft_endpoints_type)
        c.argument('publish_internet_endpoints', publish_internet_endpoints_type)
        c.argument('allow_blob_public_access', arg_type=get_three_state_flag(), min_api='2019-04-01',
                   help='Allow or disallow public access to all blobs or containers in the storage account. '
                   'The default value for this property is null, which is equivalent to true. When true, containers '
                   'in the account may be configured for public access. Note that setting this property to true does '
                   'not enable anonymous access to any data in the account. The additional step of configuring the '
                   'public access setting for a container is required to enable anonymous access.')
        c.argument('min_tls_version', arg_type=get_enum_type(t_tls_version),
                   help='The minimum TLS version to be permitted on requests to storage. '
                        'The default interpretation is TLS 1.0 for this property')
        c.argument('allow_shared_key_access', allow_shared_key_access_type)
        c.argument('identity_type', arg_type=get_enum_type(t_identity_type), arg_group='Identity',
                   help='The identity type.')
        c.argument('user_identity_id', arg_group='Identity',
                   help='The key is the ARM resource identifier of the identity. Only 1 User Assigned identity is '
                   'permitted here.')
        c.argument('key_expiration_period_in_days', key_expiration_period_in_days_type, is_preview=True)
        c.argument('sas_expiration_period', sas_expiration_period_type, is_preview=True)
        c.argument('allow_cross_tenant_replication', allow_cross_tenant_replication_type)
        c.argument('default_share_permission', default_share_permission_type)
        c.argument('immutability_period_since_creation_in_days',
                   arg_type=immutability_period_since_creation_in_days_type,
                   arg_group='Account Level Immutability')
        c.argument('immutability_policy_state', arg_type=immutability_policy_state_type,
                   arg_group='Account Level Immutability')
        c.argument('allow_protected_append_writes', arg_type=get_three_state_flag(),
                   options_list=['--allow-protected-append-writes', '--allow-append', '-w'],
                   min_api='2021-06-01',
                   help='This property can only be changed for disabled and unlocked time-based retention policies. '
                        'When enabled, new blocks can be written to an append blob while maintaining immutability '
                        'protection and compliance. Only new blocks can be added and any existing blocks cannot be '
                        'modified or deleted.',
                   arg_group='Account Level Immutability')
        c.argument('public_network_access', arg_type=get_enum_type(public_network_access_enum), min_api='2021-06-01',
                   help='Enable or disable public network access to the storage account. '
                        'Possible values include: `Enabled` or `Disabled`.')

    for scope in ['storage account create', 'storage account update']:
        with self.argument_context(scope, arg_group='Customer managed key', min_api='2017-06-01',
                                   resource_type=ResourceType.MGMT_STORAGE) as c:
            t_key_source = self.get_models('KeySource', resource_type=ResourceType.MGMT_STORAGE)
            c.argument('encryption_key_name', help='The name of the KeyVault key.', )
            c.argument('encryption_key_vault', help='The Uri of the KeyVault.')
            c.argument('encryption_key_version',
                       help='The version of the KeyVault key to use, which will opt out of implicit key rotation. '
                       'Please use "" to opt in key auto-rotation again.')
            c.argument('encryption_key_source',
                       arg_type=get_enum_type(t_key_source),
                       help='The default encryption key source',
                       validator=validate_encryption_source)
            c.argument('key_vault_user_identity_id', options_list=['--key-vault-user-identity-id', '-u'],
                       min_api='2021-01-01',
                       help='Resource identifier of the UserAssigned identity to be associated with server-side '
                            'encryption on the storage account.')

    for scope in ['storage account create', 'storage account update']:
        with self.argument_context(scope, resource_type=ResourceType.MGMT_STORAGE, min_api='2017-06-01',
                                   arg_group='Network Rule') as c:
            t_bypass, t_default_action = self.get_models('Bypass', 'DefaultAction',
                                                         resource_type=ResourceType.MGMT_STORAGE)

            c.argument('bypass', nargs='+', validator=validate_bypass, arg_type=get_enum_type(t_bypass),
                       help='Bypass traffic for space-separated uses.')
            c.argument('default_action', arg_type=get_enum_type(t_default_action),
                       help='Default action to apply when no rule matches.')
            c.argument('subnet', help='Name or ID of subnet. If name is supplied, `--vnet-name` must be supplied.')
            c.argument('vnet_name', help='Name of a virtual network.', validator=validate_subnet)
            c.argument('action', action_type)

    with self.argument_context('storage account show-connection-string') as c:
        c.argument('protocol', help='The default endpoint protocol.', arg_type=get_enum_type(['http', 'https']))
        c.argument('sas_token', help='The SAS token to be used in the connection-string.')
        c.argument('key_name', options_list=['--key'], help='The key to use.',
                   arg_type=get_enum_type(list(storage_account_key_options.keys())))
        for item in ['blob', 'file', 'queue', 'table']:
            c.argument('{}_endpoint'.format(item), help='Custom endpoint for {}s.'.format(item))

    with self.argument_context('storage account encryption-scope') as c:
        c.argument('account_name', help='The storage account name.')
        c.argument('resource_group_name', validator=process_resource_group, required=False)
        c.argument('encryption_scope_name', options_list=['--name', '-n'],
                   help='The name of the encryption scope within the specified storage account.')

    for scope in ['storage account encryption-scope create', 'storage account encryption-scope update']:
        with self.argument_context(scope, resource_type=ResourceType.MGMT_STORAGE) as c:
            from ._validators import validate_encryption_key
            t_encryption_key_source = self.get_models('EncryptionScopeSource', resource_type=ResourceType.MGMT_STORAGE)
            c.argument('key_source', options_list=['-s', '--key-source'],
                       arg_type=get_enum_type(t_encryption_key_source, default="Microsoft.Storage"),
                       help='The provider for the encryption scope.', validator=validate_encryption_key)
            c.argument('key_uri', options_list=['-u', '--key-uri'],
                       help='The object identifier for a key vault key object. When applied, the encryption scope will '
                       'use the key referenced by the identifier to enable customer-managed key support on this '
                       'encryption scope.')
            c.argument('require_infrastructure_encryption', options_list=['--require-infrastructure-encryption', '-i'],
                       arg_type=get_three_state_flag(), min_api='2021-01-01',
                       help='A boolean indicating whether or not the service applies a secondary layer of encryption '
                       'with platform managed keys for data at rest.')

    with self.argument_context('storage account encryption-scope update') as c:
        t_state = self.get_models("EncryptionScopeState", resource_type=ResourceType.MGMT_STORAGE)
        c.argument('key_source', options_list=['-s', '--key-source'],
                   arg_type=get_enum_type(t_encryption_key_source),
                   help='The provider for the encryption scope.', validator=validate_encryption_key)
        c.argument('state', arg_type=get_enum_type(t_state),
                   help='Change the state the encryption scope. When disabled, '
                   'all blob read/write operations using this encryption scope will fail.')

    with self.argument_context('storage account keys list', resource_type=ResourceType.MGMT_STORAGE) as c:
        t_expand_key_type = self.get_models('ListKeyExpand', resource_type=ResourceType.MGMT_STORAGE)
        c.argument("expand", options_list=['--expand-key-type'], help='Specify the expanded key types to be listed.',
                   arg_type=get_enum_type(t_expand_key_type), min_api='2019-04-01', is_preview=True)

    with self.argument_context('storage account keys renew', resource_type=ResourceType.MGMT_STORAGE) as c:
        c.argument('key_name', options_list=['--key'], help='The key options to regenerate.',
                   arg_type=get_enum_type(list(storage_account_key_options.keys())))
        c.extra('key_type', help='The key type to regenerate. If --key-type is not specified, one of access keys will '
                'be regenerated by default.', arg_type=get_enum_type(['kerb']), min_api='2019-04-01')
        c.argument('account_name', acct_name_type, id_part=None)

    with self.argument_context('storage account management-policy create') as c:
        c.argument('policy', type=file_type, completer=FilesCompleter(),
                   help='The Storage Account ManagementPolicies Rules, in JSON format. See more details in: '
                        'https://docs.microsoft.com/azure/storage/common/storage-lifecycle-managment-concepts.')

    for item in ['create', 'update', 'show', 'delete']:
        with self.argument_context('storage account management-policy {}'.format(item)) as c:
            c.argument('account_name', help='The name of the storage account within the specified resource group.')

    with self.argument_context('storage account keys list') as c:
        c.argument('account_name', acct_name_type, id_part=None)

    with self.argument_context('storage account network-rule', resource_type=ResourceType.MGMT_STORAGE) as c:
        c.argument('account_name', acct_name_type, id_part=None)
        c.argument('ip_address', help='IPv4 address or CIDR range.')
        c.argument('subnet', help='Name or ID of subnet. If name is supplied, `--vnet-name` must be supplied.')
        c.argument('vnet_name', help='Name of a virtual network.', validator=validate_subnet)
        c.argument('action', action_type)
        c.argument('resource_id', help='The resource id to add in network rule.', arg_group='Resource Access Rule',
                   min_api='2020-08-01-preview')
        c.argument('tenant_id', help='The tenant id to add in network rule.', arg_group='Resource Access Rule',
                   min_api='2020-08-01-preview')

    with self.argument_context('storage account blob-service-properties show',
                               resource_type=ResourceType.MGMT_STORAGE) as c:
        c.argument('account_name', acct_name_type, id_part=None)
        c.argument('resource_group_name', required=False, validator=process_resource_group)

    with self.argument_context('storage account blob-service-properties update',
                               resource_type=ResourceType.MGMT_STORAGE) as c:
        c.argument('account_name', acct_name_type, id_part=None)
        c.argument('resource_group_name', required=False, validator=process_resource_group)
        c.argument('enable_change_feed', arg_type=get_three_state_flag(), min_api='2019-04-01',
                   arg_group='Change Feed Policy')
        c.argument('change_feed_retention_days', is_preview=True,
                   options_list=['--change-feed-retention-days', '--change-feed-days'],
                   type=int, min_api='2019-06-01', arg_group='Change Feed Policy',
                   validator=validator_change_feed_retention_days,
                   help='Indicate the duration of changeFeed retention in days. '
                        'Minimum value is 1 day and maximum value is 146000 days (400 years). '
                        'A null value indicates an infinite retention of the change feed.'
                        '(Use `--enable-change-feed` without `--change-feed-days` to indicate null)')
        c.argument('enable_container_delete_retention',
                   arg_type=get_three_state_flag(),
                   options_list=['--enable-container-delete-retention', '--container-retention'],
                   arg_group='Container Delete Retention Policy', min_api='2019-06-01',
                   help='Enable container delete retention policy for container soft delete when set to true. '
                        'Disable container delete retention policy when set to false.')
        c.argument('container_delete_retention_days',
                   options_list=['--container-delete-retention-days', '--container-days'],
                   type=int, arg_group='Container Delete Retention Policy',
                   min_api='2019-06-01', validator=validate_container_delete_retention_days,
                   help='Indicate the number of days that the deleted container should be retained. The minimum '
                        'specified value can be 1 and the maximum value can be 365.')
        c.argument('enable_delete_retention', arg_type=get_three_state_flag(), arg_group='Delete Retention Policy',
                   min_api='2018-07-01')
        c.argument('delete_retention_days', type=int, arg_group='Delete Retention Policy',
                   validator=validate_delete_retention_days, min_api='2018-07-01')
        c.argument('enable_restore_policy', arg_type=get_three_state_flag(), arg_group='Restore Policy',
                   min_api='2019-06-01', help="Enable blob restore policy when it set to true.")
        c.argument('restore_days', type=int, arg_group='Restore Policy',
                   min_api='2019-06-01', help="The number of days for the blob can be restored. It should be greater "
                   "than zero and less than Delete Retention Days.")
        c.argument('enable_versioning', arg_type=get_three_state_flag(), help='Versioning is enabled if set to true.',
                   min_api='2019-06-01')
        c.argument('default_service_version', options_list=['--default-service-version', '-d'],
                   type=get_api_version_type(), min_api='2018-07-01',
                   help="Indicate the default version to use for requests to the Blob service if an incoming request's "
                        "version is not specified.")
        c.argument('enable_last_access_tracking', arg_type=get_three_state_flag(), min_api='2019-06-01',
                   options_list=['--enable-last-access-tracking', '-t'],
                   help='When set to true last access time based tracking policy is enabled.')

    with self.argument_context('storage account file-service-properties show',
                               resource_type=ResourceType.MGMT_STORAGE) as c:
        c.argument('account_name', acct_name_type, id_part=None)
        c.argument('resource_group_name', required=False, validator=process_resource_group)

    with self.argument_context('storage account file-service-properties update',
                               resource_type=ResourceType.MGMT_STORAGE) as c:
        c.argument('account_name', acct_name_type, id_part=None)
        c.argument('resource_group_name', required=False, validator=process_resource_group)
        c.argument('enable_delete_retention', arg_type=get_three_state_flag(), arg_group='Delete Retention Policy',
                   min_api='2019-06-01', help='Enable file service properties for share soft delete.')
        c.argument('delete_retention_days', type=int, arg_group='Delete Retention Policy',
                   validator=validate_file_delete_retention_days, min_api='2019-06-01',
                   help='Indicate the number of days that the deleted item should be retained. The minimum specified '
                   'value can be 1 and the maximum value can be 365.')
        c.argument('enable_smb_multichannel', options_list=['--enable-smb-multichannel', '--mc'],
                   arg_type=get_three_state_flag(), min_api='2020-08-01-preview', arg_group='SMB Setting',
                   help='Set SMB Multichannel setting for file service. Applies to Premium FileStorage only.')
        c.argument('versions', arg_group='SMB Setting', min_api='2020-08-01-preview',
                   help="SMB protocol versions supported by server. Valid values are SMB2.1, SMB3.0, "
                        "SMB3.1.1. Should be passed as a string with delimiter ';'.")
        c.argument('authentication_methods', options_list='--auth-methods', arg_group='SMB Setting',
                   min_api='2020-08-01-preview',
                   help="SMB authentication methods supported by server. Valid values are NTLMv2, Kerberos. "
                        "Should be passed as a string with delimiter ';'.")
        c.argument('kerberos_ticket_encryption', options_list=['--kerb-ticket-encryption', '-k'],
                   arg_group='SMB Setting', min_api='2020-08-01-preview',
                   help="Kerberos ticket encryption supported by server. Valid values are RC4-HMAC, AES-256. "
                        "Should be passed as a string with delimiter ';'.")
        c.argument('channel_encryption', arg_group='SMB Setting', min_api='2020-08-01-preview',
                   help="SMB channel encryption supported by server. Valid values are AES-128-CCM, AES-128-GCM, "
                        "AES-256-GCM. Should be passed as a string with delimiter ';' ")

    with self.argument_context('storage account generate-sas', resource_type=ResourceType.DATA_STORAGE_BLOB) as c:
        t_account_permissions = self.get_sdk('_shared.models#AccountSasPermissions',
                                             resource_type=ResourceType.DATA_STORAGE_BLOB)
        c.register_sas_arguments()
        c.argument('services', type=services_type_v2())
        c.argument('resource_types', type=resource_type_type_v2(self))
        c.argument('expiry', type=get_datetime_type(True))
        c.argument('start', type=get_datetime_type(True))
        c.argument('account_name', acct_name_type, options_list=['--account-name'])
        c.argument('permission', options_list=('--permissions',),
                   help='The permissions the SAS grants. Allowed values: {}. Can be combined.'.format(
                       get_permission_help_string(t_account_permissions)),
                   validator=get_permission_validator(t_account_permissions))
        c.extra('encryption_scope', help='A predefined encryption scope used to encrypt the data on the service.')
        c.ignore('sas_token')

    or_policy_type = CLIArgumentType(
        options_list=['--policy', '-p'],
        help='The object replication policy definition between two storage accounts, in JSON format. '
             'Multiple rules can be defined in one policy.'
    )
    policy_id_type = CLIArgumentType(
        options_list=['--policy-id'],
        help='The ID of object replication policy or "default" if the policy ID is unknown. Policy Id will be '
             'auto-generated when setting on destination account. Required when setting on source account.'
    )
    rule_id_type = CLIArgumentType(
        options_list=['--rule-id', '-r'],
        help='Rule Id is auto-generated for each new rule on destination account. It is required '
             'for put policy on source account.'
    )
    prefix_math_type = CLIArgumentType(
        nargs='+', arg_group='Filters', options_list=['--prefix-match', '--prefix'],
        help='Optional. Filter the results to replicate only blobs whose names begin with the specified '
             'prefix.'
    )
    min_creation_time_type = CLIArgumentType(
        options_list=['--min-creation-time', '-t'], arg_group='Filters', type=get_datetime_type(True),
        help="Blobs created after the time will be replicated to the destination. It must be in datetime format "
             "'yyyy-MM-ddTHH:mm:ssZ'. Example: 2020-02-19T16:05:00Z")

    with self.argument_context('storage account or-policy') as c:
        c.argument('account_name', acct_name_type, id_part=None)
        c.argument('resource_group_name', required=False, validator=process_resource_group)
        c.argument('object_replication_policy_id', policy_id_type)
        c.argument('policy_id', policy_id_type)
        c.argument('source_account', options_list=['--source-account', '-s'],
                   help='The source storage account name or resource Id. Required when no --policy provided.')
        c.argument('destination_account', options_list=['--destination-account', '-d'],
                   help='The destination storage account name or resource Id. Apply --account-name value as '
                   'destination account when there is no destination account provided in --policy and '
                   '--destination-account.')
        c.argument('properties', or_policy_type)
        c.argument('prefix_match', prefix_math_type)
        c.argument('min_creation_time', min_creation_time_type)

    for item in ['create', 'update']:
        with self.argument_context('storage account or-policy {}'.format(item),
                                   arg_group="Object Replication Policy Rule") as c:
            c.argument('rule_id', help='Rule Id is auto-generated for each new rule on destination account. It is '
                                       'required for put policy on source account.')
            c.argument('source_container', options_list=['--source-container', '--scont'],
                       help='The source storage container name. Required when no --policy provided.')
            c.argument('destination_container', options_list=['--destination-container', '--dcont'],
                       help='The destination storage container name. Required when no --policy provided.')

    with self.argument_context('storage account or-policy create') as c:
        c.argument('properties', or_policy_type, validator=validate_or_policy)

    with self.argument_context('storage account or-policy rule') as c:
        c.argument('policy_id', policy_id_type)
        c.argument('source_container', options_list=['--source-container', '-s'],
                   help='The source storage container name.')
        c.argument('destination_container', options_list=['--destination-container', '-d'],
                   help='The destination storage container name.')
        c.argument('rule_id', rule_id_type)

    with self.argument_context('storage account hns-migration start') as c:
        c.argument('request_type', options_list=['--type', '--request-type'],
                   arg_type=get_enum_type(['validation', 'upgrade']), validator=validate_hns_migration_type,
                   help='Start a validation request for migration or start a migration request')

    for item in ['show', 'off']:
        with self.argument_context('storage logging {}'.format(item)) as c:
            c.extra('services', validator=get_char_options_validator('bqt', 'services'), default='bqt')

    with self.argument_context('storage logging update') as c:
        c.extra('services', validator=get_char_options_validator('bqt', 'services'), options_list='--services',
                required=True)
        c.argument('log', validator=get_char_options_validator('rwd', 'log'))
        c.argument('retention', type=int)
        c.argument('version', type=float, validator=validate_logging_version)

    with self.argument_context('storage metrics show') as c:
        c.extra('services', validator=get_char_options_validator('bfqt', 'services'), default='bfqt')
        c.argument('interval', arg_type=get_enum_type(['hour', 'minute', 'both']))

    with self.argument_context('storage metrics update') as c:
        c.extra('services', validator=get_char_options_validator('bfqt', 'services'), options_list='--services',
                required=True)
        c.argument('hour', validator=process_metric_update_namespace, arg_type=get_enum_type(['true', 'false']))
        c.argument('minute', arg_type=get_enum_type(['true', 'false']))
        c.argument('api', arg_type=get_enum_type(['true', 'false']))
        c.argument('retention', type=int)

    with self.argument_context('storage blob') as c:
        c.argument('blob_name', options_list=('--name', '-n'), arg_type=blob_name_type)
        c.argument('destination_path', help='The destination path that will be prepended to the blob name.')
        c.argument('socket_timeout', deprecate_info=c.deprecate(hide=True),
                   help='The socket timeout(secs), used by the service to regulate data flow.')

    with self.argument_context('storage blob list') as c:
        from ._validators import get_include_help_string
        t_blob_include = self.get_sdk('_generated.models._azure_blob_storage_enums#ListBlobsIncludeItem',
                                      resource_type=ResourceType.DATA_STORAGE_BLOB)
        c.register_container_arguments()
        c.argument('delimiter',
                   help='When the request includes this parameter, the operation returns a BlobPrefix element in the '
                   'result list that acts as a placeholder for all blobs whose names begin with the same substring '
                   'up to the appearance of the delimiter character. The delimiter may be a single character or a '
                   'string.')
        c.argument('include', help="Specify one or more additional datasets to include in the response. "
                   "Options include: {}. Can be combined.".format(get_include_help_string(t_blob_include)),
                   validator=validate_included_datasets_validator(include_class=t_blob_include))
        c.argument('marker', arg_type=marker_type)
        c.argument('num_results', arg_type=num_results_type)
        c.argument('prefix',
                   help='Filter the results to return only blobs whose name begins with the specified prefix.')
        c.argument('show_next_marker', action='store_true',
                   help='Show nextMarker in result when specified.')

    with self.argument_context('storage blob generate-sas', resource_type=ResourceType.DATA_STORAGE_BLOB) as c:
        from .completers import get_storage_acl_name_completion_list

        t_blob_permissions = self.get_sdk('_models#BlobSasPermissions', resource_type=ResourceType.DATA_STORAGE_BLOB)
        c.register_sas_arguments()
        c.register_blob_arguments_track2()
        c.argument('cache_control', help='Response header value for Cache-Control when resource is accessed '
                                         'using this shared access signature.')
        c.argument('content_disposition', help='Response header value for Content-Disposition when resource is '
                                               'accessed using this shared access signature.')
        c.argument('content_encoding', help='Response header value for Content-Encoding when resource is accessed '
                                            'using this shared access signature.')
        c.argument('content_language', help='Response header value for Content-Language when resource is accessed '
                                            'using this shared access signature.')
        c.argument('content_type', help='Response header value for Content-Type when resource is accessed '
                                        'using this shared access signature.')
        c.argument('full_uri', action='store_true',
                   help='Indicates that this command return the full blob URI and the shared access signature token.')
        c.argument('as_user', min_api='2018-11-09', action='store_true',
                   validator=as_user_validator,
                   help="Indicates that this command return the SAS signed with the user delegation key. "
                        "The expiry parameter and '--auth-mode login' are required if this argument is specified. ")
        c.argument('id', options_list='--policy-name', validator=validate_policy,
                   help='The name of a stored access policy within the container\'s ACL.',
                   completer=get_storage_acl_name_completion_list(t_base_blob_service, 'container_name',
                                                                  'get_container_acl'))
        c.argument('permission', options_list='--permissions',
                   help=sas_help.format(get_permission_help_string(t_blob_permissions)),
                   validator=get_permission_validator(t_blob_permissions))
        c.argument('snapshot', help='An optional blob snapshot ID. Opaque DateTime value that, when present, '
                                    'specifies the blob snapshot to grant permission.')
        c.extra('encryption_scope', help='A predefined encryption scope used to encrypt the data on the service.')
        c.ignore('sas_token')

    with self.argument_context('storage blob restore', resource_type=ResourceType.MGMT_STORAGE) as c:
        from ._validators import BlobRangeAddAction
        c.argument('blob_ranges', options_list=['--blob-range', '-r'], action=BlobRangeAddAction, nargs='+',
                   help='Blob ranges to restore. You need to two values to specify start_range and end_range for each '
                        'blob range, e.g. -r blob1 blob2. Note: Empty means account start as start range value, and '
                        'means account end for end range.')
        c.argument('account_name', acct_name_type, id_part=None)
        c.argument('resource_group_name', required=False, validator=process_resource_group)
        c.argument('time_to_restore', type=get_datetime_type(True), options_list=['--time-to-restore', '-t'],
                   help='Restore blob to the specified time, which should be UTC datetime in (Y-m-d\'T\'H:M:S\'Z\').')

    with self.argument_context('storage blob rewrite', resource_type=ResourceType.DATA_STORAGE_BLOB,
                               min_api='2020-04-08') as c:
        c.register_blob_arguments()
        c.register_precondition_options()

        c.argument('source_url', options_list=['--source-uri', '-u'],
                   help='A URL of up to 2 KB in length that specifies a file or blob. The value should be URL-encoded '
                   'as it would appear in a request URI. If the source is in another account, the source must either '
                   'be public or must be authenticated via a shared access signature. If the source is public, no '
                   'authentication is required.')
        c.extra('lease', options_list='--lease-id',
                help='Required if the blob has an active lease. Value can be a BlobLeaseClient object '
                'or the lease ID as a string.')
        c.extra('standard_blob_tier', arg_type=get_enum_type(t_blob_tier), options_list='--tier',
                help='A standard blob tier value to set the blob to. For this version of the library, '
                     'this is only applicable to block blobs on standard storage accounts.')
        c.extra('encryption_scope',
                help='A predefined encryption scope used to encrypt the data on the service. An encryption scope '
                'can be created using the Management API and referenced here by name. If a default encryption scope '
                'has been defined at the container, this value will override it if the container-level scope is '
                'configured to allow overrides. Otherwise an error will be raised.')

    with self.argument_context('storage blob update') as c:
        c.register_blob_arguments()
        c.register_precondition_options()
        t_blob_content_settings = self.get_sdk('_models#ContentSettings', resource_type=ResourceType.DATA_STORAGE_BLOB)
        c.register_content_settings_argument(t_blob_content_settings, update=True)
        c.extra('lease', options_list=['--lease-id'], help='Required if the blob has an active lease.')

    with self.argument_context('storage blob exists') as c:
        c.register_blob_arguments()
        c.extra('snapshot', help='The snapshot parameter is an opaque DateTime value that, when present, '
                                 'specifies the snapshot.')

    with self.argument_context('storage blob url') as c:
        from ._validators import get_not_none_validator
        c.extra('blob_name', required=True)
        c.extra('container_name', required=True, validator=get_not_none_validator('container_name'))
        c.extra('protocol', arg_type=get_enum_type(['http', 'https'], 'https'), help='Protocol to use.')
        c.extra('snapshot', help='An string value that uniquely identifies the snapshot. The value of this query '
                                 'parameter indicates the snapshot version.')

    with self.argument_context('storage blob snapshot') as c:
        c.register_blob_arguments()
        c.register_precondition_options()
        c.extra('lease', options_list=['--lease-id'], help='Required if the blob has an active lease.')

    with self.argument_context('storage blob set-tier') as c:
        from azure.cli.command_modules.storage._validators import (blob_rehydrate_priority_validator)
        c.register_blob_arguments()

        c.argument('blob_type', options_list=('--type', '-t'), arg_type=get_enum_type(('block', 'page')))
        c.argument('tier', validator=blob_tier_validator)
        c.argument('rehydrate_priority', options_list=('--rehydrate-priority', '-r'),
                   arg_type=get_enum_type(('High', 'Standard')), validator=blob_rehydrate_priority_validator,
                   is_preview=True, help="Indicate the priority with which to rehydrate an archived blob. "
                                         "The priority can be set on a blob only once, default value is Standard.")

    with self.argument_context('storage blob set-legal-hold') as c:
        c.register_blob_arguments()
        c.argument('legal_hold', arg_type=get_three_state_flag(),
                   help='Specified if a legal hold should be set on the blob.')

    with self.argument_context('storage blob immutability-policy delete') as c:
        c.register_blob_arguments()

    with self.argument_context('storage blob immutability-policy set') as c:
        c.register_blob_arguments()
        c.argument('expiry_time', type=get_datetime_type(False),
                   help='expiration UTC datetime in (Y-m-d\'T\'H:M:S\'Z\')')
        c.argument('policy_mode', arg_type=get_enum_type(['Locked', 'Unlocked']), help='Lock or Unlock the policy')

    with self.argument_context('storage blob service-properties delete-policy update') as c:
        c.argument('enable', arg_type=get_enum_type(['true', 'false']), help='Enables/disables soft-delete.')
        c.argument('days_retained', type=int,
                   help='Number of days that soft-deleted blob will be retained. Must be in range [1,365].')

    with self.argument_context('storage blob service-properties update', min_api='2018-03-28') as c:
        c.argument('delete_retention', arg_type=get_three_state_flag(), arg_group='Soft Delete',
                   help='Enables soft-delete.')
        c.argument('delete_retention_period', type=int, arg_group='Soft Delete',
                   help='Number of days that soft-deleted blob will be retained. Must be in range [1,365].')
        c.argument('static_website', arg_group='Static Website', arg_type=get_three_state_flag(),
                   help='Enables static-website.')
        c.argument('index_document', help='Represents the name of the index document. This is commonly "index.html".',
                   arg_group='Static Website')
        c.argument('error_document_404_path', options_list=['--404-document'], arg_group='Static Website',
                   help='Represents the path to the error document that should be shown when an error 404 is issued,'
                        ' in other words, when a browser requests a page that does not exist.')

    with self.argument_context('storage blob show') as c:
        c.register_blob_arguments()
        c.register_precondition_options()
        c.extra('snapshot', help='The snapshot parameter is an opaque DateTime value that, when present, '
                                 'specifies the blob snapshot to retrieve.')
        c.argument('lease_id', help='Required if the blob has an active lease.')

    # pylint: disable=line-too-long
    with self.argument_context('storage blob upload', resource_type=ResourceType.DATA_STORAGE_BLOB) as c:
        from ._validators import validate_encryption_scope_client_params, validate_upload_blob

        from .sdkutil import get_blob_types

        t_blob_content_settings = self.get_sdk('_models#ContentSettings', resource_type=ResourceType.DATA_STORAGE_BLOB)

        c.register_blob_arguments_track2()
        c.register_precondition_options()
        c.register_content_settings_argument(t_blob_content_settings, update=False, arg_group="Content Control",
                                             process_md5=True)
        c.extra('blob_name', validator=validate_blob_name_for_upload)

        c.argument('file_path', options_list=('--file', '-f'), type=file_type, completer=FilesCompleter(),
                   help='Path of the file to upload as the blob content.', validator=validate_upload_blob)
        c.argument('data', help='The blob data to upload.', required=False, is_preview=True, min_api='2019-02-02')
        c.argument('length', type=int, help='Number of bytes to read from the stream. This is optional, but should be '
                                            'supplied for optimal performance. Cooperate with --data.', is_preview=True,
                   min_api='2019-02-02')
        c.argument('overwrite', arg_type=get_three_state_flag(), arg_group="Additional Flags", is_preview=True,
                   help='Whether the blob to be uploaded should overwrite the current data. If True, blob upload '
                        'operation will overwrite the existing data. If set to False, the operation will fail with '
                        'ResourceExistsError. The exception to the above is with Append blob types: if set to False and the '
                        'data already exists, an error will not be raised and the data will be appended to the existing '
                        'blob. If set overwrite=True, then the existing append blob will be deleted, and a new one created. '
                        'Defaults to False.')
        c.argument('max_connections', type=int, arg_group="Additional Flags",
                   help='Maximum number of parallel connections to use when the blob size exceeds 64MB.')
        c.extra('maxsize_condition', type=int, arg_group="Content Control",
                help='The max length in bytes permitted for the append blob.')
        c.argument('blob_type', options_list=('--type', '-t'), validator=validate_blob_type,
                   arg_type=get_enum_type(get_blob_types()), arg_group="Additional Flags")
        c.argument('validate_content', action='store_true', min_api='2016-05-31', arg_group="Content Control")
        c.extra('no_progress', progress_type, validator=add_progress_callback, arg_group="Additional Flags")
        c.extra('tier', tier_type, validator=blob_tier_validator_track2, arg_group="Additional Flags")
        c.argument('encryption_scope', validator=validate_encryption_scope_client_params,
                   help='A predefined encryption scope used to encrypt the data on the service.',
                   arg_group="Additional Flags")
        c.argument('lease_id', help='Required if the blob has an active lease.')
        c.extra('tags', arg_type=tags_type, arg_group="Additional Flags")
        c.argument('metadata', arg_group="Additional Flags")
        c.argument('timeout', arg_group="Additional Flags")

    # pylint: disable=line-too-long
    with self.argument_context('storage blob upload-batch', resource_type=ResourceType.DATA_STORAGE_BLOB) as c:
        from .sdkutil import get_blob_types

        t_blob_content_settings = self.get_sdk('_models#ContentSettings', resource_type=ResourceType.DATA_STORAGE_BLOB)
        c.register_precondition_options()
        c.register_content_settings_argument(t_blob_content_settings, update=False, arg_group='Content Control')
        c.ignore('source_files', 'destination_container_name')

        c.argument('source', options_list=('--source', '-s'))
        c.argument('destination', options_list=('--destination', '-d'))
        c.argument('max_connections', type=int,
                   help='Maximum number of parallel connections to use when the blob size exceeds 64MB.')
        c.argument('maxsize_condition', arg_group='Content Control')
        c.argument('validate_content', action='store_true', min_api='2016-05-31', arg_group='Content Control')
        c.argument('blob_type', options_list=('--type', '-t'), arg_type=get_enum_type(get_blob_types()))
        c.extra('no_progress', progress_type, validator=add_progress_callback)
        c.extra('tier', tier_type, is_preview=True, validator=blob_tier_validator_track2)
        c.extra('overwrite', arg_type=get_three_state_flag(), is_preview=True,
                help='Whether the blob to be uploaded should overwrite the current data. If True, blob upload '
                     'operation will overwrite the existing data. If set to False, the operation will fail with '
                     'ResourceExistsError. The exception to the above is with Append blob types: if set to False and the '
                     'data already exists, an error will not be raised and the data will be appended to the existing '
                     'blob. If set overwrite=True, then the existing append blob will be deleted, and a new one created. '
                     'Defaults to False.')

    with self.argument_context('storage blob download', resource_type=ResourceType.DATA_STORAGE_BLOB) as c:
        c.register_blob_arguments_track2()
        c.register_precondition_options()
        c.argument('file_path', options_list=('--file', '-f'), type=file_type, completer=FilesCompleter(),
                   help='Path of file to write out to. If not specified, stdout will be used '
                        'and max_connections will be set to 1.', validator=blob_download_file_path_validator)
        c.argument('start_range', type=int,
                   help='Start of byte range to use for downloading a section of the blob. If no end_range is given, '
                        'all bytes after the start_range will be downloaded. The start_range and end_range params are '
                        'inclusive. Ex: start_range=0, end_range=511 will download first 512 bytes of blob.')
        c.argument('end_range', type=int,
                   help='End of byte range to use for downloading a section of the blob. If end_range is given, '
                        'start_range must be provided. The start_range and end_range params are inclusive. '
                        'Ex: start_range=0, end_range=511 will download first 512 bytes of blob.')
        c.extra('no_progress', progress_type, validator=add_progress_callback)
        c.extra('snapshot', help='The snapshot parameter is an opaque DateTime value that, when present, '
                                 'specifies the blob snapshot to retrieve.')
        c.extra('lease', options_list=['--lease-id'], help='Required if the blob has an active lease.')
        c.extra('version_id', version_id_type)
        c.extra('max_concurrency', options_list=['--max-connections'], type=int, default=2,
                help='The number of parallel connections with which to download.')
        c.argument('open_mode', help='Mode to use when opening the file. Note that specifying append only open_mode '
                                     'prevents parallel download. So, max_connections must be set to 1 '
                                     'if this open_mode is used.')
        c.extra('validate_content', action='store_true', min_api='2016-05-31',
                help='If true, calculates an MD5 hash for each chunk of the blob. The storage service checks the '
                     'hash of the content that has arrived with the hash that was sent. This is primarily valuable for '
                     'detecting bitflips on the wire if using http instead of https, as https (the default), '
                     'will already validate. Note that this MD5 hash is not stored with the blob. Also note that '
                     'if enabled, the memory-efficient algorithm will not be used because computing the MD5 hash '
                     'requires buffering entire blocks, and doing so defeats the purpose of the memory-efficient '
                     'algorithm.')

    with self.argument_context('storage blob download-batch') as c:
        c.ignore('source_container_name')
        c.argument('destination', options_list=('--destination', '-d'))
        c.argument('source', options_list=('--source', '-s'))
        c.extra('no_progress', progress_type)
        c.extra('max_concurrency', options_list=['--max-connections'], type=int, default=2,
                help='The number of parallel connections with which to download.')

    with self.argument_context('storage blob delete') as c:
        from .sdkutil import get_delete_blob_snapshot_type_names
        c.register_blob_arguments()
        c.register_precondition_options()
        c.argument('delete_snapshots', arg_type=get_enum_type(get_delete_blob_snapshot_type_names()),
                   help='Required if the blob has associated snapshots. '
                        'Values include: "only": Deletes only the blobs snapshots. '
                        '"include": Deletes the blob along with all snapshots.')
        c.extra('lease', options_list='--lease-id', help='Required if the blob has an active lease.')
        c.extra('snapshot', help='The snapshot parameter is an opaque DateTime value that, when present, '
                                 'specifies the blob snapshot to delete.')

    with self.argument_context('storage blob undelete') as c:
        c.register_blob_arguments()

    with self.argument_context('storage blob delete-batch') as c:
        c.ignore('source_container_name')
        c.argument('source', options_list=('--source', '-s'))
        c.argument('delete_snapshots', arg_type=get_enum_type(get_delete_blob_snapshot_type_names()),
                   help='Required if the blob has associated snapshots.')
        c.argument('lease_id', help='The active lease id for the blob.')

    with self.argument_context('storage blob lease') as c:
        c.argument('blob_name', arg_type=blob_name_type)

    with self.argument_context('storage blob lease acquire') as c:
        c.register_precondition_options()
        c.register_blob_arguments()
        c.extra('lease_id', options_list='--proposed-lease-id', help='Proposed lease ID, in a GUID string format. '
                'The Blob service returns 400 (Invalid request) if the proposed lease ID is not in the correct format.')
        c.argument('lease_duration', help='Specify the duration of the lease, in seconds, or negative one (-1) for '
                   'a lease that never expires. A non-infinite lease can be between 15 and 60 seconds. A lease '
                   'duration cannot be changed using renew or change. Default is -1 (infinite lease)', type=int)

    with self.argument_context('storage blob lease break') as c:
        c.register_precondition_options()
        c.register_blob_arguments()
        c.argument('lease_break_period', type=int,
                   help="This is the proposed duration of seconds that the lease should continue before it is broken, "
                   "between 0 and 60 seconds. This break period is only used if it is shorter than the time remaining "
                   "on the lease. If longer, the time remaining on the lease is used. A new lease will not be "
                   "available before the break period has expired, but the lease may be held for longer than the break "
                   "period. If this header does not appear with a break operation, a fixed-duration lease breaks after "
                   "the remaining lease period elapses, and an infinite lease breaks immediately.")

    with self.argument_context('storage blob lease change') as c:
        c.register_precondition_options()
        c.register_blob_arguments()
        c.extra('proposed_lease_id', help='Proposed lease ID, in a GUID string format. The Blob service returns 400 '
                '(Invalid request) if the proposed lease ID is not in the correct format.', required=True)
        c.extra('lease_id', help='Required if the blob has an active lease.', required=True)

    for item in ['release', 'renew']:
        with self.argument_context('storage blob lease {}'.format(item)) as c:
            c.register_precondition_options()
            c.register_blob_arguments()
            c.extra('lease_id', help='Required if the blob has an active lease.', required=True)

    with self.argument_context('storage copy') as c:
        c.argument('destination',
                   options_list=['--destination', '-d',
                                 c.deprecate(target='--destination-local-path', redirect='--destination')],
                   help="The path/url of copy destination. "
                   "It can be a local path, an url to azure storage server. If you provide destination parameter "
                   "here, you do not need to provide arguments in copy destination arguments group and copy "
                   "destination arguments will be deprecated in future.", required=False)
        c.argument('source',
                   options_list=['--source', '-s',
                                 c.deprecate(target='--source-local-path', redirect='--source')],
                   help="The path/url of copy source. It can be a local"
                   " path, an url to azure storage server or AWS S3 buckets. If you provide source parameter here,"
                   " you do not need to provide arguments in copy source arguments group and copy source arguments"
                   " will be deprecated in future.", required=False)
        for item in ['destination', 'source']:
            c.extra('{}_container'.format(item), arg_group='Copy {}'.format(item),
                    help='Container name of copy {} storage account'.format(item))
            c.extra('{}_blob'.format(item), arg_group='Copy {}'.format(item),
                    help='Blob name in blob container of copy {} storage account'.format(item))
            c.extra('{}_share'.format(item), arg_group='Copy {}'.format(item),
                    help='File share name of copy {} storage account'.format(item))
            c.extra('{}_file_path'.format(item), arg_group='Copy {}'.format(item),
                    help='File path in file share of copy {} storage account'.format(item))

        c.argument('account_name', acct_name_type, arg_group='Storage Account', id_part=None,
                   options_list=['--account-name',
                                 c.deprecate(target='--destination-account-name', redirect='--account-name')],
                   help='Storage account name of copy destination')
        c.extra('source_account_name', arg_group='Copy source',
                help='Account name of copy source storage account.')
        c.extra('source_account_key', arg_group='Copy source',
                help='Account key of copy source storage account. Must be used in conjunction with source storage '
                     'account name.')
        c.extra('source_connection_string', arg_group='Copy source',
                options_list=['--source-connection-string', '--src-conn'],
                help='Connection string of source storage account.')
        c.extra('source_sas', arg_group='Copy source',
                help='Shared Access Signature (SAS) token of copy source. Must be used in conjunction with source '
                     'storage account name.')
        c.argument('put_md5', arg_group='Additional Flags', action='store_true',
                   help='Create an MD5 hash of each file, and save the hash as the Content-MD5 property of the '
                   'destination blob/file.Only available when uploading.')
        c.argument('blob_type', arg_group='Additional Flags',
                   arg_type=get_enum_type(["BlockBlob", "PageBlob", "AppendBlob"]),
                   help='The type of blob at the destination.')
        c.argument('preserve_s2s_access_tier', arg_group='Additional Flags', arg_type=get_three_state_flag(),
                   help='Preserve access tier during service to service copy. '
                   'Please refer to https://docs.microsoft.com/azure/storage/blobs/storage-blob-storage-tiers '
                   'to ensure destination storage account support setting access tier. In the cases that setting '
                   'access tier is not supported, please use `--preserve-s2s-access-tier false` to bypass copying '
                   'access tier. (Default true)')
        c.argument('exclude_pattern', exclude_pattern_type)
        c.argument('include_pattern', include_pattern_type)
        c.argument('exclude_path', exclude_path_type)
        c.argument('include_path', include_path_type)
        c.argument('recursive', recursive_type)
        c.argument('content_type', arg_group='Additional Flags', help="Specify content type of the file. ")
        c.argument('follow_symlinks', arg_group='Additional Flags', action='store_true',
                   help='Follow symbolic links when uploading from local file system.')
        c.argument('cap_mbps', arg_group='Additional Flags', help="Caps the transfer rate, in megabits per second. "
                   "Moment-by-moment throughput might vary slightly from the cap. "
                   "If this option is set to zero, or it is omitted, the throughput isn't capped. ")
        c.positional('extra_options', nargs='*', is_experimental=True, default=[],
                     help="Other options which will be passed through to azcopy as it is. "
                          "Please put all the extra options after a `--`")

    with self.argument_context('storage blob copy') as c:
        for item in ['destination', 'source']:
            c.argument('{}_if_modified_since'.format(item), arg_group='Pre-condition', arg_type=if_modified_since_type)
            c.argument('{}_if_unmodified_since'.format(item), arg_group='Pre-condition',
                       arg_type=if_unmodified_since_type)
            c.argument('{}_if_match'.format(item), arg_group='Pre-condition')
            c.argument('{}_if_none_match'.format(item), arg_group='Pre-condition')
        c.argument('container_name', container_name_type, options_list=('--destination-container', '-c'))
        c.argument('blob_name', blob_name_type, options_list=('--destination-blob', '-b'),
                   help='Name of the destination blob. If the exists, it will be overwritten.')
        c.argument('source_lease_id', arg_group='Copy Source')

    with self.argument_context('storage blob copy start', resource_type=ResourceType.DATA_STORAGE_BLOB) as c:
        from ._validators import validate_source_url

        c.register_blob_arguments()
        c.register_precondition_options()
        c.register_precondition_options(prefix='source_')
        c.register_source_uri_arguments(validator=validate_source_url)

        c.ignore('incremental_copy')
        c.argument('if_match', options_list=['--destination-if-match'])
        c.argument('if_modified_since', options_list=['--destination-if-modified-since'])
        c.argument('if_none_match', options_list=['--destination-if-none-match'])
        c.argument('if_unmodified_since', options_list=['--destination-if-unmodified-since'])
        c.argument('if_tags_match_condition', options_list=['--destination-tags-condition'])

        c.argument('blob_name', options_list=['--destination-blob', '-b'], required=True,
                   help='Name of the destination blob. If the exists, it will be overwritten.')
        c.argument('container_name', options_list=['--destination-container', '-c'], required=True,
                   help='The container name.')
        c.extra('destination_lease', options_list='--destination-lease-id',
                help='The lease ID specified for this header must match the lease ID of the estination blob. '
                'If the request does not include the lease ID or it is not valid, the operation fails with status '
                'code 412 (Precondition Failed).')
        c.extra('source_lease', options_list='--source-lease-id', arg_group='Copy Source',
                help='Specify this to perform the Copy Blob operation only if the lease ID given matches the '
                'active lease ID of the source blob.')
        c.extra('rehydrate_priority', rehydrate_priority_type)
        c.extra('requires_sync', arg_type=get_three_state_flag(),
                help='Enforce that the service will not return a response until the copy is complete.')
        c.extra('tier', tier_type)
        c.extra('tags', tags_type)

    with self.argument_context('storage blob copy start-batch', arg_group='Copy Source') as c:
        from azure.cli.command_modules.storage._validators import get_source_file_or_blob_service_client

        c.argument('source_client', ignore_type, validator=get_source_file_or_blob_service_client)

        c.extra('source_account_name')
        c.extra('source_account_key')
        c.extra('source_uri')
        c.argument('source_sas')
        c.argument('source_container')
        c.argument('source_share')

    with self.argument_context('storage blob incremental-copy start') as c:
        from azure.cli.command_modules.storage._validators import process_blob_source_uri

        c.register_source_uri_arguments(validator=process_blob_source_uri, blob_only=True)
        c.argument('destination_if_modified_since', arg_group='Pre-condition', arg_type=if_modified_since_type)
        c.argument('destination_if_unmodified_since', arg_group='Pre-condition', arg_type=if_unmodified_since_type)
        c.argument('destination_if_match', arg_group='Pre-condition')
        c.argument('destination_if_none_match', arg_group='Pre-condition')
        c.argument('container_name', container_name_type, options_list=('--destination-container', '-c'))
        c.argument('blob_name', blob_name_type, options_list=('--destination-blob', '-b'),
                   help='Name of the destination blob. If the exists, it will be overwritten.')
        c.argument('source_lease_id', arg_group='Copy Source')

    with self.argument_context('storage blob query') as c:
        from ._validators import validate_text_configuration
        c.register_blob_arguments()
        c.register_precondition_options()
        line_separator = CLIArgumentType(help="The string used to separate records.", default='\n')
        column_separator = CLIArgumentType(help="The string used to separate columns.", default=',')
        quote_char = CLIArgumentType(help="The string used to quote a specific field.", default='"')
        record_separator = CLIArgumentType(help="The string used to separate records.", default='\n')
        escape_char = CLIArgumentType(help="The string used as an escape character. Default to empty.", default="")
        has_header = CLIArgumentType(
            arg_type=get_three_state_flag(),
            help="Whether the blob data includes headers in the first line. "
            "The default value is False, meaning that the data will be returned inclusive of the first line. "
            "If set to True, the data will be returned exclusive of the first line.", default=False)
        c.extra('lease', options_list='--lease-id',
                help='Required if the blob has an active lease.')
        c.argument('query_expression', help='The query expression in SQL. The maximum size of the query expression '
                   'is 256KiB. For more information about the expression syntax, please see '
                   'https://docs.microsoft.com/azure/storage/blobs/query-acceleration-sql-reference')
        c.extra('input_format', arg_type=get_enum_type(['csv', 'json']), validator=validate_text_configuration,
                help='Serialization type of the data currently stored in the blob. '
                'The default is to treat the blob data as CSV data formatted in the default dialect.'
                'The blob data will be reformatted according to that profile when blob format is specified. '
                'If you choose `json`, please specify `Output Json Text Configuration Arguments` accordingly; '
                'If you choose `csv`, please specify `Output Delimited Text Configuration Arguments`.')
        c.extra('output_format', arg_type=get_enum_type(['csv', 'json']),
                help='Output serialization type for the data stream. '
                'By default the data will be returned as it is represented in the blob. '
                'By providing an output format, the blob data will be reformatted according to that profile. '
                'If you choose `json`, please specify `Output Json Text Configuration Arguments` accordingly; '
                'If you choose `csv`, please specify `Output Delimited Text Configuration Arguments`.')
        c.extra('in_line_separator',
                arg_group='Input Json Text Configuration',
                arg_type=line_separator)
        c.extra('in_column_separator', arg_group='Input Delimited Text Configuration',
                arg_type=column_separator)
        c.extra('in_quote_char', arg_group='Input Delimited Text Configuration',
                arg_type=quote_char)
        c.extra('in_record_separator', arg_group='Input Delimited Text Configuration',
                arg_type=record_separator)
        c.extra('in_escape_char', arg_group='Input Delimited Text Configuration',
                arg_type=escape_char)
        c.extra('in_has_header', arg_group='Input Delimited Text Configuration',
                arg_type=has_header)
        c.extra('out_line_separator',
                arg_group='Output Json Text Configuration',
                arg_type=line_separator)
        c.extra('out_column_separator', arg_group='Output Delimited Text Configuration',
                arg_type=column_separator)
        c.extra('out_quote_char', arg_group='Output Delimited Text Configuration',
                arg_type=quote_char)
        c.extra('out_record_separator', arg_group='Output Delimited Text Configuration',
                arg_type=record_separator)
        c.extra('out_escape_char', arg_group='Output Delimited Text Configuration',
                arg_type=escape_char)
        c.extra('out_has_header', arg_group='Output Delimited Text Configuration',
                arg_type=has_header)
        c.extra('result_file', help='Specify the file path to save result.')
        c.ignore('input_config')
        c.ignore('output_config')

    with self.argument_context('storage blob sync') as c:
        from .sdkutil import get_blob_sync_delete_destination_types
        c.extra('destination_container', options_list=['--container', '-c'], required=True,
                help='The sync destination container.')
        c.extra('destination_path', options_list=['--destination', '-d'],
                validator=validate_azcopy_upload_destination_url,
                help='The sync destination path.')
        c.argument('source', options_list=['--source', '-s'],
                   help='The source file path to sync from.')
        c.ignore('destination')
        c.argument('delete_destination', arg_type=get_enum_type(get_blob_sync_delete_destination_types()),
                   arg_group='Additional Flags', help='Defines whether to delete extra files from the destination that '
                   'are not present at the source. Could be set to true, false, or prompt. If set to prompt, the user '
                   'will be asked a question before scheduling files and blobs for deletion. ')
        c.argument('exclude_pattern', exclude_pattern_type)
        c.argument('include_pattern', include_pattern_type)
        c.argument('exclude_path', exclude_path_type)

    with self.argument_context('storage container') as c:
        t_public_access = self.get_sdk('_models#PublicAccess', resource_type=ResourceType.DATA_STORAGE_BLOB)
        c.argument('container_name', container_name_type, options_list=('--name', '-n'))
        c.argument('public_access', validator=validate_container_public_access,
                   arg_type=get_enum_type(t_public_access),
                   help='Specifies whether data in the container may be accessed publicly.')
    for scope in ['show', 'exists', 'show-permission', 'set-permission', 'metadata show', 'metadata update']:
        with self.argument_context('storage container {}'.format(scope)) as c:
            c.extra('container_name', container_name_type, options_list=('--name', '-n'), required=True)
            c.extra('timeout', timeout_type)

    for scope in ['show', 'show-permission', 'set-permission', 'metadata show', 'metadata update']:
        with self.argument_context('storage container {}'.format(scope)) as c:
            c.extra('lease', options_list='--lease-id',
                    help="If specified, only succeed if the container's lease is active and matches this ID.")

    for scope in ['set-permission', 'metadata update']:
        with self.argument_context(f'storage container {scope}') as c:
            c.extra('if_modified_since', arg_group='Precondition', type=get_datetime_type(False),
                    help="Commence only if modified since supplied UTC datetime (Y-m-d'T'H:M'Z').")
            c.extra('if_unmodified_since', arg_group='Precondition', type=get_datetime_type(False),
                    help="Commence only if unmodified since supplied UTC datetime (Y-m-d'T'H:M'Z').")

    with self.argument_context('storage container create') as c:
        from ._validators import validate_encryption_scope_parameter
        c.argument('resource_group_name', required=False, validator=None, deprecate_info=c.deprecate())
        c.argument('container_name', container_name_type, options_list=('--name', '-n'), completer=None)
        c.argument('fail_on_exist', help='Throw an exception if the container already exists.')
        c.argument('account_name', help='Storage account name. Related environment variable: AZURE_STORAGE_ACCOUNT.')
        c.argument('default_encryption_scope', options_list=['--default-encryption-scope', '-d'],
                   arg_group='Encryption Policy', is_preview=True, validator=validate_encryption_scope_parameter,
                   help='Default the container to use specified encryption scope for all writes.')
        c.argument('prevent_encryption_scope_override', options_list=['--prevent-encryption-scope-override', '-p'],
                   arg_type=get_three_state_flag(), arg_group='Encryption Policy', is_preview=True,
                   help='Block override of encryption scope from the container default.')

    with self.argument_context('storage container delete') as c:
        c.argument('fail_not_exist', help='Throw an exception if the container does not exist.')
        c.argument('bypass_immutability_policy', action='store_true', help='Bypasses upcoming service behavior that '
                   'will block a container from being deleted if it has a immutability-policy. Specifying this will '
                   'ignore arguments aside from those used to identify the container ("--name", "--account-name").')
        c.argument('lease_id', help="If specified, delete_container only succeeds if the container's lease is active "
                                    "and matches this ID. Required if the container has an active lease.")
        c.ignore('processed_resource_group')
        c.ignore('processed_account_name')
        c.ignore('mgmt_client')

    for item in ['create', 'extend']:
        with self.argument_context('storage container immutability-policy {}'.format(item)) as c:
            c.argument('account_name',
                       help='Storage account name. Related environment variable: AZURE_STORAGE_ACCOUNT.')
            c.argument('if_match', help="An ETag value, or the wildcard character (*). Specify this header to perform "
                                        "the operation only if the resource's ETag matches the value specified.")
            c.extra('allow_protected_append_writes', options_list=['--allow-protected-append-writes', '-w'],
                    arg_type=get_three_state_flag(), help='This property can only be changed for unlocked time-based '
                                                          'retention policies. When enabled, new blocks can be '
                                                          'written to an append blob while maintaining immutability '
                                                          'protection and compliance. Only new blocks can be added '
                                                          'and any existing blocks cannot be modified or deleted. '
                                                          'This property cannot be changed with '
                                                          'ExtendImmutabilityPolicy API.')
            c.extra('allow_protected_append_writes_all', options_list=['--allow-protected-append-writes-all',
                                                                       '--w-all'],
                    arg_type=get_three_state_flag(), help="This property can only be changed for unlocked time-based "
                                                          "retention policies. When enabled, new blocks can be written "
                                                          "to both 'Append and Block Blobs' while maintaining "
                                                          "immutability protection and compliance. "
                                                          "Only new blocks can be added and any existing blocks cannot "
                                                          "be modified or deleted. This property cannot be changed with"
                                                          " ExtendImmutabilityPolicy API. The "
                                                          "'allowProtectedAppendWrites' and "
                                                          "'allowProtectedAppendWritesAll' properties are mutually "
                                                          "exclusive.")
            c.extra('period', type=int, help='The immutability period for the blobs in the container since the policy '
                                             'creation, in days.')
            c.ignore('parameters')

    with self.argument_context('storage container list') as c:
        c.argument('num_results', arg_type=num_results_type)

    with self.argument_context('storage container set-permission') as c:
        c.ignore('signed_identifiers')

    with self.argument_context('storage container') as c:
        c.argument('account_name', completer=get_resource_name_completion_list('Microsoft.Storage/storageAccounts'))
        c.argument('resource_group_name', required=False, validator=process_resource_group)

    with self.argument_context('storage container immutability-policy') as c:
        c.argument('immutability_period_since_creation_in_days', options_list='--period')
        c.argument('container_name', container_name_type)

    with self.argument_context('storage container legal-hold') as c:
        c.argument('container_name', container_name_type)
        c.argument('account_name',
                   help='Storage account name. Related environment variable: AZURE_STORAGE_ACCOUNT.')
        c.argument('tags', nargs='+',
                   help='Space-separated tags. Each tag should be 3 to 23 alphanumeric characters and is normalized '
                        'to lower case')
    for item in ['set', 'clear']:
        with self.argument_context(f'storage container legal-hold {item}') as c:
            c.extra('allow_protected_append_writes_all', options_list=['--allow-protected-append-writes-all',
                                                                       '--w-all'],
                    arg_type=get_three_state_flag(),
                    help="When enabled, new blocks can be written to both Append and Block Blobs while maintaining "
                         "legal hold protection and compliance. Only new blocks can be added and any existing blocks "
                         "cannot be modified or deleted.")

    with self.argument_context('storage container policy') as c:
        from .completers import get_storage_acl_name_completion_list
        t_container_permissions = self.get_sdk('blob.models#ContainerPermissions')

        c.argument('container_name', container_name_type)
        c.argument('policy_name', options_list=('--name', '-n'), help='The stored access policy name.',
                   completer=get_storage_acl_name_completion_list(t_base_blob_service, 'container_name',
                                                                  'get_container_acl'))
        help_str = 'Allowed values: {}. Can be combined'.format(get_permission_help_string(t_container_permissions))
        c.argument('permission', options_list='--permissions', help=help_str,
                   validator=get_permission_validator(t_container_permissions))

        c.argument('start', type=get_datetime_type(True),
                   help='start UTC datetime (Y-m-d\'T\'H:M:S\'Z\'). Defaults to time of request.')
        c.argument('expiry', type=get_datetime_type(True), help='expiration UTC datetime in (Y-m-d\'T\'H:M:S\'Z\')')

    for item in ['create', 'delete', 'list', 'show', 'update']:
        with self.argument_context('storage container policy {}'.format(item)) as c:
            c.extra('lease_id', options_list='--lease-id', help='The container lease ID.')

    with self.argument_context('storage container generate-sas', resource_type=ResourceType.DATA_STORAGE_BLOB) as c:
        from .completers import get_storage_acl_name_completion_list
        t_container_permissions = self.get_sdk('_models#ContainerSasPermissions',
                                               resource_type=ResourceType.DATA_STORAGE_BLOB)
        c.register_sas_arguments()
        c.argument('id', options_list='--policy-name', validator=validate_policy,
                   help='The name of a stored access policy within the container\'s ACL.',
                   completer=get_storage_acl_name_completion_list(t_base_blob_service, 'container_name',
                                                                  'get_container_acl'))
        c.argument('permission', options_list='--permissions',
                   help=sas_help.format(get_permission_help_string(t_container_permissions)),
                   validator=get_permission_validator(t_container_permissions))
        c.argument('cache_control', help='Response header value for Cache-Control when resource is accessed '
                                         'using this shared access signature.')
        c.argument('content_disposition', help='Response header value for Content-Disposition when resource is '
                                               'accessed using this shared access signature.')
        c.argument('content_encoding', help='Response header value for Content-Encoding when resource is accessed '
                                            'using this shared access signature.')
        c.argument('content_language', help='Response header value for Content-Language when resource is accessed '
                                            'using this shared access signature.')
        c.argument('content_type', help='Response header value for Content-Type when resource is accessed '
                                        'using this shared access signature.')
        c.argument('as_user', min_api='2018-11-09', action='store_true',
                   validator=as_user_validator,
                   help="Indicates that this command return the SAS signed with the user delegation key. "
                        "The expiry parameter and '--auth-mode login' are required if this argument is specified. ")
        c.extra('encryption_scope', help='A predefined encryption scope used to encrypt the data on the service.')
        c.ignore('sas_token')

    for cmd in ['acquire', 'renew', 'break', 'change', 'release']:
        with self.argument_context(f'storage container lease {cmd}') as c:
            c.register_precondition_options()
            c.register_container_arguments()
            c.argument('container_name', required=True, options_list=['--container-name', '-c'])

    with self.argument_context('storage container lease acquire') as c:
        c.argument('lease_duration',
                   help='Specify the duration of the lease, in seconds, or negative one (-1) for a lease that never'
                        ' expires. A non-infinite lease can be between 15 and 60 seconds. A lease duration cannot '
                        'be changed using renew or change. Default is -1 (infinite lease)', type=int)
        c.extra('lease_id', options_list='--proposed-lease-id',
                help='Proposed lease ID, in a GUID string format. The Blob service returns 400 (Invalid request) '
                     'if the proposed lease ID is not in the correct format.')

    for cmd in ['renew', 'change', 'release']:
        with self.argument_context(f'storage container lease {cmd}') as c:
            c.extra('lease_id', help='Lease ID for active lease.', required=True)

    with self.argument_context('storage container lease break') as c:
        c.extra('lease_break_period', type=int, help='This is the proposed duration of seconds that the lease should '
                                                     'continue before it is broken, between 0 and 60 seconds. '
                                                     'This break period is only used if it is shorter than the time '
                                                     'remaining on the lease. If longer, the time remaining on the '
                                                     'lease is used. A new lease will not be available before the '
                                                     'break period has expired, but the lease may be held for longer '
                                                     'than the break period. If this header does not appear with a '
                                                     'break operation, a fixed-duration lease breaks after the '
                                                     'remaining lease period elapses, and an infinite lease breaks '
                                                     'immediately.')

    with self.argument_context('storage container lease change') as c:
        c.extra('proposed_lease_id', help='Proposed lease ID, in a GUID string format. The Blob service returns 400'
                                          ' (Invalid request) if the proposed lease ID is not in the correct format.',
                required=True)

    with self.argument_context('storage container list', resource_type=ResourceType.DATA_STORAGE_BLOB) as c:
        c.extra('timeout', timeout_type)
        c.argument('marker', arg_type=marker_type)
        c.argument('num_results', arg_type=num_results_type)
        c.argument('prefix',
                   help='Filter the results to return only blobs whose name begins with the specified prefix.')
        c.argument('include_metadata', arg_type=get_three_state_flag(),
                   help='Specify that container metadata to be returned in the response.')
        c.argument('show_next_marker', action='store_true', is_preview=True,
                   help='Show nextMarker in result when specified.')
        c.argument('include_deleted', arg_type=get_three_state_flag(), min_api='2020-02-10',
                   help='Specify that deleted containers to be returned in the response. This is for container restore '
                   'enabled account. The default value is `False`')

    with self.argument_context('storage container restore') as c:
        c.argument('deleted_container_name', options_list=['--name', '-n'],
                   help='Specify the name of the deleted container to restore.')
        c.argument('deleted_container_version', options_list=['--deleted-version'],
                   help='Specify the version of the deleted container to restore.')
        c.extra('timeout', timeout_type)

    with self.argument_context('storage container-rm', resource_type=ResourceType.MGMT_STORAGE) as c:
        from .sdkutil import get_container_access_type_names
        c.argument('container_name', container_name_type, options_list=('--name', '-n'), id_part='child_name_2')
        c.argument('account_name', storage_account_type)
        c.argument('resource_group_name', required=False)
        c.argument('public_access', validator=validate_container_public_access,
                   arg_type=get_enum_type(get_container_access_type_names()),
                   help='Specify whether data in the container may be accessed publicly.')
        c.ignore('filter', 'maxpagesize')

    with self.argument_context('storage container-rm create', resource_type=ResourceType.MGMT_STORAGE) as c:
        c.argument('fail_on_exist', help='Throw an exception if the container already exists.')
        c.argument('enable_vlw', arg_type=get_three_state_flag(), min_api='2021-01-01', is_preview=True,
                   help='The object level immutability property of the container. The property is immutable and can '
                   'only be set to true at the container creation time. Existing containers must undergo a migration '
                   'process.')

    for item in ['create', 'update']:
        with self.argument_context('storage container-rm {}'.format(item),
                                   resource_type=ResourceType.MGMT_STORAGE) as c:
            from ._validators import validate_container_nfsv3_squash
            t_root_squash = self.get_models('RootSquashType', resource_type=ResourceType.MGMT_STORAGE)
            c.argument('default_encryption_scope', options_list=['--default-encryption-scope', '-d'],
                       arg_group='Encryption Policy', min_api='2019-06-01',
                       help='Default the container to use specified encryption scope for all writes.')
            c.argument('deny_encryption_scope_override',
                       options_list=['--deny-encryption-scope-override', '--deny-override'],
                       arg_type=get_three_state_flag(), arg_group='Encryption Policy', min_api='2019-06-01',
                       help='Block override of encryption scope from the container default.')
            c.extra('root_squash', arg_type=get_enum_type(t_root_squash), min_api='2021-06-01',
                    help='Enable NFSv3 squash on blob container.', validator=validate_container_nfsv3_squash)
            c.ignore('enable_nfs_v3_root_squash')
            c.ignore('enable_nfs_v3_all_squash')

    with self.argument_context('storage container-rm list', resource_type=ResourceType.MGMT_STORAGE) as c:
        c.argument('account_name', storage_account_type, id_part=None)
        c.argument('include_deleted', action='store_true',
                   help='Include soft deleted containers when specified.')

    with self.argument_context('storage share') as c:
        c.argument('share_name', share_name_type, options_list=('--name', '-n'))

    with self.argument_context('storage share-rm', resource_type=ResourceType.MGMT_STORAGE) as c:
        c.argument('resource_group_name', required=False)
        c.argument('account_name', storage_account_type)
        c.argument('share_name', share_name_type, options_list=('--name', '-n'), id_part='child_name_2')
        c.argument('expand', default=None)
        c.argument('x_ms_snapshot', options_list=['--snapshot'], is_preview=True,
                   help='The DateTime value that specifies the share snapshot to retrieve.')
        c.ignore('filter', 'maxpagesize')

    with self.argument_context('storage share-rm delete', resource_type=ResourceType.MGMT_STORAGE) as c:
        c.argument('include', default='none')

    with self.argument_context('storage share-rm update', resource_type=ResourceType.MGMT_STORAGE) as c:
        c.ignore('x_ms_snapshot')

    for item in ['create', 'update', 'snapshot']:
        with self.argument_context('storage share-rm {}'.format(item), resource_type=ResourceType.MGMT_STORAGE) as c:
            t_enabled_protocols, t_root_squash, t_access_tier = \
                self.get_models('EnabledProtocols', 'RootSquashType', 'ShareAccessTier',
                                resource_type=ResourceType.MGMT_STORAGE)
            c.argument('share_quota', type=int, options_list=['--quota', '-q'],
                       help='The maximum size of the share in gigabytes. Must be greater than 0, and less than or '
                            'equal to 5TB (5120). For Large File Shares, the maximum size is 102400.')
            c.argument('metadata', nargs='+',
                       help='Metadata in space-separated key=value pairs that is associated with the share. '
                            'This overwrites any existing metadata',
                       validator=validate_metadata)
            c.argument('enabled_protocols', arg_type=get_enum_type(t_enabled_protocols),
                       min_api='2019-06-01', help='Immutable property for file shares protocol. NFS protocol will be '
                       'only available for premium file shares (file shares in the FileStorage account type).')
            c.argument('root_squash', arg_type=get_enum_type(t_root_squash),
                       min_api='2019-06-01', help='Reduction of the access rights for the remote superuser.')
            c.argument('access_tier', arg_type=get_enum_type(t_access_tier), min_api='2019-06-01',
                       help='Access tier for specific share. GpV2 account can choose between TransactionOptimized '
                       '(default), Hot, and Cool. FileStorage account can choose Premium.')

    with self.argument_context('storage share-rm list', resource_type=ResourceType.MGMT_STORAGE) as c:
        c.argument('account_name', storage_account_type, id_part=None)
        c.argument('include_deleted', action='store_true',
                   help='Include soft deleted file shares when specified.')
        c.argument('include_snapshot', action='store_true',
                   help='Include file share snapshots when specified.')

    with self.argument_context('storage share-rm restore', resource_type=ResourceType.MGMT_STORAGE) as c:
        c.argument('deleted_version',
                   help='Identify the version of the deleted share that will be restored.')
        c.argument('share_name',
                   help='The file share name. Identify the name of the deleted share that will be restored.')
        c.argument('restored_name',
                   help='A new file share name to be restored. If not specified, deleted share name will be used.')

    with self.argument_context('storage share create') as c:
        c.extra('share_name', share_name_type, options_list=('--name', '-n'), required=True)
        c.argument('fail_on_exist', help='Specify whether to throw an exception when the share exists. False by '
                                         'default.')
        c.argument('quota', type=int, help='Specifies the maximum size of the share, in gigabytes. Must be greater '
                                           'than 0, and less than or equal to 5TB (5120).')

    with self.argument_context('storage share url') as c:
        c.argument('unc', action='store_true', help='Output UNC network path.')
        c.argument('protocol', arg_type=get_enum_type(['http', 'https'], 'https'), help='Protocol to use.')

    with self.argument_context('storage share list') as c:
        c.argument('num_results', arg_type=num_results_type)
        c.extra('marker', help='An opaque continuation token. This value can be retrieved from the next_marker field '
                               'of a previous generator object if num_results was specified and that generator has '
                               'finished enumerating results. If specified, this generator will begin returning '
                               'results from the point where the previous generator stopped.')
        c.extra('timeout', timeout_type)
        c.argument('include_snapshots', help='Specifies that share snapshots be returned in the response.')
        c.argument('include_metadata', help='Specifies that share metadata be returned in the response.')
        c.extra('prefix',
                help='Filter the results to return only blobs whose name begins with the specified prefix.')
        c.ignore('name_starts_with')

    with self.argument_context('storage share exists') as c:
        c.extra('share_name', share_name_type, options_list=('--name', '-n'), required=True)
        c.extra('snapshot', options_list=['--snapshot'],
                help='A string that represents the snapshot version, if applicable.')
        c.ignore('directory_name', 'file_name')
        c.extra('timeout', timeout_type)

    for item in ['show', 'metadata show']:
        with self.argument_context('storage share {}'.format(item)) as c:
            c.extra('share_name', share_name_type, options_list=('--name', '-n'), required=True)
            c.extra('snapshot', options_list=['--snapshot'],
                    help='A string that represents the snapshot version, if applicable.')
            c.extra('timeout', timeout_type)

    for item in ['stats', 'metadata update']:
        with self.argument_context('storage share {}'.format(item)) as c:
            c.extra('share_name', share_name_type, options_list=('--name', '-n'), required=True)
            c.extra('timeout', timeout_type)

    with self.argument_context('storage share policy') as c:
        from .completers import get_storage_acl_name_completion_list

        t_file_svc = self.get_sdk('file#FileService')
        t_share_permissions = self.get_sdk('file.models#SharePermissions')

        c.argument('container_name', share_name_type)
        c.argument('policy_name', options_list=('--name', '-n'), help='The stored access policy name.',
                   completer=get_storage_acl_name_completion_list(t_file_svc, 'container_name', 'get_share_acl'))

        help_str = 'Allowed values: {}. Can be combined'.format(get_permission_help_string(t_share_permissions))
        c.argument('permission', options_list='--permissions', help=help_str,
                   validator=get_permission_validator(t_share_permissions))

        c.argument('start', type=get_datetime_type(True),
                   help='start UTC datetime (Y-m-d\'T\'H:M:S\'Z\'). Defaults to time of request.')
        c.argument('expiry', type=get_datetime_type(True), help='expiration UTC datetime in (Y-m-d\'T\'H:M:S\'Z\')')

    with self.argument_context('storage share delete') as c:
        from .sdkutil import get_delete_file_snapshot_type_names
        c.extra('share_name', share_name_type, options_list=('--name', '-n'), required=True)
        c.argument('delete_snapshots', arg_type=get_enum_type(get_delete_file_snapshot_type_names()),
                   help='Specify the deletion strategy when the share has snapshots.')
        c.argument('fail_not_exist', help="Specify whether to throw an exception when the share doesn't exists. False "
                                          "by default.")
        c.extra('snapshot', options_list=['--snapshot'],
                help='A string that represents the snapshot version, if applicable.Specify this argument to delete a '
                     'specific snapshot only. delete_snapshots must be None if this is specified.')
        c.extra('timeout', timeout_type)

    with self.argument_context('storage share generate-sas') as c:
        from .completers import get_storage_acl_name_completion_list

        t_share_permissions = self.get_sdk('_models#ShareSasPermissions',
                                           resource_type=ResourceType.DATA_STORAGE_FILESHARE)
        c.register_sas_arguments()
        c.extra('share_name', share_name_type, options_list=('--name', '-n'), required=True)
        c.argument('cache_control', help='Response header value for Cache-Control when resource is accessed using this '
                                         'shared access signature.')
        c.argument('content_disposition', help='Response header value for Content-Disposition when resource is '
                                               'accessed using this shared access signature.')
        c.argument('content_encoding', help='Response header value for Content-Encoding when resource is accessed '
                                            'using this shared access signature.')
        c.argument('content_language', help='Response header value for Content-Language when resource is accessed '
                                            'using this shared access signature.')
        c.argument('content_type', help='Response header value for Content-Type when resource is accessed using this '
                                        'shared access signature.')
        c.argument('policy_id', options_list='--policy-name',
                   help='The name of a stored access policy within the share\'s ACL.',
                   completer=get_storage_acl_name_completion_list(t_share_service, 'share_name',
                                                                  'get_share_access_policy'))
        c.argument('permission', options_list='--permissions',
                   help=sas_help.format(get_permission_help_string(t_share_permissions)),
                   validator=get_permission_validator(t_share_permissions))
        c.ignore('sas_token')

    with self.argument_context('storage share update') as c:
        c.extra('share_name', share_name_type, options_list=('--name', '-n'), required=True)
        c.argument('quota', help='Specifies the maximum size of the share, in gigabytes. Must be greater than 0, and '
                                 'less than or equal to 5 TB (5120 GB).')
        c.extra('timeout', timeout_type)

    with self.argument_context('storage share list-handle') as c:
        c.register_path_argument(default_file_param="", fileshare=True)
        c.extra('share_name', share_name_type, options_list=('--name', '-n'), required=True)
        c.extra('marker', help='An opaque continuation token. This value can be retrieved from the '
                               'next_marker field of a previous generator object if max_results was '
                               'specified and that generator has finished enumerating results. If '
                               'specified, this generator will begin returning results from the point '
                               'where the previous generator stopped.')
        c.extra('num_results', options_list='--max-results', type=int,
                help='Specifies the maximum number of handles taken on files and/or directories '
                     'to return. If the request does not specify max_results or specifies a '
                     'value greater than 5,000, the server will return up to 5,000 items. '
                     'Setting max_results to a value less than or equal to zero results in '
                     'error response code 400 (Bad Request).')
        c.extra('recursive', arg_type=get_three_state_flag(),
                help='Boolean that specifies if operation should apply to the directory specified in the URI, '
                     'its files, with its subdirectories and their files.')
        c.extra('snapshot', help="A string that represents the snapshot version, if applicable.")
        c.extra('timeout', help='Request timeout in seconds. Applies to each call to the service.', type=int)

    with self.argument_context('storage share close-handle') as c:
        c.register_path_argument(default_file_param="", fileshare=True)
        c.extra('share_name', share_name_type, options_list=('--name', '-n'), required=True)
        c.extra('recursive', arg_type=get_three_state_flag(),
                help="Boolean that specifies if operation should apply to the directory specified in the URI, its "
                     "files, with its subdirectories and their files.")
        c.extra('close_all', arg_type=get_three_state_flag(), validator=validate_share_close_handle,
                help="Whether or not to close all the file handles. Specify close-all or a specific handle-id.")
        c.extra('handle', options_list='--handle-id',
                help="Specifies handle ID opened on the file or directory to be closed. "
                     "Astrix (‘*’) is a wildcard that specifies all handles.")
        c.extra('snapshot', help="A string that represents the snapshot version, if applicable.")
        c.extra('timeout', help='Request timeout in seconds. Applies to each call to the service.', type=int)

    for scope in ['create', 'delete', 'show', 'exists', 'metadata show', 'metadata update']:
        with self.argument_context(f'storage directory {scope}') as c:
            c.extra('share_name', share_name_type, required=True)
            c.extra('snapshot', help="A string that represents the snapshot version, if applicable.")
            c.extra('directory_path', directory_type, options_list=('--name', '-n'), required=True)
            c.extra('timeout', help='Request timeout in seconds. Applies to each call to the service.', type=int)

    with self.argument_context('storage directory list') as c:
        c.extra('share_name', share_name_type, required=True)
        c.extra('directory_path', directory_type, options_list=('--name', '-n'))
        c.argument('exclude_extended_info',
                   help='Specify to exclude "timestamps", "Etag", "Attributes", "PermissionKey" info from response')
        c.extra('timeout', help='Request timeout in seconds. Applies to each call to the service.', type=int)

    with self.argument_context('storage directory create') as c:
        c.argument('fail_on_exist', help='Throw an exception if the directory already exists.')

    with self.argument_context('storage directory delete') as c:
        c.argument('fail_not_exist', help='Throw an exception if the directory does not exist.')

    with self.argument_context('storage directory metadata update') as c:
        c.argument('metadata', required=False)

    with self.argument_context('storage file') as c:
        c.argument('file_name', file_name_type, options_list=('--name', '-n'))
        c.argument('directory_name', directory_type, required=False)

    with self.argument_context('storage file copy') as c:
        c.argument('share_name', share_name_type, options_list=('--destination-share', '-s'),
                   help='Name of the destination share. The share must exist.')

    with self.argument_context('storage file copy cancel') as c:
        c.register_path_argument(options_list=('--destination-path', '-p'))

    with self.argument_context('storage file delete') as c:
        c.extra('file_path', type=file_type, required=True, options_list=('--path', '-p'),
                help='The path to the file within the file share.')
        c.extra('share_name', share_name_type, required=True)
        c.extra('timeout', help='Request timeout in seconds. Applies to each call to the service.', type=int)

    with self.argument_context('storage file download') as c:
        c.register_path_argument()
        c.argument('file_path', options_list=('--dest',), type=file_type, required=False,
                   help='Path of the file to write to. The source filename will be used if not specified.',
                   validator=process_file_download_namespace, completer=FilesCompleter())
        c.argument('path', validator=None)  # validator called manually from process_file_download_namespace
        c.extra('no_progress', progress_type)
        c.argument('max_connections', type=int)
        c.argument('start_range', type=int)
        c.argument('end_range', type=int)

    with self.argument_context('storage file exists') as c:
        c.register_path_argument()

    with self.argument_context('storage file generate-sas') as c:
        from .completers import get_storage_acl_name_completion_list

        c.register_path_argument()
        c.register_sas_arguments()

        t_file_svc = self.get_sdk('file.fileservice#FileService')
        t_file_permissions = self.get_sdk('file.models#FilePermissions')
        c.argument('id', options_list='--policy-name',
                   help='The name of a stored access policy within the container\'s ACL.',
                   completer=get_storage_acl_name_completion_list(t_file_svc, 'container_name', 'get_container_acl'))
        c.argument('permission', options_list='--permissions',
                   help=sas_help.format(get_permission_help_string(t_file_permissions)),
                   validator=get_permission_validator(t_file_permissions))
        c.ignore('sas_token')

    with self.argument_context('storage file list') as c:
        from .completers import dir_path_completer
        c.extra('share_name', share_name_type, required=True)
        c.extra('snapshot', help="A string that represents the snapshot version, if applicable.")
        c.argument('directory_name', options_list=('--path', '-p'), help='The directory path within the file share.',
                   completer=dir_path_completer)
        c.argument('num_results', arg_type=num_results_type)
        c.argument('marker', arg_type=marker_type)
        c.argument('exclude_extended_info',
                   help='Specify to exclude "timestamps", "Etag", "Attributes", "PermissionKey" info from response')

    with self.argument_context('storage file metadata show') as c:
        c.register_path_argument()

    with self.argument_context('storage file metadata update') as c:
        c.register_path_argument()

    with self.argument_context('storage file resize') as c:
        c.extra('file_path', type=file_type, required=True, options_list=('--path', '-p'),
                help='The path to the file within the file share.')
        c.extra('share_name', share_name_type, required=True)
        c.extra('timeout', help='Request timeout in seconds. Applies to each call to the service.', type=int)
        c.argument('content_length', options_list='--size', type=int)

    with self.argument_context('storage file show') as c:
        c.register_path_argument()

    with self.argument_context('storage file update') as c:
        t_file_content_settings = self.get_sdk('file.models#ContentSettings')

        c.register_path_argument()
        c.register_content_settings_argument(t_file_content_settings, update=True)

    with self.argument_context('storage file upload') as c:
        t_file_content_settings = self.get_sdk('file.models#ContentSettings')

        c.register_path_argument(default_file_param='local_file_path')
        c.register_content_settings_argument(t_file_content_settings, update=False, guess_from_file='local_file_path')
        c.argument('local_file_path', options_list='--source', type=file_type, completer=FilesCompleter())
        c.extra('no_progress', progress_type)
        c.argument('max_connections', type=int)

    with self.argument_context('storage file url') as c:
        c.register_path_argument()
        c.argument('protocol', arg_type=get_enum_type(['http', 'https'], 'https'), help='Protocol to use.')

    with self.argument_context('storage file upload-batch') as c:
        from ._validators import process_file_upload_batch_parameters
        c.argument('source', options_list=('--source', '-s'), validator=process_file_upload_batch_parameters)
        c.argument('destination', options_list=('--destination', '-d'))
        c.argument('max_connections', arg_group='Download Control', type=int)
        c.argument('validate_content', action='store_true', min_api='2016-05-31')
        c.register_content_settings_argument(t_file_content_settings, update=False, arg_group='Content Settings')
        c.extra('no_progress', progress_type)

    with self.argument_context('storage file download-batch') as c:
        from ._validators import process_file_download_batch_parameters
        c.argument('source', options_list=('--source', '-s'), validator=process_file_download_batch_parameters)
        c.argument('destination', options_list=('--destination', '-d'))
        c.argument('max_connections', arg_group='Download Control', type=int)
        c.argument('validate_content', action='store_true', min_api='2016-05-31')
        c.extra('no_progress', progress_type)

    with self.argument_context('storage file delete-batch') as c:
        from ._validators import process_file_batch_source_parameters
        c.argument('source', options_list=('--source', '-s'), validator=process_file_batch_source_parameters)

    with self.argument_context('storage file copy start') as c:
        from azure.cli.command_modules.storage._validators import validate_source_uri

        c.register_path_argument(options_list=('--destination-path', '-p'))
        c.register_source_uri_arguments(validator=validate_source_uri)
        c.extra('file_snapshot', default=None, arg_group='Copy Source',
                help='The file snapshot for the source storage account.')

    with self.argument_context('storage file copy start-batch', arg_group='Copy Source') as c:
        from ._validators import get_source_file_or_blob_service_client
        c.argument('source_client', ignore_type, validator=get_source_file_or_blob_service_client)
        c.extra('source_account_name')
        c.extra('source_account_key')
        c.extra('source_uri')
        c.argument('source_sas')
        c.argument('source_container')
        c.argument('source_share')

    with self.argument_context('storage cors list') as c:
        c.extra('services', validator=get_char_options_validator('bfqt', 'services'), default='bfqt',
                options_list='--services', required=False)

    with self.argument_context('storage cors add') as c:
        t_cors_rule_allowed_methods = self.get_models('CorsRuleAllowedMethodsItem',
                                                      resource_type=ResourceType.MGMT_STORAGE)
        c.extra('services', validator=get_char_options_validator('bfqt', 'services'), required=True,
                options_list='--services')
        c.argument('max_age')
        c.argument('origins', nargs='+')
        c.argument('methods', nargs='+',
                   arg_type=get_enum_type(t_cors_rule_allowed_methods))
        c.argument('allowed_headers', nargs='+')
        c.argument('exposed_headers', nargs='+')

    with self.argument_context('storage cors clear') as c:
        c.extra('services', validator=get_char_options_validator('bfqt', 'services'), required=True,
                options_list='--services')

    for item in ['stats', 'exists', 'metadata show', 'metadata update']:
        with self.argument_context('storage queue {}'.format(item)) as c:
            c.extra('timeout', help='Request timeout in seconds. Applies to each call to the service.', type=int)

    for item in ['exists', 'generate-sas', 'create', 'delete', 'metadata show', 'metadata update']:
        with self.argument_context('storage queue {}'.format(item)) as c:
            c.extra('queue_name', queue_name_type, options_list=('--name', '-n'), required=True)

    with self.argument_context('storage queue generate-sas') as c:
        from .completers import get_storage_acl_name_completion_list

        t_queue_permissions = self.get_sdk('_models#QueueSasPermissions', resource_type=ResourceType.DATA_STORAGE_QUEUE)

        c.register_sas_arguments()

        c.argument('policy_id', options_list='--policy-name',
                   help='The name of a stored access policy within the share\'s ACL.',
                   completer=get_storage_acl_name_completion_list(t_queue_service, 'container_name',
                                                                  'get_queue_access_policy'))
        c.argument('permission', options_list='--permissions',
                   help=sas_help.format(get_permission_help_string(t_queue_permissions)),
                   validator=get_permission_validator(t_queue_permissions))
        c.ignore('sas_token')

    with self.argument_context('storage queue list') as c:
        c.argument('include_metadata', help='Specify that queue metadata be returned in the response.')
        c.argument('marker', arg_type=marker_type)
        c.argument('num_results', arg_type=num_results_type)
        c.argument('prefix', help='Filter the results to return only queues whose names '
                                  'begin with the specified prefix.')
        c.argument('show_next_marker', action='store_true',
                   help='Show nextMarker in result when specified.')
        c.extra('timeout', help='Request timeout in seconds. Apply to each call to the service.', type=int)

    with self.argument_context('storage queue create') as c:
        c.argument('fail_on_exist', help='Specify whether to throw an exception if the queue already exists.')

    with self.argument_context('storage queue delete') as c:
        c.argument('fail_not_exist', help='Specify whether to throw an exception if the queue doesn\'t exist.')

    for item in ['create', 'delete', 'show', 'list', 'update']:
        with self.argument_context('storage queue policy {}'.format(item)) as c:
            c.extra('queue_name', queue_name_type, required=True)

    with self.argument_context('storage queue policy') as c:
        from .completers import get_storage_acl_name_completion_list

        t_queue_permissions = self.get_sdk('_models#QueueSasPermissions', resource_type=ResourceType.DATA_STORAGE_QUEUE)

        c.argument('container_name', queue_name_type)
        c.argument('policy_name', options_list=('--name', '-n'), help='The stored access policy name.',
                   completer=get_storage_acl_name_completion_list(t_queue_service, 'container_name',
                                                                  'get_queue_access_policy'))

        help_str = 'Allowed values: {}. Can be combined'.format(get_permission_help_string(t_queue_permissions))
        c.argument('permission', options_list='--permissions', help=help_str,
                   validator=get_permission_validator(t_queue_permissions))

        c.argument('start', type=get_datetime_type(True),
                   help='start UTC datetime (Y-m-d\'T\'H:M:S\'Z\'). Defaults to time of request.')
        c.argument('expiry', type=get_datetime_type(True), help='expiration UTC datetime in (Y-m-d\'T\'H:M:S\'Z\')')
        c.ignore('auth_mode')

    from six import u as unicode_string
    for item in ['get', 'peek', 'put', 'update', 'delete', 'clear']:
        with self.argument_context('storage message {}'.format(item)) as c:
            c.extra('queue_name', queue_name_type, required=True)
            c.extra('timeout', help='Request timeout in seconds. Applies to each call to the service.', type=int)

    for item in ['update', 'delete']:
        with self.argument_context('storage message {}'.format(item)) as c:
            c.argument('message', options_list='--id', required=True,
                       help='The message id identifying the message to delete.')
            c.argument('pop_receipt', required=True,
                       help='A valid pop receipt value returned from an earlier call to '
                            'the :func:`~get_messages` or :func:`~update_message` operation.')

    with self.argument_context('storage message put') as c:
        c.argument('content', type=unicode_string, help='Message content, up to 64KB in size.')
        c.extra('time_to_live', type=int,
                help='Specify the time-to-live interval for the message, in seconds. '
                     'The time-to-live may be any positive number or -1 for infinity. '
                     'If this parameter is omitted, the default time-to-live is 7 days.')
        c.extra('visibility_timeout', type=int,
                help='If not specified, the default value is 0. Specify the new visibility timeout value, '
                     'in seconds, relative to server time. The value must be larger than or equal to 0, '
                     'and cannot be larger than 7 days. The visibility timeout of a message cannot be set '
                     'to a value later than the expiry time. visibility_timeout should be set to a value '
                     'smaller than the time_to_live value.')

    with self.argument_context('storage message get') as c:
        c.extra('messages_per_page', options_list='--num-messages', type=int, default=1,
                help='A nonzero integer value that specifies the number of messages to retrieve from the queue, '
                     'up to a maximum of 32. If fewer are visible, the visible messages are returned. '
                     'By default, a single message is retrieved from the queue with this operation.')
        c.extra('visibility_timeout', type=int,
                help='Specify the new visibility timeout value, in seconds, relative to server time. '
                     'The new value must be larger than or equal to 1 second, and cannot be larger than 7 days. '
                     'The visibility timeout of a message can be set to a value later than the expiry time.')

    with self.argument_context('storage message peek') as c:
        c.extra('max_messages', options_list='--num-messages', type=int,
                help='A nonzero integer value that specifies the number of messages to peek from the queue, up to '
                     'a maximum of 32. By default, a single message is peeked from the queue with this operation.')

    with self.argument_context('storage message update') as c:
        c.argument('content', type=unicode_string, help='Message content, up to 64KB in size.')
        c.extra('visibility_timeout', type=int,
                help='If not specified, the default value is 0. Specify the new visibility timeout value, in seconds, '
                     'relative to server time. The new value must be larger than or equal to 0, and cannot be larger '
                     'than 7 days. The visibility timeout of a message cannot be set to a value later than the expiry '
                     'time. A message can be updated until it has been deleted or has expired.')

    with self.argument_context('storage remove') as c:
        from .completers import file_path_completer

        c.extra('container_name', container_name_type, validator=validate_azcopy_remove_arguments)
        c.extra('blob_name', options_list=('--name', '-n'), arg_type=blob_name_type)
        c.extra('share_name', share_name_type, help='The file share name.')
        c.extra('path', options_list=('--path', '-p'),
                help='The path to the file within the file share.',
                completer=file_path_completer)
        c.argument('exclude_pattern', exclude_pattern_type)
        c.argument('include_pattern', include_pattern_type)
        c.argument('exclude_path', exclude_path_type)
        c.argument('include_path', include_path_type)
        c.argument('recursive', recursive_type)
        c.ignore('destination')
        c.ignore('service')
        c.ignore('target')

    for scope in ['create', 'delete', 'exists', 'generate-sas', 'stats']:
        with self.argument_context('storage table {}'.format(scope)) as c:
            c.argument('table_name', table_name_type, options_list=('--name', '-n'))

    with self.argument_context('storage table create') as c:
        c.argument('table_name', table_name_type, options_list=('--name', '-n'), completer=None)
        c.argument('fail_on_exist', help='Throw an exception if the table already exists.')

    with self.argument_context('storage table delete') as c:
        c.argument('fail_not_exist', help='Throw an exception if the table does not exist.')

    with self.argument_context('storage table list') as c:
        c.argument('marker', arg_type=marker_type)
        c.argument('num_results', type=int, help='The maximum number of tables to return.')
        c.argument('show_next_marker', action='store_true',
                   help='Show nextMarker in result when specified.')

    for scope in ['create', 'delete', 'list', 'show', 'update']:
        with self.argument_context('storage table policy {}'.format(scope)) as c:
            c.extra('table_name', table_name_type, required=True)

    with self.argument_context('storage table policy') as c:
        from ._validators import table_permission_validator
        from .completers import get_storage_acl_name_completion_list

        c.argument('policy_name', options_list=('--name', '-n'), help='The stored access policy name.',
                   completer=get_storage_acl_name_completion_list(t_table_service, 'table_name', 'get_table_acl'))

        help_str = 'Allowed values: (r)ead/query (a)dd (u)pdate (d)elete. Can be combined.'
        c.argument('permission', options_list='--permissions', help=help_str, validator=table_permission_validator)

        c.argument('start', type=get_datetime_type(True),
                   help='start UTC datetime (Y-m-d\'T\'H:M:S\'Z\'). Defaults to time of request.')
        c.argument('expiry', type=get_datetime_type(True), help='expiration UTC datetime in (Y-m-d\'T\'H:M:S\'Z\')')

    with self.argument_context('storage table generate-sas') as c:
        from .completers import get_storage_acl_name_completion_list

        c.register_sas_arguments()
        c.argument('id', options_list='--policy-name',
                   help='The name of a stored access policy within the table\'s ACL.',
                   completer=get_storage_acl_name_completion_list(t_table_service, 'table_name', 'get_table_acl'))
        c.argument('permission', options_list='--permissions',
                   help=sas_help.format('(r)ead/query (a)dd (u)pdate (d)elete'),
                   validator=table_permission_validator)
        c.argument('start_pk', help='The minimum partition key accessible with this shared access signature. '
                                    'startpk must accompany startrk. Key values are inclusive. If omitted, '
                                    'there is no lower bound on the table entities that can be accessed.')
        c.argument('start_rk', help='The minimum row key accessible with this shared access signature. '
                                    'startpk must accompany startrk. Key values are inclusive. If omitted, '
                                    'there is no lower bound on the table entities that can be accessed.')
        c.argument('end_pk', help='The maximum partition key accessible with this shared access signature. '
                                  'endpk must accompany endrk. Key values are inclusive. If omitted, '
                                  'there is no upper bound on the table entities that can be accessed.')
        c.argument('end_rk', help='The maximum row key accessible with this shared access signature. '
                                  'endpk must accompany endrk. Key values are inclusive. If omitted, '
                                  'there is no upper bound on the table entities that can be accessed.')
        c.ignore('sas_token')

    with self.argument_context('storage entity') as c:
        c.argument('entity', options_list=('--entity', '-e'), validator=validate_entity, nargs='+',
                   help='Space-separated list of key=value pairs. Must contain a PartitionKey and a RowKey.')
        c.argument('partition_key', help='The PartitionKey of the entity.')
        c.argument('row_key', help='The RowKey of the entity.')

    for scope in ['insert', 'show', 'query', 'replace', 'merge', 'delete']:
        with self.argument_context('storage entity {}'.format(scope)) as c:
            c.extra('table_name', table_name_type, required=True)

    for scope in ['show', 'query']:
        with self.argument_context('storage entity {}'.format(scope)) as c:
            c.extra('select', nargs='+', validator=validate_select,
                    help='Space-separated list of properties to return for each entity.')

    for scope in ['replace', 'merge', 'delete']:
        with self.argument_context('storage entity {}'.format(scope)) as c:
            c.argument('if_match', arg_group='Precondition',
                       help="An ETag value, or the wildcard character (*). "
                            "Specify this header to perform the operation only if "
                            "the resource's ETag matches the value specified.")

    with self.argument_context('storage entity insert') as c:
        c.argument('if_exists', arg_type=get_enum_type(['fail', 'merge', 'replace']))

    with self.argument_context('storage entity query') as c:
        c.argument('filter', help='Specify a filter to return certain entities')
        c.argument('marker', validator=validate_marker, nargs='+')
        c.argument('num_results', type=int, help='Number of entities returned per service request.')

    for item in ['create', 'show', 'delete', 'exists', 'metadata update', 'metadata show']:
        with self.argument_context('storage fs {}'.format(item)) as c:
            c.extra('file_system_name', options_list=['--name', '-n'],
                    help="File system name (i.e. container name).", required=True)
            c.extra('timeout', timeout_type)

    with self.argument_context('storage fs create') as c:
        from .sdkutil import get_fs_access_type_names
        c.argument('public_access', arg_type=get_enum_type(get_fs_access_type_names()),
                   validator=validate_fs_public_access,
                   help="Specify whether data in the file system may be accessed publicly and the level of access.")

    with self.argument_context('storage fs generate-sas') as c:
        t_file_system_permissions = self.get_sdk('_models#FileSystemSasPermissions',
                                                 resource_type=ResourceType.DATA_STORAGE_FILEDATALAKE)
        c.register_sas_arguments()
        c.argument('file_system', options_list=['--name', '-n'], help="File system name (i.e. container name).")
        c.argument('id', options_list='--policy-name',
                   help='The name of a stored access policy.')
        c.argument('permission', options_list='--permissions',
                   help=sas_help.format(get_permission_help_string(t_file_system_permissions)),
                   validator=get_permission_validator(t_file_system_permissions))
        c.argument('cache_control', help='Response header value for Cache-Control when resource is accessed'
                                         'using this shared access signature.')
        c.argument('content_disposition', help='Response header value for Content-Disposition when resource is accessed'
                                               'using this shared access signature.')
        c.argument('content_encoding', help='Response header value for Content-Encoding when resource is accessed'
                                            'using this shared access signature.')
        c.argument('content_language', help='Response header value for Content-Language when resource is accessed'
                                            'using this shared access signature.')
        c.argument('content_type', help='Response header value for Content-Type when resource is accessed'
                                        'using this shared access signature.')
        c.argument('as_user', min_api='2018-11-09', action='store_true',
                   validator=as_user_validator,
                   help="Indicates that this command return the SAS signed with the user delegation key. "
                        "The expiry parameter and '--auth-mode login' are required if this argument is specified. ")
        c.ignore('sas_token')
        c.argument('full_uri', action='store_true',
                   help='Indicate that this command return the full blob URI and the shared access signature token.')

    with self.argument_context('storage fs list') as c:
        c.argument('include_metadata', arg_type=get_three_state_flag(),
                   help='Specify that file system metadata be returned in the response. The default value is "False".')
        c.argument('name_starts_with', options_list=['--prefix'],
                   help='Filter the results to return only file systems whose names begin with the specified prefix.')

    for item in ['list-deleted-path', 'undelete-path']:
        with self.argument_context('storage fs {}'.format(item)) as c:
            c.extra('file_system_name', options_list=['--file-system', '-f'],
                    help="File system name.", required=True)
            c.extra('timeout', timeout_type)

    with self.argument_context('storage fs list-deleted-path') as c:
        c.argument('path_prefix', help='Filter the results to return only paths under the specified path.')
        c.argument('num_results', type=int, help='Specify the maximum number to return.')
        c.argument('marker', help='A string value that identifies the portion of the list of containers to be '
                                  'returned with the next listing operation. The operation returns the NextMarker '
                                  'value within the response body if the listing operation did not return all '
                                  'containers remaining to be listed with the current page. If specified, this '
                                  'generator will begin returning results from the point where the previous '
                                  'generator stopped.')

    with self.argument_context('storage fs service-properties update', resource_type=ResourceType.DATA_STORAGE_FILEDATALAKE,
                               min_api='2020-06-12') as c:
        c.argument('delete_retention', arg_type=get_three_state_flag(), arg_group='Soft Delete',
                   help='Enable soft-delete.')
        c.argument('delete_retention_period', type=int, arg_group='Soft Delete',
                   options_list=['--delete-retention-period', '--period'],
                   help='Number of days that soft-deleted fs will be retained. Must be in range [1,365].')
        c.argument('enable_static_website', options_list=['--static-website'], arg_group='Static Website',
                   arg_type=get_three_state_flag(),
                   help='Enable static-website.')
        c.argument('index_document', help='Represent the name of the index document. This is commonly "index.html".',
                   arg_group='Static Website')
        c.argument('error_document_404_path', options_list=['--404-document'], arg_group='Static Website',
                   help='Represent the path to the error document that should be shown when an error 404 is issued,'
                        ' in other words, when a browser requests a page that does not exist.')

    for item in ['create', 'show', 'delete', 'exists', 'move', 'metadata update', 'metadata show']:
        with self.argument_context('storage fs directory {}'.format(item)) as c:
            c.extra('file_system_name', options_list=['-f', '--file-system'],
                    help="File system name (i.e. container name).", required=True)
            c.extra('directory_path', options_list=['--name', '-n'],
                    help="The name of directory.", required=True)
            c.extra('timeout', timeout_type)

    with self.argument_context('storage fs directory create') as c:
        c.extra('permissions', permissions_type)
        c.extra('umask', umask_type)

    with self.argument_context('storage fs directory list') as c:
        c.extra('file_system_name', options_list=['-f', '--file-system'],
                help="File system name (i.e. container name).", required=True)
        c.argument('recursive', arg_type=get_three_state_flag(), default=True,
                   help='Look into sub-directories recursively when set to true.')
        c.argument('path', help="Filter the results to return only paths under the specified path.")
        c.argument('num_results', type=int, help='Specify the maximum number of results to return.')

    with self.argument_context('storage fs directory move') as c:
        c.argument('new_name', options_list=['--new-directory', '-d'],
                   help='The new directory name the users want to move to. The value must have the following format: '
                        '"{filesystem}/{directory}/{subdirectory}".')

    with self.argument_context('storage fs directory upload') as c:
        from ._validators import validate_fs_directory_upload_destination_url
        c.extra('destination_fs', options_list=['--file-system', '-f'], required=True,
                help='The upload destination file system.')
        c.extra('destination_path', options_list=['--destination-path', '-d'],
                validator=validate_fs_directory_upload_destination_url,
                help='The upload destination directory path. It should be an absolute path to file system. '
                     'If the specified destination path does not exist, a new directory path will be created.')
        c.argument('source', options_list=['--source', '-s'],
                   help='The source file path to upload from.')
        c.argument('recursive', recursive_type, help='Recursively upload files. If enabled, all the files '
                                                     'including the files in subdirectories will be uploaded.')
        c.ignore('destination')

    with self.argument_context('storage fs directory download') as c:
        from ._validators import validate_fs_directory_download_source_url
        c.extra('source_fs', options_list=['--file-system', '-f'], required=True,
                help='The download source file system.')
        c.extra('source_path', options_list=['--source-path', '-s'],
                validator=validate_fs_directory_download_source_url,
                help='The download source directory path. It should be an absolute path to file system.')
        c.argument('destination', options_list=['--destination-path', '-d'],
                   help='The destination local directory path to download.')
        c.argument('recursive', recursive_type, help='Recursively download files. If enabled, all the files '
                                                     'including the files in subdirectories will be downloaded.')
        c.ignore('source')

    with self.argument_context('storage fs directory generate-sas') as c:
        t_file_system_permissions = self.get_sdk('_models#FileSystemSasPermissions',
                                                 resource_type=ResourceType.DATA_STORAGE_FILEDATALAKE)
        c.register_sas_arguments()
        c.argument('file_system_name', options_list=['--file-system', '-f'],
                   help="File system name (i.e. container name).", required=True)
        c.argument('directory_name', options_list=['--name', '-n'], help="The name of directory.", required=True)
        c.argument('id', options_list='--policy-name',
                   help='The name of a stored access policy.')
        c.argument('permission', options_list='--permissions',
                   help=sas_help.format(get_permission_help_string(t_file_system_permissions)),
                   validator=get_permission_validator(t_file_system_permissions))
        c.argument('cache_control', help='Response header value for Cache-Control when resource is accessed'
                                         'using this shared access signature.')
        c.argument('content_disposition', help='Response header value for Content-Disposition when resource is accessed'
                                               'using this shared access signature.')
        c.argument('content_encoding', help='Response header value for Content-Encoding when resource is accessed'
                                            'using this shared access signature.')
        c.argument('content_language', help='Response header value for Content-Language when resource is accessed'
                                            'using this shared access signature.')
        c.argument('content_type', help='Response header value for Content-Type when resource is accessed'
                                        'using this shared access signature.')
        c.argument('as_user', action='store_true',
                   validator=as_user_validator,
                   help="Indicates that this command return the SAS signed with the user delegation key. "
                        "The expiry parameter and '--auth-mode login' are required if this argument is specified. ")
        c.ignore('sas_token')
        c.argument('full_uri', action='store_true',
                   help='Indicate that this command return the full blob URI and the shared access signature token.')

    with self.argument_context('storage fs file list') as c:
        c.extra('file_system_name', options_list=['-f', '--file-system'],
                help="File system name (i.e. container name).", required=True)
        c.argument('recursive', arg_type=get_three_state_flag(), default=True,
                   help='Look into sub-directories recursively when set to true.')
        c.argument('exclude_dir', action='store_true',
                   help='List only files in the given file system.')
        c.argument('path', help='Filter the results to return only paths under the specified path.')
        c.argument('num_results', type=int, default=5000,
                   help='Specify the maximum number of results to return. If the request does not specify num_results '
                        'or specifies a value greater than 5,000, the server will return up to 5,000 items.')
        c.argument('marker',
                   help='An opaque continuation token. This value can be retrieved from the next_marker field of a '
                   'previous generator object. If specified, this generator will begin returning results from this '
                   'point.')
        c.argument('show_next_marker', action='store_true', is_preview=True,
                   help='Show nextMarker in result when specified.')

    for item in ['create', 'show', 'delete', 'exists', 'upload', 'append', 'download', 'show', 'metadata update',
                 'metadata show']:
        with self.argument_context('storage fs file {}'.format(item)) as c:
            c.extra('file_system_name', options_list=['-f', '--file-system'],
                    help='File system name (i.e. container name).', required=True)
            c.extra('path', options_list=['-p', '--path'], help="The file path in a file system.",
                    required=True)
            c.extra('timeout', timeout_type)
            c.argument('content', help='Content to be appended to file.')

    with self.argument_context('storage fs file create') as c:
        t_file_content_settings = self.get_sdk('_models#ContentSettings',
                                               resource_type=ResourceType.DATA_STORAGE_FILEDATALAKE)
        c.register_content_settings_argument(t_file_content_settings, update=False)
        c.extra('permissions', permissions_type)
        c.extra('umask', umask_type)
        c.extra('timeout', timeout_type)

    with self.argument_context('storage fs file download') as c:
        c.argument('destination_path', options_list=['--destination', '-d'], type=file_type,
                   help='The local file where the file or folder will be downloaded to. The source filename will be '
                        'used if not specified.')
        c.argument('overwrite', arg_type=get_three_state_flag(),
                   help="Overwrite an existing file when specified. Default value is false.")

    with self.argument_context('storage fs file move') as c:
        t_file_content_settings = self.get_sdk('_models#ContentSettings',
                                               resource_type=ResourceType.DATA_STORAGE_FILEDATALAKE)
        c.register_content_settings_argument(t_file_content_settings, update=False)
        c.extra('file_system_name', options_list=['-f', '--file-system'],
                help='File system name (i.e. container name).', required=True)
        c.extra('path', options_list=['-p', '--path'], required=True,
                help="The original file path users want to move in a file system.")
        c.argument('new_name', options_list=['--new-path'],
                   help='The new path the users want to move to. The value must have the following format: '
                   '"{filesystem}/{directory}/{subdirectory}/{file}".')

    with self.argument_context('storage fs file upload') as c:
        t_file_content_settings = self.get_sdk('_models#ContentSettings',
                                               resource_type=ResourceType.DATA_STORAGE_FILEDATALAKE)
        c.register_content_settings_argument(t_file_content_settings, update=False)
        c.argument('local_path', options_list=['--source', '-s'],
                   help='Path of the local file to upload as the file content.')
        c.argument('overwrite', arg_type=get_three_state_flag(), help="Overwrite an existing file when specified.")
        c.argument('if_match', arg_group='Precondition',
                   help="An ETag value, or the wildcard character (*). Specify this header to perform the operation "
                   "only if the resource's ETag matches the value specified.")
        c.argument('if_none_match', arg_group='Precondition',
                   help="An ETag value, or the wildcard character (*). Specify this header to perform the operation "
                   "only if the resource's ETag does not match the value specified.")
        c.argument('if_modified_since', arg_group='Precondition',
                   help="A Commence only if modified since supplied UTC datetime (Y-m-d'T'H:M'Z').")
        c.argument('if_unmodified_since', arg_group='Precondition',
                   help="A Commence only if unmodified since supplied UTC datetime (Y-m-d'T'H:M'Z').")
        c.argument('permissions', permissions_type)
        c.argument('umask', umask_type)

    for item in ['set', 'show']:
        with self.argument_context('storage fs access {}'.format(item)) as c:
            from ._validators import validate_access_control
            c.extra('file_system_name', options_list=['-f', '--file-system'],
                    help='File system name (i.e. container name).', required=True)
            c.extra('directory_path', options_list=['-p', '--path'],
                    help='The path to a file or directory in the specified file system.', required=True)
            c.argument('permissions', validator=validate_access_control)
            c.ignore('upn')

    for item in ['set-recursive', 'update-recursive', 'remove-recursive']:
        with self.argument_context('storage fs access {}'.format(item)) as c:
            c.register_fs_directory_arguments()
            c.argument('acl', help='The value is a comma-separated list of access control entries. Each access control '
                       'entry (ACE) consists of a scope, a type, a user or group identifier, and permissions in the '
                       'format "[scope:][type]:[id]:[permissions]".  For more information, please refer to '
                       'https://docs.microsoft.com/azure/storage/blobs/data-lake-storage-access-control.')
            c.extra('continuation',
                    help='Optional continuation token that can be used to resume previously stopped operation.')
            c.extra('batch_size', type=int, help='Optional. If data set size exceeds batch size then operation will '
                    'be split into multiple requests so that progress can be tracked. Batch size should be between 1 '
                    'and 2000. The default when unspecified is 2000.')
            c.extra('max_batches', type=int, help='Optional. Define maximum number of batches that single change '
                    'Access Control operation can execute. If maximum is reached before all sub-paths are processed, '
                    'then continuation token can be used to resume operation. Empty value indicates that maximum '
                    'number of batches in unbound and operation continues till end.')
            c.extra('continue_on_failure', arg_type=get_three_state_flag(),
                    help='If set to False, the operation will terminate quickly on encountering user errors (4XX). '
                         'If True, the operation will ignore user errors and proceed with the operation on other '
                         'sub-entities of the directory. Continuation token will only be returned when '
                         '--continue-on-failure is True in case of user errors. If not set the default value is False '
                         'for this.')
