# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import unittest
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer
import os


class EventGridTestConfiguration:
    def __init__(self):
        self.event_subscription_sanitized_endpoint = "https://eventgridclilivetest.azurewebsites.net/api/HttpTriggerCSharp1?code=hidden"
        self.event_subscription_base_endpoint = "https://eventgridclilivetest.azurewebsites.net/api/HttpTriggerCSharp1"
        try:
            self.event_subscription_endpoint = os.environ['A01_EVENTGRID_ENDPOINT']
        except Exception:
            self.event_subscription_endpoint = self.event_subscription_sanitized_endpoint


test_config = EventGridTestConfiguration()


class EventGridTests(ScenarioTest):
    def test_topic_types(self):
        self.kwargs.update({
            'topic_type_name': 'Microsoft.Resources.Subscriptions'
        })

        self.cmd('az eventgrid topic-type list', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/topicTypes')
        ])
        self.cmd('az eventgrid topic-type show --name {topic_type_name}', checks=[
            self.check('type', 'Microsoft.EventGrid/topicTypes'),
            self.check('name', self.kwargs['topic_type_name'])
        ])
        self.cmd('az eventgrid topic-type list-event-types --name {topic_type_name}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/topicTypes/eventTypes')
        ])

    @ResourceGroupPreparer()
    def test_create_topic(self, resource_group):
        topic_name = self.create_random_name(prefix='cli', length=40)
        event_subscription_name = self.create_random_name(prefix='cli', length=40)

        self.kwargs.update({
            'topic_name': topic_name,
            'location': 'eastus2euap',
            'event_subscription_name': event_subscription_name,
            'event_subscription_endpoint': test_config.event_subscription_endpoint,
            'event_subscription_base_endpoint': test_config.event_subscription_base_endpoint,
            'event_subscription_sanitized_endpoint': test_config.event_subscription_sanitized_endpoint,
        })

        self.cmd('az eventgrid topic create --name {topic_name} --resource-group {rg} --location {location}', checks=[
            self.check('type', 'Microsoft.EventGrid/topics'),
            self.check('name', self.kwargs['topic_name']),
            self.check('provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid topic show --name {topic_name} --resource-group {rg}', checks=[
            self.check('type', 'Microsoft.EventGrid/topics'),
            self.check('name', self.kwargs['topic_name']),
        ])

        self.cmd('az eventgrid topic update --name {topic_name} --resource-group {rg} --tags Dept=IT', checks=[
            self.check('name', self.kwargs['topic_name']),
            self.check('tags', {'Dept': 'IT'}),
        ])

        self.cmd('az eventgrid topic list --resource-group {rg}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/topics'),
            self.check('[0].name', self.kwargs['topic_name']),
        ])

        output = self.cmd('az eventgrid topic key list --name {topic_name} --resource-group {rg}').get_output_in_json()
        self.assertIsNotNone(output['key1'])
        self.assertIsNotNone(output['key2'])

        output = self.cmd('az eventgrid topic key regenerate --name {topic_name} --resource-group {rg} --key-name key1').get_output_in_json()
        self.assertIsNotNone(output['key1'])
        self.assertIsNotNone(output['key2'])

        self.cmd('az eventgrid topic key regenerate --name {topic_name} --resource-group {rg} --key-name key2').get_output_in_json()
        self.assertIsNotNone(output['key1'])
        self.assertIsNotNone(output['key2'])

        self.cmd('az eventgrid event-subscription create --topic-name {topic_name} -g {rg} --name {event_subscription_name} --endpoint {event_subscription_endpoint}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
            self.check('destination.endpointBaseUrl', self.kwargs['event_subscription_base_endpoint'])
        ])

        self.cmd('az eventgrid event-subscription show --topic-name {topic_name} -g {rg} --name {event_subscription_name}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
        ])

        endpoint_to_check = self._get_endpoint_to_check()
        self.cmd('az eventgrid event-subscription show --topic-name {topic_name} -g {rg} --name {event_subscription_name} --include-full-endpoint-url', checks=[
            self.check('destination.endpointUrl', endpoint_to_check),
            self.check('destination.endpointBaseUrl', self.kwargs['event_subscription_base_endpoint'])
        ])

        self.cmd('az eventgrid event-subscription update --topic-name {topic_name} -g {rg} --name {event_subscription_name} --endpoint {event_subscription_endpoint}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
            self.check('destination.endpointBaseUrl', self.kwargs['event_subscription_base_endpoint'])
        ])

        self.cmd('az eventgrid event-subscription list --topic-name {topic_name} -g {rg}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])
        self.cmd('az eventgrid event-subscription delete --topic-name {topic_name} -g {rg} --name {event_subscription_name}')
        self.cmd('az eventgrid topic delete --name {topic_name} --resource-group {rg}')

    @ResourceGroupPreparer()
    def test_create_event_subscriptions_to_arm_resource_group(self, resource_group):
        event_subscription_name = 'eventsubscription2'

        self.kwargs.update({
            'event_subscription_name': event_subscription_name,
            'event_subscription_endpoint': test_config.event_subscription_endpoint,
            'event_subscription_base_endpoint': test_config.event_subscription_base_endpoint,
            'event_subscription_sanitized_endpoint': test_config.event_subscription_sanitized_endpoint,
        })

        self.cmd('az eventgrid event-subscription create -g {rg} --name {event_subscription_name} --endpoint {event_subscription_endpoint} --subject-begins-with mysubject_prefix', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
            self.check('destination.endpointBaseUrl', self.kwargs['event_subscription_base_endpoint'])
        ])

        self.cmd('az eventgrid event-subscription show -g {rg} --name {event_subscription_name}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('filter.subjectBeginsWith', 'mysubject_prefix')
        ])

        endpoint_to_check = self._get_endpoint_to_check()
        self.cmd('az eventgrid event-subscription show --include-full-endpoint-url --resource-group {rg} --name {event_subscription_name}', checks=[
            self.check('destination.endpointUrl', endpoint_to_check)
        ])

        self.cmd('az eventgrid event-subscription update -g {rg} --name {event_subscription_name}  --endpoint {event_subscription_endpoint} --subject-ends-with .jpg', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
            self.check('destination.endpointBaseUrl', self.kwargs['event_subscription_base_endpoint']),
            self.check('filter.subjectEndsWith', '.jpg'),
        ])

        self.cmd('az eventgrid event-subscription list -g {rg}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            # There's currently a service bug (fix is being rolled out as of 05/29/2018) that impacts this.
            # Uncomment this as part of a later checkin
            # self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription delete --resource-group {rg} --name {event_subscription_name}')

    @ResourceGroupPreparer(name_prefix='clieventgridrg')
    @StorageAccountPreparer(name_prefix='clieventgrid')
    def test_create_event_subscriptions_to_resource(self, resource_group, resource_group_location, storage_account):
        event_subscription_name = self.create_random_name(prefix='cli', length=40)

        self.kwargs.update({
            'event_subscription_name': event_subscription_name,
            'location': resource_group_location,
            'event_subscription_endpoint': test_config.event_subscription_endpoint,
            'event_subscription_base_endpoint': test_config.event_subscription_base_endpoint,
            'event_subscription_sanitized_endpoint': test_config.event_subscription_sanitized_endpoint,
        })

        self.kwargs['resource_id'] = self.cmd('storage account create -g {rg} -n {sa} --sku Standard_LRS -l {location}').get_output_in_json()['id']
        self.cmd('az storage account update -g {rg} -n {sa} --set kind=StorageV2')

        self.cmd('az eventgrid event-subscription create --resource-id {resource_id} --name {event_subscription_name} --endpoint {event_subscription_endpoint}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
        ])

        self.cmd('az eventgrid event-subscription show --resource-id {resource_id} --name {event_subscription_name}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
        ])

        endpoint_to_check = self._get_endpoint_to_check()
        self.cmd('az eventgrid event-subscription show --include-full-endpoint-url --resource-id {resource_id} --name {event_subscription_name}', checks=[
            self.check('destination.endpointUrl', endpoint_to_check)
        ])

        self.cmd('az eventgrid event-subscription update --resource-id {resource_id} --name {event_subscription_name} --endpoint {event_subscription_endpoint} --subject-ends-with .jpg', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
            self.check('destination.endpointBaseUrl', self.kwargs['event_subscription_base_endpoint']),
            self.check('filter.subjectEndsWith', '.jpg'),
        ])

        self.cmd('az eventgrid event-subscription list --resource-id {resource_id}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            # There's currently a service bug (fix is being rolled out as of 05/29/2018) that impacts this.
            # Uncomment this as part of a later checkin
            # self.check('[0].provisioningState', 'Succeeded'),
        ])
        self.cmd('az eventgrid event-subscription delete --resource-id {resource_id} --name {event_subscription_name}')

    @ResourceGroupPreparer()
    def test_create_event_subscriptions_with_filters(self, resource_group):
        event_subscription_name = 'eventsubscription2'
        subject_ends_with = 'mysubject_suffix'
        event_type_1 = 'blobCreated'
        event_type_2 = 'blobUpdated'
        label_1 = 'Finance'
        label_2 = 'HR'

        self.kwargs.update({
            'event_subscription_name': event_subscription_name,
            'event_subscription_endpoint': test_config.event_subscription_endpoint,
            'event_subscription_base_endpoint': test_config.event_subscription_base_endpoint,
            'event_subscription_sanitized_endpoint': test_config.event_subscription_sanitized_endpoint,
            'subject_ends_with': subject_ends_with,
            'event_type_1': event_type_1,
            'event_type_2': event_type_2,
            'label_1': label_1,
            'label_2': label_2
        })

        self.cmd('az eventgrid event-subscription create -g {rg} --name {event_subscription_name} --endpoint {event_subscription_endpoint} --subject-ends-with {subject_ends_with} --included-event-types {event_type_1} {event_type_2} --subject-case-sensitive --labels {label_1} {label_2}')

        # TODO: Add a verification that filter.isSubjectCaseSensitive is true after resolving why it shows as null in the response
        self.cmd('az eventgrid event-subscription show -g {rg} --name {event_subscription_name}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('filter.subjectEndsWith', self.kwargs['subject_ends_with']),
            self.check('filter.includedEventTypes[0]', self.kwargs['event_type_1']),
            self.check('filter.includedEventTypes[1]', self.kwargs['event_type_2']),
            self.check('labels[0]', self.kwargs['label_1']),
            self.check('labels[1]', self.kwargs['label_2']),
        ])

        endpoint_to_check = self._get_endpoint_to_check()
        self.cmd('az eventgrid event-subscription show --include-full-endpoint-url --resource-group {rg} --name {event_subscription_name}', checks=[
            self.check('destination.endpointUrl', endpoint_to_check),
        ])

        self.cmd('az eventgrid event-subscription list -g {rg}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            # There's currently a service bug (fix is being rolled out as of 05/29/2018) that impacts this.
            # Uncomment this as part of a later checkin
            # self.check('[0].provisioningState', 'Succeeded'),
        ])
        self.cmd('az eventgrid event-subscription delete --resource-group {rg} --name {event_subscription_name}')

    def _get_endpoint_to_check(self):
        if self.is_live:
            endpoint_to_check = self.kwargs['event_subscription_endpoint']
        else:
            endpoint_to_check = self.kwargs['event_subscription_sanitized_endpoint']

        return endpoint_to_check
