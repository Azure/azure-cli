# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import unittest
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


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
            'location': 'westus2',
            'event_subscription_name': event_subscription_name
        })

        self.cmd('az eventgrid topic create --name {topic_name} --resource-group {rg} --location {location}')
        self.cmd('az eventgrid topic show --name {topic_name} --resource-group {rg}', checks=[
            self.check('type', 'Microsoft.EventGrid/topics'),
            self.check('name', self.kwargs['topic_name']),
        ])
        self.cmd('az eventgrid topic key list --name {topic_name} --resource-group {rg}')
        self.cmd('az eventgrid topic key regenerate --name {topic_name} --resource-group {rg} --key-name key1')
        self.cmd('az eventgrid topic key regenerate --name {topic_name} --resource-group {rg} --key-name key2')
        self.cmd('az eventgrid topic event-subscription create --topic-name {topic_name} -g {rg} --name {event_subscription_name} --endpoint https://requestb.in/18zmdhv1', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
        ])
        self.cmd('az eventgrid topic event-subscription show --topic-name {topic_name} -g {rg} --name {event_subscription_name}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
        ])
        self.cmd('az eventgrid topic event-subscription show-endpoint-url --topic-name {topic_name} -g {rg} --name {event_subscription_name}', checks=[
            self.check('endpointUrl', 'https://requestb.in/18zmdhv1'),
        ])
        self.cmd('az eventgrid topic event-subscription list --topic-name {topic_name} -g {rg}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])
        self.cmd('az eventgrid topic event-subscription delete --topic-name {topic_name} -g {rg} --name {event_subscription_name}')
        self.cmd('az eventgrid topic delete --name {topic_name} --resource-group {rg}')

    @ResourceGroupPreparer()
    def test_create_event_subscriptions_to_arm_resource_group(self, resource_group):
        event_subscription_name = 'eventsubscription2'
        endpoint_url = 'https://requestb.in/18zmdhv1'

        self.kwargs.update({
            'event_subscription_name': event_subscription_name,
            'endpoint_url': endpoint_url
        })

        self.cmd('az eventgrid event-subscription create -g {rg} --name {event_subscription_name} --endpoint {endpoint_url} --subject-begins-with mysubject_prefix')
        self.cmd('az eventgrid event-subscription show -g {rg} --name {event_subscription_name}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('filter.subjectBeginsWith', 'mysubject_prefix')
        ])
        self.cmd('az eventgrid event-subscription show-endpoint-url --resource-group {rg} --name {event_subscription_name}', checks=[
            self.check('endpointUrl', self.kwargs['endpoint_url']),
        ])
        self.cmd('az eventgrid event-subscription list -g {rg}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])
        self.cmd('az eventgrid event-subscription delete --resource-group {rg} --name {event_subscription_name}')

    # TODO This test fails on recording due to https://github.com/Azure/azure-cli/issues/4997
    @unittest.skip('Skipped test due to outstanding service issue.')
    def test_create_event_subscriptions_to_resource(self):
        event_subscription_name = self.create_random_name(prefix='cli', length=40)

        resource_group = 'rajagrid'
        storage_account = 'rajagridstorageblobonly'

        self.kwargs.update({
            'rg': resource_group,
            'storage_account': storage_account,
            'rt': 'storageAccounts',
            'pn': 'Microsoft.Storage',
            'event_subscription_name': event_subscription_name
        })

        self.cmd('az eventgrid resource event-subscription create -g {rg} --provider-namespace {pn} --resource-type {rt} --resource-name {storage_account} --name {event_subscription_name} --endpoint https://requestb.in/18zmdhv1', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
        ])
        self.cmd('az eventgrid resource event-subscription show -g {rg} --provider-namespace {pn} --resource-type {rt} --resource-name {storage_account} --name {event_subscription_name}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
        ])
        self.cmd('az eventgrid resource event-subscription show-endpoint-url -g {rg} --provider-namespace {pn} --resource-type {rt} --resource-name {storage_account} --name {event_subscription_name}', checks=[
            self.check('endpointUrl', 'https://requestb.in/18zmdhv1'),
        ])
        self.cmd('az eventgrid resource event-subscription list -g {rg} --provider-namespace {pn} --resource-type {rt} --resource-name {storage_account}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])
        self.cmd('az eventgrid resource event-subscription delete -g {rg} --name {event_subscription_name} --provider-namespace {pn} --resource-type {rt} --resource-name {storage_account}')

    @ResourceGroupPreparer()
    def test_create_event_subscriptions_with_filters(self, resource_group):
        event_subscription_name = 'eventsubscription2'
        endpoint_url = 'https://requestb.in/18zmdhv1'
        subject_ends_with = 'mysubject_suffix'
        event_type_1 = 'blobCreated'
        event_type_2 = 'blobUpdated'
        label_1 = 'Finance'
        label_2 = 'HR'

        self.kwargs.update({
            'event_subscription_name': event_subscription_name,
            'endpoint_url': endpoint_url,
            'subject_ends_with': subject_ends_with,
            'event_type_1': event_type_1,
            'event_type_2': event_type_2,
            'label_1': label_1,
            'label_2': label_2
        })

        self.cmd('az eventgrid event-subscription create -g {rg} --name {event_subscription_name} --endpoint {endpoint_url} --subject-ends-with {subject_ends_with} --included-event-types {event_type_1} {event_type_2} --subject-case-sensitive --labels {label_1} {label_2}')

        # TODO: Add a verification that filter.isSubjectCaseSensitive is true after resolving why it shows as null in the response
        self.cmd('az eventgrid event-subscription show -g {rg} --name {event_subscription_name}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('filter.subjectEndsWith', self.kwargs['subject_ends_with']),
            self.check('filter.includedEventTypes[0]', self.kwargs['event_type_1']),
            self.check('filter.includedEventTypes[1]', self.kwargs['event_type_2']),
            self.check('labels[0]', self.kwargs['label_1']),
            self.check('labels[1]', self.kwargs['label_2']),
        ])
        self.cmd('az eventgrid event-subscription show-endpoint-url --resource-group {rg} --name {event_subscription_name}', checks=[
            self.check('endpointUrl', self.kwargs['endpoint_url']),
        ])
        self.cmd('az eventgrid event-subscription list -g {rg}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])
        self.cmd('az eventgrid event-subscription delete --resource-group {rg} --name {event_subscription_name}')
