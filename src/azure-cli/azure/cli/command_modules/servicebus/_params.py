# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
# pylint: disable=too-many-statements

from azure.cli.core.commands.parameters import tags_type, get_enum_type, resource_group_name_type, name_type,\
    get_location_type, get_three_state_flag, get_resource_name_completion_list
from azure.cli.core.commands.validators import get_default_location_from_resource_group
from azure.cli.command_modules.servicebus.action import AlertAddEncryption
from azure.cli.core.profiles import ResourceType


def load_arguments_sb(self, _):
    from azure.cli.command_modules.servicebus._completers import get_queue_command_completion_list, \
        get_rules_command_completion_list, get_subscriptions_command_completion_list, get_topic_command_completion_list
    from azure.cli.command_modules.servicebus._validators import _validate_auto_delete_on_idle, \
        _validate_duplicate_detection_history_time_window, \
        _validate_default_message_time_to_live, \
        _validate_lock_duration, validate_partner_namespace, validate_premiumsku_capacity

    (SkuName, FilterType, TlsVersion) = self.get_models('SkuName', 'FilterType', 'TlsVersion', resource_type=ResourceType.MGMT_SERVICEBUS)

    with self.argument_context('servicebus') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('namespace_name', options_list=['--namespace-name'], id_part='name', help='Name of Namespace')

    with self.argument_context('servicebus namespace') as c:
        c.argument('namespace_name', id_part='name', arg_type=name_type, completer=get_resource_name_completion_list('Microsoft.ServiceBus/namespaces'), help='Name of Namespace')
        c.argument('tags', arg_type=tags_type)
        c.argument('sku', arg_type=get_enum_type(SkuName), help='Namespace SKU.')
        c.argument('tier', arg_type=get_enum_type(SkuName), help='The billing tier of this particular SKU.')
        c.argument('disable_local_auth', options_list=['--disable-local-auth'], is_preview=True, arg_type=get_three_state_flag(),
                   help='A boolean value that indicates whether SAS authentication is enabled/disabled for the Service Bus')
        c.argument('capacity', type=int, choices=[1, 2, 4, 8, 16], help='Number of message units. This property is only applicable to namespaces of Premium SKU', validator=validate_premiumsku_capacity)
        c.argument('mi_system_assigned', arg_group='Managed Identity', arg_type=get_three_state_flag(),
                   help='Enable System Assigned Identity')
        c.argument('mi_user_assigned', arg_group='Managed Identity', nargs='+', help='List of User Assigned Identity ids.')
        c.argument('encryption_config', action=AlertAddEncryption, nargs='+',
                   help='List of KeyVaultProperties objects.')
        c.argument('minimum_tls_version', options_list=['--minimum-tls-version', '--min-tls'], arg_type=get_enum_type(TlsVersion),
                   help='The minimum TLS version for the cluster to support, e.g. 1.2')
        c.argument('require_infrastructure_encryption', options_list=['--infra-encryption'], is_preview=True,
                   arg_type=get_three_state_flag(),
                   help='A boolean value that indicates whether Infrastructure Encryption (Double Encryption)')
        c.argument('public_network_access', options_list=['--public-network-access', '--public-network'],
                   arg_type=get_enum_type(['Enabled', 'Disabled']),
                   help='This determines if traffic is allowed over public network. By default it is enabled. If value is SecuredByPerimeter then Inbound and Outbound communication is controlled by the network security perimeter and profile\' access rules.')
        c.argument('premium_messaging_partitions', options_list=['--premium-messaging-partitions', '--premium-partitions'], type=int, help='The number of partitions of a Service Bus namespace. This property is only applicable to Premium SKU namespaces. The default value is 1 and possible values are 1, 2 and 4')
        c.argument('alternate_name', help='Alternate name specified when alias and namespace names are same.')

    with self.argument_context('servicebus namespace create') as c:
        c.argument('location', arg_type=get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)
        c.argument('zone_redundant', options_list=['--zone-redundant'], is_preview=True, arg_type=get_three_state_flag(),
                   help='Enabling this property creates a ServiceBus Zone Redundant Namespace in regions supported availability zones')

    # region Queue
    with self.argument_context('servicebus queue') as c:
        c.argument('queue_name', arg_type=name_type, id_part='child_name_1', completer=get_queue_command_completion_list, help='Name of Queue')

    # region - Queue Create
    for scope in ['create', 'update']:
        with self.argument_context('servicebus queue {}'.format(scope)) as c:
            c.argument('queue_name', arg_type=name_type, id_part='child_name_1', help='Name of Queue')
            c.argument('lock_duration', validator=_validate_lock_duration, help='String ISO 8601 timespan or duration format for duration of a peek-lock; that is, the amount of time that the message is locked for other receivers. The maximum value for LockDuration is 5 minutes; the default value is 1 minute.')
            c.argument('max_size_in_megabytes', options_list=['--max-size'], type=int, choices=[1024, 2048, 3072, 4096, 5120, 10240, 20480, 40960, 81920], help='Maximum size of queue in megabytes, which is the size of the memory allocated for the queue. Default is 1024. Max for Standard SKU is 5120 and for Premium SKU is 81920')
            c.argument('max_message_size_in_kilobytes', options_list=['--max-message-size', '--max-message-size-in-kilobytes'], type=int, help='Maximum size (in KB) of the message payload that can be accepted by the queue. This property is only used in Premium today and default is 1024.')
            c.argument('requires_duplicate_detection', options_list=['--enable-duplicate-detection'], arg_type=get_three_state_flag(), help='A boolean value indicating if this queue requires duplicate detection.')
            c.argument('requires_session', options_list=['--enable-session'], arg_type=get_three_state_flag(), help='A boolean value indicating whether the queue supports the concept of sessions.')
            c.argument('default_message_time_to_live', validator=_validate_default_message_time_to_live, help='ISO 8601 timespan or duration time format for default message to live value. This is the duration after which the message expires, starting from when the message is sent to Service Bus. This is the default value used when TimeToLive is not set on a message itself.')
            c.argument('dead_lettering_on_message_expiration', options_list=['--enable-dead-lettering-on-message-expiration'], arg_type=get_three_state_flag(), help='A boolean value that indicates whether this queue has dead letter support when a message expires.')
            c.argument('duplicate_detection_history_time_window', validator=_validate_duplicate_detection_history_time_window, help='ISO 8601 timeSpan structure that defines the duration of the duplicate detection history. The default value is 10 minutes.')
            c.argument('max_delivery_count', type=int, help='The maximum delivery count. A message is automatically deadlettered after this number of deliveries. default value is 10.')
            c.argument('status', arg_type=get_enum_type(['Active', 'Disabled', 'SendDisabled', 'ReceiveDisabled']), help='Enumerates the possible values for the status of a messaging entity.')
            c.argument('auto_delete_on_idle', validator=_validate_auto_delete_on_idle, help='ISO 8601 timeSpan or duration time format for idle interval after which the queue is automatically deleted. The minimum duration is 5 minutes.')
            c.argument('enable_partitioning', arg_type=get_three_state_flag(), help='A boolean value that indicates whether the queue is to be partitioned across multiple message brokers.')
            c.argument('enable_express', arg_type=get_three_state_flag(), help='A boolean value that indicates whether Express Entities are enabled. An express queue holds a message in memory temporarily before writing it to persistent storage.')
            c.argument('forward_to', help='Queue/Topic name to forward the messages')
            c.argument('forward_dead_lettered_messages_to', help='Queue/Topic name to forward the Dead Letter message')
            c.argument('enable_batched_operations', arg_type=get_three_state_flag(), help='Allow server-side batched operations.')

    with self.argument_context('servicebus queue update') as c:
        c.argument('enable_partitioning', arg_type=get_three_state_flag(),
                   help='A boolean value that indicates whether the queue is to be partitioned across multiple message brokers.', deprecate_info=c.deprecate(hide=True, expiration='2.49.0'))
        c.argument('requires_session', options_list=['--enable-session'], arg_type=get_three_state_flag(), help='A boolean value indicating whether the queue supports the concept of sessions.', deprecate_info=c.deprecate(hide=True, expiration='2.49.0'))
        c.argument('requires_duplicate_detection', options_list=['--enable-duplicate-detection'],
                   arg_type=get_three_state_flag(),
                   help='A boolean value indicating if this queue requires duplicate detection.', deprecate_info=c.deprecate(hide=True, expiration='2.49.0'))

    with self.argument_context('servicebus queue list') as c:
        c.argument('namespace_name', id_part=None, options_list=['--namespace-name'], help='Name of Namespace')

    # region - Topic
    for scope in ['servicebus topic show', 'servicebus topic delete']:
        with self.argument_context(scope) as c:
            c.argument('topic_name', arg_type=name_type, id_part='child_name_1', completer=get_topic_command_completion_list, help='Name of Topic')

    # region - Topic Create
    for scope in ['create', 'update']:
        with self.argument_context('servicebus topic {}'.format(scope)) as c:
            c.argument('topic_name', arg_type=name_type, id_part='child_name_1', completer=get_topic_command_completion_list, help='Name of Topic')
            c.argument('default_message_time_to_live', validator=_validate_default_message_time_to_live, help='ISO 8601 or duration time format for Default message timespan to live value. This is the duration after which the message expires, starting from when the message is sent to Service Bus. This is the default value used when TimeToLive is not set on a message itself.')
            c.argument('max_size_in_megabytes', options_list=['--max-size'], type=int, choices=[1024, 2048, 3072, 4096, 5120, 10240, 20480, 40960, 81920], help='Maximum size of topic in megabytes, which is the size of the memory allocated for the topic. Default is 1024. Max for Standard SKU is 5120 and for Premium SKU is 81920')
            c.argument('requires_duplicate_detection', options_list=['--enable-duplicate-detection'], arg_type=get_three_state_flag(), help='A boolean value indicating if this topic requires duplicate detection.')
            c.argument('duplicate_detection_history_time_window', validator=_validate_duplicate_detection_history_time_window, help='ISO 8601 timespan or duration time format for structure that defines the duration of the duplicate detection history. The default value is 10 minutes.')
            c.argument('enable_batched_operations', arg_type=get_three_state_flag(), help='Allow server-side batched operations.')
            c.argument('status', arg_type=get_enum_type(['Active', 'Disabled', 'SendDisabled']), help='Enumerates the possible values for the status of a messaging entity.')
            c.argument('support_ordering', options_list=['--enable-ordering'], arg_type=get_three_state_flag(), help='A boolean value that indicates whether the topic supports ordering.')
            c.argument('auto_delete_on_idle', validator=_validate_auto_delete_on_idle, help='ISO 8601 timespan or duration time format for idle interval after which the topic is automatically deleted. The minimum duration is 5 minutes.')
            c.argument('enable_partitioning', arg_type=get_three_state_flag(), help='A boolean value that indicates whether the topic to be partitioned across multiple message brokers is enabled.')
            c.argument('enable_express', arg_type=get_three_state_flag(), help='A boolean value that indicates whether Express Entities are enabled. An express topic holds a message in memory temporarily before writing it to persistent storage.')
            c.argument('max_message_size_in_kilobytes', options_list=['--max-message-size', '--max-message-size-in-kilobytes'], type=int, help='Maximum size (in KB) of the message payload that can be accepted by the queue. This property is only used in Premium today and default is 1024.')

    for scope in ['servicebus topic show', 'servicebus topic delete']:
        with self.argument_context(scope) as c:
            c.argument('topic_name', arg_type=name_type, id_part='child_name_1', completer=get_topic_command_completion_list, help='Name of Topic')

    with self.argument_context('servicebus topic list') as c:
        c.argument('namespace_name', id_part=None, options_list=['--namespace-name'], help='Name of Namespace')

    with self.argument_context('servicebus topic subscription') as c:
        c.argument('subscription_name', arg_type=name_type, id_part='child_name_2', completer=get_subscriptions_command_completion_list, help='Name of Subscription')
        c.argument('topic_name', id_part='child_name_1', options_list=['--topic-name'], help='Name of Topic')

    # region - Subscription Create and update
    for scope in ['create', 'update']:
        with self.argument_context('servicebus topic subscription {}'.format(scope)) as c:
            c.argument('lock_duration', validator=_validate_lock_duration, help='ISO 8601 or duration format (day:minute:seconds) for lock duration timespan for the subscription. The default value is 1 minute.')
            c.argument('requires_session', options_list=['--enable-session'], arg_type=get_three_state_flag(), help='A boolean value indicating if a subscription supports the concept of sessions.')
            c.argument('default_message_time_to_live', validator=_validate_default_message_time_to_live, help='ISO 8601 or duration time format for Default message timespan to live value. This is the duration after which the message expires, starting from when the message is sent to Service Bus. This is the default value used when TimeToLive is not set on a message itself.')
            c.argument('dead_lettering_on_message_expiration', options_list=['--enable-dead-lettering-on-message-expiration'], arg_type=get_three_state_flag(), help='A boolean Value that indicates whether a subscription has dead letter support when a message expires.')
            c.argument('max_delivery_count', type=int, help='Number of maximum deliveries.')
            c.argument('status', arg_type=get_enum_type(['Active', 'Disabled', 'SendDisabled', 'ReceiveDisabled']), help='Enumerates the possible values for the status of a messaging entity.')
            c.argument('enable_batched_operations', arg_type=get_three_state_flag(), help='Allow server-side batched operations.')
            c.argument('auto_delete_on_idle', validator=_validate_auto_delete_on_idle, options_list=['--auto-delete-on-idle'], help='ISO 8601 timeSpan  or duration time format for idle interval after which the subscription is automatically deleted. The minimum duration is 5 minutes.')
            c.argument('forward_to', help='Queue/Topic name to forward the messages')
            c.argument('forward_dead_lettered_messages_to', help='Queue/Topic name to forward the Dead Letter message')
            c.argument('dead_lettering_on_filter_evaluation_exceptions', options_list=['--dead-letter-on-filter-exceptions'], arg_type=get_three_state_flag(), help='Allow dead lettering when filter evaluation exceptions occur.')

    with self.argument_context('servicebus topic subscription create') as c:
        c.argument('is_client_affine', arg_type=get_three_state_flag(), help='Value that indicates whether the subscription has an affinity to the client id.')
        c.argument('client_id', help='Indicates the Client ID of the application that created the client-affine subscription.')
        c.argument('is_shared', arg_type=get_three_state_flag(), help='For client-affine subscriptions, this value indicates whether the subscription is shared or not.')
        c.argument('is_durable', arg_type=get_three_state_flag(), help='For client-affine subscriptions, this value indicates whether the subscription is durable or not.')

    with self.argument_context('servicebus topic subscription list') as c:
        c.argument('namespace_name', options_list=['--namespace-name'], id_part=None, help='Name of Namespace')
        c.argument('topic_name', options_list=['--topic-name'], id_part=None, help='Name of Topic')

    # Region Subscription Rules
    # Region Rules Create

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
    with self.argument_context('servicebus georecovery-alias exists') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('namespace_name', options_list=['--namespace-name'], id_part='name', help='Name of Namespace')
        c.argument('name', options_list=['--alias', '-a'], arg_type=name_type, help='Name of Geo-Disaster Recovery Configuration Alias to check availability')

    with self.argument_context('servicebus georecovery-alias') as c:
        c.argument('alias', options_list=['--alias', '-a'], id_part='child_name_1', help='Name of the Geo-Disaster Recovery Configuration Alias')

    with self.argument_context('servicebus georecovery-alias set') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('namespace_name', options_list=['--namespace-name'], id_part='name', help='Name of Namespace')
        c.argument('alias', options_list=['--alias', '-a'], help='Name of the Geo-Disaster Recovery Configuration Alias')
        c.argument('partner_namespace', required=True, options_list=['--partner-namespace'], validator=validate_partner_namespace, help='Name (if within the same resource group) or ARM Id of Primary/Secondary Service Bus  namespace name, which is part of GEO DR pairing')
        c.argument('alternate_name', help='Alternate Name (Post failover) for Primary Namespace, when Namespace name and Alias name are same')

    for scope in ['servicebus georecovery-alias authorization-rule show', 'servicebus georecovery-alias authorization-rule keys list']:
        with self.argument_context(scope)as c:
            c.argument('authorization_rule_name', arg_type=name_type, id_part='child_name_2', help='name of Namespace Authorization Rule')

    with self.argument_context('servicebus georecovery-alias list') as c:
        c.argument('namespace_name', options_list=['--namespace-name'], id_part=None, help='Name of Namespace')

    with self.argument_context('servicebus georecovery-alias fail-over') as c:
        c.argument('parameters', options_list=['--parameters'], deprecate_info=c.deprecate(expiration='2.49.0'), help='Parameters required to create an Alias(Disaster Recovery configuration). Is either a FailoverProperties type or a IO type. Default value is None.')

    with self.argument_context('servicebus georecovery-alias authorization-rule list') as c:
        c.argument('alias', options_list=['--alias', '-a'], help='Name of Geo-Disaster Recovery Configuration Alias')
        c.argument('namespace_name', options_list=['--namespace-name'], id_part=None, help='Name of Namespace')

    with self.argument_context('servicebus georecovery-alias authorization-rule keys list') as c:
        c.argument('alias', options_list=['--alias', '-a'], id_part=None, help='Name of Geo-Disaster Recovery Configuration Alias')
        c.argument('namespace_name', options_list=['--namespace-name'], id_part=None, help='Name of Namespace')
        c.argument('authorization_rule_name', arg_type=name_type, help='Name of Namespace AuthorizationRule')

# Region Namespace NetworkRuleSet
    with self.argument_context('servicebus namespace network-rule') as c:
        c.argument('namespace_name', options_list=['--namespace-name'], id_part=None, help='Name of the Namespace')

    for scope in ['servicebus namespace network-rule add', 'servicebus namespace network-rule remove']:
        with self.argument_context(scope) as c:
            c.argument('subnet', arg_group='Virtual Network Rule', options_list=['--subnet'], help='Name or ID of subnet. If name is supplied, `--vnet-name` must be supplied.')
            c.argument('ip_mask', arg_group='IP Address Rule', options_list=['--ip-address'], help='IPv4 address or CIDR range.', deprecate_info=c.deprecate(redirect='--ip-rule', expiration='2.49.0'))
            c.argument('namespace_name', options_list=['--namespace-name'], id_part=None, help='Name of the Namespace')
            c.extra('vnet_name', arg_group='Virtual Network Rule', options_list=['--vnet-name'], help='Name of the Virtual Network', deprecate_info=c.deprecate(expiration='2.49.0'))

    with self.argument_context('servicebus namespace network-rule update', resource_type=ResourceType.MGMT_SERVICEBUS,
                               min_api='2017-04-01') as c:
        c.argument('public_network_access', options_list=['--public-network-access', '--public-network'],
                   arg_type=get_enum_type(['Enabled', 'Disabled']),
                   help='This determines if traffic is allowed over public network. By default it is enabled. If value is SecuredByPerimeter then Inbound and Outbound communication is controlled by the network security perimeter and profile\' access rules.')
        c.argument('trusted_service_access_enabled', options_list=['--enable-trusted-service-access', '-t'],
                   arg_type=get_three_state_flag(),
                   help='A boolean value that indicates whether Trusted Service Access is enabled for Network Rule Set.')
        c.argument('default_action', arg_group='networkrule', options_list=['--default-action'],
                   arg_type=get_enum_type(['Allow', 'Deny']),
                   help='Default Action for Network Rule Set.')

    with self.argument_context('servicebus namespace network-rule add') as c:
        c.argument('ignore_missing_vnet_service_endpoint', arg_group='Virtual Network Rule', options_list=['--ignore-missing-endpoint'], arg_type=get_three_state_flag(), help='A boolean value that indicates whether to ignore missing vnet Service Endpoint')
        c.argument('action', arg_group='IP Address Rule', options_list=['--action'], arg_type=get_enum_type(['Allow']), help='Action of the IP rule')

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
            c.argument('require_infrastructure_encryption', options_list=['--infra-encryption'], is_preview=True,
                       arg_type=get_three_state_flag(),
                       help='A boolean value that indicates whether Infrastructure Encryption (Double Encryption)')
