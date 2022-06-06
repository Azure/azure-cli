# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from knack.arguments import CLIArgumentType

from azure.cli.core.commands.parameters import (
    resource_group_name_type,
    get_resource_name_completion_list,
    get_three_state_flag,
    get_location_type,
    get_enum_type,
    tags_type,
    name_type
)

from .advanced_filter import EventSubscriptionAddFilter
from .event_channel_filter import EventChannelAddFilter
from .inbound_ip_rules import AddInboundIpRule
from .delivery_attribute_mapping import AddDeliveryAttributeMapping
from .user_assigned import AddUserAssignedIdentities

included_event_types_type = CLIArgumentType(
    help="A space-separated list of event types (e.g., Microsoft.Storage.BlobCreated and Microsoft.Storage.BlobDeleted). In order to subscribe to all default event types, do not specify any value for this argument. For event grid topics, event types are customer defined. For Azure events, e.g., Storage Accounts, IoT Hub, etc., you can query their event types using this CLI command 'az eventgrid topic-type list-event-types'.",
    nargs='+'
)

labels_type = CLIArgumentType(
    help="A space-separated list of labels to associate with this event subscription.",
    nargs='+'
)

authorized_subscription_ids_type = CLIArgumentType(
    help="A space-separated list of Azure subscription Ids that are authorized to create a partner namespace associated with this partner registration. This is an optional property. Creating partner namespaces is always permitted under the same Azure subscription as the one used for creating the partner registration.",
    nargs='+'
)

input_schema_type = CLIArgumentType(
    help="Schema in which incoming events will be published to this topic/domain. If you specify customeventschema as the value for this parameter, you must also provide values for at least one of --input_mapping_default_values / --input_mapping_fields.",
    arg_type=get_enum_type(['eventgridschema', 'customeventschema', 'cloudeventschemav1_0'], default='eventgridschema')
)

public_network_access_type = CLIArgumentType(
    help="This determines if traffic is allowed over public network. By default it is enabled. You can further restrict to specific IPs by configuring.",
    arg_type=get_enum_type(['enabled', 'disabled']),
    options_list=['--public-network-access']
)

sku_type = CLIArgumentType(
    help="The Sku name of the resource.",
    arg_type=get_enum_type(['basic', 'premium']),
    options_list=['--sku'],
    is_preview=True
)

identity_type = CLIArgumentType(
    help="The managed identity type for the resource. Will be deprecated and replaced by --mi-system-assigned-identity in future",
    arg_type=get_enum_type(['noidentity', 'systemassigned']),
    options_list=['--identity'],
    is_preview=True
)

delivery_identity_type = CLIArgumentType(
    help="The identity type of the delivery destination resource (e.g., storage queue, or eventhub).",
    arg_type=get_enum_type(['systemassigned']),
    options_list=['--delivery-identity'],
    is_preview=True
)

deadletter_identity_type = CLIArgumentType(
    help="The identity type of the deadletter destination resource.",
    arg_type=get_enum_type(['systemassigned']),
    options_list=['--deadletter-identity'],
    is_preview=True
)

input_mapping_fields_type = CLIArgumentType(
    help="When input-schema is specified as customeventschema, this parameter is used to specify input mappings based on field names. Specify space separated mappings in 'key=value' format. Allowed key names are 'id', 'topic', 'eventtime', 'subject', 'eventtype', 'dataversion'. The corresponding value names should specify the names of the fields in the custom input schema. If a mapping for either 'id' or 'eventtime' is not provided, Event Grid will auto-generate a default value for these two fields.",
    arg_type=tags_type
)

input_mapping_default_values_type = CLIArgumentType(
    help="When input-schema is specified as customeventschema, this parameter can be used to specify input mappings based on default values. You can use this parameter when your custom schema does not include a field that corresponds to one of the three fields supported by this parameter. Specify space separated mappings in 'key=value' format. Allowed key names are 'subject', 'eventtype', 'dataversion'. The corresponding value names should specify the default values to be used for the mapping and they will be used only when the published event doesn't have a valid mapping for a particular field.",
    arg_type=tags_type
)


odata_query_type = CLIArgumentType(
    help="The OData query used for filtering the list results. Filtering is currently allowed on the Name property only. The supported operations include: CONTAINS, eq (for equal), ne (for not equal), AND, OR and NOT.",
    options_list=['--odata-query']
)

topic_name_type = CLIArgumentType(
    help='Name of the topic.',
    arg_type=name_type,
    options_list=['--topic-name'],
    completer=get_resource_name_completion_list('Microsoft.EventGrid/topics'))

domain_name_type = CLIArgumentType(
    help='Name of the domain.',
    arg_type=name_type,
    options_list=['--domain-name'],
    completer=get_resource_name_completion_list('Microsoft.EventGrid/domains'))

domain_topic_name_type = CLIArgumentType(
    help='Name of the domain topic.',
    arg_type=name_type,
    options_list=['--domain-topic-name'],
    completer=get_resource_name_completion_list('Microsoft.EventGrid/domains/topic'))

system_topic_name_type = CLIArgumentType(
    help='Name of the system topic.',
    arg_type=name_type,
    options_list=['--system-topic-name'],
    completer=get_resource_name_completion_list('Microsoft.EventGrid/systemtopics'))

partner_registration_name_type = CLIArgumentType(
    help='Name of the partner registration.',
    arg_type=name_type,
    options_list=['--partner-registration-name'],
    completer=get_resource_name_completion_list('Microsoft.EventGrid/partnerregistrations'))

partner_namespace_name_type = CLIArgumentType(
    help='Name of the partner namespace.',
    arg_type=name_type,
    options_list=['--partner-namespace-name'],
    completer=get_resource_name_completion_list('Microsoft.EventGrid/partnernamespaces'))

event_channel_name_type = CLIArgumentType(
    help='Name of the event channel.',
    arg_type=name_type,
    options_list=['--event-channel-name'],
    completer=get_resource_name_completion_list('Microsoft.EventGrid/partnernamespaces/eventchannels'))

partner_topic_name_type = CLIArgumentType(
    help='Name of the partner topic.',
    arg_type=name_type,
    options_list=['--partner-topic-name'],
    completer=get_resource_name_completion_list('Microsoft.EventGrid/partnertopics'))

partner_topic_source_type = CLIArgumentType(
    help='The identifier of the resource that forms the partner source of the events. This represents a unique resource in the partner\'s resource model.',
    arg_type=name_type,
    options_list=['--partner-topic-source'])


phone_number_type = CLIArgumentType(
    help='The customer service number of the publisher. The expected phone format should start with a \'+\' sign'
         ' followed by the country code. The remaining digits are then followed. Only digits and spaces are allowed and its'
         ' length cannot exceed 16 digits including country code. Examples of valid phone numbers are: +1 515 123 4567 and'
         ' +966 7 5115 2471. Examples of invalid phone numbers are: +1 (515) 123-4567, 1 515 123 4567 and +966 121 5115 24 7 551 1234 43.')

phone_extension_type = CLIArgumentType(
    help='The extension of the customer service number of the publisher. Only digits are allowed and number of digits should not exceed 10.')

kind_type = CLIArgumentType(
    help="The kind of topic resource.",
    arg_type=get_enum_type(['azure', 'azurearc']),
    options_list=['--kind'],
    is_preview=True
)

extended_location_name = CLIArgumentType(
    help="The extended location name if kind==azurearc.",
    options_list=['--extended-location-name'],
    arg_group="Azure Arc",
    is_preview=True
)

extended_location_type = CLIArgumentType(
    help="The extended location type if kind==azurearc.",
    arg_type=get_enum_type(['customlocation']),
    arg_group="Azure Arc",
    options_list=['--extended-location-type'],
    is_preview=True
)


def load_arguments(self, _):    # pylint: disable=too-many-statements
    with self.argument_context('eventgrid') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('location', arg_type=get_location_type(self.cli_ctx))
        c.argument('tags', arg_type=tags_type)
        c.argument('included_event_types', arg_group="Filtering", arg_type=included_event_types_type)
        c.argument('labels', arg_type=labels_type)
        c.argument('endpoint_type', arg_type=get_enum_type(['webhook', 'eventhub', 'storagequeue', 'hybridconnection', 'servicebusqueue', 'servicebustopic', 'azurefunction'], default='webhook'))
        c.argument('delivery_identity_endpoint_type', arg_type=get_enum_type(['webhook', 'eventhub', 'storagequeue', 'hybridconnection', 'servicebusqueue', 'servicebustopic', 'azurefunction'], default=None), is_preview=True)
        c.argument('source_resource_id', help="Fully qualified identifier of the source Azure resource.")
        c.argument('endpoint', help="Endpoint where EventGrid should deliver events matching this event subscription. For webhook endpoint type, this should be the corresponding webhook URL. For other endpoint types, this should be the Azure resource identifier of the endpoint. It is expected that the destination endpoint to be already created and available for use before executing any Event Grid command.")
        c.argument('delivery_identity_endpoint', help="Endpoint with identity where EventGrid should deliver events matching this event subscription. For webhook endpoint type, this should be the corresponding webhook URL. For other endpoint types, this should be the Azure resource identifier of the endpoint.", is_preview=True)
        c.argument('event_subscription_name', help="Name of the event subscription.")
        c.argument('subject_begins_with', arg_group="Filtering", help="An optional string to filter events for an event subscription based on a prefix. Wildcard characters are not supported.")
        c.argument('subject_ends_with', arg_group="Filtering", help="An optional string to filter events for an event subscription based on a suffix. Wildcard characters are not supported.")
        c.argument('topic_type_name', help="Name of the topic type.")
        c.argument('is_subject_case_sensitive', arg_group="Filtering", arg_type=get_three_state_flag(), options_list=['--subject-case-sensitive'], help="Specify to indicate whether the subject fields should be compared in a case sensitive manner. True if flag present.", )
        c.argument('input_mapping_fields', arg_type=input_mapping_fields_type)
        c.argument('input_mapping_default_values', arg_type=input_mapping_default_values_type)
        c.argument('input_schema', arg_type=input_schema_type)
        c.argument('odata_query', arg_type=odata_query_type)
        c.argument('domain_name', arg_type=domain_name_type)
        c.argument('domain_topic_name', arg_type=domain_topic_name_type)
        c.argument('system_topic_name', arg_type=system_topic_name_type)
        c.argument('source', help="The ARM Id for the topic, e.g., /subscriptions/{SubId}/resourceGroups/{RgName}/providers/Microsoft.Storage/storageAccounts/{AccountName}")
        c.argument('public_network_access', arg_type=public_network_access_type)
        c.argument('inbound_ip_rules', action=AddInboundIpRule, nargs='+')
        c.argument('sku', arg_type=sku_type)
        c.argument('identity', arg_type=identity_type, deprecate_info=c.deprecate(expiration='2.46.0'))
        c.argument('delivery_identity', arg_type=delivery_identity_type)
        c.argument('deadletter_identity', arg_type=deadletter_identity_type)
        c.argument('partner_registration_name', arg_type=partner_registration_name_type)
        c.argument('partner_namespace_name', arg_type=partner_namespace_name_type)
        c.argument('event_channel_name', arg_type=event_channel_name_type)
        c.argument('partner_topic_name', arg_type=partner_topic_name_type)
        c.argument('authorized_subscription_ids', arg_type=authorized_subscription_ids_type)
        c.argument('partner_name', help="Official name of the partner.")
        c.argument('display_name', help="Display name for the partner topic type.")
        c.argument('resource_type_name', help="Name of the partner topic resource type. This name should be unique among all partner topic types names.")
        c.argument('description', help="Description of the partner topic type.")
        c.argument('logo_uri', help="URI of the partner logo.")
        c.argument('setup_uri', help="URI of the partner website that can be used by Azure customers to setup Event Grid integration on an event source.")
        c.argument('partner_registration_id', help="The fully qualified ARM Id of the partner registration that should be associated with this partner namespace. This takes the following format: /subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.EventGrid/partnerRegistrations/{partnerRegistrationName}.")
        c.argument('partner_topic_source', arg_type=partner_topic_source_type)
        c.argument('destination_topic_name', help="Name of the partner topic associated with the event channel.")
        c.argument('destination_resource_group_name', help="Azure Resource Group of the customer creating the event channel. The partner topic associated with the event channel will be created under this resource group.")
        c.argument('destination_subscription_id', help="Azure subscription Id of the customer creating the event channel. The partner topic associated with the event channel will be created under this Azure subscription.")
        c.argument('topic_type', help="Name of the topic type.", completer=get_resource_name_completion_list('Microsoft.EventGrid/topictypes'))
        c.argument('system_assigned', options_list=['--mi-system-assigned'], action='store_true', help='Presence of this param indicates that SystemAssigned managed identity will be used')
        c.argument('user_assigned',
                   action=AddUserAssignedIdentities,
                   nargs='+',
                   is_preview=True,
                   help='Add user assigned identities when identityType is user or mixed. This attribute is valid for all destination types except StorageQueue. Multiple attributes can be specified by using more than one `--mi-user-assigned` argument',
                   options_list=['--mi-user-assigned'])

    with self.argument_context('eventgrid topic') as c:
        c.argument('topic_name', arg_type=name_type, help='Name of the topic.', id_part='name', completer=get_resource_name_completion_list('Microsoft.EventGrid/topics'))
        c.argument('kind', arg_type=kind_type)
        c.argument('extended_location_name', arg_type=extended_location_name)
        c.argument('extended_location_type', arg_type=extended_location_type)

    with self.argument_context('eventgrid topic key') as c:
        c.argument('topic_name', arg_type=name_type, help='Name of the topic', id_part=None, completer=get_resource_name_completion_list('Microsoft.EventGrid/topics'))
        c.argument('key_name', help='Key name to regenerate key1 or key2')

    with self.argument_context('eventgrid topic list') as c:
        c.argument('odata_query', arg_type=odata_query_type, id_part=None)

    with self.argument_context('eventgrid topic event-subscription') as c:
        c.argument('topic_name', arg_type=topic_name_type, id_part=None, completer=get_resource_name_completion_list('Microsoft.EventGrid/topicss'))
        c.argument('event_subscription_name', arg_type=name_type, options_list=['--name', '-n'], help='Name of the event subscription.')
        c.argument('endpoint_type', arg_type=get_enum_type(['webhook', 'eventhub', 'storagequeue', 'hybridconnection', 'servicebusqueue', 'servicebustopic', 'azurefunction'], default='webhook'))
        c.argument('event_delivery_schema', arg_type=get_enum_type(['eventgridschema', 'custominputschema', 'cloudeventschemav1_0']), help='The schema in which events should be delivered for this event subscription. By default, events will be delivered in the same schema in which they are published (based on the corresponding topic\'s input schema).')
        c.argument('max_delivery_attempts', type=int, help="Maximum number of delivery attempts. Must be a number between 1 and 30.")
        c.argument('max_events_per_batch', type=int, help="Maximum number of events in a batch. Must be a number between 1 and 5000.")
        c.argument('preferred_batch_size_in_kilobytes', type=int, help="Preferred batch size in kilobytes. Must be a number between 1 and 1024.")
        c.argument('event_ttl', type=int, help="Event time to live (in minutes). Must be a number between 1 and 1440.")
        c.argument('deadletter_endpoint', help="The Azure resource ID of an Azure Storage blob container destination where EventGrid should deadletter undeliverable events for this event subscription.")
        c.argument('advanced_filter', arg_group="Filtering", action=EventSubscriptionAddFilter, nargs='+')
        c.argument('expiration_date', help="Date or datetime (in UTC, e.g. '2018-11-30T11:59:59+00:00' or '2018-11-30') after which the event subscription would expire. By default, there is no expiration for the event subscription.")
        c.argument('azure_active_directory_tenant_id', help="The Azure Active Directory Tenant Id to get the access token that will be included as the bearer token in delivery requests. Applicable only for webhook as a destination")
        c.argument('azure_active_directory_application_id_or_uri', help="The Azure Active Directory Application Id or Uri to get the access token that will be included as the bearer token in delivery requests. Applicable only for webhook as a destination")
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('enable_advanced_filtering_on_arrays', is_preview=True, arg_type=get_three_state_flag(),
                   options_list=['--enable-advanced-filtering-on-arrays', '--enable-af-arr'], arg_group="Filtering",
                   help="Allows advanced filters to be evaluated against an array of values instead of expecting a singular value.")
        c.argument('storage_queue_msg_ttl',
                   help="Storage queue message time to live in seconds.",
                   type=int,
                   options_list=['--storage-queue-msg-ttl', '--qttl'],
                   is_preview=True)
        c.argument('delivery_attribute_mapping',
                   action=AddDeliveryAttributeMapping,
                   nargs='+',
                   is_preview=True,
                   help='Add delivery attribute mapping to send additional information via HTTP headers when delivering events. This attribute is valid for all destination types except StorageQueue. Multiple attributes can be specified by using more than one `--delivery-attribute-mapping` argument',
                   options_list=['--delivery-attribute-mapping'])

    with self.argument_context('eventgrid topic event-subscription list') as c:
        c.argument('odata_query', arg_type=odata_query_type, id_part=None)

    with self.argument_context('eventgrid topic event-subscription show') as c:
        c.argument('topic_name', arg_type=topic_name_type, completer=get_resource_name_completion_list('Microsoft.EventGrid/topicss'))
        c.argument('include_full_endpoint_url', arg_type=get_three_state_flag(), options_list=['--include-full-endpoint-url'], help="Specify to indicate whether the full endpoint URL should be returned. True if flag present.")
        c.argument('include_static_delivery_attribute_secret', arg_type=get_three_state_flag(), options_list=['--include-static-delivery-attribute-secret', '--include-attrib-secret'], help="Indicate whether any static delivery attribute secrets should be returned. True if flag present.", is_preview=True)

    with self.argument_context('eventgrid domain') as c:
        c.argument('domain_name', arg_type=domain_name_type, options_list=['--name', '-n'], id_part='name')

    with self.argument_context('eventgrid domain list') as c:
        c.argument('odata_query', arg_type=odata_query_type, id_part=None)

    with self.argument_context('eventgrid domain key') as c:
        c.argument('domain_name', arg_type=domain_name_type, options_list=['--name', '-n'], id_part=None)
        c.argument('key_name', help='Key name to regenerate key1 or key2')

    with self.argument_context('eventgrid domain topic') as c:
        c.argument('domain_name', arg_type=domain_name_type, id_part='name')
        c.argument('domain_topic_name', arg_type=domain_topic_name_type, options_list=['--name', '-n'], id_part='topics')

    with self.argument_context('eventgrid domain topic list') as c:
        c.argument('domain_name', arg_type=domain_name_type, id_part=None)
        c.argument('odata_query', arg_type=odata_query_type, id_part=None)

    with self.argument_context('eventgrid system-topic') as c:
        c.argument('system_topic_name', arg_type=system_topic_name_type, options_list=['--name', '-n'], id_part='name', completer=get_resource_name_completion_list('Microsoft.EventGrid/systemtopics'))

    with self.argument_context('eventgrid system-topic create') as c:
        c.argument('source', help="The ARM Id for the topic, e.g., /subscriptions/{SubId}/resourceGroups/{RgName}/providers/Microsoft.Storage/storageAccounts/{AccountName}")

    with self.argument_context('eventgrid system-topic list') as c:
        c.argument('odata_query', arg_type=odata_query_type, id_part=None)

    with self.argument_context('eventgrid partner registration') as c:
        c.argument('partner_registration_name', arg_type=partner_registration_name_type, options_list=['--name', '-n'], id_part='name', completer=get_resource_name_completion_list('Microsoft.EventGrid/partnerregistrations'))
        c.argument('long_description', help='Description of the custom scenarios and integration. Length of this description should not exceed 2048 characters', id_part=None)
        c.argument('customer_service_number', arg_type=phone_number_type, id_part=None)
        c.argument('customer_service_extension', arg_type=phone_extension_type, id_part=None)
        c.argument('customer_service_uri', help='The customer service URI of the publisher.', id_part=None)

    with self.argument_context('eventgrid partner registration list') as c:
        c.argument('odata_query', arg_type=odata_query_type, id_part=None)

    with self.argument_context('eventgrid partner namespace') as c:
        c.argument('partner_namespace_name', arg_type=partner_namespace_name_type, options_list=['--name', '-n'], id_part='name', completer=get_resource_name_completion_list('Microsoft.EventGrid/partnernamespaces'))

    with self.argument_context('eventgrid partner namespace key') as c:
        c.argument('partner_namespace_name', arg_type=partner_namespace_name_type, help='Name of the partner namespace', id_part=None, completer=get_resource_name_completion_list('Microsoft.EventGrid/partnernamespaces'))
        c.argument('key_name', help='Key name to regenerate key1 or key2')

    with self.argument_context('eventgrid partner namespace show') as c:
        c.argument('partner_namespace_name', arg_type=partner_namespace_name_type, options_list=['--name', '-n'], id_part='name', completer=get_resource_name_completion_list('Microsoft.EventGrid/partnernamespaces'))

    with self.argument_context('eventgrid partner namespace list') as c:
        c.argument('odata_query', arg_type=odata_query_type, id_part=None)

    with self.argument_context('eventgrid partner namespace event-channel') as c:
        c.argument('partner_namespace_name', arg_type=partner_namespace_name_type, id_part='name')
        c.argument('event_channel_name', arg_type=event_channel_name_type, options_list=['--name', '-n'], id_part='name', completer=get_resource_name_completion_list('Microsoft.EventGrid/partnernamespaes/eventchannels'))
        c.argument('partner_topic_source', arg_type=partner_topic_source_type, options_list=['--source'])
        c.argument('activation_expiration_date', help="Date or datetime in UTC ISO 8601 format (e.g., '2022-02-17T01:59:59+00:00' or '2022-02-17') after which the event channel and corresponding partner topic would expire and get auto deleted. If this time is not specified, the expiration date is set to seven days by default.")
        c.argument('partner_topic_description', help="Friendly description of the corresponding partner topic. This will be helpful to remove any ambiguity of the origin of creation of the partner topic for the customer.")
        c.argument('publisher_filter', action=EventChannelAddFilter, nargs='+')

    with self.argument_context('eventgrid partner namespace event-channel show') as c:
        c.argument('partner_namespace_name', arg_type=partner_namespace_name_type, id_part='name')

    with self.argument_context('eventgrid partner namespace event-channel list') as c:
        c.argument('partner_namespace_name', arg_type=partner_namespace_name_type, id_part=None)
        c.argument('odata_query', arg_type=odata_query_type, id_part=None)

    with self.argument_context('eventgrid partner topic') as c:
        c.argument('partner_topic_name', arg_type=partner_topic_name_type, options_list=['--name', '-n'], id_part='name', completer=get_resource_name_completion_list('Microsoft.EventGrid/partnertopics'))

    with self.argument_context('eventgrid partner topic list') as c:
        c.argument('odata_query', arg_type=odata_query_type, id_part=None)

    with self.argument_context('eventgrid event-subscription') as c:
        c.argument('event_subscription_name', arg_type=name_type, help='Name of the event subscription.')
        c.argument('event_delivery_schema', arg_type=get_enum_type(['eventgridschema', 'custominputschema', 'cloudeventschemav1_0']), help='The schema in which events should be delivered for this event subscription. By default, events will be delivered in the same schema in which they are published (based on the corresponding topic\'s input schema).')
        c.argument('max_delivery_attempts', type=int, help="Maximum number of delivery attempts. Must be a number between 1 and 30.")
        c.argument('max_events_per_batch', type=int, help="Maximum number of events in a batch. Must be a number between 1 and 5000.")
        c.argument('preferred_batch_size_in_kilobytes', type=int, help="Preferred batch size in kilobytes. Must be a number between 1 and 1024.")
        c.argument('event_ttl', type=int, help="Event time to live (in minutes). Must be a number between 1 and 1440.")
        c.argument('deadletter_endpoint', help="The Azure resource ID of an Azure Storage blob container destination where EventGrid should deadletter undeliverable events for this event subscription.")
        c.argument('deadletter_identity_endpoint', help="The Azure resource ID of an Azure Storage blob container destination with identity where EventGrid should deadletter undeliverable events for this event subscription.")
        c.argument('advanced_filter', arg_group="Filtering", action=EventSubscriptionAddFilter, nargs='+')
        c.argument('expiration_date', help="Date or datetime (in UTC, e.g. '2018-11-30T11:59:59+00:00' or '2018-11-30') after which the event subscription would expire. By default, there is no expiration for the event subscription.")
        c.argument('azure_active_directory_tenant_id', help="The Azure Active Directory Tenant Id to get the access token that will be included as the bearer token in delivery requests. Applicable only for webhook as a destination")
        c.argument('azure_active_directory_application_id_or_uri', help="The Azure Active Directory Application Id or Uri to get the access token that will be included as the bearer token in delivery requests. Applicable only for webhook as a destination")
        c.argument('delivery_identity', arg_type=delivery_identity_type)
        c.argument('deadletter_identity', arg_type=deadletter_identity_type)
        c.argument('delivery_identity_endpoint', help="Endpoint with identity where EventGrid should deliver events matching this event subscription. For webhook endpoint type, this should be the corresponding webhook URL. For other endpoint types, this should be the Azure resource identifier of the endpoint.", is_preview=True)
        c.argument('delivery_identity_endpoint_type', arg_type=get_enum_type(['webhook', 'eventhub', 'storagequeue', 'hybridconnection', 'servicebusqueue', 'servicebustopic', 'azurefunction'], default=None), is_preview=True)
        c.argument('enable_advanced_filtering_on_arrays', is_preview=True, arg_type=get_three_state_flag(),
                   options_list=['--enable-advanced-filtering-on-arrays', '--enable-af-arr'], arg_group="Filtering",
                   help="Allows advanced filters to be evaluated against an array of values instead of expecting a singular value.")
        c.argument('storage_queue_msg_ttl',
                   help="Storage queue message time to live in seconds.",
                   type=int,
                   options_list=['--storage-queue-msg-ttl', '--qttl'],
                   is_preview=True)
        c.argument('delivery_attribute_mapping',
                   action=AddDeliveryAttributeMapping,
                   nargs='+',
                   is_preview=True,
                   help='Add delivery attribute mapping to send additional information via HTTP headers when delivering events. This attribute is valid for all destination types except StorageQueue. Multiple attributes can be specified by using more than one `--delivery-attribute-mapping` argument',
                   options_list=['--delivery-attribute-mapping'])

    with self.argument_context('eventgrid event-subscription list') as c:
        c.argument('odata_query', arg_type=odata_query_type, id_part=None)

    with self.argument_context('eventgrid event-subscription show') as c:
        c.argument('include_full_endpoint_url', arg_type=get_three_state_flag(), options_list=['--include-full-endpoint-url'], help="Specify to indicate whether the full endpoint URL should be returned. True if flag present.")
        c.argument('include_static_delivery_attribute_secret', arg_type=get_three_state_flag(), options_list=['--include-static-delivery-attribute-secret', '--include-attrib-secret'], help="Indicate whether any static delivery attribute secrets should be returned. True if flag present.", is_preview=True)

    with self.argument_context('eventgrid system-topic event-subscription') as c:
        c.argument('system_topic_name', arg_type=system_topic_name_type, id_part=None, completer=get_resource_name_completion_list('Microsoft.EventGrid/systemtopics'))
        c.argument('event_subscription_name', arg_type=name_type, options_list=['--name', '-n'], help='Name of the event subscription.')
        c.argument('endpoint_type', arg_type=get_enum_type(['webhook', 'eventhub', 'storagequeue', 'hybridconnection', 'servicebusqueue', 'servicebustopic', 'azurefunction'], default='webhook'))
        c.argument('event_delivery_schema', arg_type=get_enum_type(['eventgridschema', 'custominputschema', 'cloudeventschemav1_0']), help='The schema in which events should be delivered for this event subscription. By default, events will be delivered in the same schema in which they are published (based on the corresponding topic\'s input schema).')
        c.argument('max_delivery_attempts', type=int, help="Maximum number of delivery attempts. Must be a number between 1 and 30.")
        c.argument('max_events_per_batch', type=int, help="Maximum number of events in a batch. Must be a number between 1 and 5000.")
        c.argument('preferred_batch_size_in_kilobytes', type=int, help="Preferred batch size in kilobytes. Must be a number between 1 and 1024.")
        c.argument('event_ttl', type=int, help="Event time to live (in minutes). Must be a number between 1 and 1440.")
        c.argument('deadletter_endpoint', help="The Azure resource ID of an Azure Storage blob container destination where EventGrid should deadletter undeliverable events for this event subscription.")
        c.argument('advanced_filter', arg_group="Filtering", action=EventSubscriptionAddFilter, nargs='+')
        c.argument('expiration_date', help="Date or datetime (in UTC, e.g. '2018-11-30T11:59:59+00:00' or '2018-11-30') after which the event subscription would expire. By default, there is no expiration for the event subscription.")
        c.argument('azure_active_directory_tenant_id', help="The Azure Active Directory Tenant Id to get the access token that will be included as the bearer token in delivery requests. Applicable only for webhook as a destination")
        c.argument('azure_active_directory_application_id_or_uri', help="The Azure Active Directory Application Id or Uri to get the access token that will be included as the bearer token in delivery requests. Applicable only for webhook as a destination")
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('enable_advanced_filtering_on_arrays', is_preview=True, arg_type=get_three_state_flag(),
                   options_list=['--enable-advanced-filtering-on-arrays', '--enable-af-arr'], arg_group="Filtering",
                   help="Allows advanced filters to be evaluated against an array of values instead of expecting a singular value.")
        c.argument('storage_queue_msg_ttl',
                   help="Storage queue message time to live in seconds.",
                   type=int,
                   options_list=['--storage-queue-msg-ttl', '--qttl'],
                   is_preview=True)
        c.argument('delivery_attribute_mapping',
                   action=AddDeliveryAttributeMapping,
                   nargs='+',
                   is_preview=True,
                   help='Add delivery attribute mapping to send additional information via HTTP headers when delivering events. This attribute is valid for all destination types except StorageQueue. Multiple attributes can be specified by using more than one `--delivery-attribute-mapping` argument',
                   options_list=['--delivery-attribute-mapping'])

    with self.argument_context('eventgrid system-topic event-subscription list') as c:
        c.argument('odata_query', arg_type=odata_query_type, id_part=None)

    with self.argument_context('eventgrid system-topic event-subscription show') as c:
        c.argument('system_topic_name', arg_type=system_topic_name_type, completer=get_resource_name_completion_list('Microsoft.EventGrid/systemtopics'))
        c.argument('include_full_endpoint_url', arg_type=get_three_state_flag(), options_list=['--include-full-endpoint-url'], help="Specify to indicate whether the full endpoint URL should be returned. True if flag present.")
        c.argument('include_static_delivery_attribute_secret', arg_type=get_three_state_flag(), options_list=['--include-static-delivery-attribute-secret', '--include-attrib-secret'], help="Indicate whether any static delivery attribute secrets should be returned. True if flag present.", is_preview=True)

    with self.argument_context('eventgrid partner topic event-subscription') as c:
        c.argument('partner_topic_name', arg_type=partner_topic_name_type, id_part=None, completer=get_resource_name_completion_list('Microsoft.EventGrid/partnertopics'))
        c.argument('event_subscription_name', arg_type=name_type, options_list=['--name', '-n'], help='Name of the event subscription.')
        c.argument('endpoint_type', arg_type=get_enum_type(['webhook', 'eventhub', 'storagequeue', 'hybridconnection', 'servicebusqueue', 'servicebustopic', 'azurefunction'], default='webhook'))
        c.argument('event_delivery_schema', arg_type=get_enum_type(['eventgridschema', 'custominputschema', 'cloudeventschemav1_0']), help='The schema in which events should be delivered for this event subscription. By default, events will be delivered in the same schema in which they are published (based on the corresponding topic\'s input schema).')
        c.argument('max_delivery_attempts', type=int, help="Maximum number of delivery attempts. Must be a number between 1 and 30.")
        c.argument('max_events_per_batch', type=int, help="Maximum number of events in a batch. Must be a number between 1 and 5000.")
        c.argument('preferred_batch_size_in_kilobytes', type=int, help="Preferred batch size in kilobytes. Must be a number between 1 and 1024.")
        c.argument('event_ttl', type=int, help="Event time to live (in minutes). Must be a number between 1 and 1440.")
        c.argument('deadletter_endpoint', help="The Azure resource ID of an Azure Storage blob container destination where EventGrid should deadletter undeliverable events for this event subscription.")
        c.argument('advanced_filter', arg_group="Filtering", action=EventSubscriptionAddFilter, nargs='+')
        c.argument('expiration_date', help="Date or datetime (in UTC, e.g. '2018-11-30T11:59:59+00:00' or '2018-11-30') after which the event subscription would expire. By default, there is no expiration for the event subscription.")
        c.argument('azure_active_directory_tenant_id', help="The Azure Active Directory Tenant Id to get the access token that will be included as the bearer token in delivery requests. Applicable only for webhook as a destination")
        c.argument('azure_active_directory_application_id_or_uri', help="The Azure Active Directory Application Id or Uri to get the access token that will be included as the bearer token in delivery requests. Applicable only for webhook as a destination")
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('enable_advanced_filtering_on_arrays', is_preview=True, arg_type=get_three_state_flag(),
                   options_list=['--enable-advanced-filtering-on-arrays', '--enable-af-arr'], arg_group="Filtering",
                   help="Allows advanced filters to be evaluated against an array of values instead of expecting a singular value.")
        c.argument('storage_queue_msg_ttl',
                   help="Storage queue message time to live in seconds.",
                   type=int,
                   options_list=['--storage-queue-msg-ttl', '--qttl'],
                   is_preview=True)
        c.argument('delivery_attribute_mapping',
                   action=AddDeliveryAttributeMapping,
                   nargs='+',
                   is_preview=True,
                   help='Add delivery attribute mapping to send additional information via HTTP headers when delivering events. This attribute is valid for all destination types except StorageQueue. Multiple attributes can be specified by using more than one `--delivery-attribute-mapping` argument',
                   options_list=['--delivery-attribute-mapping'])

    with self.argument_context('eventgrid partner topic event-subscription list') as c:
        c.argument('odata_query', arg_type=odata_query_type, id_part=None)

    with self.argument_context('eventgrid partner topic event-subscription show') as c:
        c.argument('partner_topic_name', arg_type=partner_topic_name_type, completer=get_resource_name_completion_list('Microsoft.EventGrid/partnertopics'))
        c.argument('include_full_endpoint_url', arg_type=get_three_state_flag(), options_list=['--include-full-endpoint-url'], help="Specify to indicate whether the full endpoint URL should be returned. True if flag present.")
        c.argument('include_static_delivery_attribute_secret', arg_type=get_three_state_flag(), options_list=['--include-static-delivery-attribute-secret', '--include-attrib-secret'], help="Indicate whether any static delivery attribute secrets should be returned. True if flag present.", is_preview=True)

    with self.argument_context('eventgrid topic-type') as c:
        c.argument('topic_type_name', arg_type=name_type, help="Name of the topic type.", completer=get_resource_name_completion_list('Microsoft.EventGrid/topictypes'))
