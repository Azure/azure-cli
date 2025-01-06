# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
# pylint: disable=too-many-statements

from azure.cli.core.commands.parameters import tags_type, get_enum_type, resource_group_name_type, name_type, \
    get_location_type, get_three_state_flag, get_resource_name_completion_list
from azure.cli.core.commands.validators import get_default_location_from_resource_group
from azure.cli.command_modules.servicebus.action import AlertAddEncryption, AlertAddIpRule, AlertAddVirtualNetwork
from azure.cli.core.profiles import ResourceType


def load_arguments_sb(self, _):
    from azure.cli.command_modules.servicebus._completers import get_rules_command_completion_list
    from azure.cli.command_modules.servicebus._validators import _validate_auto_delete_on_idle, \
        _validate_duplicate_detection_history_time_window, \
        _validate_default_message_time_to_live, \
        _validate_lock_duration, validate_partner_namespace, validate_premiumsku_capacity
    from azure.cli.command_modules.servicebus.action import AlertAddlocation

    (SkuName, FilterType, TlsVersion) = self.get_models('SkuName', 'FilterType', 'TlsVersion', resource_type=ResourceType.MGMT_SERVICEBUS)

    with self.argument_context('servicebus') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('namespace_name', options_list=['--namespace-name'], id_part='name', help='Name of Namespace')

    with self.argument_context('servicebus namespace') as c:
        c.argument('namespace_name', id_part='name', arg_type=name_type, completer=get_resource_name_completion_list('Microsoft.ServiceBus/namespaces'), help='Name of Namespace')
        c.argument('tags', arg_type=tags_type)
        c.argument('sku', arg_type=get_enum_type(SkuName), help='Namespace SKU.')
        c.argument('tier', arg_type=get_enum_type(SkuName), help='The billing tier of this particular SKU.')
        c.argument('disable_local_auth', options_list=['--disable-local-auth'], arg_type=get_three_state_flag(),
                   help='A boolean value that indicates whether SAS authentication is enabled/disabled for the Service Bus')
        c.argument('capacity', type=int, choices=[1, 2, 4, 8, 16], help='Number of message units. This property is only applicable to namespaces of Premium SKU', validator=validate_premiumsku_capacity)
        c.argument('mi_system_assigned', arg_group='Managed Identity', arg_type=get_three_state_flag(),
                   help='Enable System Assigned Identity')
        c.argument('mi_user_assigned', arg_group='Managed Identity', nargs='+', help='List of User Assigned Identity ids.')
        c.argument('encryption_config', action=AlertAddEncryption, nargs='+',
                   help='List of KeyVaultProperties objects.')
        c.argument('minimum_tls_version', options_list=['--minimum-tls-version', '--min-tls'], arg_type=get_enum_type(TlsVersion),
                   help='The minimum TLS version for the cluster to support, e.g. 1.2')
        c.argument('require_infrastructure_encryption', options_list=['--infra-encryption'],
                   arg_type=get_three_state_flag(),
                   help='A boolean value that indicates whether Infrastructure Encryption (Double Encryption)')
        c.argument('public_network_access', options_list=['--public-network-access', '--public-network'],
                   arg_type=get_enum_type(['Enabled', 'Disabled']),
                   help='This determines if traffic is allowed over public network. By default it is enabled. If value is SecuredByPerimeter then Inbound and Outbound communication is controlled by the network security perimeter and profile\' access rules.')
        c.argument('premium_messaging_partitions', options_list=['--premium-messaging-partitions', '--premium-partitions'], is_preview=True, type=int, help='The number of partitions of a Service Bus namespace. This property is only applicable to Premium SKU namespaces. The default value is 1 and possible values are 1, 2 and 4')
        c.argument('alternate_name', help='Alternate name specified when alias and namespace names are same.')
        c.argument('geo_data_replication_config', action=AlertAddlocation, nargs='+', options_list=['--geo-data-replication-config', '--replica-config'],
                   help='A list of regions where replicas of the namespace are maintained Object')
        c.argument('max_replication_lag_duration_in_seconds', type=int, options_list=['--max-replication-lag-duration-in-seconds', '--max-lag'],
                   help='The maximum acceptable lag for data replication operations from the primary replica to a quorum of secondary replicas')

    with self.argument_context('servicebus namespace create') as c:
        c.argument('location', arg_type=get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)
        c.argument('zone_redundant', options_list=['--zone-redundant'], arg_type=get_three_state_flag(),
                   help='Enabling this property creates a ServiceBus Zone Redundant Namespace in regions supported availability zones')

# Region Subscription Rules
    with self.argument_context('servicebus topic subscription rule') as c:
        c.argument('rule_name', arg_type=name_type, id_part='child_name_3', completer=get_rules_command_completion_list, help='Name of Rule')
        c.argument('subscription_name', options_list=['--subscription-name'], id_part='child_name_2', help='Name of Subscription')
        c.argument('topic_name', options_list=['--topic-name'], id_part='child_name_1', help='Name of Topic')

    for scope in ['servicebus topic subscription rule create', 'servicebus topic subscription rule update']:
        with self.argument_context(scope, arg_group='Action') as c:
            c.argument('filter_type', arg_type=get_enum_type(FilterType), help='Rule Filter types')
            c.argument('action_sql_expression', help='Action SQL expression.')
            c.argument('action_compatibility_level', type=int, help='This property is reserved for future use. An integer value showing the compatibility level, currently hard-coded to 20.')
            c.argument('action_requires_preprocessing', options_list=['--enable-action-preprocessing'], arg_type=get_three_state_flag(), help='A boolean value that indicates whether the rule action requires preprocessing.')
        with self.argument_context(scope, arg_group='SQL Filter') as c:
            c.argument('filter_sql_expression', help='SQL expression. e.g. myproperty=test')
            c.argument('filter_requires_preprocessing', options_list=['--enable-sql-preprocessing'], arg_type=get_three_state_flag(), help='A boolean value that indicates whether the rule action requires preprocessing.')
        with self.argument_context(scope, arg_group='Correlation Filter') as c:
            c.argument('correlation_id', help='Identifier of correlation.')
            c.argument('message_id', help='Identifier of message.')
            c.argument('to', help='Address to send to.')
            c.argument('reply_to', help='Address of the queue to reply to.')
            c.argument('label', help='Application specific label.')
            c.argument('session_id', help='Session identifier')
            c.argument('reply_to_session_id', help='Session identifier to reply to.')
            c.argument('content_type', help='Content type of message.')
            c.argument('requires_preprocessing', options_list=['--enable-correlation-preprocessing'], arg_type=get_three_state_flag(), help='A boolean value that indicates whether the rule action requires preprocessing.')
            c.argument('tags', options_list=['--correlation-filter-property', '--correlation-filter'], arg_type=tags_type, help='dictionary object for custom filters')

    with self.argument_context('servicebus topic subscription rule list') as c:
        c.argument('subscription_name', options_list=['--subscription-name'], id_part=None, help='Name of Subscription')
        c.argument('topic_name', options_list=['--topic-name'], id_part=None, help='Name of Topic')
        c.argument('namespace_name', options_list=['--namespace-name'], id_part=None, help='Name of Namespace')

# Geo DR - Disaster Recovery Configs - Alias  : Region
    with self.argument_context('servicebus georecovery-alias set') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('namespace_name', options_list=['--namespace-name'], id_part='name', help='Name of Namespace')
        c.argument('alias', options_list=['--alias', '-a'], help='Name of the Geo-Disaster Recovery Configuration Alias')
        c.argument('partner_namespace', required=True, options_list=['--partner-namespace'], validator=validate_partner_namespace, help='Name (if within the same resource group) or ARM Id of Primary/Secondary Service Bus  namespace name, which is part of GEO DR pairing')
        c.argument('alternate_name', help='Alternate Name (Post failover) for Primary Namespace, when Namespace name and Alias name are same')

# Region Namespace NetworkRuleSet
    with self.argument_context('servicebus namespace network-rule-set') as c:
        c.argument('namespace_name', options_list=['--namespace-name', '--name', '-n'], id_part=None,
                   help='Name of the Namespace')
    for scope in ['servicebus namespace network-rule-set ip-rule add', 'servicebus namespace network-rule-set ip-rule remove']:
        with self.argument_context(scope) as c:
            c.argument('ip_rule', action=AlertAddIpRule, nargs='+', help='List VirtualNetwork Rules.')
            c.argument('namespace_name', options_list=['--namespace-name', '--name', '-n'], id_part=None,
                       help='Name of the Namespace')
    for scope in ['servicebus namespace network-rule-set virtual-network-rule add', 'servicebus namespace network-rule-set virtual-network-rule remove']:
        with self.argument_context(scope) as c:
            c.argument('namespace_name', options_list=['--namespace-name', '--name', '-n'], id_part=None,
                       help='Name of the Namespace')
            c.argument('subnet', action=AlertAddVirtualNetwork, nargs='+', help='List VirtualNetwork Rules.')
            c.argument('namespace_name', options_list=['--namespace-name'], id_part=None, help='Name of the Namespace')

# Private end point connection
    with self.argument_context('servicebus namespace private-endpoint-connection') as c:
        c.argument('namespace_name', options_list=['--namespace-name'], id_part=None, help='Name of the Namespace')
        c.argument('private_endpoint_connection_name', options_list=['--name', '-n'],
                   help='The name of the private endpoint connection associated with the Service bus Namespace.')
    for item in ['approve', 'reject', 'show', 'delete']:
        with self.argument_context('servicebus namespace private-endpoint-connection {}'.format(item)) as c:
            c.argument('private_endpoint_connection_name', options_list=['--name', '-n'], required=False,
                       help='The name of the private endpoint connection associated with the Service Bus Namespace.')
            c.extra('connection_id', options_list=['--id'],
                    help='The ID of the private endpoint connection associated with the Service Bus Namespace. You can get '
                         'it using `az servicebus namespace show`.')
            c.argument('namespace_name', help='The Service Bus namesapce name.', required=False)
            c.argument('resource_group_name', help='The resource group name of specified Service bus namespace.',
                       required=False)
            c.argument('description', help='Comments for {} operation.'.format(item))

# Private end point connection
    with self.argument_context('servicebus namespace private-link-resource') as c:
        c.argument('namespace_name', options_list=['--namespace-name'], id_part=None, help='Name of the Namespace')
# Identity
    with self.argument_context('servicebus namespace identity',
                               resource_type=ResourceType.MGMT_SERVICEBUS) as c:
        c.argument('namespace_name', options_list=['--namespace-name'], id_part=None, help='Name of the Namespace')

    for scope in ['servicebus namespace identity assign', 'servicebus namespace identity remove']:
        with self.argument_context(scope, resource_type=ResourceType.MGMT_SERVICEBUS) as c:
            c.argument('namespace_name', options_list=['--namespace-name'], id_part=None, help='Name of the Namespace')
            c.argument('system_assigned', arg_type=get_three_state_flag(), help='System Assigned Identity')
            c.argument('user_assigned', nargs='+', help='User Assigned Identity')

# Encryption
    with self.argument_context('servicebus namespace encryption', resource_type=ResourceType.MGMT_SERVICEBUS) as c:
        c.argument('namespace_name', options_list=['--namespace-name'], id_part=None, help='Name of the Namespace')

    for scope in ['servicebus namespace encryption add', 'servicebus namespace encryption remove']:
        with self.argument_context(scope, resource_type=ResourceType.MGMT_SERVICEBUS) as c:
            c.argument('encryption_config', action=AlertAddEncryption, nargs='+', help='List of KeyVaultProperties objects.')
            c.argument('require_infrastructure_encryption', options_list=['--infra-encryption'],
                       arg_type=get_three_state_flag(),
                       help='A boolean value that indicates whether Infrastructure Encryption (Double Encryption)')

# Location
    with self.argument_context('servicebus namespace replica', resource_type=ResourceType.MGMT_SERVICEBUS) as c:
        c.argument('namespace_name', options_list=['--namespace-name'], id_part=None, help='Name of the Namespace')

    for scope in ['servicebus namespace replica add', 'servicebus namespace replica remove']:
        with self.argument_context(scope, resource_type=ResourceType.MGMT_SERVICEBUS) as c:
            c.argument('geo_data_replication_config', action=AlertAddlocation, nargs='+',
                       help='A list of regions where replicas of the namespace are maintained Object')
