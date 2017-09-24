# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import register_cli_argument, CliArgumentType

from azure.cli.core.commands.parameters import (
    resource_group_name_type,
    location_type,
    enum_choice_list,
    three_state_flag,
    tags_type,
    name_type
)

included_event_types_type = CliArgumentType(
    help="A space separated list of event types. To subscribe to all event types, the string \"All\" should be specified.",
    nargs='+'
)

labels_type = CliArgumentType(
    help="A space separated list of labels to associate with this event subscription.",
    nargs='+'
)

register_cli_argument('eventgrid', 'resource_group_name', resource_group_name_type)
register_cli_argument('eventgrid', 'location', location_type)
register_cli_argument('eventgrid', 'tags', tags_type, help="Space separated tags in 'key[=value]' format.")

register_cli_argument('eventgrid', 'endpoint', help="Endpoint where EventGrid should deliver events matching this event subscription. For webhook endpoint type, this should be the corresponding webhook URL. For eventhub endpoint type, this should be the Azure ResourceID of the event hub.")
register_cli_argument('eventgrid', 'event_subscription_name', help="Name of the event subscription.")
register_cli_argument('eventgrid', 'subject_begins_with', help="An optional string to filter events for an event subscription based on a prefix. Wildcard characters are not supported.")
register_cli_argument('eventgrid', 'subject_ends_with', help="An optional string to filter events for an event subscription based on a suffix. Wildcard characters are not supported.")
register_cli_argument('eventgrid', 'topic_type_name', help="Name of the topic type.")


register_cli_argument('eventgrid topic', 'topic_name', arg_type=name_type, help='Name of the topic', id_part="name")
register_cli_argument('eventgrid topic event-subscription', 'topic_name', options_list=['--topic-name'])
register_cli_argument('eventgrid topic event-subscription', 'event_subscription_name', name_type, help='Name of the event subscription')
register_cli_argument('eventgrid event-subscription', 'event_subscription_name', name_type, help='Name of the event subscription')
register_cli_argument('eventgrid resource event-subscription', 'event_subscription_name', name_type, help='Name of the event subscription')

register_cli_argument('eventgrid', 'is_subject_case_sensitive', options_list=['--subject-case-sensitive'], help="Specify to indicate whether the subject fields should be compared in a case sensitive manner. True if flag present.", **three_state_flag())

register_cli_argument('eventgrid', 'included_event_types', included_event_types_type)
register_cli_argument('eventgrid', 'labels', labels_type)
register_cli_argument('eventgrid', 'endpoint_type', **enum_choice_list(['webhook', 'eventhub']))

register_cli_argument('eventgrid', 'provider_namespace', help="Namespace of the provider owning the resource.")
register_cli_argument('eventgrid', 'resource_type', help="Type of the resource.")
register_cli_argument('eventgrid', 'resource_name', help="Name of the resource whose event subscription needs to be managed.")

register_cli_argument('eventgrid topic-type', 'topic_type_name', name_type)
