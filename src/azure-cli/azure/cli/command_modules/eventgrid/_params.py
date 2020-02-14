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

included_event_types_type = CLIArgumentType(
    help="A space-separated list of event types (e.g., Microsoft.Storage.BlobCreated Microsoft.Storage.BlobDeleted). To subscribe to all default event types, do not specify this argument. For event grid topics, event types are customer defined. For Azure events, e.g., Storage Accounts, IoT Hub, etc., you can query their event types using this CLI command 'az eventgrid topic-type list-event-types'.",
    nargs='+'
)

labels_type = CLIArgumentType(
    help="A space-separated list of labels to associate with this event subscription.",
    nargs='+'
)

odata_query_type = CLIArgumentType(
    help="The OData query used for filtering the list results. Filtering is currently allowed on the Name property only. The supported operations include: CONTAINS, eq (for equal), ne (for not equal), AND, OR and NOT.",
    options_list=['--odata-query']
)


domain_name_type = CLIArgumentType(
    help='Name of the domain.',
    arg_type=name_type,
    options_list=['--domain-name'],
    completer=get_resource_name_completion_list('Microsoft.EventGrid/domains'))

domain_topic_name_type = CLIArgumentType(
    help='Name of the domain topic.',
    arg_type=name_type,
    options_list=['--domain-topic-name'])

key_values = ['key1', 'key2']

key_name_type = CLIArgumentType(
    help='Key name to regenerate, which can be either \'key1\' or \'key2\'.',
    arg_type=get_enum_type(key_values),
    options_list=['--key-name'])


def load_arguments(self, _):    # pylint: disable=too-many-statements
    with self.argument_context('eventgrid') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('location', arg_type=get_location_type(self.cli_ctx))
        c.argument('tags', arg_type=tags_type)
        c.argument('included_event_types', arg_type=included_event_types_type)
        c.argument('labels', arg_type=labels_type)
        c.argument('endpoint_type', arg_type=get_enum_type(['webhook', 'eventhub', 'storagequeue', 'hybridconnection', 'servicebusqueue'], default='webhook'))
        c.argument('source_resource_id', help="Fully qualified identifier of the source Azure resource.")
        c.argument('resource_id', deprecate_info=c.deprecate(redirect="--source-resource-id", expiration='3.0.0', hide=True), help="Fully qualified identifier of the Azure resource.")
        c.argument('endpoint', help="Endpoint where EventGrid should deliver events matching this event subscription. For webhook endpoint type, this should be the corresponding webhook URL. For other endpoint types, this should be the Azure resource identifier of the endpoint. It is expected that the destination endpoint to be already created and available for use before executing any Event Grid command.")
        c.argument('event_subscription_name', help="Name of the event subscription.")
        c.argument('subject_begins_with', help="An optional string to filter events for an event subscription based on a prefix. Wildcard characters are not supported.")
        c.argument('subject_ends_with', help="An optional string to filter events for an event subscription based on a suffix. Wildcard characters are not supported.")
        c.argument('topic_type_name', help="Name of the topic type.")
        c.argument('is_subject_case_sensitive', arg_type=get_three_state_flag(), options_list=['--subject-case-sensitive'], help="Specify to indicate whether the subject fields should be compared in a case sensitive manner. True if flag present.", )
        c.argument('odata_query', arg_type=odata_query_type)
        c.argument('domain_name', arg_type=domain_name_type)
        c.argument('domain_topic_name', arg_type=domain_topic_name_type)

    with self.argument_context('eventgrid topic') as c:
        c.argument('topic_name', arg_type=name_type, help='Name of the topic.', id_part='name', completer=get_resource_name_completion_list('Microsoft.EventGrid/topics'))

    with self.argument_context('eventgrid topic key') as c:
        c.argument('topic_name', arg_type=name_type, help='Name of the topic', id_part=None, completer=get_resource_name_completion_list('Microsoft.EventGrid/topics'))
        c.argument('key_name', arg_type=key_name_type)

    with self.argument_context('eventgrid topic list') as c:
        c.argument('odata_query', arg_type=odata_query_type, id_part=None)

    with self.argument_context('eventgrid domain') as c:
        c.argument('domain_name', arg_type=domain_name_type, options_list=['--name', '-n'], id_part='name')

    with self.argument_context('eventgrid domain list') as c:
        c.argument('odata_query', arg_type=odata_query_type, id_part=None)

    with self.argument_context('eventgrid domain key') as c:
        c.argument('domain_name', arg_type=domain_name_type, options_list=['--name', '-n'], id_part=None)
        c.argument('key_name', arg_type=key_name_type)

    with self.argument_context('eventgrid domain topic') as c:
        c.argument('domain_name', arg_type=domain_name_type, id_part='name')
        c.argument('domain_topic_name', arg_type=domain_topic_name_type, options_list=['--name', '-n'], id_part='topics')

    with self.argument_context('eventgrid domain topic list') as c:
        c.argument('domain_name', arg_type=domain_name_type, id_part=None)
        c.argument('odata_query', arg_type=odata_query_type, id_part=None)

    with self.argument_context('eventgrid event-subscription') as c:
        c.argument('topic_name', deprecate_info=c.deprecate(redirect="--source-resource-id", expiration='3.0.0', hide=True), help='Name of Event Grid topic.', options_list=['--topic-name'], completer=get_resource_name_completion_list('Microsoft.EventGrid/topics'))
        c.argument('event_subscription_name', arg_type=name_type, help='Name of the event subscription.')
        c.argument('max_delivery_attempts', help="Maximum number of delivery attempts. Must be a number between 1 and 30.")
        c.argument('event_ttl', help="Event time to live (in minutes). Must be a number between 1 and 1440.")
        c.argument('deadletter_endpoint', help="The Azure resource ID of an Azure Storage blob container destination where EventGrid should deadletter undeliverable events for this event subscription.")
        c.argument('advanced_filter', action=EventSubscriptionAddFilter, nargs='+')
        c.argument('expiration_date', help="Date or datetime (in UTC, e.g. '2018-11-30T11:59:59+00:00' or '2018-11-30') after which the event subscription would expire. By default, there is no expiration for the event subscription.")

    with self.argument_context('eventgrid event-subscription create') as c:
        c.argument('resource_group_name', deprecate_info=c.deprecate(redirect="--source-resource-id", expiration='3.0.0', hide=True), arg_type=resource_group_name_type)

    with self.argument_context('eventgrid event-subscription delete') as c:
        c.argument('resource_group_name', deprecate_info=c.deprecate(redirect="--source-resource-id", expiration='3.0.0', hide=True), arg_type=resource_group_name_type)

    with self.argument_context('eventgrid event-subscription update') as c:
        c.argument('resource_group_name', deprecate_info=c.deprecate(redirect="--source-resource-id", expiration='3.0.0', hide=True), arg_type=resource_group_name_type)

    with self.argument_context('eventgrid event-subscription list') as c:
        c.argument('odata_query', arg_type=odata_query_type, id_part=None)

    with self.argument_context('eventgrid event-subscription show') as c:
        c.argument('resource_group_name', deprecate_info=c.deprecate(redirect="--source-resource-id", expiration='3.0.0', hide=True), arg_type=resource_group_name_type)
        c.argument('include_full_endpoint_url', arg_type=get_three_state_flag(), options_list=['--include-full-endpoint-url'], help="Specify to indicate whether the full endpoint URL should be returned. True if flag present.", )

    with self.argument_context('eventgrid topic-type') as c:
        c.argument('topic_type_name', arg_type=name_type, help="Name of the topic type.", completer=get_resource_name_completion_list('Microsoft.EventGrid/topictypes'))
