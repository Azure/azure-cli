# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.testsdk import ScenarioTest, JMESPathCheck, ResourceGroupPreparer, StorageAccountPreparer


class EventGridTests(ScenarioTest):
    def test_topic_types(self):
        self.cmd('az eventgrid topic-type list', checks=[
            JMESPathCheck('[0].type', 'Microsoft.EventGrid/topicTypes'),
        ])
        self.cmd('az eventgrid topic-type show --name Microsoft.Resources.Subscriptions', checks=[
            JMESPathCheck('type', 'Microsoft.EventGrid/topicTypes'),
            JMESPathCheck('name', 'Microsoft.Resources.Subscriptions'),
        ])
        self.cmd('az eventgrid topic-type list-event-types --name Microsoft.Resources.Subscriptions', checks=[
            JMESPathCheck('[0].type', 'Microsoft.EventGrid/topicTypes/eventTypes'),
        ])

    @ResourceGroupPreparer()
    def test_create_topic(self, resource_group):
        topic_name = self.create_random_name(prefix='cli', length=40)
        event_subscription_name = self.create_random_name(prefix='cli', length=40)
        self.cmd(
            'az eventgrid topic create --name {} --resource-group {} --location {}'
            .format(topic_name, resource_group, 'westus2'))
        self.cmd('az eventgrid topic show --name {} --resource-group {}'.format(topic_name, resource_group), checks=[
            JMESPathCheck('type', 'Microsoft.EventGrid/topics'),
            JMESPathCheck('name', topic_name),
        ])
        self.cmd('az eventgrid topic key list --name {} --resource-group {}'.format(topic_name, resource_group))
        self.cmd('az eventgrid topic key regenerate --name {} --resource-group {} --key-name key1'.format(topic_name, resource_group))
        self.cmd('az eventgrid topic key regenerate --name {} --resource-group {} --key-name key2'.format(topic_name, resource_group))
        self.cmd('az eventgrid topic event-subscription create --topic-name {} -g {} --name {} --endpoint https://requestb.in/18zmdhv1'.format(topic_name, resource_group, event_subscription_name), checks=[
            JMESPathCheck('type', 'Microsoft.EventGrid/eventSubscriptions'),
            JMESPathCheck('provisioningState', 'Succeeded'),
            JMESPathCheck('name', event_subscription_name),
        ])
        self.cmd('az eventgrid topic event-subscription show --topic-name {} -g {} --name {}'.format(topic_name, resource_group, event_subscription_name), checks=[
            JMESPathCheck('type', 'Microsoft.EventGrid/eventSubscriptions'),
            JMESPathCheck('provisioningState', 'Succeeded'),
            JMESPathCheck('name', event_subscription_name),
        ])
        self.cmd('az eventgrid topic event-subscription show-endpoint-url --topic-name {} -g {} --name {}'.format(topic_name, resource_group, event_subscription_name), checks=[
            JMESPathCheck('endpointUrl', 'https://requestb.in/18zmdhv1'),
        ])
        self.cmd('az eventgrid topic event-subscription list --topic-name {} -g {}'.format(topic_name, resource_group), checks=[
            JMESPathCheck('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            JMESPathCheck('[0].provisioningState', 'Succeeded'),
        ])
        self.cmd('az eventgrid topic event-subscription delete --topic-name {} -g {} --name {}'.format(topic_name, resource_group, event_subscription_name))
        self.cmd('az eventgrid topic delete --name {} --resource-group {}'
                 .format(topic_name, resource_group))

    @ResourceGroupPreparer()
    def test_create_event_subscriptions_to_arm_resource_group(self, resource_group):
        event_subscription_name = 'eventsubscription2'
        ENDPOINT_URL = 'https://requestb.in/18zmdhv1'
        self.cmd('az eventgrid event-subscription create -g {} --name {} --endpoint {} --subject-begins-with mysubject_prefix'.format(resource_group, event_subscription_name, ENDPOINT_URL))
        self.cmd('az eventgrid event-subscription show -g {} --name {}'.format(resource_group, event_subscription_name), checks=[
            JMESPathCheck('type', 'Microsoft.EventGrid/eventSubscriptions'),
            JMESPathCheck('filter.subjectBeginsWith', 'mysubject_prefix')
        ])
        self.cmd('az eventgrid event-subscription show-endpoint-url --resource-group {} --name {}'.format(resource_group, event_subscription_name), checks=[
            JMESPathCheck('endpointUrl', ENDPOINT_URL),
        ])
        self.cmd('az eventgrid event-subscription list -g {}'.format(resource_group), checks=[
            JMESPathCheck('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            JMESPathCheck('[0].provisioningState', 'Succeeded'),
        ])
        self.cmd('az eventgrid event-subscription delete --resource-group {} --name {}'.format(resource_group, event_subscription_name))

    def test_create_event_subscriptions_to_resource(self):
        event_subscription_name = self.create_random_name(prefix='cli', length=40)

        resource_group = 'rajagrid'
        storage_account = 'rajagridstorageblobonly'

        self.cmd('az eventgrid resource event-subscription create -g {} --provider-namespace Microsoft.Storage --resource-type storageAccounts --resource-name {} --name {} --endpoint https://requestb.in/18zmdhv1'.format(resource_group, storage_account, event_subscription_name), checks=[
            JMESPathCheck('type', 'Microsoft.EventGrid/eventSubscriptions'),
            JMESPathCheck('provisioningState', 'Succeeded'),
            JMESPathCheck('name', event_subscription_name),
        ])
        self.cmd('az eventgrid resource event-subscription show -g {} --provider-namespace Microsoft.Storage --resource-type storageAccounts --resource-name {} --name {}'.format(resource_group, storage_account, event_subscription_name), checks=[
            JMESPathCheck('type', 'Microsoft.EventGrid/eventSubscriptions'),
            JMESPathCheck('provisioningState', 'Succeeded'),
            JMESPathCheck('name', event_subscription_name),
        ])
        self.cmd('az eventgrid resource event-subscription show-endpoint-url -g {} --provider-namespace Microsoft.Storage --resource-type storageAccounts --resource-name {} --name {}'.format(resource_group, storage_account, event_subscription_name), checks=[
            JMESPathCheck('endpointUrl', 'https://requestb.in/18zmdhv1'),
        ])
        self.cmd('az eventgrid resource event-subscription list -g {} --provider-namespace Microsoft.Storage --resource-type storageAccounts --resource-name {}'.format(resource_group, storage_account), checks=[
            JMESPathCheck('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            JMESPathCheck('[0].provisioningState', 'Succeeded'),
        ])
        self.cmd('az eventgrid resource event-subscription delete -g {} --name {} --provider-namespace Microsoft.Storage --resource-type storageAccounts --resource-name {}'.format(resource_group, event_subscription_name, storage_account))

    @ResourceGroupPreparer()
    def test_create_event_subscriptions_with_filters(self, resource_group):
        event_subscription_name = 'eventsubscription2'
        ENDPOINT_URL = 'https://requestb.in/18zmdhv1'
        SUBJECT_ENDS_WITH = 'mysubject_suffix'
        EVENT_TYPE_1 = 'blobCreated'
        EVENT_TYPE_2 = 'blobUpdated'
        LABEL_1 = 'Finance'
        LABEL_2 = 'HR'

        self.cmd('az eventgrid event-subscription create -g {} --name {} --endpoint {} --subject-ends-with {} --included-event-types {} {} --subject-case-sensitive --labels {} {}'.format(resource_group, event_subscription_name, ENDPOINT_URL, SUBJECT_ENDS_WITH, EVENT_TYPE_1, EVENT_TYPE_2, LABEL_1, LABEL_2))

        # TODO: Add a verification that filter.isSubjectCaseSensitive is true after resolving why it shows as null in the response
        self.cmd('az eventgrid event-subscription show -g {} --name {}'.format(resource_group, event_subscription_name), checks=[
            JMESPathCheck('type', 'Microsoft.EventGrid/eventSubscriptions'),
            JMESPathCheck('filter.subjectEndsWith', SUBJECT_ENDS_WITH),
            JMESPathCheck('filter.includedEventTypes[0]', EVENT_TYPE_1),
            JMESPathCheck('filter.includedEventTypes[1]', EVENT_TYPE_2),
            JMESPathCheck('labels[0]', LABEL_1),
            JMESPathCheck('labels[1]', LABEL_2),
        ])
        self.cmd('az eventgrid event-subscription show-endpoint-url --resource-group {} --name {}'.format(resource_group, event_subscription_name), checks=[
            JMESPathCheck('endpointUrl', ENDPOINT_URL),
        ])
        self.cmd('az eventgrid event-subscription list -g {}'.format(resource_group), checks=[
            JMESPathCheck('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            JMESPathCheck('[0].provisioningState', 'Succeeded'),
        ])
        self.cmd('az eventgrid event-subscription delete --resource-group {} --name {}'.format(resource_group, event_subscription_name))
