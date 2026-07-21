# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
# pylint: disable=too-many-statements
# pylint: disable=too-many-locals


# pylint: disable=line-too-long
def load_arguments_eh(self, _):
    from azure.cli.core.commands.parameters import tags_type, get_enum_type, resource_group_name_type, name_type, \
        get_location_type, get_three_state_flag, get_resource_name_completion_list
    from azure.cli.core.commands.validators import get_default_location_from_resource_group
    from azure.cli.command_modules.eventhubs._completers import get_eventhubs_command_completion_list
    from azure.cli.command_modules.eventhubs._validator import validate_storageaccount, validate_partner_namespace
    from knack.arguments import CLIArgumentType
    from azure.cli.core.profiles import ResourceType
    (SkuName, TlsVersion) = self.get_models('SkuName', 'TlsVersion', resource_type=ResourceType.MGMT_EVENTHUB)
    from azure.cli.command_modules.eventhubs.action import AlertAddEncryption, ConstructPolicy, AlertAddIpRule, AlertAddVirtualNetwork, ConstructPolicyName, AlertAddlocation

    namespace_name_arg_type = CLIArgumentType(options_list=['--namespace-name'], help='Name of Namespace', id_part='name')

    with self.argument_context('eventhubs') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('namespace_name', id_part='name', help='name of Namespace')

    with self.argument_context('eventhubs namespace exists') as c:
        c.argument('name', arg_type=name_type, help='Namespace name. Name can contain only letters, numbers, and hyphens. The namespace must start with a letter, and it must end with a letter or number.')

    with self.argument_context('eventhubs namespace') as c:
        c.argument('namespace_name', arg_type=name_type, id_part='name', completer=get_resource_name_completion_list('Microsoft.eventhubs/namespaces'), help='Name of Namespace')
        c.argument('is_kafka_enabled', options_list=['--enable-kafka'], arg_type=get_three_state_flag(),
                   help='A boolean value that indicates whether Kafka is enabled for eventhub namespace.')
        c.argument('tags', arg_type=tags_type)
        c.argument('sku', options_list=['--sku'], arg_type=get_enum_type(SkuName), help='Namespace SKU.')
        c.argument('location', arg_type=get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)
        c.argument('capacity', type=int, help='Capacity for Sku')
        c.argument('is_auto_inflate_enabled', options_list=['--enable-auto-inflate'], arg_type=get_three_state_flag(), help='A boolean value that indicates whether AutoInflate is enabled for eventhub namespace.')
        c.argument('maximum_throughput_units', type=int, help='Upper limit of throughput units when AutoInflate is enabled, vaule should be within 0 to 20 throughput units. ( 0 if AutoInflateEnabled = true)')
        c.argument('zone_redundant', options_list=['--zone-redundant'], arg_type=get_three_state_flag(),
                   help='Enabling this property creates a Standard EventHubs Namespace in regions supported availability zones')
        c.argument('disable_local_auth', options_list=['--disable-local-auth'], arg_type=get_three_state_flag(),
                   help='A boolean value that indicates whether SAS authentication is enabled/disabled for the Event Hubs')
        c.argument('mi_system_assigned', arg_group='Managed Identity',
                   arg_type=get_three_state_flag(),
                   help='Enable System Assigned Identity')
        c.argument('mi_user_assigned', arg_group='Managed Identity', nargs='+', help='List of User Assigned Identity ids.')
        c.argument('encryption_config', action=AlertAddEncryption, nargs='+', help='List of KeyVaultProperties objects.')
        c.argument('geo_data_replication_config', action=AlertAddlocation, options_list=['--geo-data-replication-config', '--replica-config'], nargs='+', help='A list of regions where replicas of the namespace are maintained Object')
        c.argument('minimum_tls_version', arg_type=get_enum_type(TlsVersion), options_list=['--minimum-tls-version', '--min-tls'], help='The minimum TLS version for the cluster to support, e.g. 1.2')
        c.argument('require_infrastructure_encryption', options_list=['--infra-encryption'],
                   arg_type=get_three_state_flag(),
                   help='A boolean value that indicates whether Infrastructure Encryption (Double Encryption) is enabled/disabled')
        c.argument('public_network_access', options_list=['--public-network-access', '--public-network'],
                   arg_type=get_enum_type(['Enabled', 'Disabled']),
                   help='This determines if traffic is allowed over public network. By default it is enabled. If value is SecuredByPerimeter then Inbound and Outbound communication is controlled by the network security perimeter and profile\' access rules.')
        c.argument('alternate_name', help='Alternate name specified when alias and namespace names are same.')
        c.argument('max_replication_lag_duration_in_seconds', type=int, options_list=['--max-replication-lag-duration-in-seconds', '--max-lag'], help='The maximum acceptable lag for data replication operations from the primary replica to a quorum of secondary replicas')

    with self.argument_context('eventhubs namespace create') as c:
        c.argument('cluster_arm_id', options_list=['--cluster-arm-id'], help='Cluster ARM ID of the Namespace')

# region - Eventhub Create
    with self.argument_context('eventhubs eventhub') as c:
        c.argument('event_hub_name', arg_type=name_type, id_part='child_name_1', completer=get_eventhubs_command_completion_list, help='Name of Eventhub')

    for scope in ['eventhubs eventhub create', 'eventhubs eventhub update']:
        with self.argument_context(scope) as c:
            c.argument('partition_count', type=int, help='Number of partitions created for the Event Hub. By default, allowed values are 2-32. Lower value of 1 is supported with Kafka enabled namespaces. In presence of a custom quota, the upper limit will match the upper limit of the quota.')
            c.argument('status', arg_type=get_enum_type(['Active', 'Disabled', 'SendDisabled']), help='Status of Eventhub')
            c.argument('enable_capture', options_list=['--enable-capture'], arg_group='Capture', arg_type=get_three_state_flag(), help='A boolean value that indicates whether capture is enabled.')
            c.argument('skip_empty_archives', options_list=['--skip-empty-archives'], arg_type=get_three_state_flag(), help='A boolean value that indicates whether to Skip Empty.')
            c.argument('capture_interval', arg_group='Capture', options_list=['--capture-interval'], type=int, help='Allows you to set the frequency with which the capture to Azure Blobs will happen, value should between 60 to 900 seconds')
            c.argument('capture_size_limit', arg_group='Capture', options_list=['--capture-size-limit'], type=int, help='Defines the amount of data built up in your Event Hub before an capture operation, value should be between 10485760 to 524288000 bytes')
            c.argument('destination_name', arg_group='Capture-Destination', help='Name for capture destination, should be EventHubArchive.AzureBlockBlob.')
            c.argument('storage_account', arg_group='Capture-Destination', validator=validate_storageaccount, options_list=['--storage-account'], help='Name (if within same resource group and not of type Classic Storage) or ARM id of the storage account to be used to create the blobs')
            c.argument('blob_container', arg_group='Capture-Destination', help='Blob container Name')
            c.argument('archive_name_format', arg_group='Capture-Destination', help='Blob naming convention for archive, e.g. {Namespace}/{EventHub}/{PartitionId}/{Year}/{Month}/{Day}/{Hour}/{Minute}/{Second}. Here all the parameters (Namespace,EventHub .. etc) are mandatory irrespective of order')
            c.argument('retention_time_in_hours', type=int, arg_group='Retention-Description', options_list=['--retention-time-in-hours', '--retention-time'], help="Number of hours to retain the events for this Event Hub. This value is only used when cleanupPolicy is Delete. If cleanupPolicy is Compaction the returned value of this property is Long.MaxValue")
            c.argument('tombstone_retention_time_in_hours', type=int, arg_group='Retention-Description', options_list=['--tombstone-retention-time-in-hours', '--tombstone-time'], help="Number of hours to retain the tombstone markers of a compacted Event Hub. This value is only used when cleanupPolicy is Compaction. Consumer must complete reading the tombstone marker within this specified amount of time if consumer begins from starting offset to ensure they get a valid snapshot for the specific key described by the tombstone marker within the compacted Event Hub")
            c.argument('cleanup_policy', arg_group='Retention-Description', arg_type=get_enum_type(['Delete', 'Compact', 'DeleteOrCompact']), help="Enumerates the possible values for cleanup policy")
            c.argument('mi_system_assigned', arg_group='Capture-Destination', arg_type=get_three_state_flag(),
                       help='Enable System Assigned Identity')
            c.argument('mi_user_assigned', arg_group='Capture-Destination', help='List of User Assigned Identity ids.')
            c.argument('user_metadata', help="Gets and Sets Metadata of User.")
            c.argument('timestamp_type', arg_type=get_enum_type(['Create', 'LogAppend']), help='Denotes the type of timestamp the message will hold.')
            c.argument('min_compaction_lag_in_mins', type=int, arg_group='Retention-Description', options_list=['--min-lag', '--min-compaction-lag-in-mins'], help="The minimum time a message will remain ineligible for compaction in the log. This value is used when cleanupPolicy is Compact or DeleteOrCompact.")
            c.argument('encoding', arg_group='Capture', options_list=['encoding'], help='Enumerates the possible values for the encoding format of capture description. Note: \'AvroDeflate\' will be deprecated in New API Version')
    with self.argument_context('eventhubs eventhub list') as c:
        c.argument('namespace_name', options_list=['--namespace-name'], id_part=None, help='Name of Namespace')

# Region Geo DR Configuration
    with self.argument_context('eventhubs georecovery-alias set') as c:
        c.argument('partner_namespace', required=True, validator=validate_partner_namespace, help='Name (if within the same resource group) or ARM Id of the Primary/Secondary eventhub namespace name, which is part of GEO DR pairing')
        c.argument('alternate_name', help='Alternate Name for the Alias, when the Namespace name and Alias name are same')
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('namespace_name', options_list=['--namespace-name'], id_part='name', help='Name of Namespace')
        c.argument('alias', options_list=['--alias', '-a'],
                   help='Name of the Geo-Disaster Recovery Configuration Alias')

# Region Namespace NetworkRuleSet
    with self.argument_context('eventhubs namespace network-rule-set') as c:
        c.argument('namespace_name', options_list=['--namespace-name', '--name', '-n'], id_part=None, help='Name of the Namespace')

    for scope in ['eventhubs namespace network-rule-set ip-rule add', 'eventhubs namespace network-rule-set ip-rule remove']:
        with self.argument_context(scope) as c:
            c.argument('ip_rule', action=AlertAddIpRule, nargs='+', help='List VirtualNetwork Rules.')
            c.argument('namespace_name', options_list=['--namespace-name', '--name', '-n'], id_part=None, help='Name of the Namespace')

    for scope in ['eventhubs namespace network-rule-set virtual-network-rule add', 'eventhubs namespace network-rule-set virtual-network-rule remove']:
        with self.argument_context(scope) as c:
            c.argument('namespace_name', options_list=['--namespace-name', '--name', '-n'], id_part=None, help='Name of the Namespace')
            c.argument('subnet', action=AlertAddVirtualNetwork, nargs='+', help='List VirtualNetwork Rules.')

# Private end point connection
    with self.argument_context('eventhubs namespace private-endpoint-connection',
                               resource_type=ResourceType.MGMT_EVENTHUB) as c:
        c.argument('namespace_name', options_list=['--namespace-name'], id_part=None, help='Name of the Namespace')
        c.argument('private_endpoint_connection_name', options_list=['--name', '-n'],
                   help='The name of the private endpoint connection associated with the EventHubs Namespace.')
    for item in ['approve', 'reject', 'show', 'delete']:
        with self.argument_context('eventhubs namespace private-endpoint-connection {}'.format(item),
                                   resource_type=ResourceType.MGMT_EVENTHUB) as c:
            c.argument('private_endpoint_connection_name', options_list=['--name', '-n'], required=False,
                       help='The name of the private endpoint connection associated with the EventHubs Namespace.')
            c.extra('connection_id', options_list=['--id'],
                    help='The ID of the private endpoint connection associated with the EventHubs Namespace. You can get '
                         'it using `az eventhubs namespace show`.')
            c.argument('namespace_name', help='The eventhubs namesapce name.', required=False)
            c.argument('resource_group_name', help='The resource group name of specified eventhubs namespace.',
                       required=False)
            c.argument('description', help='Comments for {} operation.'.format(item))

# Private end point connection
    with self.argument_context('eventhubs namespace private-link-resource',
                               resource_type=ResourceType.MGMT_EVENTHUB) as c:
        c.argument('namespace_name', options_list=['--namespace-name'], id_part=None, help='Name of the Namespace')

# Identity
    with self.argument_context('eventhubs namespace identity',
                               resource_type=ResourceType.MGMT_EVENTHUB) as c:
        c.argument('namespace_name', options_list=['--namespace-name'], id_part=None, help='Name of the Namespace')

    for scope in ['eventhubs namespace identity assign', 'eventhubs namespace identity remove']:
        with self.argument_context(scope, resource_type=ResourceType.MGMT_EVENTHUB) as c:
            c.argument('namespace_name', options_list=['--namespace-name'], id_part=None, help='Name of the Namespace')
            c.argument('system_assigned', arg_type=get_three_state_flag(), help='System Assigned Identity')
            c.argument('user_assigned', nargs='+', help='User Assigned Identity')

# Encryption
    with self.argument_context('eventhubs namespace encryption', resource_type=ResourceType.MGMT_EVENTHUB) as c:
        c.argument('namespace_name', options_list=['--namespace-name'], id_part=None, help='Name of the Namespace')

    for scope in ['eventhubs namespace encryption add', 'eventhubs namespace encryption remove']:
        with self.argument_context(scope, resource_type=ResourceType.MGMT_EVENTHUB) as c:
            c.argument('encryption_config', action=AlertAddEncryption, nargs='+', help='List of KeyVaultProperties objects.')
            c.argument('require_infrastructure_encryption', options_list=['--infra-encryption'],
                       arg_type=get_three_state_flag(),
                       help='A boolean value that indicates whether Infrastructure Encryption (Double Encryption) is enabled/disabled')
# Location
    with self.argument_context('eventhubs namespace replica', resource_type=ResourceType.MGMT_EVENTHUB) as c:
        c.argument('namespace_name', options_list=['--namespace-name'], id_part=None, help='Name of the Namespace')

    for scope in ['eventhubs namespace replica add', 'eventhubs namespace replica remove']:
        with self.argument_context(scope, resource_type=ResourceType.MGMT_EVENTHUB) as c:
            c.argument('geo_data_replication_config', action=AlertAddlocation, nargs='+',
                       help='A list of regions where replicas of the namespace are maintained Object')

# Application Group
    with self.argument_context('eventhubs namespace application-group') as c:
        c.argument('namespace_name', options_list=['--namespace-name'], arg_type=namespace_name_arg_type, help='Name of Namespace')
        c.argument('application_group_name', arg_type=name_type, id_part='child_name_1', help='Name of Application Group')

    for scope in ['eventhubs namespace application-group create', 'eventhubs namespace application-group list']:
        with self.argument_context(scope) as c:
            c.argument('namespace_name', options_list=['--namespace-name'], id_part=None, help='Name of Namespace')
            c.argument('application_group_name', arg_type=name_type, id_part=None, help='Name of Application Group')

    for scope in ['eventhubs namespace application-group create', 'eventhubs namespace application-group update']:
        with self.argument_context(scope) as c:
            c.argument('is_enabled', arg_type=get_three_state_flag(),
                       help='Determines if Application Group is allowed to create connection with namespace or not. '
                            'Once the isEnabled is set to false, all the existing connections of application group gets dropped and no new connections will be allowed')

    with self.argument_context('eventhubs namespace application-group create') as c:
        c.argument('client_app_group_identifier', options_list=['--client-app-group-identifier', '--client-app-group-id'], help='The Unique identifier for application group.Supports SAS(NamespaceSASKeyName=KeyName or EntitySASKeyName=KeyName) or AAD(AADAppID=Guid)')

    for scope in ['eventhubs namespace application-group create', 'eventhubs namespace application-group policy add']:
        with self.argument_context(scope) as c:
            c.argument('throttling_policy_config', action=ConstructPolicy, options_list=['--throttling-policy-config', '--throttling-policy', '--policy-config'], nargs='+', help='List of Throttling Policy Objects')

    with self.argument_context('eventhubs namespace application-group policy remove') as c:
        c.argument('policy', action=ConstructPolicyName, nargs='+', help='List of Throttling Policy Objects')
