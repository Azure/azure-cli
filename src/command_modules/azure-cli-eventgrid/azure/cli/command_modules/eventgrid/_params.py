# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from knack.arguments import CLIArgumentType

from azure.cli.core.commands.parameters import (
    resource_group_name_type,
    get_three_state_flag,
    get_location_type,
    get_enum_type,
    tags_type,
    name_type
)

included_event_types_type = CLIArgumentType(
    help="A space separated list of event types. To subscribe to all event types, the string \"All\" should be specified.",
    nargs='+'
)

labels_type = CLIArgumentType(
    help="A space separated list of labels to associate with this event subscription.",
    nargs='+'
)


def load_arguments(self, _):
    with self.argument_context('eventgrid') as c:
        c.argument('resource_group_name', arg_type=resource_group_name_type)
        c.argument('location', arg_type=get_location_type(self.cli_ctx))
        c.argument('tags', arg_type=tags_type)
        c.argument('included_event_types', arg_type=included_event_types_type)
        c.argument('labels', arg_type=labels_type)
        c.argument('endpoint_type', arg_type=get_enum_type(['webhook', 'eventhub'], default='webhook'))
        c.argument('provider_namespace', help="Namespace of the provider owning the resource.")
        c.argument('resource_type', help="Type of the resource.")
        c.argument('resource_name', help="Name of the resource whose event subscription needs to be managed.")
        c.argument('endpoint', help="Endpoint where EventGrid should deliver events matching this event subscription. For webhook endpoint type, this should be the corresponding webhook URL. For eventhub endpoint type, this should be the Azure ResourceID of the event hub.")
        c.argument('event_subscription_name', help="Name of the event subscription.")
        c.argument('subject_begins_with', help="An optional string to filter events for an event subscription based on a prefix. Wildcard characters are not supported.")
        c.argument('subject_ends_with', help="An optional string to filter events for an event subscription based on a suffix. Wildcard characters are not supported.")
        c.argument('topic_type_name', help="Name of the topic type.")
        c.argument('is_subject_case_sensitive', arg_type=get_three_state_flag(), options_list=['--subject-case-sensitive'], help="Specify to indicate whether the subject fields should be compared in a case sensitive manner. True if flag present.", )

    with self.argument_context('eventgrid topic') as c:
        c.argument('topic_name', arg_type=name_type, help='Name of the topic', id_part='name')

    with self.argument_context('eventgrid topic event-subscription') as c:
        c.argument('topic_name', options_list=['--topic-name'])
        c.argument('event_subscription_name', arg_type=name_type, help='Name of the event subscription')
    with self.argument_context('eventgrid event-subscription') as c:
        c.argument('event_subscription_name', arg_type=name_type, help='Name of the event subscription')
    with self.argument_context('eventgrid resource event-subscription') as c:
        c.argument('event_subscription_name', arg_type=name_type, help='Name of the event subscription')

    with self.argument_context('eventgrid topic-type') as c:
        c.argument('topic_type_name', arg_type=name_type, help="Name of the topic type.")
