# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-statements

from knack.arguments import CLIArgumentType
from azure.cli.core.commands.parameters import (get_enum_type,
                                                get_location_type,
                                                get_three_state_flag,
                                                tags_type,
                                                resource_group_name_type)
from azure.cli.core.commands.validators import \
    get_default_location_from_resource_group
from ._constants import ImportExportProfiles, ImportMode, FeatureFlagConstants, ARMAuthenticationMode

from ._validators import (validate_appservice_name_or_id, validate_aks_cluster_name_or_id,
                          validate_sku, validate_snapshot_query_fields,
                          validate_connection_string, validate_datetime,
                          validate_export, validate_import,
                          validate_import_depth, validate_query_fields,
                          validate_feature_query_fields, validate_filter_parameters,
                          validate_separator, validate_secret_identifier,
                          validate_key, validate_feature, validate_feature_key,
                          validate_identity, validate_auth_mode,
                          validate_resolve_keyvault, validate_export_profile, validate_import_profile,
                          validate_strict_import, validate_export_as_reference, validate_snapshot_filters,
                          validate_snapshot_export, validate_snapshot_import, validate_tag_filters,
                          validate_import_tag_filters, validate_dry_run, validate_kv_revision_retention_period)


def load_arguments(self, _):

    # PARAMETER REGISTRATION
    fields_arg_type = CLIArgumentType(
        nargs='+',
        help='Space-separated customized output fields.',
        validator=validate_query_fields,
        arg_type=get_enum_type(['key', 'value', 'label', 'content_type', 'etag', 'tags', 'locked', 'last_modified'])
    )
    feature_fields_arg_type = CLIArgumentType(
        nargs='+',
        help='Customize output fields for Feature Flags.',
        validator=validate_feature_query_fields,
        arg_type=get_enum_type(['name', 'key', 'label', 'locked', 'last_modified', 'state', 'description', 'conditions'])
    )
    snapshot_fields_arg_type = CLIArgumentType(
        nargs='+',
        help='Customize output fields for Snapshots',
        validator=validate_snapshot_query_fields,
        arg_type=get_enum_type(['name', 'etag', 'retention_period', 'filters', 'status', 'created', 'expires', 'size', 'items_count', 'composition_type', 'tags'])
    )
    filter_parameters_arg_type = CLIArgumentType(
        validator=validate_filter_parameters,
        help="Space-separated filter parameters in 'name[=value]' format. The value must be an escaped JSON string.",
        nargs='*'
    )
    datatime_filter_arg_type = CLIArgumentType(
        validator=validate_datetime,
        help='Format: "YYYY-MM-DDThh:mm:ss["Z"/±hh:mm]. If no time zone or offset specified, use UTC by default.'
    )
    top_arg_type = CLIArgumentType(
        options_list=['--top', '-t'],
        type=int,
        help='Maximum number of items to return. Must be a positive integer. Default to 100.'
    )
    retention_days_arg_type = CLIArgumentType(
        options_list=['--retention-days'],
        type=int,
        help='Number of days to retain the soft delete enabled App Configuration store after deleting. Must be a positive integer between 0 and 7.'
    )
    identities_arg_type = CLIArgumentType(
        nargs='*',
        validator=validate_identity
    )
    store_name_arg_type = CLIArgumentType(
        options_list=['--store-name', '-s'],
        type=str,
        help='Name of the App Configuration store. You can configure the default name using `az configure --defaults app_configuration_store=<name>`.',
        configured_default='app_configuration_store'
    )

    store_creation_replica_name_arg_type = CLIArgumentType(
        options_list=['--replica-name'],
        help='Name of the replica of the App Configuration store.',
        configured_default=None
    )

    replica_location_arg_type = CLIArgumentType(
        options_list=['--replica-location'],
        help='The location of the replica of the App Configuration store.',
        configured_default=None
    )

    replica_name_arg_type = CLIArgumentType(
        options_list=['--name', '-n'],
        type=str,
        help='Name of the replica of the App Configuration store.',
        configured_default=None
    )

    snapshot_name_arg_type = CLIArgumentType(
        options_list=['--snapshot-name', '-s'],
        type=str,
        help='Name of the App Configuration snapshot.',
        configured_default=None
    )

    snapshot_filter_arg_type = CLIArgumentType(
        options_list=['--filters'],
        validator=validate_snapshot_filters,
        nargs='+',
        help='Space-separated list of escaped JSON objects that represent the key, label and tag filters used to build an App Configuration snapshot.'
    )
    snapshot_status_arg_type = CLIArgumentType(
        options_list=['--status'],
        arg_type=get_enum_type(['archived', 'failed', 'provisioning', 'ready']),
        nargs='+',
        help='Filter snapshots by their status. If no status specified, return all snapshots by default.'
    )

    arm_auth_mode_arg_type = CLIArgumentType(
        options_list=['--arm-auth-mode'],
        arg_type=get_enum_type([ARMAuthenticationMode.LOCAL, ARMAuthenticationMode.PASS_THROUGH]),
        help="The authentication mode for accessing the App Configuration Store via ARM. 'pass-through' (Recommended) uses Microsoft Entra ID to access the store via ARM with proper authorization.'local' uses access keys for authentication. This requires access keys to be enabled."
    )

    enable_arm_private_network_access_arg_type = CLIArgumentType(
        option_list=['--enable-arm-private-network-access'],
        arg_type=get_three_state_flag(),
        help="Enable access to the App Configuration store via ARM Private Link if resource is restricted to private network access. Requires Pass-through ARM authentication mode."
    )

    tags_arg_type = CLIArgumentType(
        nargs='*',
        validator=validate_tag_filters
    )

    kv_revision_retention_period_arg_type = CLIArgumentType(
        options_list=['--kv-revision-retention-period'],
        type=int,
        help='Duration in seconds to retain key-value revisions in the App Configuration store. For Free and Developer sku stores, revisions can be retained for a maximum of 7 days (604,800s); for Standard and Premium sku stores, up to 30 days (2,592,000s). Only Non-Free tiers can update this value. If specified, retention period must be at least 1 hour (3600s).',
        validator=validate_kv_revision_retention_period
    )

    # Used with data plane commands. These take either a store name or connection string argument.
    # We only read default values when neither connection string nor store name is provided so configured defaults are not supplied.
    data_plane_name_arg_type = CLIArgumentType(
        options_list=['--name', '-n'],
        type=str,
        help='Name of the App Configuration store. You can configure the default name using `az configure --defaults app_configuration_store=<name>`.',
        configured_default=None
    )

    with self.argument_context('appconfig') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('name', options_list=['--name', '-n'], id_part='None', help='Name of the App Configuration store. You can configure the default name using `az configure --defaults app_configuration_store=<name>`', configured_default='app_configuration_store')
        c.argument('connection_string', validator=validate_connection_string,
                   help="Combination of access key and endpoint of the App Configuration store. Can be found using 'az appconfig credential list'. Users can preset it using `az configure --defaults appconfig_connection_string=<connection_string>` or environment variable with the name AZURE_APPCONFIG_CONNECTION_STRING.")
        c.argument('yes', options_list=['--yes', '-y'], help='Do not prompt for confirmation.')
        c.argument('datetime', arg_type=datatime_filter_arg_type)
        c.argument('top', arg_type=top_arg_type)
        c.argument('all_', options_list=['--all'], action='store_true', help="List all items.")
        c.argument('fields', arg_type=fields_arg_type)
        c.argument('endpoint', help='If auth mode is "login" or "anonymous", provide endpoint URL of the App Configuration store. The endpoint can be retrieved using "az appconfig show" command. You can configure the default endpoint using `az configure --defaults appconfig_endpoint=<endpoint>`', configured_default='appconfig_endpoint')
        c.argument('auth_mode', arg_type=get_enum_type(['login', 'key', 'anonymous']), configured_default='appconfig_auth_mode', validator=validate_auth_mode,
                   help='This parameter can be used for indicating how a data operation is to be authorized. ' +
                   'If the auth mode is "key", provide connection string or store name and your account access keys will be retrieved for authorization. ' +
                   'If the auth mode is "login", provide the `--endpoint` or `--name` and your "az login" credentials will be used for authorization. ' +
                   'If the auth mode is "anonymous", provide the --endpoint that will be used for authorization. Anonymous mode is intended for custom endpoints only, such as the App Configuration emulator. ' +
                   'You can configure the default auth mode using `az configure --defaults appconfig_auth_mode=<auth_mode>`. ' +
                   'For more information, see https://learn.microsoft.com/azure/azure-app-configuration/concept-enable-rbac')

    with self.argument_context('appconfig create') as c:
        c.argument('sku', help='The sku of the App Configuration store', arg_type=get_enum_type(['Free', 'Developer', 'Premium', 'Standard']), validator=validate_sku)
        c.argument('location', options_list=['--location', '-l'], arg_type=get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)
        c.argument('tags', arg_type=tags_type, help="Space-separated tags: key[=value] [key[=value] ...].")
        c.argument('assign_identity', arg_type=identities_arg_type,
                   help='Space-separated list of managed identities to be assigned. Use "[system]" to refer to system-assigned managed identity or a resource ID to refer to user-assigned managed identity. If this argument is provided without any value, system-assigned managed identity will be assigned by default. If this argument is not provided, no managed identities will be assigned to this App Configuration store.')
        c.argument('enable_public_network', options_list=['--enable-public-network', '-e'], arg_type=get_three_state_flag(),
                   help='When true, requests coming from public networks have permission to access this store while private endpoint is enabled. When false, only requests made through Private Links can reach this store.')
        c.argument('disable_local_auth', arg_type=get_three_state_flag(), help='Disable all authentication methods other than AAD authentication.')
        c.argument('retention_days', arg_type=retention_days_arg_type)
        c.argument('enable_purge_protection', options_list=['--enable-purge-protection', '-p'], arg_type=get_three_state_flag(), help='Property specifying whether protection against purge is enabled for this App Configuration store. Setting this property to true activates protection against purge for this App Configuration store and its contents. Enabling this functionality is irreversible.')
        c.argument('replica_name', arg_type=store_creation_replica_name_arg_type)
        c.argument('replica_location', arg_type=replica_location_arg_type)
        c.argument('no_replica', help='Proceed without replica creation for premium tier store.', arg_type=get_three_state_flag())
        c.argument('arm_auth_mode', arg_type=arm_auth_mode_arg_type)
        c.argument('enable_arm_private_network_access', arg_type=enable_arm_private_network_access_arg_type)
        c.argument('kv_revision_retention_period', arg_type=kv_revision_retention_period_arg_type)

    with self.argument_context('appconfig update') as c:
        c.argument('sku', help='The sku of the App Configuration store', arg_type=get_enum_type(['Free', 'Developer', 'Premium', 'Standard']))
        c.argument('tags', arg_type=tags_type)
        c.argument('enable_public_network', options_list=['--enable-public-network', '-e'], arg_type=get_three_state_flag(),
                   help='When true, requests coming from public networks have permission to access this store while private endpoint is enabled. When false, only requests made through Private Links can reach this store.')
        c.argument('disable_local_auth', arg_type=get_three_state_flag(), help='Disable all authentication methods other than AAD authentication.')
        c.argument('enable_purge_protection', options_list=['--enable-purge-protection', '-p'], arg_type=get_three_state_flag(), help='Property specifying whether protection against purge is enabled for this App Configuration store. Setting this property to true activates protection against purge for this App Configuration store and its contents. Enabling this functionality is irreversible.')
        c.argument('arm_auth_mode', arg_type=arm_auth_mode_arg_type)
        c.argument('enable_arm_private_network_access', arg_type=enable_arm_private_network_access_arg_type)
        c.argument('kv_revision_retention_period', arg_type=kv_revision_retention_period_arg_type)

    with self.argument_context('appconfig recover') as c:
        c.argument('location', arg_type=get_location_type(self.cli_ctx), help='Location of the deleted App Configuration store. Can be viewed using command `az appconfig show-deleted`.')
        c.argument('resource_group_name', arg_type=resource_group_name_type, help='Resource group of the deleted App Configuration store.')

    with self.argument_context('appconfig show-deleted') as c:
        c.argument('location', arg_type=get_location_type(self.cli_ctx), help='Location of the deleted App Configuration store.')

    with self.argument_context('appconfig purge') as c:
        c.argument('location', arg_type=get_location_type(self.cli_ctx), help='Location of the deleted App Configuration store. Can be viewed using command `az appconfig show-deleted`.')

    with self.argument_context('appconfig update', arg_group='Customer Managed Key') as c:
        c.argument('encryption_key_name', help='The name of the KeyVault key.')
        c.argument('encryption_key_vault', help='The URI of the KeyVault.')
        c.argument('encryption_key_version', help='The version of the KeyVault key. Use the latest version by default.')
        c.argument('identity_client_id', help='Client ID of the managed identity with wrap and unwrap access to encryption key. Use system-assigned managed identity by default.')

    with self.argument_context('appconfig identity assign') as c:
        c.argument('identities', arg_type=identities_arg_type, help="Accept system-assigned or user-assigned managed identities separated by spaces. Use '[system]' to refer to system-assigned managed identity or a resource ID to refer to user-assigned managed identity. If this argument is not provided or this argument is provided without any value, system-assigned managed identity will be used by default.")

    with self.argument_context('appconfig identity remove') as c:
        c.argument('identities', arg_type=identities_arg_type, help="Accept system-assigned or user-assigned managed identities separated by spaces. Use '[system]' to refer to system-assigned managed identity, '[all]' for all managed identities or a resource ID to refer user-assigned managed identity. If this argument is not provided or this argument is provided without any value, system-assigned managed identity will be removed by default.")

    with self.argument_context('appconfig credential regenerate') as c:
        c.argument('id_', options_list=['--id'], help='Id of the key to be regenerated. Can be found using az appconfig credential list command.')

    with self.argument_context('appconfig kv') as c:
        c.argument('name', arg_type=data_plane_name_arg_type)

    with self.argument_context('appconfig kv import') as c:
        c.argument('label', help="Imported KVs and feature flags will be assigned with this label. If no label specified, will assign null label.")
        c.argument('tags', nargs="*", help="Imported KVs and feature flags will be assigned with these tags. If no tags are specified, imported KVs and feature flags will retain existing tags. Support space-separated tags: key[=value] [key[=value] ...]. Use "" to clear existing tags.")
        c.argument('prefix', help="This prefix will be appended to the front of imported keys. Prefix will be ignored for feature flags.")
        c.argument('source', options_list=['--source', '-s'], arg_type=get_enum_type(['file', 'appconfig', 'appservice', 'aks']), validator=validate_import, help="The source of importing. Note that importing feature flags from appservice is not supported.")
        c.argument('yes', help="Do not prompt for preview.")
        c.argument('skip_features', help="Import only key values and exclude all feature flags. By default, all feature flags will be imported from file or appconfig. Not applicable for appservice.", arg_type=get_three_state_flag())
        c.argument('content_type', help='Content type of all imported items.')
        c.argument('import_mode', arg_type=get_enum_type([ImportMode.ALL, ImportMode.IGNORE_MATCH]), help='If import mode is "ignore-match", only source key-values that do not already exist or whose value, content-type or tags are different from that of an existing key-value with the same key and label, will be written. Import mode "all" writes all key-values to the destination regardless of whether they exist or not.')
        c.argument('dry_run', validator=validate_dry_run, help="Preview the result of import operation without making any changes to the App Configuration store.")

    with self.argument_context('appconfig kv import', arg_group='File') as c:
        c.argument('path', help='Local configuration file path. Required for file arguments.')
        c.argument('format_', options_list=['--format'], arg_type=get_enum_type(['json', 'yaml', 'properties']), help='Imported file format. Required for file arguments. Currently, feature flags are not supported in properties format.')
        c.argument('depth', validator=validate_import_depth, help="Depth for flattening the json or yaml file to key-value pairs. Flatten to the deepest level by default if --separator is provided. Not applicable for property files or feature flags.")
        # bypass cli allowed values limitation
        c.argument('separator', validator=validate_separator, help="Delimiter for flattening the json or yaml file to key-value pairs. Separator will be ignored for property files and feature flags. Supported values: '.', ',', ';', '-', '_', '__', '/', ':' ")
        c.argument('profile', validator=validate_import_profile, arg_type=get_enum_type([ImportExportProfiles.DEFAULT, ImportExportProfiles.KVSET]), help="Import profile to be used for importing the key-values. Options 'depth', 'separator', 'content-type', 'label', 'skip-features', 'tags' and, 'prefix' are not supported when using '{}' profile.".format(ImportExportProfiles.KVSET))
        c.argument('strict', validator=validate_strict_import, arg_type=get_three_state_flag(), help="Delete all other key-values in the store with specified prefix and label")

    with self.argument_context('appconfig kv import', arg_group='AppConfig') as c:
        c.argument('src_name', help='The name of the source App Configuration store.')
        c.argument('src_connection_string', validator=validate_connection_string, help="Combination of access key and endpoint of the source store.")
        c.argument('src_key', help='If no key specified, import all keys by default. Support star sign as filters, for instance abc* means keys with abc as prefix. Key filtering not applicable for feature flags. By default, all feature flags with specified label will be imported.')
        c.argument('src_label', help="Only keys with this label in source AppConfig will be imported. If no value specified, import keys with null label by default. Support star sign as filters, for instance * means all labels, abc* means labels with abc as prefix.")
        c.argument('preserve_labels', arg_type=get_three_state_flag(), help="Flag to preserve labels from source AppConfig. This argument should NOT be specified along with --label.")
        c.argument('src_endpoint', help='If --src-auth-mode is "login", provide endpoint URL of the source App Configuration store.')
        c.argument('src_auth_mode', arg_type=get_enum_type(['login', 'key', 'anonymous']),
                   help='Auth mode for connecting to source App Configuration store. For details, refer to "--auth-mode" argument.')
        c.argument('src_snapshot', validator=validate_snapshot_import,
                   help='Import all keys in a given snapshot of the source App Configuration store. If no snapshot is specified, the keys currently in the store are imported based on the specified key and label filters.')
        c.argument('src_tags', nargs="*", validator=validate_import_tag_filters, help="Key-values which contain the specified tags in source AppConfig will be imported. If no tags are specified, all key-values with any tags can be imported. Support space-separated tag filters: key[=value] [key[=value] ...].")

    with self.argument_context('appconfig kv import', arg_group='AppService') as c:
        c.argument('appservice_account', validator=validate_appservice_name_or_id, help='ARM ID for AppService OR the name of the AppService, assuming it is in the same subscription and resource group as the App Configuration store. Required for AppService arguments')

    with self.argument_context('appconfig kv import', arg_group='AKS') as c:
        c.argument('aks_cluster', validator=validate_aks_cluster_name_or_id, help='ARM ID for AKS OR the name of the AKS, assuming it is in the same subscription and resource group as the App Configuration store. Required for AKS arguments')
        c.argument('configmap_name', help='Name of the ConfigMap. Required for AKS arguments.')
        c.argument('configmap_namespace', help='Namespace of the ConfigMap. default to "default" namespace if not specified.')

    with self.argument_context('appconfig kv export') as c:
        c.argument('label', help="Only keys and feature flags with this label will be exported. If no label specified, export keys and feature flags with null label by default. When export destination is appconfig, or when export destination is file with `appconfig/kvset` profile, this argument supports asterisk and comma signs for label filtering, for instance, * means all labels, abc* means labels with abc as prefix, and abc,xyz means labels with abc or xyz.")
        c.argument('prefix', help="Prefix to be trimmed from keys. Prefix will be ignored for feature flags.")
        c.argument('key', help='If no key specified, return all keys by default. Support star sign as filters, for instance abc* means keys with abc as prefix. Key filtering not applicable for feature flags. By default, all feature flags with specified label will be exported.')
        c.argument('destination', options_list=['--destination', '-d'], arg_type=get_enum_type(['file', 'appconfig', 'appservice']), validator=validate_export, help="The destination of exporting. Note that exporting feature flags to appservice is not supported.")
        c.argument('yes', help="Do not prompt for preview.")
        c.argument('skip_features', help="Export items excluding all feature flags. By default, all features with the specified label will be exported to file or appconfig. Not applicable for appservice.", arg_type=get_three_state_flag())
        c.argument('skip_keyvault', help="Export items excluding all key vault references. By default, all key vault references with the specified label will be exported.", arg_type=get_three_state_flag())
        c.argument('snapshot', validator=validate_snapshot_export,
                   help="Export all keys in a given snapshot of the App Configuration store. If no snapshot is specified, the keys currently in the store are exported based on the specified key and label filters.")
        c.argument('tags', arg_type=tags_arg_type, help="Key-values which contain the specified tags in source AppConfig will be exported. If no tags are specified, all key-values with any tags can be exported. Support space-separated tag filters: key[=value] [key[=value] ...].")
        c.argument('dry_run', validator=validate_dry_run, help="Preview the result of export operation without making any changes to the App Configuration store.")

    with self.argument_context('appconfig kv export', arg_group='File') as c:
        c.argument('path', help='Local configuration file path. Required for file arguments.')
        c.argument('format_', options_list=['--format'], arg_type=get_enum_type(['json', 'yaml', 'properties']), help='File format exporting to. Required for file arguments. Currently, feature flags are not supported in properties format.')
        c.argument('depth', validator=validate_import_depth, help="Depth for flattening the key-value pairs to json or yaml file. Flatten to the deepest level by default. Not applicable for property files or feature flags.")
        # bypass cli allowed values limitation
        c.argument('separator', validator=validate_separator, help="Delimiter for flattening the key-value pairs to json or yaml file. Required for exporting hierarchical structure. Separator will be ignored for property files and feature flags. Supported values: '.', ',', ';', '-', '_', '__', '/', ':' ")
        c.argument('naming_convention', arg_type=get_enum_type(['pascal', 'camel', 'underscore', 'hyphen']), help='Naming convention to be used for "Feature Management" section of file. Example: pascal = FeatureManagement, camel = featureManagement, underscore = feature_management, hyphen = feature-management.')
        c.argument('resolve_keyvault', arg_type=get_three_state_flag(), validator=validate_resolve_keyvault, help="Resolve the content of key vault reference.")
        c.argument('profile', validator=validate_export_profile, arg_type=get_enum_type([ImportExportProfiles.DEFAULT, ImportExportProfiles.KVSET]), help="Export profile to be used for exporting the key-values. Options 'depth', 'separator', 'naming-convention', 'prefix', 'dest-label' , 'dest-tags' and, 'resolve-keyvault' are not supported when using '{}' profile".format(ImportExportProfiles.KVSET))

    with self.argument_context('appconfig kv export', arg_group='AppConfig') as c:
        c.argument('dest_name', help='The name of the destination App Configuration store.')
        c.argument('dest_connection_string', validator=validate_connection_string, help="Combination of access key and endpoint of the destination store.")
        c.argument('dest_label', help="Exported KVs will be labeled with this destination label. If neither --dest-label nor --preserve-labels is specified, will assign null label.")
        c.argument('preserve_labels', arg_type=get_three_state_flag(), help="Flag to preserve labels from source AppConfig. This argument should NOT be specified along with --dest-label.")
        c.argument('dest_endpoint', help='If --dest-auth-mode is "login", provide endpoint URL of the destination App Configuration store.')
        c.argument('dest_auth_mode', arg_type=get_enum_type(['login', 'key', 'anonymous']),
                   help='Auth mode for connecting to the destination App Configuration store. For details, refer to "--auth-mode" argument.')
        c.argument('dest_tags', nargs="*", help="Exported KVs and feature flags will be assigned with these tags. If no tags are specified, exported KVs and features will retain existing tags. Support space-separated tags: key[=value] [key[=value] ...]. Use "" to clear existing tags.")

    with self.argument_context('appconfig kv export', arg_group='AppService') as c:
        c.argument('appservice_account', validator=validate_appservice_name_or_id, help='ARM ID for AppService OR the name of the AppService, assuming it is in the same subscription and resource group as the App Configuration store. Required for AppService arguments')
        c.argument('export_as_reference', options_list=['--export-as-reference', '-r'], arg_type=get_three_state_flag(), validator=validate_export_as_reference,
                   help="Export key-values as App Configuration references. For more information, see https://learn.microsoft.com/en-us/azure/app-service/app-service-configuration-references")

    with self.argument_context('appconfig kv set') as c:
        c.argument('key', validator=validate_key, help="Key to be set. Key cannot be a '.' or '..', or contain the '%' character.")
        c.argument('label', help="If no label specified, set the key with null label by default")
        c.argument('tags', arg_type=tags_type)
        c.argument('content_type', help='Content type of the key-value to be set.')
        c.argument('value', help='Value of the key-value to be set.')

    with self.argument_context('appconfig kv set-keyvault') as c:
        c.argument('key', validator=validate_key, help="Key to be set. Key cannot be a '.' or '..', or contain the '%' character.")
        c.argument('label', help="If no label specified, set the key with null label by default")
        c.argument('tags', arg_type=tags_type)
        c.argument('secret_identifier', validator=validate_secret_identifier, help="ID of the Key Vault object. Can be found using 'az keyvault {collection} show' command, where collection is key, secret or certificate. To set reference to the latest version of your secret, remove version information from secret identifier.")

    with self.argument_context('appconfig kv delete') as c:
        c.argument('key', validator=validate_key, help='Support star sign as filters, for instance * means all key and abc* means keys with abc as prefix.')
        c.argument('label', help="If no label specified, delete entry with null label. Support star sign as filters, for instance * means all label and abc* means labels with abc as prefix.")
        c.argument('tags', arg_type=tags_arg_type, help="If no tags are specified, delete all key-values with any tags. Support space-separated tags: key[=value] [key[=value] ...].")

    with self.argument_context('appconfig kv show') as c:
        c.argument('key', help='Key to be showed.')
        c.argument('label', help="If no label specified, show entry with null label. Filtering is not supported.")

    with self.argument_context('appconfig kv list') as c:
        c.argument('key', help='If no key specified, return all keys by default. Support star sign as filters, for instance abc* means keys with abc as prefix.')
        c.argument('label', help="If no label specified, list all labels. Support star sign as filters, for instance abc* means labels with abc as prefix. Use '\\0' for null label.")
        c.argument('tags', arg_type=tags_arg_type, help="If no tags are specified, return all key-values with any tags. Support space-separated tags: key[=value] [key[=value] ...].")
        c.argument('snapshot', help="List all keys in a given snapshot of the App Configuration store. If no snapshot is specified, the keys currently in the store are listed.")
        c.argument('resolve_keyvault', arg_type=get_three_state_flag(), help="Resolve the content of key vault reference. This argument should NOT be specified along with --fields. Instead use --query for customized query.")

    with self.argument_context('appconfig kv restore') as c:
        c.argument('key', help='If no key specified, restore all keys by default. Support star sign as filters, for instance abc* means keys with abc as prefix.')
        c.argument('label', help="If no label specified, restore all key-value pairs with all labels. Support star sign as filters, for instance abc* means labels with abc as prefix. Use '\\0' for null label.")
        c.argument('tags', arg_type=tags_arg_type, help="If no tags are specified, restore all key-values with any tags. Support space-separated tags: key[=value] [key[=value] ...].")
        c.argument('dry_run', validator=validate_dry_run, help="Preview the result of restore operation without making any changes to the App Configuration store.")

    with self.argument_context('appconfig kv lock') as c:
        c.argument('key', help='Key to be locked.')
        c.argument('label', help="If no label specified, lock entry with null label. Filtering is not supported.")

    with self.argument_context('appconfig kv unlock') as c:
        c.argument('key', help='Key to be unlocked.')
        c.argument('label', help="If no label specified, unlock entry with null label. Filtering is not supported.")

    with self.argument_context('appconfig revision list') as c:
        c.argument('name', arg_type=data_plane_name_arg_type)
        c.argument('key', help='If no key specified, return all keys by default. Support star sign as filters, for instance abc* means keys with abc as prefix.')
        c.argument('label', help="If no label specified, list all labels. Support star sign as filters, for instance abc* means labels with abc as prefix. Use '\\0' for null label.")
        c.argument('tags', arg_type=tags_arg_type, help="If no tags are specified, return all key-values with any tags. Support space-separated tags: key[=value] [key[=value] ...].")

    with self.argument_context('appconfig feature') as c:
        c.argument('name', arg_type=data_plane_name_arg_type)
        c.argument('key', validator=validate_feature_key, help='Key of the feature flag. Key must start with the ".appconfig.featureflag/" prefix. Key cannot contain the "%" character. If both key and feature arguments are provided, only key will be used. Default key is the reserved prefix ".appconfig.featureflag/" + feature name.')

    with self.argument_context('appconfig feature show') as c:
        c.argument('feature', help='Name of the feature flag to be retrieved. If the feature flag key is different from the default key, provide the `--key` argument instead.')
        c.argument('label', help="If no label specified, show entry with null label. Filtering is not supported.")
        c.argument('fields', arg_type=feature_fields_arg_type)

    with self.argument_context('appconfig feature set') as c:
        c.argument('feature', validator=validate_feature, help="Name of the feature flag to be set. Feature name cannot contain the '%' or ':' characters.")
        c.argument('label', help="If no label specified, set the feature flag with null label by default")
        c.argument('description', help='Description of the feature flag to be set.')
        c.argument('key', validator=validate_feature_key, help='Key of the feature flag. Key must start with the ".appconfig.featureflag/" prefix. Key cannot contain the "%" character. Default key is the reserved prefix ".appconfig.featureflag/" + feature name.')
        c.argument('requirement_type', arg_type=get_enum_type([FeatureFlagConstants.REQUIREMENT_TYPE_ALL, FeatureFlagConstants.REQUIREMENT_TYPE_ANY]),
                   help='Requirement type determines if filters should use "Any" or "All" logic when evaluating the state of a feature.')
        c.argument('tags', arg_type=tags_type)

    with self.argument_context('appconfig feature delete') as c:
        c.argument('feature', help='Name of the feature to be deleted. If the feature flag key is different from the default key, provide the `--key` argument instead. Support star sign as filters, for instance * means all features and abc* means features with abc as prefix. Comma separated features are not supported. Please provide escaped string if your feature name contains comma.')
        c.argument('label', help="If no label specified, delete the feature flag with null label by default. Support star sign as filters, for instance * means all labels and abc* means labels with abc as prefix.")
        c.argument('key', validator=validate_feature_key, help='Key of the feature flag. Key must start with the ".appconfig.featureflag/" prefix. Key cannot contain the "%" character. If both key and feature arguments are provided, only key will be used. Support star sign as filters, for instance ".appconfig.featureflag/*" means all features and ".appconfig.featureflag/abc*" means features with abc as prefix. Comma separated features are not supported. Please provide escaped string if your feature name contains comma.')
        c.argument('tags', arg_type=tags_arg_type, help="If no tags are specified, delete all feature flags with any tags. Support space-separated tags: key[=value] [key[=value] ...].")

    with self.argument_context('appconfig feature list') as c:
        c.argument('feature', help='Name of the feature to be listed. If the feature flag key is different from the default key, provide the `--key` argument instead. Support star sign as filters, for instance * means all features and abc* means features with abc as prefix. Comma separated features are not supported. Please provide escaped string if your feature name contains comma.')
        c.argument('label', help="If no label specified, list all labels. Support star sign as filters, for instance * means all labels and abc* means labels with abc as prefix. Use '\\0' for null label.")
        c.argument('fields', arg_type=feature_fields_arg_type)
        c.argument('all_', help="List all feature flags.")
        c.argument('key', validator=validate_feature_key, help='Key of the feature flag. Key must start with the ".appconfig.featureflag/" prefix. Key cannot contain the "%" character. If both key and feature arguments are provided, only key will be used. Support star sign as filters, for instance ".appconfig.featureflag/*" means all features and ".appconfig.featureflag/abc*" means features with abc as prefix. Comma separated features are not supported. Please provide escaped string if your feature name contains comma.')
        c.argument('tags', arg_type=tags_arg_type, help="If no tags are specified, list all feature flags with any tags. Support space-separated tags: key[=value] [key[=value] ...].")

    with self.argument_context('appconfig feature lock') as c:
        c.argument('feature', help='Name of the feature to be locked. If the feature flag key is different from the default key, provide the `--key` argument instead.')
        c.argument('label', help="If no label specified, lock the feature flag with null label by default.")

    with self.argument_context('appconfig feature unlock') as c:
        c.argument('feature', help='Name of the feature to be unlocked. If the feature flag key is different from the default key, provide the `--key` argument instead.')
        c.argument('label', help="If no label specified, unlock the feature flag with null label by default.")

    with self.argument_context('appconfig feature enable') as c:
        c.argument('feature', help='Name of the feature to be enabled. If the feature flag key is different from the default key, provide the `--key` argument instead.')
        c.argument('label', help="If no label specified, enable the feature flag with null label by default.")

    with self.argument_context('appconfig feature disable') as c:
        c.argument('feature', help='Name of the feature to be disabled. If the feature flag key is different from the default key, provide the `--key` argument instead.')
        c.argument('label', help="If no label specified, disable the feature flag with null label by default.")

    with self.argument_context('appconfig feature filter add') as c:
        c.argument('feature', help='Name of the feature to which you want to add the filter. If the feature flag key is different from the default key, provide the `--key` argument instead.')
        c.argument('label', help="If no label specified, add to the feature flag with null label by default.")
        c.argument('filter_name', help='Name of the filter to be added.')
        c.argument('filter_parameters', arg_type=filter_parameters_arg_type)
        c.argument('index', type=int, help='Zero-based index in the list of filters where you want to insert the new filter. If no index is specified or index is invalid, filter will be added to the end of the list.')

    with self.argument_context('appconfig feature filter update') as c:
        c.argument('feature', help='Name of the feature whose filter you want to update. If the feature flag key is different from the default key, provide the `--key` argument instead.')
        c.argument('label', help="If no label specified, update the feature flag with null label by default.")
        c.argument('filter_name', help='Name of the filter to be updated.')
        c.argument('filter_parameters', arg_type=filter_parameters_arg_type)
        c.argument('index', type=int, help='Zero-based index of the filter to be updated in case there are multiple instances with same filter name.')

    with self.argument_context('appconfig feature filter delete') as c:
        c.argument('feature', help='Name of the feature from which you want to delete the filter. If the feature flag key is different from the default key, provide the `--key` argument instead.')
        c.argument('label', help="If no label specified, delete from the feature flag with null label by default.")
        c.argument('filter_name', help='Name of the filter to be deleted.')
        c.argument('index', type=int, help='Zero-based index of the filter to be deleted in case there are multiple instances with same filter name.')
        c.argument('all_', help="Delete all filters associated with a feature flag.")

    with self.argument_context('appconfig feature filter show') as c:
        c.argument('feature', help='Name of the feature which contains the filter. If the feature flag key is different from the default key, provide the `--key` argument instead.')
        c.argument('label', help="If no label specified, show the feature flag with null label by default.")
        c.argument('filter_name', help='Name of the filter to be displayed.')
        c.argument('index', type=int, help='Zero-based index of the filter to be displayed in case there are multiple instances with same filter name.')

    with self.argument_context('appconfig feature filter list') as c:
        c.argument('feature', help='Name of the feature whose filters you want to be displayed. If the feature flag key is different from the default key, provide the `--key` argument instead.')
        c.argument('label', help="If no label specified, display filters from the feature flag with null label by default.")
        c.argument('all_', help="List all filters associated with a feature flag.")

    with self.argument_context('appconfig replica') as c:
        c.argument('store_name', arg_type=store_name_arg_type)
        c.argument('name', arg_type=replica_name_arg_type)

    with self.argument_context('appconfig replica create') as c:
        c.argument('location', arg_type=get_location_type(self.cli_ctx), help='Location at which to create the replica.')

    with self.argument_context('appconfig snapshot') as c:
        c.argument('snapshot_name', arg_type=snapshot_name_arg_type)

    with self.argument_context('appconfig snapshot create') as c:
        c.argument('filters', arg_type=snapshot_filter_arg_type)
        c.argument('composition_type', arg_type=get_enum_type(["key", "key_label"]), help='Composition type used in building App Configuration snapshots. If not specified, defaults to key.')
        c.argument('retention_period', type=int, help='Duration in seconds for which a snapshot can remain archived before expiry. A snapshot can be archived for a maximum of 7 days (604,800s) for free and developer tier stores and 90 days (7,776,000s) for standard and premium tier stores. If specified, retention period must be at least 1 hour (3600s)')
        c.argument('tags', arg_type=tags_type, help="Space-separated tags: key[=value] [key[=value] ...].")

    with self.argument_context('appconfig snapshot show') as c:
        c.argument('fields', arg_type=snapshot_fields_arg_type)

    with self.argument_context('appconfig snapshot list') as c:
        c.argument('snapshot_name', options_list=['--snapshot-name', '-s'], help='If no name specified, return all snapshots by default. Support star sign as filters, for instance abc* means snapshots with abc as prefix to the name.')
        c.argument('status', arg_type=snapshot_status_arg_type)
        c.argument('fields', arg_type=snapshot_fields_arg_type)
