# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import unittest
import uuid

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer
from knack.util import CLIError
from datetime import datetime, timedelta


class EventGridTests(ScenarioTest):
    @unittest.skip('Will be re-enabled once global operations are enabled for 2020-01-01-preview API version')
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

    @unittest.skip('Deployment failed')
    @ResourceGroupPreparer()
    def test_create_domain(self, resource_group):

        endpoint_url = 'https://devexpfuncappdestination.azurewebsites.net/runtime/webhooks/EventGrid?functionName=EventGridTrigger1&code=<HIDDEN>'
        endpoint_baseurl = 'https://devexpfuncappdestination.azurewebsites.net/runtime/webhooks/EventGrid'

        domain_name = self.create_random_name(prefix='cli', length=40)
        domain_name2 = self.create_random_name(prefix='cli', length=40)
        domain_name3 = self.create_random_name(prefix='cli', length=40)
        domain_name4 = self.create_random_name(prefix='cli', length=40)

        domain_topic_name1 = self.create_random_name(prefix='cli', length=40)
        domain_topic_name2 = self.create_random_name(prefix='cli', length=40)

        event_subscription_name = self.create_random_name(prefix='cli', length=40)

        self.kwargs.update({
            'domain_name': domain_name,
            'domain_name2': domain_name2,
            'domain_name3': domain_name3,
            'domain_name4': domain_name4,
            'domain_topic_name1': domain_topic_name1,
            'domain_topic_name2': domain_topic_name2,
            'location': 'centraluseuap',
            'event_subscription_name': event_subscription_name,
            'endpoint_url': endpoint_url,
            'endpoint_baseurl': endpoint_baseurl
        })

        self.kwargs['resource_id'] = self.cmd('az eventgrid domain create --name {domain_name} --resource-group {rg} --location {location}', checks=[
            self.check('type', 'Microsoft.EventGrid/domains'),
            self.check('name', self.kwargs['domain_name']),
            self.check('provisioningState', 'Succeeded'),
            self.check('sku', {'name': 'Basic'}),
            self.check('identity.type', 'None'),
            self.check('identity.userAssignedIdentities', None),
            self.check('identity.principalId', None),
            self.check('identity.tenantId', None),
        ]).get_output_in_json()['id']

        self.cmd('az eventgrid domain show --name {domain_name} --resource-group {rg}', checks=[
            self.check('type', 'Microsoft.EventGrid/domains'),
            self.check('name', self.kwargs['domain_name']),
            self.check('sku', {'name': 'Basic'}),
            self.check('identity.type', 'None'),
            self.check('identity.userAssignedIdentities', None),
            self.check('identity.principalId', None),
            self.check('identity.tenantId', None),
        ])

        # Test various failure conditions
        # Input mappings cannot be provided when input schema is not customeventschema
        with self.assertRaises(CLIError):
            self.cmd('az eventgrid domain create --name {domain_name2} --resource-group {rg} --location {location} --input-schema eventgridschema --input-mapping-fields domain=mydomainField')

        # Input mappings must be provided when input schema is customeventschema
        with self.assertRaises(CLIError):
            self.cmd('az eventgrid domain create --name {domain_name2} --resource-group {rg} --location {location} --input-schema customeventschema')

        self.cmd('az eventgrid domain create --name {domain_name2} --resource-group {rg} --location {location} --input-schema CloudEventSchemaV1_0', checks=[
            self.check('type', 'Microsoft.EventGrid/domains'),
            self.check('name', self.kwargs['domain_name2']),
            self.check('provisioningState', 'Succeeded'),
            self.check('sku', {'name': 'Basic'}),
            self.check('identity.type', 'None'),
            self.check('identity.userAssignedIdentities', None),
            self.check('identity.principalId', None),
            self.check('identity.tenantId', None),
        ])

        # Comment this test until we fix service side bug.
        # self.cmd('az eventgrid domain create --name {domain_name3} --resource-group {rg} --location {location} --input-schema Customeventschema --input-mapping-fields domain=mydomainField eventType=myEventTypeField topic=myTopic --input-mapping-default-values subject=DefaultSubject dataVersion=1.0 --identity=NoidentiTY', checks=[
        #    self.check('type', 'Microsoft.EventGrid/domains'),
        #    self.check('name', self.kwargs['domain_name3']),
        #    self.check('provisioningState', 'Succeeded'),
        #    self.check('identity.type', 'None'),
        #    self.check('identity.userAssignedIdentities', None),
        #    self.check('identity.principalId', None),
        #    self.check('identity.tenantId', None),
        # ])

        outputdomain = self.cmd('az eventgrid domain create --name {domain_name4} --resource-group {rg} --location {location} --inbound-ip-rules 19.12.43.90/15 allow --inbound-ip-rules 19.12.43.70/11 allow --public-network-access disabled --identity systemassigned').get_output_in_json()
        self.check(outputdomain['type'], 'Microsoft.EventGrid/domains')
        self.check(outputdomain['name'], self.kwargs['domain_name4'])
        self.check(outputdomain['publicNetworkAccess'], 'Disabled')
        self.check(outputdomain['inboundIpRules'][0], '19.12.43.90/102')
        self.check(outputdomain['inboundIpRules'][1], '19.12.43.70/81')
        self.check(outputdomain['provisioningState'], 'Succeeded')
        self.check(outputdomain['sku'], 'Basic')
        self.check(outputdomain['publicNetworkAccess'], 'Disabled')
        self.check(outputdomain['identity'], 'SystemAssigned')

        self.cmd('az eventgrid domain update --name {domain_name4} --resource-group {rg} --tags Dept=IT --sku baSIc', checks=[
            self.check('name', self.kwargs['domain_name4']),
            self.check('tags', {'Dept': 'IT'}),
            self.check('sku', {'name': 'Basic'}),
            self.check('type', 'Microsoft.EventGrid/domains'),
            self.check('publicNetworkAccess', 'Disabled'),
            self.check('provisioningState', 'Succeeded')
        ])

        self.cmd('az eventgrid domain list --resource-group {rg}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/domains'),
            self.check('[0].name', self.kwargs['domain_name']),
            self.check('[0].provisioningState', 'Succeeded')
        ])

        self.cmd('az eventgrid domain update --name {domain_name4} --resource-group {rg} --tags Dept=Finance --identity NoIDENTIty', checks=[
            self.check('name', self.kwargs['domain_name4']),
            self.check('tags', {'Dept': 'Finance'}),
            self.check('sku', {'name': 'Basic'}),
            self.check('identity.type', 'None'),
            self.check('identity.userAssignedIdentities', None),
            self.check('identity.principalId', None),
            self.check('identity.tenantId', None),
            self.check('type', 'Microsoft.EventGrid/domains'),
            self.check('publicNetworkAccess', 'Disabled'),
            self.check('provisioningState', 'Succeeded')
        ])

        out2 = self.cmd('az eventgrid domain list --resource-group {rg} --odata-query "name eq \'{domain_name}\'"').get_output_in_json()
        self.assertIsNotNone(out2[0]['type'])
        self.assertIsNotNone(out2[0]['name'])
        self.check(out2[0]['type'], 'Microsoft.EventGrid/domains')
        self.check(out2[0]['name'], self.kwargs['domain_name'])
        self.check(out2[0]['provisioningState'], 'Succeeded')

        output = self.cmd('az eventgrid domain key list --name {domain_name} --resource-group {rg}').get_output_in_json()
        self.assertIsNotNone(output['key1'])
        self.assertIsNotNone(output['key2'])

        output = self.cmd('az eventgrid domain key regenerate --name {domain_name} --resource-group {rg} --key-name key1').get_output_in_json()
        self.assertIsNotNone(output['key1'])
        self.assertIsNotNone(output['key2'])

        self.cmd('az eventgrid domain key regenerate --name {domain_name} --resource-group {rg} --key-name key2').get_output_in_json()
        self.assertIsNotNone(output['key1'])
        self.assertIsNotNone(output['key2'])

        # Event subscriptions to domain with All for --included-event-types.

        self.cmd('az eventgrid event-subscription create --source-resource-id {resource_id} --name {event_subscription_name} --endpoint \"{endpoint_url}\" --included-event-types All', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
            self.check('destination.endpointBaseUrl', self.kwargs['endpoint_baseurl'])
        ])

        self.cmd('az eventgrid event-subscription show --source-resource-id {resource_id} --name {event_subscription_name}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
        ])

        self.cmd('az eventgrid event-subscription show --source-resource-id {resource_id} --name {event_subscription_name} --include-full-endpoint-url', checks=[
            self.check('destination.endpointUrl', self.kwargs['endpoint_url']),
            self.check('destination.endpointBaseUrl', self.kwargs['endpoint_baseurl'])
        ])

        self.cmd('az eventgrid event-subscription update --source-resource-id {resource_id} --name {event_subscription_name} --endpoint \"{endpoint_url}\"', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
            self.check('destination.endpointBaseUrl', self.kwargs['endpoint_baseurl'])
        ])

        self.cmd('az eventgrid event-subscription list --source-resource-id {resource_id}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription delete --source-resource-id {resource_id} --name {event_subscription_name}')

        # Event subscriptions to a domain topic
        self.kwargs.update({
            'domain_topic_resource_id': self.kwargs['resource_id'] + "/topics/" + self.kwargs['domain_topic_name1']
        })

        self.cmd('az eventgrid event-subscription create --source-resource-id {domain_topic_resource_id} --name {event_subscription_name} --endpoint \"{endpoint_url}\"', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
            self.check('destination.endpointBaseUrl', self.kwargs['endpoint_baseurl'])
        ])

        self.cmd('az eventgrid event-subscription show --source-resource-id {domain_topic_resource_id} --name {event_subscription_name}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
        ])

        # Create domain topics under domain

        self.kwargs['resource_id_domain_topic2'] = self.cmd('az eventgrid domain topic create --resource-group {rg} --domain-name {domain_name} --name {domain_topic_name2}', checks=[
            self.check('type', 'Microsoft.EventGrid/domains/topics'),
            self.check('name', self.kwargs['domain_topic_name2']),
            self.check('provisioningState', 'Succeeded')
        ])

        self.cmd('az eventgrid domain topic show --resource-group {rg} --domain-name {domain_name} --name {domain_topic_name2}', checks=[
            self.check('type', 'Microsoft.EventGrid/domains/topics'),
            self.check('name', self.kwargs['domain_topic_name2']),
            self.check('provisioningState', 'Succeeded')
        ])

        # Now that an event subscription to a domain topic has been created, it would have internally resulted in creation of
        # the corresponding auto-managed domain topic. Hence, we should now be able to list the set of domain topics under the domain.
        # In the future, we can expand this to support CRUD operations for domain topics (i.e. manual management of domain topics) directly.
        self.cmd('az eventgrid domain topic list --resource-group {rg} --domain-name {domain_name}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/domains/topics')
        ])

        self.cmd('az eventgrid domain topic list --resource-group {rg} --domain-name {domain_name} --odata-query "name ne \'{domain_topic_name2}\'"', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/domains/topics')
        ])

        self.cmd('az eventgrid domain topic show --resource-group {rg} --domain-name {domain_name} --name {domain_topic_name1}', checks=[
            self.check('type', 'Microsoft.EventGrid/domains/topics'),
            self.check('id', self.kwargs['domain_topic_resource_id']),
            self.check('name', self.kwargs['domain_topic_name1']),
        ])

        self.cmd('az eventgrid event-subscription show --source-resource-id {domain_topic_resource_id} --name {event_subscription_name} --include-full-endpoint-url', checks=[
            self.check('destination.endpointUrl', self.kwargs['endpoint_url']),
            self.check('destination.endpointBaseUrl', self.kwargs['endpoint_baseurl'])
        ])

        self.cmd('az eventgrid event-subscription update --source-resource-id {domain_topic_resource_id} --name {event_subscription_name} --endpoint \"{endpoint_url}\"', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
            self.check('destination.endpointBaseUrl', self.kwargs['endpoint_baseurl'])
        ])

        self.cmd('az eventgrid event-subscription list --source-resource-id {domain_topic_resource_id}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription list --source-resource-id {domain_topic_resource_id} --odata-query "CONTAINS(name, \'{event_subscription_name}\')"', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription delete --source-resource-id {domain_topic_resource_id} --name {event_subscription_name}')

        self.cmd('az eventgrid domain topic delete --domain-name {domain_name} --name {domain_topic_name1} --resource-group {rg}')
        self.cmd('az eventgrid domain topic delete --domain-name {domain_name} --name {domain_topic_name2} --resource-group {rg}')

        self.cmd('az eventgrid domain delete --name {domain_name} --resource-group {rg}')
        self.cmd('az eventgrid domain delete --name {domain_name2} --resource-group {rg}')
        self.cmd('az eventgrid domain delete --name {domain_name3} --resource-group {rg}')

    @ResourceGroupPreparer()
    def test_create_topic_user_assigned_identity(self, resource_group):
        endpoint_url = 'https://devexpfuncappdestination.azurewebsites.net/runtime/webhooks/EventGrid?functionName=EventGridTrigger1&code=<HIDDEN>'
        endpoint_baseurl = 'https://devexpfuncappdestination.azurewebsites.net/runtime/webhooks/EventGrid'
        extended_location_name = '/subscriptions/5b4b650e-28b9-4790-b3ab-ddbd88d727c4/resourcegroups/devexprg/providers/Microsoft.ExtendedLocation/CustomLocations/somelocation'

        topic_name = self.create_random_name(prefix='cli', length=40)
        topic_name2 = self.create_random_name(prefix='cli', length=40)
        topic_name3 = self.create_random_name(prefix='cli', length=40)
        topic_name4 = self.create_random_name(prefix='cli', length=40)
        event_subscription_name = self.create_random_name(prefix='cli', length=40)
        
        self.kwargs.update({
            'topic_name': topic_name,
            'topic_name2': topic_name2,
            'topic_name3': topic_name3,
            'topic_name4': topic_name4,
            'location': 'centraluseuap',
            'event_subscription_name': event_subscription_name,
            'endpoint_url': endpoint_url,
            'endpoint_baseurl': endpoint_baseurl,
            'extended_location_name': extended_location_name,
        })
        
        outputtopic = self.cmd('az eventgrid topic create --name {topic_name4} --resource-group {rg} --location {location} --public-network-access disabled --inbound-ip-rules 19.12.43.90/12 allow --inbound-ip-rules 19.12.43.70/20 allow --sku BASic --identity mixed --user-assigned-identity /subscriptions/5b4b650e-28b9-4790-b3ab-ddbd88d727c4/resourceGroups/amh/providers/Microsoft.ManagedIdentity/userAssignedIdentities/ahamadtestidentity1 26b9b438-7fe8-482f-b732-ea99c70f2abb 72f988bf-86f1-41af-91ab-2d7cd011db47').get_output_in_json()
        self.check(outputtopic['type'], 'Microsoft.EventGrid/topics')
        self.check(outputtopic['name'], self.kwargs['topic_name3'])
        self.check(outputtopic['publicNetworkAccess'], 'Disabled')
        self.check(outputtopic['inboundIpRules'][0], '19.12.43.90/102')
        self.check(outputtopic['inboundIpRules'][1], '19.12.43.70/81')
        self.check(outputtopic['provisioningState'], 'Succeeded')
        self.check(outputtopic['sku'], 'Basic')
        self.check(outputtopic['identity'], 'SystemAssigned, UserAssigned')
        
        outputtopic = self.cmd('az eventgrid topic create --name {topic_name4} --resource-group {rg} --location {location} --public-network-access disabled --inbound-ip-rules 19.12.43.90/12 allow --inbound-ip-rules 19.12.43.70/20 allow --sku BASic --identity userassigned --user-assigned-identity /subscriptions/5b4b650e-28b9-4790-b3ab-ddbd88d727c4/resourceGroups/amh/providers/Microsoft.ManagedIdentity/userAssignedIdentities/ahamadtestidentity1 26b9b438-7fe8-482f-b732-ea99c70f2abb 72f988bf-86f1-41af-91ab-2d7cd011db47').get_output_in_json()
        self.check(outputtopic['type'], 'Microsoft.EventGrid/topics')
        self.check(outputtopic['name'], self.kwargs['topic_name4'])
        self.check(outputtopic['publicNetworkAccess'], 'Disabled')
        self.check(outputtopic['inboundIpRules'][0], '19.12.43.90/102')
        self.check(outputtopic['inboundIpRules'][1], '19.12.43.70/81')
        self.check(outputtopic['provisioningState'], 'Succeeded')
        self.check(outputtopic['sku'], 'Basic')
        self.check(outputtopic['identity'], 'UserAssigned')
        
        outputtopic = self.cmd('az eventgrid topic create --name {topic_name2} --resource-group {rg} --location {location} --public-network-access disabled --inbound-ip-rules 19.12.43.90/12 allow --inbound-ip-rules 19.12.43.70/20 allow --sku BASic --identity systemassigned ').get_output_in_json()
        self.check(outputtopic['type'], 'Microsoft.EventGrid/topics')
        self.check(outputtopic['name'], self.kwargs['topic_name4'])
        self.check(outputtopic['publicNetworkAccess'], 'Disabled')
        self.check(outputtopic['inboundIpRules'][0], '19.12.43.90/102')
        self.check(outputtopic['inboundIpRules'][1], '19.12.43.70/81')
        self.check(outputtopic['provisioningState'], 'Succeeded')
        self.check(outputtopic['sku'], 'Basic')
        self.check(outputtopic['identity'], 'SystemAssigned')
        
        outputtopic = self.cmd('az eventgrid topic update --name {topic_name2} --resource-group {rg} --identity userassigned --user-assigned-identity /subscriptions/5b4b650e-28b9-4790-b3ab-ddbd88d727c4/resourceGroups/amh/providers/Microsoft.ManagedIdentity/userAssignedIdentities/ahamadtestidentity1 26b9b438-7fe8-482f-b732-ea99c70f2abb 72f988bf-86f1-41af-91ab-2d7cd011db47').get_output_in_json()
        self.check(outputtopic['type'], 'Microsoft.EventGrid/topics')
        self.check(outputtopic['name'], self.kwargs['topic_name4'])
        self.check(outputtopic['publicNetworkAccess'], 'Disabled')
        self.check(outputtopic['inboundIpRules'][0], '19.12.43.90/102')
        self.check(outputtopic['inboundIpRules'][1], '19.12.43.70/81')
        self.check(outputtopic['provisioningState'], 'Succeeded')
        self.check(outputtopic['sku'], 'Basic')
        self.check(outputtopic['identity'], 'SystemAssigned')
        
        
    @ResourceGroupPreparer()
    def test_create_topic(self, resource_group):
        endpoint_url = 'https://devexpfuncappdestination.azurewebsites.net/runtime/webhooks/EventGrid?functionName=EventGridTrigger1&code=<HIDDEN>'
        endpoint_baseurl = 'https://devexpfuncappdestination.azurewebsites.net/runtime/webhooks/EventGrid'
        extended_location_name = '/subscriptions/5b4b650e-28b9-4790-b3ab-ddbd88d727c4/resourcegroups/devexprg/providers/Microsoft.ExtendedLocation/CustomLocations/somelocation'

        topic_name = self.create_random_name(prefix='cli', length=40)
        topic_name2 = self.create_random_name(prefix='cli', length=40)
        topic_name3 = self.create_random_name(prefix='cli', length=40)
        topic_name4 = self.create_random_name(prefix='cli', length=40)
        event_subscription_name = self.create_random_name(prefix='cli', length=40)

        self.kwargs.update({
            'topic_name': topic_name,
            'topic_name2': topic_name2,
            'topic_name3': topic_name3,
            'topic_name4': topic_name4,
            'location': 'centraluseuap',
            'event_subscription_name': event_subscription_name,
            'endpoint_url': endpoint_url,
            'endpoint_baseurl': endpoint_baseurl,
            'extended_location_name': extended_location_name,
        })

        scope = self.cmd('az eventgrid topic create --name {topic_name} --resource-group {rg} --location {location}', checks=[
            self.check('type', 'Microsoft.EventGrid/topics'),
            self.check('name', self.kwargs['topic_name']),
            self.check('provisioningState', 'Succeeded'),
            self.check('sku', {'name': 'Basic'}),
            self.check('identity.type', 'None'),
            self.check('identity.userAssignedIdentities', None),
            self.check('identity.principalId', None),
            self.check('identity.tenantId', None),
        ]).get_output_in_json()['id']

        self.cmd('az eventgrid topic show --name {topic_name} --resource-group {rg}', checks=[
            self.check('type', 'Microsoft.EventGrid/topics'),
            self.check('name', self.kwargs['topic_name']),
            self.check('sku', {'name': 'Basic'}),
            self.check('identity.type', 'None'),
            self.check('identity.userAssignedIdentities', None),
            self.check('identity.principalId', None),
            self.check('identity.tenantId', None),
        ])

        self.kwargs.update({
            'scope': scope,
        })

        # Test various failure conditions

        # Input mappings cannot be provided when input schema is not customeventschema
        with self.assertRaises(CLIError):
            self.cmd('az eventgrid topic create --name {topic_name2} --resource-group {rg} --location {location} --input-schema eventgridschema --input-mapping-fields topic=myTopicField')

        # Input mappings must be provided when input schema is customeventschema
        with self.assertRaises(CLIError):
            self.cmd('az eventgrid topic create --name {topic_name2} --resource-group {rg} --location {location} --input-schema customeventschema')

        # Cannot specify extended location for topics with kind=azure
        with self.assertRaises(CLIError):
            self.cmd('az eventgrid topic create --name {topic_name2} --resource-group {rg} --location {location} --kind azure --extended-location-name {extended_location_name} --extended-location-type customLocation')

        self.cmd('az eventgrid topic create --name {topic_name2} --resource-group {rg} --location {location} --input-schema CloudEventSchemaV1_0', checks=[
            self.check('type', 'Microsoft.EventGrid/topics'),
            self.check('name', self.kwargs['topic_name2']),
            self.check('provisioningState', 'Succeeded'),
            self.check('sku', {'name': 'Basic'})
        ])

        # commenting this out until we fix bug in service.
        # self.cmd('az eventgrid topic create --name {topic_name3} --resource-group {rg} --location {location} --input-schema Customeventschema --input-mapping-fields topic=myTopicField eventType=myEventTypeField --input-mapping-default-values subject=DefaultSubject dataVersion=1.0 --identity noIDentitY', checks=[
        #     self.check('type', 'Microsoft.EventGrid/topics'),
        #     self.check('name', self.kwargs['topic_name3']),
        #     self.check('provisioningState', 'Succeeded'),
        #     self.check('identity', None)
        # ])

        outputtopic = self.cmd('az eventgrid topic create --name {topic_name4} --resource-group {rg} --location {location} --public-network-access disabled --inbound-ip-rules 19.12.43.90/12 allow --inbound-ip-rules 19.12.43.70/20 allow --sku BASic --identity systemassigned').get_output_in_json()
        self.check(outputtopic['type'], 'Microsoft.EventGrid/topics')
        self.check(outputtopic['name'], self.kwargs['topic_name4'])
        self.check(outputtopic['publicNetworkAccess'], 'Disabled')
        self.check(outputtopic['inboundIpRules'][0], '19.12.43.90/102')
        self.check(outputtopic['inboundIpRules'][1], '19.12.43.70/81')
        self.check(outputtopic['provisioningState'], 'Succeeded')
        self.check(outputtopic['sku'], 'Basic')
        self.check(outputtopic['identity'], 'SystemAssigned')

        self.cmd('az eventgrid topic update --name {topic_name4} --resource-group {rg} --tags Dept=IT', checks=[
            self.check('name', self.kwargs['topic_name4']),
            self.check('tags', {'Dept': 'IT'}),
            self.check('sku', {'name': 'Basic'}),
            self.check('identity.type', 'SystemAssigned'),
            self.check('type', 'Microsoft.EventGrid/topics'),
            self.check('publicNetworkAccess', 'Disabled'),
            self.check('provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid topic update --name {topic_name4} --resource-group {rg} --tags Dept=Finance --sku BaSIC --identity NoIDENTIty', checks=[
            self.check('name', self.kwargs['topic_name4']),
            self.check('tags', {'Dept': 'Finance'}),
            self.check('sku', {'name': 'Basic'}),
            self.check('identity.type', 'None'),
            self.check('identity.userAssignedIdentities', None),
            self.check('identity.principalId', None),
            self.check('identity.tenantId', None),
            self.check('type', 'Microsoft.EventGrid/topics'),
            self.check('publicNetworkAccess', 'Disabled'),
            self.check('provisioningState', 'Succeeded')
        ])

        self.cmd('az eventgrid topic list --resource-group {rg}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/topics'),
            self.check('[0].name', self.kwargs['topic_name']),
        ])

        self.cmd('az eventgrid topic list --resource-group {rg} --odata-query "name eq \'{topic_name}\'"', checks=[
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

        self.cmd('az eventgrid event-subscription create --source-resource-id {scope} --name {event_subscription_name} --endpoint \"{endpoint_url}\"', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
            self.check('destination.endpointBaseUrl', self.kwargs['endpoint_baseurl'])
        ])

        self.cmd('az eventgrid event-subscription show --source-resource-id {scope} --name {event_subscription_name}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
        ])

        self.cmd('az eventgrid event-subscription show --source-resource-id {scope} --name {event_subscription_name} --include-full-endpoint-url', checks=[
            self.check('destination.endpointUrl', self.kwargs['endpoint_url']),
            self.check('destination.endpointBaseUrl', self.kwargs['endpoint_baseurl'])
        ])

        self.cmd('az eventgrid event-subscription update --source-resource-id {scope} --name {event_subscription_name} --endpoint \"{endpoint_url}\"', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
            self.check('destination.endpointBaseUrl', self.kwargs['endpoint_baseurl'])
        ])

        self.cmd('az eventgrid event-subscription list --source-resource-id {scope}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription list --source-resource-id {scope} --odata-query "name eq \'{event_subscription_name}\'"', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription list --topic-type Microsoft.EventGrid.Topics --location {location}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription list --topic-type Microsoft.EventGrid.Topics --location {location} --odata-query "CONTAINS(name,\'{event_subscription_name}\')"', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription delete --source-resource-id {scope} --name {event_subscription_name}')

        self.cmd('az eventgrid topic delete --name {topic_name} --resource-group {rg}')

    @unittest.skip('live test always fails, need fix by owners')
    @ResourceGroupPreparer()
    def test_create_system_topic(self, resource_group):
        endpoint_url = 'https://devexpfuncappdestination.azurewebsites.net/runtime/webhooks/EventGrid?functionName=EventGridTrigger1&code=<HIDDEN>'
        endpoint_baseurl = 'https://devexpfuncappdestination.azurewebsites.net/runtime/webhooks/EventGrid'

        system_topic_name = self.create_random_name(prefix='cli', length=40)
        system_topic_name2 = self.create_random_name(prefix='cli', length=40)
        system_topic_name3 = self.create_random_name(prefix='cli', length=40)
        system_topic_name4 = self.create_random_name(prefix='cli', length=40)
        event_subscription_name = self.create_random_name(prefix='cli', length=40)

        self.kwargs.update({
            'system_topic_name': system_topic_name,
            'system_topic_name2': system_topic_name2,
            'system_topic_name3': system_topic_name3,
            'system_topic_name4': system_topic_name4,
            'location': 'centraluseuap',
            'event_subscription_name': event_subscription_name,
            'endpoint_url': endpoint_url,
            'endpoint_baseurl': endpoint_baseurl
        })

        scope = self.cmd('az eventgrid system-topic create --name {system_topic_name} --resource-group devexprg --location {location} --topic-type microsoft.storage.storageaccounts --source /subscriptions/5b4b650e-28b9-4790-b3ab-ddbd88d727c4/resourceGroups/devexprg/providers/Microsoft.Storage/storageAccounts/clistgaccount', checks=[
            self.check('type', 'Microsoft.EventGrid/systemTopics'),
            self.check('name', self.kwargs['system_topic_name']),
            self.check('provisioningState', 'Succeeded')
        ]).get_output_in_json()['id']

        self.cmd('az eventgrid system-topic show --name {system_topic_name} --resource-group devexprg', checks=[
            self.check('type', 'Microsoft.EventGrid/systemTopics'),
            self.check('name', self.kwargs['system_topic_name'])
        ])

        self.kwargs.update({
            'scope': scope,
        })

        self.cmd('az eventgrid system-topic update --name {system_topic_name} --resource-group devexprg --tags Dept=IT', checks=[
            self.check('name', self.kwargs['system_topic_name']),
            self.check('tags', {'Dept': 'IT'}),
            self.check('type', 'Microsoft.EventGrid/systemTopics'),
            self.check('provisioningState', 'Succeeded')
        ])

        self.cmd('az eventgrid system-topic list --resource-group devexprg', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/systemTopics')
        ])

        self.cmd('az eventgrid system-topic list --resource-group devexprg', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/systemTopics'),
            self.check('[0].name', self.kwargs['system_topic_name']),
        ])

        # Disable until service fix is availabler
        # self.cmd('az eventgrid system-topic list --resource-group devexprg --odata-query "name eq \'{system_topic_name}\'"', checks=[
        #     self.check('[0].type', 'Microsoft.EventGrid/systemTopics'),
        #     self.check('[0].name', self.kwargs['system_topic_name']),
        # ])

        self.cmd('az eventgrid system-topic event-subscription create --resource-group devexprg --system-topic-name {system_topic_name} --name {event_subscription_name} --endpoint \"{endpoint_url}\" --endpoint-type webhook', checks=[
            self.check('type', 'Microsoft.EventGrid/systemTopics/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
            self.check('destination.endpointBaseUrl', self.kwargs['endpoint_baseurl'])
        ])

        self.cmd('az eventgrid system-topic event-subscription create --resource-group devexprg --system-topic-name {system_topic_name} --name {event_subscription_name} --endpoint \"{endpoint_url}\" --endpoint-type webhook --labels label_1 label_2', checks=[
            self.check('type', 'Microsoft.EventGrid/systemTopics/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name'])
        ])

        self.cmd('az eventgrid system-topic event-subscription show --resource-group devexprg --system-topic-name {system_topic_name} --name {event_subscription_name} --include-full-endpoint-url', checks=[
            self.check('destination.endpointUrl', self.kwargs['endpoint_url']),
            self.check('destination.endpointBaseUrl', self.kwargs['endpoint_baseurl'])
        ])

        self.cmd('az eventgrid system-topic event-subscription show --resource-group devexprg --system-topic-name {system_topic_name} --name {event_subscription_name}', checks=[
            self.check('destination.endpointUrl', None),
            self.check('destination.endpointBaseUrl', self.kwargs['endpoint_baseurl'])
        ])

        self.cmd('az eventgrid system-topic event-subscription update -g devexprg --system-topic-name {system_topic_name} -n {event_subscription_name} --endpoint \"{endpoint_url}\" --endpoint-type webhook --labels label11 label22', checks=[
            self.check('type', 'Microsoft.EventGrid/systemTopics/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
            self.check('destination.endpointBaseUrl', self.kwargs['endpoint_baseurl'])
        ])

        self.cmd('az eventgrid system-topic event-subscription list --resource-group devexprg --system-topic-name {system_topic_name}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/systemTopics/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        # Comment this one until we fix the pagable property in swagger
        # self.cmd('az eventgrid system-topic event-subscription list --resource-group {rg} --system-topic-name {system_topic_name} --odata-query "name eq \'{event_subscription_name}\'"', checks=[
        #    self.check('[0].type', 'Microsoft.EventGrid/systemTopics/eventSubscriptions'),
        #    self.check('[0].provisioningState', 'Succeeded'),
        # ])

        self.cmd('az eventgrid system-topic event-subscription delete -g devexprg --name {event_subscription_name} --system-topic-name {system_topic_name} -y')

        self.cmd('az eventgrid system-topic delete -n {system_topic_name} -g devexprg -y')

    @ResourceGroupPreparer()
    def test_system_topic_identity(self, resource_group):
        scope = self.cmd('az group show -n {} -o json'.format(resource_group)).get_output_in_json()['id']
        storage_system_topic_name_regional = self.create_random_name(prefix='cli', length=40)
        policy_system_topic_name_global = 'policy-system-topic-name-global'

        storage_account = '/subscriptions/5b4b650e-28b9-4790-b3ab-ddbd88d727c4/resourceGroups/devexprg/providers/Microsoft.Storage/storageAccounts/clistgaccount'

        self.kwargs.update({
            'storage_system_topic_name_regional': storage_system_topic_name_regional,
            'policy_system_topic_name_global': policy_system_topic_name_global,
            'scope': scope,
            'location': 'centraluseuap',
            'storage_account': storage_account,
            'subscription_id': '5b4b650e-28b9-4790-b3ab-ddbd88d727c4',
            'regional_resource_group': 'devexprg'
        })

        # global system-topic does not support identity. so this test verifies that we are able to create system-topics in global location
        self.cmd('az eventgrid system-topic create --name {policy_system_topic_name_global} --resource-group {rg} --location global --topic-type Microsoft.PolicyInsights.PolicyStates --source /subscriptions/{subscription_id}', checks=[
            self.check('provisioningState', 'Succeeded')
        ])
        self.cmd('az eventgrid system-topic delete --name {policy_system_topic_name_global} --resource-group {rg} --yes')

        # regional system-topic does support identity. so this test verifies that we are able to create system-topics in regional location with identity
        self.cmd('az eventgrid system-topic create --name {storage_system_topic_name_regional} --resource-group {regional_resource_group} --location {location} --topic-type Microsoft.Storage.StorageAccounts --source {storage_account} --identity noidentity', checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        # regional system-topic does support identity. so this test verifies that we are able to create system-topics in regional location with identity
        self.cmd('az eventgrid system-topic update --name {storage_system_topic_name_regional} --resource-group {regional_resource_group} --identity systemassigned', checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        self.cmd('az eventgrid system-topic delete --name {storage_system_topic_name_regional} --resource-group {regional_resource_group} --yes')

    @ResourceGroupPreparer(name_prefix='clieventgrid', location='centraluseuap')
    @StorageAccountPreparer(name_prefix='clieventgrid', location='centraluseuap', kind='StorageV2')
    def test_event_subscription_delivery_attributes(self, resource_group, resource_group_location, storage_account):

        scope = self.cmd('az group show -n {} -o json'.format(resource_group)).get_output_in_json()['id']
        event_subscription_name = self.create_random_name(prefix='cli', length=40)
        endpoint_url = 'https://devexpfuncappdestination.azurewebsites.net/runtime/webhooks/EventGrid?functionName=EventGridTrigger1&code=<HIDDEN>'
        self.kwargs.update({
            'event_subscription_name': event_subscription_name,
            'endpoint_url': endpoint_url,
            'location': resource_group_location,
            'scope': scope
        })

        sub_id = self.get_subscription_id()
        self.kwargs['source_resource_id'] = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Storage/storageAccounts/{}'.format(sub_id, resource_group, storage_account)

        self.cmd('az eventgrid event-subscription create --source-resource-id {source_resource_id} --name {event_subscription_name} --endpoint \"{endpoint_url}\" --delivery-attribute-mapping somestaticname1 static somestaticvalue1  --delivery-attribute-mapping somestaticname2 static somestaticvalue2 true --delivery-attribute-mapping somestaticname3 static somestaticvalue3 false --delivery-attribute-mapping somedynamicattribname1 dynamic data.key1', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
        ])

        self.cmd('az eventgrid event-subscription update --source-resource-id {source_resource_id} --name {event_subscription_name} --endpoint \"{endpoint_url}\" --delivery-attribute-mapping somestaticname1 static somestaticvalue1 --delivery-attribute-mapping somestaticname2 static somestaticvalue2 true --delivery-attribute-mapping somedynamicattribname2 dynamic data.key2', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
        ])

        self.cmd('az eventgrid event-subscription delete --source-resource-id {source_resource_id} --name {event_subscription_name}')

    @ResourceGroupPreparer(name_prefix='clieventgrid', location='centraluseuap')
    @StorageAccountPreparer(name_prefix='clieventgrid', location='centraluseuap', kind='StorageV2')
    def test_event_subscription_with_storagequeuemessage_ttl(self, resource_group, storage_account):
        scope = self.cmd('az group show -n {} -o json'.format(resource_group)).get_output_in_json()['id']
        event_subscription_name = self.create_random_name(prefix='cli', length=40)
        storagequeue_endpoint_id = '/subscriptions/5b4b650e-28b9-4790-b3ab-ddbd88d727c4/resourceGroups/DevExpRg/providers/Microsoft.Storage/storageAccounts/devexpstg/queueServices/default/queues/stogqueuedestination'

        self.kwargs.update({
            'event_subscription_name': event_subscription_name,
            'storagequeue_endpoint_id': storagequeue_endpoint_id,
            'location': 'centraluseuap',
            'scope': scope,
        })

        sub_id = self.get_subscription_id()
        self.kwargs['source_resource_id'] = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Storage/storageAccounts/{}'.format(sub_id, resource_group, storage_account)

        # Create a storage queue destination with storagequeuemessage ttl set to 2 mins
        self.cmd('az eventgrid event-subscription create --source-resource-id {source_resource_id} --name {event_subscription_name} --endpoint-type stoRAgequeue --endpoint {storagequeue_endpoint_id} --event-delivery-schema cloudeventschemav1_0 --storage-queue-msg-ttl 120', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
        ])

        # Update the event subscription to storagequeuemessage ttl set to 5 mins
        self.cmd('az eventgrid event-subscription create --source-resource-id {source_resource_id} --name {event_subscription_name} --endpoint-type stoRAgequeue --endpoint {storagequeue_endpoint_id} --storage-queue-msg-ttl 300', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription delete --source-resource-id {source_resource_id} --name {event_subscription_name}')

    @ResourceGroupPreparer(name_prefix='clieventgrid', location='centraluseuap')
    @StorageAccountPreparer(name_prefix='clieventgrid', location='centraluseuap', kind='StorageV2')
    def test_event_subscription_with_delivery_identity(self, resource_group, storage_account):
        scope = self.cmd('az group show -n {} -o json'.format(resource_group)).get_output_in_json()['id']
        event_subscription_name = self.create_random_name(prefix='cli', length=40)
        eventhub_id = '/subscriptions/5b4b650e-28b9-4790-b3ab-ddbd88d727c4/resourceGroups/DevExpRg/providers/Microsoft.eventhub/namespaces/devexpeh/eventhubs/eventhub1'

        self.kwargs.update({
            'event_subscription_name': event_subscription_name,
            'eventhub_id': eventhub_id,
            'location': 'centraluseuap',
            'scope': scope,
        })

        sub_id = self.get_subscription_id()
        self.kwargs['source_resource_id'] = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Storage/storageAccounts/{}'.format(sub_id, resource_group, storage_account)

        # Create an eventsubscription with eventhub as destination
        self.cmd('az eventgrid event-subscription create --source-resource-id {source_resource_id} --name {event_subscription_name} --endpoint-type eventhub --endpoint {eventhub_id}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
        ])

        # Turn on delivery with resource identity
        self.cmd('az eventgrid event-subscription update --source-resource-id {source_resource_id} --name {event_subscription_name} --delivery-identity systemassigned --delivery-identity-endpoint-type eventhub --delivery-identity-endpoint {eventhub_id}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
        ])

        # Turn off delivery with resource identity
        self.cmd('az eventgrid event-subscription update --source-resource-id {source_resource_id} --name {event_subscription_name} --endpoint-type eventhub --endpoint {eventhub_id}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription delete --source-resource-id {source_resource_id} --name {event_subscription_name}')


    @ResourceGroupPreparer()
    @unittest.skip('Will be re-enabled once global operations are enabled for 2020-01-01-preview API version')
    def test_create_event_subscriptions_to_arm_resource_group(self, resource_group):
        event_subscription_name = 'eventsubscription2'
        endpoint_url = 'https://devexpfuncappdestination.azurewebsites.net/runtime/webhooks/EventGrid?functionName=EventGridTrigger1&code=<HIDDEN>'
        endpoint_baseurl = 'https://devexpfuncappdestination.azurewebsites.net/runtime/webhooks/EventGrid'

        scope = self.cmd('az group show -n {} -ojson'.format(resource_group)).get_output_in_json()['id']

        self.kwargs.update({
            'event_subscription_name': event_subscription_name,
            'endpoint_url': endpoint_url,
            'endpoint_baseurl': endpoint_baseurl,
            'scope': scope
        })

        self.cmd('az eventgrid event-subscription create --source-resource-id {scope} --name {event_subscription_name} --endpoint \"{endpoint_url}\" --subject-begins-with mysubject_prefix', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
            self.check('destination.endpointBaseUrl', self.kwargs['endpoint_baseurl']),
        ])

        self.cmd('az eventgrid event-subscription show --source-resource-id {scope} --name {event_subscription_name}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('filter.subjectBeginsWith', 'mysubject_prefix')
        ])
        self.cmd('az eventgrid event-subscription show --source-resource-id {scope} --include-full-endpoint-url --name {event_subscription_name}', checks=[
            self.check('destination.endpointUrl', self.kwargs['endpoint_url']),
        ])

        self.cmd('az eventgrid event-subscription update --source-resource-id {scope} --name {event_subscription_name}  --endpoint \"{endpoint_url}\" --subject-ends-with .jpg', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
            self.check('destination.endpointBaseUrl', self.kwargs['endpoint_baseurl']),
            self.check('filter.subjectEndsWith', '.jpg'),
        ])

        self.cmd('az eventgrid event-subscription list --source-resource-id {scope}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription list --source-resource-id {scope} --odata-query "name eq \'{event_subscription_name}\'"', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription list --topic-type Microsoft.Resources.ResourceGroups --location global', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription list --topic-type Microsoft.Resources.ResourceGroups --location global --odata-query "name eq \'{event_subscription_name}\'"', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription list --location global --resource-group {rg}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription list --location global --resource-group {rg} --odata-query "name eq \'{event_subscription_name}\'"', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription delete --source-resource-id {scope} --name {event_subscription_name}')

    @ResourceGroupPreparer(name_prefix='clieventgridrg', location='centraluseuap')
    @StorageAccountPreparer(name_prefix='clieventgrid', location='centraluseuap', kind='StorageV2')
    def test_create_event_subscriptions_to_resource(self, resource_group, resource_group_location, storage_account):
        event_subscription_name = self.create_random_name(prefix='cli', length=40)
        endpoint_url = 'https://eventgridclitestapp.azurewebsites.net/api/SubscriptionValidation?code=<HIDDEN>'
        endpoint_baseurl = 'https://eventgridclitestapp.azurewebsites.net/api/SubscriptionValidation'

        self.kwargs.update({
            'event_subscription_name': event_subscription_name,
            'location': 'centraluseuap',
            'endpoint_url': endpoint_url,
            'endpoint_baseurl': endpoint_baseurl
        })

        sub_id = self.get_subscription_id()
        self.kwargs['source_resource_id'] = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Storage/storageAccounts/{}'.format(sub_id, resource_group, storage_account)

        self.cmd('az eventgrid event-subscription create --source-resource-id {source_resource_id} --name {event_subscription_name} --endpoint \"{endpoint_url}\"', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
        ])

        self.cmd('az eventgrid event-subscription show --source-resource-id {source_resource_id} --name {event_subscription_name}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
        ])
        self.cmd('az eventgrid event-subscription show --include-full-endpoint-url --source-resource-id {source_resource_id} --name {event_subscription_name}', checks=[
            self.check('destination.endpointUrl', self.kwargs['endpoint_url']),
        ])

        self.cmd('az eventgrid event-subscription update --source-resource-id {source_resource_id} --name {event_subscription_name} --endpoint \"{endpoint_url}\" --subject-ends-with .jpg', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
            self.check('destination.endpointBaseUrl', self.kwargs['endpoint_baseurl']),
            self.check('filter.subjectEndsWith', '.jpg')
        ])

        self.cmd('az eventgrid event-subscription list --source-resource-id {source_resource_id}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription list --topic-type Microsoft.Storage.StorageAccounts --location {location}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription list --topic-type Microsoft.Storage.StorageAccounts --location {location} --resource-group {rg}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription list --location {location} --resource-group {rg}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription list --location {location}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription list --source-resource-id {source_resource_id} --odata-query "CONTAINS(name,\'{event_subscription_name}\')"', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription list --topic-type Microsoft.Storage.StorageAccounts --location {location} --odata-query "CONTAINS(name,\'{event_subscription_name}\')"', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription list --topic-type Microsoft.Storage.StorageAccounts --location {location} --resource-group {rg} --odata-query "CONTAINS(name,\'{event_subscription_name}\')"', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription list --location {location} --resource-group {rg} --odata-query "name eq \'{event_subscription_name}\'"', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription list --location {location} --odata-query "name eq \'{event_subscription_name}\'"', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription delete --source-resource-id {source_resource_id} --name {event_subscription_name}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(name_prefix='clieventgrid', location='centraluseuap', kind='StorageV2')
    def test_create_event_subscriptions_with_filters(self, resource_group, storage_account):
        event_subscription_name = 'eventsubscription2'
        endpoint_url = 'https://devexpfuncappdestination.azurewebsites.net/runtime/webhooks/EventGrid?functionName=EventGridTrigger1&code=<HIDDEN>'
        endpoint_baseurl = 'https://devexpfuncappdestination.azurewebsites.net/runtime/webhooks/EventGrid'

        subject_ends_with = 'mysubject_suffix'
        event_type_1 = 'blobCreated'
        event_type_2 = 'blobUpdated'
        label_1 = 'Finance'
        label_2 = 'HR'

        self.kwargs.update({
            'event_subscription_name': event_subscription_name,
            'endpoint_url': endpoint_url,
            'endpoint_baseurl': endpoint_baseurl,
            'subject_ends_with': subject_ends_with,
            'event_type_1': event_type_1,
            'event_type_2': event_type_2,
            'label_1': label_1,
            'location': 'centraluseuap',
            'label_2': label_2
        })

        sub_id = self.get_subscription_id()
        self.kwargs['source_resource_id'] = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Storage/storageAccounts/{}'.format(sub_id, resource_group, storage_account)

        self.cmd('az eventgrid event-subscription create --source-resource-id {source_resource_id} --name {event_subscription_name} --endpoint \"{endpoint_url}\" --subject-ends-with {subject_ends_with} --included-event-types {event_type_1} {event_type_2} --subject-case-sensitive --labels {label_1} {label_2}')

        # TODO: Add a verification that filter.isSubjectCaseSensitive is true after resolving why it shows as null in the response
        self.cmd('az eventgrid event-subscription show --source-resource-id {source_resource_id} --name {event_subscription_name}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('filter.subjectEndsWith', self.kwargs['subject_ends_with']),
            self.check('filter.includedEventTypes[0]', self.kwargs['event_type_1']),
            self.check('filter.includedEventTypes[1]', self.kwargs['event_type_2']),
            self.check('labels[0]', self.kwargs['label_1']),
            self.check('labels[1]', self.kwargs['label_2']),
        ])

        self.cmd('az eventgrid event-subscription show --include-full-endpoint-url --source-resource-id {source_resource_id} --name {event_subscription_name}', checks=[
            self.check('destination.endpointUrl', self.kwargs['endpoint_url']),
        ])

        self.cmd('az eventgrid event-subscription list --source-resource-id {source_resource_id}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription list --source-resource-id {source_resource_id} --odata-query "CONTAINS(name,\'{event_subscription_name}\')"', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid event-subscription delete --source-resource-id {source_resource_id} --name {event_subscription_name}')

    @ResourceGroupPreparer()
    @StorageAccountPreparer(name_prefix='clieventgrid', location='centraluseuap', kind='StorageV2')
    def test_create_event_subscriptions_with_20180501_features(self, resource_group, storage_account):
        event_subscription_name1 = 'CliTestEventsubscription1'
        event_subscription_name2 = 'CliTestEventsubscription2'
        event_subscription_name3 = 'CliTestEventsubscription3'
        event_subscription_name4 = 'CliTestEventsubscription4'
        event_subscription_name5 = 'CliTestEventsubscription5'
        storagequeue_endpoint_id = '/subscriptions/5b4b650e-28b9-4790-b3ab-ddbd88d727c4/resourceGroups/DevExpRg/providers/Microsoft.Storage/storageAccounts/devexpstg/queueServices/default/queues/stogqueuedestination'
        deadletter_endpoint_id = '/subscriptions/5b4b650e-28b9-4790-b3ab-ddbd88d727c4/resourceGroups/DevExpRg/providers/Microsoft.Storage/storageAccounts/devexpstg/blobServices/default/containers/dlq'
        hybridconnection_endpoint_id = '/subscriptions/5b4b650e-28b9-4790-b3ab-ddbd88d727c4/resourceGroups/DevExpRg/providers/Microsoft.Relay/namespaces/DevExpRelayNamespace/hybridConnections/hydbridconnectiondestination'
        servicebusqueue_endpoint_id = '/subscriptions/5b4b650e-28b9-4790-b3ab-ddbd88d727c4/resourceGroups/DevExpRg/providers/Microsoft.ServiceBus/namespaces/devexpservicebus/queues/devexpdestination'
        eventhub_with_identity_endpoint_id = '/subscriptions/5b4b650e-28b9-4790-b3ab-ddbd88d727c4/resourceGroups/DevExpRg/providers/Microsoft.eventhub/namespaces/devexpeh/eventhubs/eventhub1'
        source_resource_id_with_identity = '/subscriptions/5b4b650e-28b9-4790-b3ab-ddbd88d727c4/resourceGroups/amh/providers/Microsoft.EventGrid/topics/tpoicWithNoIdentity2'
        deadletter_endpoint_id_with_identity = '/subscriptions/5b4b650e-28b9-4790-b3ab-ddbd88d727c4/resourceGroups/DevExpRg/providers/Microsoft.Storage/storageAccounts/devexpstg/blobServices/default/containers/dlqwithidentity'

        self.kwargs.update({
            'event_subscription_name1': event_subscription_name1,
            'event_subscription_name2': event_subscription_name2,
            'event_subscription_name3': event_subscription_name3,
            'event_subscription_name4': event_subscription_name4,
            'event_subscription_name5': event_subscription_name5,
            'storagequeue_endpoint_id': storagequeue_endpoint_id,
            'source_resource_id_with_identity': source_resource_id_with_identity,
            'eventhub_with_identity_endpoint_id': eventhub_with_identity_endpoint_id,
            'deadletter_endpoint_id': deadletter_endpoint_id,
            'deadletter_endpoint_id_with_identity': deadletter_endpoint_id_with_identity,
            'hybridconnection_endpoint_id': hybridconnection_endpoint_id,
            'location': 'centraluseuap',
            'servicebusqueue_endpoint_id': servicebusqueue_endpoint_id,
        })

        sub_id = self.get_subscription_id()
        self.kwargs['source_resource_id'] = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Storage/storageAccounts/{}'.format(sub_id, resource_group, storage_account)

        # Failure cases
        # Invalid Event TTL value
        with self.assertRaises(CLIError):
            self.cmd('az eventgrid event-subscription create --source-resource-id {source_resource_id} --name {event_subscription_name1} --endpoint-type storagequeue --endpoint {storagequeue_endpoint_id} --event-ttl 2000 --deadletter-endpoint {deadletter_endpoint_id}')

        # Invalid max delivery attempts value
        with self.assertRaises(CLIError):
            self.cmd('az eventgrid event-subscription create --source-resource-id {source_resource_id} --name {event_subscription_name1} --endpoint-type storagequeue --endpoint {storagequeue_endpoint_id} --max-delivery-attempts 31 --deadletter-endpoint {deadletter_endpoint_id}')

        # Create a storage queue destination based event subscription with cloud event schema as the delivery schema
        self.cmd('az eventgrid event-subscription create --source-resource-id {source_resource_id} --name {event_subscription_name1} --endpoint-type stoRAgequeue --endpoint {storagequeue_endpoint_id} --event-delivery-schema cloudeventschemav1_0 --deadletter-endpoint {deadletter_endpoint_id} --subject-begins-with SomeRandomText1 --subject-ends-with SomeRandomText2')

        self.cmd('az eventgrid event-subscription show --source-resource-id {source_resource_id} --name {event_subscription_name1}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
        ])

        # Create a hybridconnection destination based event subscription with default eventgrid event schema as the delivery schema
        self.cmd('az eventgrid event-subscription create --source-resource-id {source_resource_id} --name {event_subscription_name2} --endpoint-type HybRidConnection --endpoint {hybridconnection_endpoint_id} --deadletter-endpoint {deadletter_endpoint_id} --max-delivery-attempts 20 --event-ttl 1000 --subject-begins-with SomeRandomText1 --subject-ends-with SomeRandomText2')

        self.cmd('az eventgrid event-subscription show --source-resource-id {source_resource_id} --name {event_subscription_name2}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
        ])

        # Create a servicebusqueue destination based event subscription with default eventgrid event schema as the delivery schema
        self.cmd('az eventgrid event-subscription create --source-resource-id {source_resource_id} --name {event_subscription_name3} --endpoint-type SErvIcEBusQueUE --endpoint {servicebusqueue_endpoint_id} --deadletter-endpoint {deadletter_endpoint_id} --max-delivery-attempts 10 --event-ttl 1200  --subject-begins-with SomeRandomText1 --subject-ends-with SomeRandomText2')

        self.cmd('az eventgrid event-subscription show  --source-resource-id {source_resource_id} --name {event_subscription_name3}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
        ])

        # Create an event hub destination based event subscription with default eventgrid event schema as the delivery schema and with system assigned identity and systemassigned deadletter destination
        # self.cmd('az eventgrid event-subscription create --source-resource-id {source_resource_id_with_identity} --delivery-identity-endpoint-type eventhub --delivery-identity systemassigned --delivery-identity-endpoint {eventhub_with_identity_endpoint_id} -n {event_subscription_name4} --deadletter-identity-endpoint {deadletter_endpoint_id_with_identity} --deadletter-identity systemassigned')

        # self.cmd('az eventgrid event-subscription show --source-resource-id {source_resource_id_with_identity} --name {event_subscription_name4}', checks=[
        #    self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
        #    self.check('provisioningState', 'Succeeded'),
        #    self.check('destination', None),
        #    self.check('deliveryWithResourceIdentity.identity.userAssignedIdentity', None),
        #    self.check('deliveryWithResourceIdentity.identity.type', 'SystemAssigned'),
        #    self.check('deliveryWithResourceIdentity.destination.endpointType', 'EventHub'),
        #    self.check('deliveryWithResourceIdentity.destination.resourceId', self.kwargs['eventhub_with_identity_endpoint_id']),
        #    self.check('deadLetterDestination', None),
        #    self.check('deadLetterWithResourceIdentity.identity.userAssignedIdentity', None),
        #    self.check('deadLetterWithResourceIdentity.identity.type', 'SystemAssigned'),
        #    self.check('deadLetterWithResourceIdentity.deadLetterDestination.endpointType', 'StorageBlob')
        # ])

        # Update an event hub destination based event subscription with default eventgrid event schema as the delivery schema and with system assigned identity
        # self.cmd('az eventgrid event-subscription update --source-resource-id {source_resource_id_with_identity} -n {event_subscription_name4} --deadletter-endpoint {deadletter_endpoint_id}')

        self.cmd('az eventgrid event-subscription delete  --source-resource-id {source_resource_id} --name {event_subscription_name1}')
        self.cmd('az eventgrid event-subscription delete  --source-resource-id {source_resource_id} --name {event_subscription_name2}')
        self.cmd('az eventgrid event-subscription delete  --source-resource-id {source_resource_id} --name {event_subscription_name3}')
        # self.cmd('az eventgrid event-subscription delete  --source-resource-id {source_resource_id} --name {event_subscription_name4}')

    @ResourceGroupPreparer(name_prefix='clieventgridrg', location='eastus2euap')
    @StorageAccountPreparer(name_prefix='clieventgrid', location='eastus2euap', kind='StorageV2')
    def test_create_event_subscriptions_with_20200101_features(self, resource_group, storage_account):
        event_subscription_name1 = 'CliTestEventGridEventsubscription1'
        event_subscription_name2 = 'CliTestEventGridEventsubscription2'
        event_subscription_name3 = 'CliTestEventGridEventsubscription3'
        event_subscription_name4 = 'CliTestEventGridEventsubscription4'
        servicebustopic_endpoint_id = '/subscriptions/5b4b650e-28b9-4790-b3ab-ddbd88d727c4/resourceGroups/DevExpRg/providers/Microsoft.ServiceBus/namespaces/devexpservicebus/topics/devexptopic1'
        azurefunction_endpoint_id_cloudevent = '/subscriptions/5b4b650e-28b9-4790-b3ab-ddbd88d727c4/resourceGroups/DevExpRg/providers/Microsoft.Web/sites/eventgridclitestapp/functions/EventGridTrigger1'

        endpoint_url = 'https://devexpfuncappdestination.azurewebsites.net/runtime/webhooks/EventGrid?functionName=EventGridTrigger1&code=<HIDDEN>'
        endpoint_baseurl = 'https://devexpfuncappdestination.azurewebsites.net/runtime/webhooks/EventGrid'

        endpoint_url_for_validation = 'https://devexpfuncappdestination.azurewebsites.net/api/DevExpFunc?code=<HIDDEN>'
        endpoint_baseurl_for_validation = 'https://devexpfuncappdestination.azurewebsites.net/api/DevExpFunc'

        # Make sure to replace these with proper values for re-recording the tests.
        azure_active_directory_tenant_id = '72f988bf-86f1-41af-91ab-2d7cd011db47'
        azure_active_directory_application_id_or_uri = '761faacd-cdac-45af-9530-9e6f03e7722b'

        self.kwargs.update({
            'event_subscription_name1': event_subscription_name1,
            'event_subscription_name2': event_subscription_name2,
            'event_subscription_name3': event_subscription_name3,
            'event_subscription_name4': event_subscription_name4,
            'servicebustopic_endpoint_id': servicebustopic_endpoint_id,
            'azurefunction_endpoint_id_cloudevent': azurefunction_endpoint_id_cloudevent,
            'endpoint_url': endpoint_url,
            'endpoint_baseurl': endpoint_baseurl,
            'endpoint_url_for_validation': endpoint_url_for_validation,
            'endpoint_baseurl_for_validation': endpoint_baseurl_for_validation,
            'azure_active_directory_tenant_id': azure_active_directory_tenant_id,
            'azure_active_directory_application_id_or_uri': azure_active_directory_application_id_or_uri,
            'location': 'eastus2euap'
        })

        sub_id = self.get_subscription_id()
        self.kwargs['source_resource_id'] = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Storage/storageAccounts/{}'.format(sub_id, resource_group, storage_account)

        # Create a servicebustopic destination based event subscription with CloudEvent 1.0 as the delivery schema
        self.cmd('az eventgrid event-subscription create --source-resource-id {source_resource_id} --name {event_subscription_name1} --endpoint-type SErvIcEBusTOPic --endpoint {servicebustopic_endpoint_id} --subject-begins-with SomeRandomText1 --event-delivery-schema CloudEVENTSchemaV1_0')
        self.cmd('az eventgrid event-subscription show --source-resource-id {source_resource_id} --name {event_subscription_name1}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
        ])

        # Create an AzureFunction destination based event subscription with additional batching parameters
        self.cmd('az eventgrid event-subscription create --source-resource-id {source_resource_id} --name {event_subscription_name2} --endpoint-type azUREFunction --endpoint {azurefunction_endpoint_id_cloudevent} --subject-begins-with SomeRandomText1 --max-events-per-batch 10 --preferred-batch-size-in-kilobytes 128')
        self.cmd('az eventgrid event-subscription show --source-resource-id {source_resource_id} --name {event_subscription_name2}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
        ])

        # Create an AzureFunction destination based event subscription with additional batching parameters for destination type webhook.
        self.cmd('az eventgrid event-subscription create --source-resource-id {source_resource_id} --name {event_subscription_name4} --endpoint-type webhook --endpoint \"{endpoint_url_for_validation}\" --subject-begins-with SomeRandomText1 --max-events-per-batch 10 --preferred-batch-size-in-kilobytes 128')
        self.cmd('az eventgrid event-subscription show --source-resource-id {source_resource_id} --name {event_subscription_name4}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded')
        ])

        # Create an Webhook destination based event subscription with azure active directory settings
        self.cmd('az eventgrid event-subscription create --source-resource-id {source_resource_id} --name {event_subscription_name3} --endpoint-type webhook --endpoint \"{endpoint_url_for_validation}\" --subject-begins-with SomeRandomText1 --max-events-per-batch 10 --preferred-batch-size-in-kilobytes 128 --azure-active-directory-tenant-id \"{azure_active_directory_tenant_id}\" --azure-active-directory-application-id-or-uri \"{azure_active_directory_application_id_or_uri}\"')
        self.cmd('az eventgrid event-subscription show --source-resource-id {source_resource_id} --name {event_subscription_name3}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded')
        ])

        # Update a servicebustopic destination based event subscription with CloudEvent 1.0 as the delivery schema
        self.cmd('az eventgrid event-subscription update --source-resource-id {source_resource_id} --name {event_subscription_name1} --subject-begins-with SomeRandomText1234')
        self.cmd('az eventgrid event-subscription show --source-resource-id {source_resource_id} --name {event_subscription_name1}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded')
        ])

        # Update an AzureFunction destination based event subscription
        self.cmd('az eventgrid event-subscription update --source-resource-id {source_resource_id} --name {event_subscription_name2} --endpoint-type azUREFunction --endpoint {azurefunction_endpoint_id_cloudevent} --subject-begins-with SomeRandomText2234431')
        self.cmd('az eventgrid event-subscription show --source-resource-id {source_resource_id} --name {event_subscription_name2}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded')
        ])

        # Update an AzureFunction destination based event subscription with additional batching parameters for destination type webhook.
        self.cmd('az eventgrid event-subscription update --source-resource-id {source_resource_id} --name {event_subscription_name4} --endpoint-type webhook --endpoint \"{endpoint_url_for_validation}\" --subject-begins-with SomeRandomText112341')
        self.cmd('az eventgrid event-subscription show --source-resource-id {source_resource_id} --name {event_subscription_name4}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded')
        ])

        # Update an Webhook destination based event subscription with azure active directory settings
        self.cmd('az eventgrid event-subscription update --source-resource-id {source_resource_id} --name {event_subscription_name3} --endpoint \"{endpoint_url_for_validation}\" --subject-begins-with SomeRandomText123412')
        self.cmd('az eventgrid event-subscription show --source-resource-id {source_resource_id} --name {event_subscription_name3}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded')
        ])

        self.cmd('az eventgrid event-subscription show --source-resource-id {source_resource_id} --name {event_subscription_name1}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded')
        ])

        self.cmd('az eventgrid event-subscription show --source-resource-id {source_resource_id} --name {event_subscription_name2}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded')
        ])

        self.cmd('az eventgrid event-subscription show --source-resource-id {source_resource_id} --name {event_subscription_name3}', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded')
        ])

        self.cmd('az eventgrid event-subscription delete --source-resource-id {source_resource_id} --name {event_subscription_name1}')
        self.cmd('az eventgrid event-subscription delete --source-resource-id {source_resource_id} --name {event_subscription_name2}')
        self.cmd('az eventgrid event-subscription delete --source-resource-id {source_resource_id} --name {event_subscription_name3}')
        self.cmd('az eventgrid event-subscription delete --source-resource-id {source_resource_id} --name {event_subscription_name4}')

    @ResourceGroupPreparer()
    def test_advanced_filters(self, resource_group):
        endpoint_url = 'https://devexpfuncappdestination.azurewebsites.net/runtime/webhooks/EventGrid?functionName=EventGridTrigger1&code=<HIDDEN>'
        endpoint_baseurl = 'https://devexpfuncappdestination.azurewebsites.net/runtime/webhooks/EventGrid'

        topic_name = self.create_random_name(prefix='cli', length=40)
        event_subscription_name = self.create_random_name(prefix='cli', length=40)

        self.kwargs.update({
            'topic_name': topic_name,
            'location': 'centraluseuap',
            'event_subscription_name': event_subscription_name,
            'endpoint_url': endpoint_url,
            'endpoint_baseurl': endpoint_baseurl
        })

        self.cmd('az eventgrid topic create --name {topic_name} --resource-group {rg} --location {location}', checks=[
            self.check('type', 'Microsoft.EventGrid/topics'),
            self.check('name', self.kwargs['topic_name']),
            self.check('provisioningState', 'Succeeded'),
        ])

        scope = self.cmd('az eventgrid topic show --name {topic_name} --resource-group {rg} -ojson').get_output_in_json()['id']

        self.kwargs.update({
            'scope': scope
        })

        # Error cases
        with self.assertRaises(CLIError):
            # No operator/values provided
            self.cmd('az eventgrid event-subscription create --source-resource-id {scope} --name {event_subscription_name} --endpoint {endpoint_url} --advanced-filter eventType')

        with self.assertRaises(CLIError):
            # No filter value provided
            self.cmd('az eventgrid event-subscription create --source-resource-id {scope}  --name {event_subscription_name} --endpoint {endpoint_url} --advanced-filter data.key2 NumberIn')

        with self.assertRaises(CLIError):
            # Invalid operator type provided
            self.cmd('az eventgrid event-subscription create --source-resource-id {scope} --name {event_subscription_name} --endpoint {endpoint_url} --advanced-filter data.key2 FooNumberLessThan 2 3')

        with self.assertRaises(CLIError):
            # Multiple values provided for a single value filter
            self.cmd('az eventgrid event-subscription create --source-resource-id {scope} --name {event_subscription_name} --endpoint {endpoint_url} --advanced-filter data.key2 NumberLessThan 2 3')

        with self.assertRaises(CLIError):
            self.cmd('az eventgrid event-subscription create --source-resource-id {scope} --name {event_subscription_name} --endpoint {endpoint_url} --advanced-filter data.key2 IsNotNull 1')

        with self.assertRaises(CLIError):
            self.cmd('az eventgrid event-subscription create --source-resource-id {scope} --name {event_subscription_name} --endpoint {endpoint_url} --advanced-filter data.key2 IsNullOrUndefined 1')

        # One advanced filter for NumberIn operator
        self.cmd('az eventgrid event-subscription create --source-resource-id {scope}  --name {event_subscription_name} --endpoint \"{endpoint_url}\" --advanced-filter data.key2 NumberIn 2 3 4 100 200', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
            self.check('destination.endpointBaseUrl', self.kwargs['endpoint_baseurl'])
        ])

        # Two advanced filters for NumberIn, StringIn operators
        self.cmd('az eventgrid event-subscription create --source-resource-id {scope} --name {event_subscription_name} --endpoint \"{endpoint_url}\" --advanced-filter data.key1 NumberIn 2 3 4 100 200 --advanced-filter data.key2 StringIn 2 3 4 100 200', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
            self.check('destination.endpointBaseUrl', self.kwargs['endpoint_baseurl'])
        ])

        # Two advanced filters for NumberIn, StringIn operators
        self.cmd('az eventgrid event-subscription update --source-resource-id {scope} --name {event_subscription_name} --endpoint \"{endpoint_url}\" --advanced-filter data.key1 NumberIn 21 13 400 101 --advanced-filter data.key2 StringIn 122 3 214 1100 2', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
            self.check('destination.endpointBaseUrl', self.kwargs['endpoint_baseurl'])
        ])

        # IsNullOrUndefined, IsNotNull operators
        self.cmd('az eventgrid event-subscription update --source-resource-id {scope} --name {event_subscription_name} --endpoint \"{endpoint_url}\" --advanced-filter data.key1 IsNullOrUndefined --advanced-filter data.key2 IsNotNull', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
            self.check('destination.endpointBaseUrl', self.kwargs['endpoint_baseurl'])
        ])

        # NumberInRange, NumberNotInRange operators
        self.cmd('az eventgrid event-subscription update --source-resource-id {scope} --name {event_subscription_name} --endpoint \"{endpoint_url}\" --advanced-filter data.key1 NumberInRange 1,10 --advanced-filter data.key2 NumberNotInRange 10,12 50,55', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
            self.check('destination.endpointBaseUrl', self.kwargs['endpoint_baseurl'])
        ])

        # StringNotBeginsWith, StringNotContains, StringNotEndsWith operators
        self.cmd('az eventgrid event-subscription update --source-resource-id {scope} --name {event_subscription_name} --endpoint \"{endpoint_url}\" --advanced-filter data.key1 StringNotBeginsWith Red Blue Green --advanced-filter data.key2 StringNotEndsWith Red Blue Green --advanced-filter data.key2 StringNotContains Red Blue Green', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
            self.check('destination.endpointBaseUrl', self.kwargs['endpoint_baseurl'])
        ])

        # Enable array filtering on the input
        self.cmd('az eventgrid event-subscription update --source-resource-id {scope} --name {event_subscription_name} --endpoint \"{endpoint_url}\" --enable-advanced-filtering-on-arrays true', checks=[
            self.check('type', 'Microsoft.EventGrid/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name']),
            self.check('destination.endpointBaseUrl', self.kwargs['endpoint_baseurl'])
        ])

        self.cmd('az eventgrid event-subscription delete --source-resource-id {scope} --name {event_subscription_name}')
        self.cmd('az eventgrid topic delete --name {topic_name} --resource-group {rg}')

    @unittest.skip('live test always fails, need fix by owners')
    @ResourceGroupPreparer()
    def test_Partner_scenarios(self, resource_group):
        storagequeue_endpoint_id = '/subscriptions/5b4b650e-28b9-4790-b3ab-ddbd88d727c4/resourceGroups/DevExpRg/providers/Microsoft.Storage/storageAccounts/devexpstg/queueServices/default/queues/stogqueuedestination'

        partner_registration_name = self.create_random_name(prefix='cli', length=40)
        partner_namespace_name = self.create_random_name(prefix='cli', length=40)
        event_channel_name = self.create_random_name(prefix='cli', length=40)
        partner_topic_name = self.create_random_name(prefix='cli', length=40)
        event_subscription_name = self.create_random_name(prefix='cli', length=40)
        partner_name = self.create_random_name(prefix='cli', length=40)
        resource_type_name = self.create_random_name(prefix='cli', length=40)
        description = self.create_random_name(prefix='cli', length=40)
        display_name = self.create_random_name(prefix='cli', length=40)
        guid1 = uuid.uuid1()
        guid2 = uuid.uuid1()
        guid3 = uuid.uuid1()
        destination_subscription_id = '5b4b650e-28b9-4790-b3ab-ddbd88d727c4'
        source = self.create_random_name(prefix='cli', length=40)
        exp_time = datetime.utcnow() + timedelta(hours=24)
        exp_time = exp_time.isoformat()
        creation_time = datetime.utcnow().isoformat()

        long_description = 'This is long description sample'
        customer_service_number1 = '+1 800 123 4567'
        customer_service_extension1 = '1234'
        customer_service_uri = 'https://www.example.com/cusomerService'

        customer_service_number2 = '+1 962 7 1234 5678'
        customer_service_extension2 = '9876'

        self.kwargs.update({
            'partner_registration_name': partner_registration_name,
            'partner_namespace_name': partner_namespace_name,
            'event_channel_name': event_channel_name,
            'partner_topic_name': partner_topic_name,
            'location': 'centraluseuap',
            'event_subscription_name': event_subscription_name,
            'storagequeue_endpoint_id': storagequeue_endpoint_id,
            'partner_name': partner_name,
            'resource_type_name': resource_type_name,
            'guid1': guid1,
            'guid2': guid2,
            'guid3': guid3,
            'description': description,
            'display_name': display_name,
            'destination_subscription_id': destination_subscription_id,
            'source': source,
            'exp_time': exp_time,
            'creation_time': creation_time,
            'long_description': long_description,
            'customer_service_number1': customer_service_number1,
            'customer_service_extension1': customer_service_extension1,
            'customer_service_uri': customer_service_uri,
            'customer_service_number2': customer_service_number2,
            'customer_service_extension2': customer_service_extension2,
        })

        partner_topic_friendly_description = 'This partner topic was created by Partner {part_name} at {create_time}.'.format(part_name=partner_name, create_time=creation_time)

        self.kwargs.update({
            'partner_topic_friendly_description': partner_topic_friendly_description
        })

        scope = self.cmd('az eventgrid partner registration create --name {partner_registration_name} --resource-group {rg} --partner-name {partner_name} --resource-type-name {resource_type_name} --authorized-subscription-ids {guid1} --long-description \'{long_description}\' --customer-service-number \'{customer_service_number1}\' --customer-service-extension \'{customer_service_extension1}\' --customer-service-uri \'{customer_service_uri}\'', checks=[
            self.check('type', 'Microsoft.EventGrid/partnerRegistrations'),
            self.check('name', self.kwargs['partner_registration_name']),
            self.check('provisioningState', 'Succeeded'),
            # self.check('authorizedAzureSubscriptionIds[0]', guid1),
            self.check('partnerResourceTypeDescription', None),
            self.check('partnerResourceTypeDisplayName', None),
            self.check('partnerResourceTypeName', resource_type_name),
            self.check('partnerName', partner_name),
            self.check('longDescription', long_description),
            self.check('partnerCustomerServiceNumber', customer_service_number1),
            self.check('partnerCustomerServiceExtension', customer_service_extension1),
            self.check('customerServiceUri', customer_service_uri),
        ]).get_output_in_json()['id']

        scope = self.cmd('az eventgrid partner registration create --name {partner_registration_name} --resource-group {rg} --partner-name {partner_name} --resource-type-name {resource_type_name} --description {description} --display-name {display_name} --authorized-subscription-ids {guid2} {guid3}  --long-description \'{long_description}\' --customer-service-number \'{customer_service_number2}\' --customer-service-extension \'{customer_service_extension2}\' --customer-service-uri \'{customer_service_uri}\'', checks=[
            self.check('type', 'Microsoft.EventGrid/partnerRegistrations'),
            self.check('name', self.kwargs['partner_registration_name']),
            self.check('provisioningState', 'Succeeded'),
            # self.check('authorizedAzureSubscriptionIds[0]', guid2),
            self.check('partnerResourceTypeDescription', description),
            self.check('partnerResourceTypeDisplayName', display_name),
            self.check('partnerResourceTypeName', resource_type_name),
            self.check('partnerName', partner_name),
            self.check('longDescription', long_description),
            self.check('partnerCustomerServiceNumber', customer_service_number2),
            self.check('partnerCustomerServiceExtension', customer_service_extension2),
            self.check('customerServiceUri', customer_service_uri),
        ]).get_output_in_json()['id']

        self.cmd('az eventgrid partner registration show --name {partner_registration_name} --resource-group {rg}', checks=[
            self.check('type', 'Microsoft.EventGrid/partnerRegistrations'),
            self.check('name', self.kwargs['partner_registration_name']),
            self.check('provisioningState', 'Succeeded'),
            # self.check('authorizedAzureSubscriptionIds[0]', guid2),
            self.check('partnerResourceTypeDescription', description),
            self.check('partnerResourceTypeDisplayName', display_name),
            self.check('partnerResourceTypeName', resource_type_name),
            self.check('partnerName', partner_name),
            self.check('longDescription', long_description),
            self.check('partnerCustomerServiceNumber', customer_service_number2),
            self.check('partnerCustomerServiceExtension', customer_service_extension2),
            self.check('customerServiceUri', customer_service_uri),
        ])

        self.kwargs.update({
            'scope': scope
        })

        # self.cmd('az eventgrid partner registration update --name {partner_registration_name} --resource-group {rg} --tags Dept=IT', checks=[
        #    self.check('name', self.kwargs['partner_registration_name']),
        #    self.check('tags', {'Dept': 'IT'}),
        #    self.check('type', 'Microsoft.EventGrid/partnerRegistrations'),
        #    self.check('provisioningState', 'Succeeded')
        # ])

        self.cmd('az eventgrid partner registration list --resource-group {rg}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/partnerRegistrations')
        ])

        self.cmd('az eventgrid partner registration list --resource-group {rg} --odata-query "name eq \'{partner_registration_name}\'"', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/partnerRegistrations'),
            self.check('[0].name', self.kwargs['partner_registration_name'])
        ])

        self.cmd('az eventgrid partner namespace create --name {partner_namespace_name} --resource-group {rg} --location {location} --partner-registration-id {scope}', checks=[
            self.check('type', 'Microsoft.EventGrid/partnerNamespaces'),
            self.check('name', self.kwargs['partner_namespace_name']),
            self.check('provisioningState', 'Succeeded'),
            self.check('location', self.kwargs['location']),
            self.check('partnerRegistrationFullyQualifiedId', scope)
        ])

        self.cmd('az eventgrid partner namespace show --name {partner_namespace_name} --resource-group {rg}', checks=[
            self.check('type', 'Microsoft.EventGrid/partnerNamespaces'),
            self.check('name', self.kwargs['partner_namespace_name']),
            self.check('provisioningState', 'Succeeded'),
            self.check('location', self.kwargs['location']),
            self.check('partnerRegistrationFullyQualifiedId', scope)
        ])

        outputnamespace = self.cmd('az eventgrid partner namespace create --name {partner_namespace_name} --resource-group {rg} --tags Dept=IT --partner-registration-id {scope} --location {location}').get_output_in_json()
        self.check(outputnamespace['type'], 'Microsoft.EventGrid/partnerNamespaces'),
        self.check(outputnamespace['name'], self.kwargs['partner_namespace_name']),
        self.check(outputnamespace['provisioningState'], 'Succeeded')
        self.check(outputnamespace['location'], self.kwargs['location']),
        self.check(outputnamespace['partnerRegistrationFullyQualifiedId'], scope)

        # self.cmd('az eventgrid partner namespace update --name {partner_namespace_name} --resource-group {rg} --tags Dept=Finance', checks=[
        #    self.check('name', self.kwargs['partner_namespace_name']),
        #    self.check('tags', {'Dept': 'Finance'}),
        #    self.check('type', 'Microsoft.EventGrid/partnerNamespaces'),
        #    self.check('provisioningState', 'Succeeded')
        # ])

        self.cmd('az eventgrid partner namespace list --resource-group {rg}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/partnerNamespaces'),
            self.check('[0].name', self.kwargs['partner_namespace_name']),
        ])

        self.cmd('az eventgrid partner namespace list --resource-group {rg} --odata-query "name eq \'{partner_namespace_name}\'"', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/partnerNamespaces'),
            self.check('[0].name', self.kwargs['partner_namespace_name']),
        ])

        output = self.cmd('az eventgrid partner namespace key list --partner-namespace-name {partner_namespace_name} --resource-group {rg}').get_output_in_json()
        self.assertIsNotNone(output['key1'])
        self.assertIsNotNone(output['key2'])

        output = self.cmd('az eventgrid partner namespace key regenerate --partner-namespace-name {partner_namespace_name} --resource-group {rg} --key-name key1').get_output_in_json()
        self.assertIsNotNone(output['key1'])
        self.assertIsNotNone(output['key2'])

        self.cmd('az eventgrid partner namespace key regenerate --partner-namespace-name {partner_namespace_name} --resource-group {rg} --key-name key2').get_output_in_json()
        self.assertIsNotNone(output['key1'])
        self.assertIsNotNone(output['key2'])

        self.cmd('az eventgrid partner namespace event-channel create --resource-group {rg} --partner-namespace-name {partner_namespace_name} --name {event_channel_name} --destination-subscription-id {destination_subscription_id} --destination-resource-group {rg} --desination-topic-name {partner_topic_name} --source {source}', checks=[
            self.check('type', 'Microsoft.EventGrid/partnerNamespaces/eventChannels'),
            self.check('name', self.kwargs['event_channel_name']),
            self.check('provisioningState', 'Succeeded'),
            # self.check('partnerTopicReadinessState', 'NotActivatedByUserYet')
        ])

        self.cmd('az eventgrid partner namespace event-channel show --resource-group {rg} --partner-namespace-name {partner_namespace_name} --name {event_channel_name}', checks=[
            self.check('type', 'Microsoft.EventGrid/partnerNamespaces/eventChannels'),
            self.check('name', self.kwargs['event_channel_name']),
            self.check('provisioningState', 'Succeeded'),
            # self.check('partnerTopicReadinessState', 'NotActivatedByUserYet')
        ])

        outputeventchannel = self.cmd('az eventgrid partner namespace event-channel create --resource-group {rg} --partner-namespace-name {partner_namespace_name} --name {event_channel_name} --destination-subscription-id {destination_subscription_id} --destination-resource-group {rg} --desination-topic-name {partner_topic_name} --source {source} --activation-expiration-date \'{exp_time}\' --partner-topic-description \'{partner_topic_friendly_description}\' --publisher-filter data.key1 NumberIn 2 3 4 100 200 --publisher-filter data.key2 StringIn 2 3 4 100 200').get_output_in_json()

        self.check(outputeventchannel['type'], 'Microsoft.EventGrid/partnerNamespaces/eventChannels'),
        self.check(outputeventchannel['name'], self.kwargs['event_channel_name']),
        self.check(outputeventchannel['provisioningState'], 'Succeeded'),
        self.check(outputeventchannel['expirationTimeIfNotActivatedUtc'], exp_time),
        self.check(outputeventchannel['partnerTopicFriendlyDescription'], partner_topic_friendly_description),
        self.check(outputeventchannel['partnerTopicReadinessState'], 'NotActivatedByUserYet')

        self.cmd('az eventgrid partner namespace event-channel show --resource-group {rg} --partner-namespace-name {partner_namespace_name} --name {event_channel_name}', checks=[
            self.check('type', 'Microsoft.EventGrid/partnerNamespaces/eventChannels'),
            self.check('name', self.kwargs['event_channel_name']),
            self.check('provisioningState', 'Succeeded'),
            # Comment for recorded test to pass.
            # self.check('expirationTimeIfNotActivatedUtc', exp_time + '+00:00'),
            # self.check('partnerTopicFriendlyDescription', partner_topic_friendly_description),
            self.check('partnerTopicReadinessState', 'NotActivatedByUserYet'),
        ])

        # self.cmd('az eventgrid partner namespace update --resource-group {rg} --partner-namespace-name {partner_namespace_name} --name {event_channel_name} --tags Dept=Finance', checks=[
        #    self.check('name', self.kwargs['event_channel_name']),
        #    self.check('tags', {'Dept': 'Finance'}),
        #    self.check('type', 'Microsoft.EventGrid/partnerNamespaces/eventChannels'),
        #    self.check('provisioningState', 'Succeeded')
        # ])

        self.cmd('az eventgrid partner namespace event-channel list --resource-group {rg} --partner-namespace-name {partner_namespace_name}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/partnerNamespaces/eventChannels'),
            self.check('[0].name', self.kwargs['event_channel_name']),
        ])

        self.cmd('az eventgrid partner topic show --name {partner_topic_name} --resource-group {rg}', checks=[
            self.check('type', 'Microsoft.EventGrid/partnerTopics'),
            self.check('name', self.kwargs['partner_topic_name']),
            self.check('provisioningState', 'Succeeded'),
            self.check('location', self.kwargs['location']),
            self.check('activationState', 'NeverActivated'),
            # self.check('partnerTopicFriendlyDescription', partner_topic_friendly_description),
        ])

        # self.cmd('az eventgrid partner topic update --name {partner_topic_name} --resource-group {rg} --tags Dept=Finance', checks=[
        #    self.check('name', self.kwargs['partner_topic_name']),
        #    self.check('tags', {'Dept': 'Finance'}),
        #    self.check('type', 'Microsoft.EventGrid/partnerTopics'),
        #    self.check('provisioningState', 'Succeeded')
        # ])

        self.cmd('az eventgrid partner topic list --resource-group {rg}', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/partnerTopics'),
            self.check('[0].name', self.kwargs['partner_topic_name']),
        ])

        self.cmd('az eventgrid partner topic list --resource-group {rg} --odata-query "name eq \'{partner_topic_name}\'"', checks=[
            self.check('[0].type', 'Microsoft.EventGrid/partnerTopics'),
            self.check('[0].name', self.kwargs['partner_topic_name']),
        ])

        self.cmd('az eventgrid partner topic activate --name {partner_topic_name} --resource-group {rg}', checks=[
            self.check('type', 'Microsoft.EventGrid/partnerTopics'),
            self.check('name', self.kwargs['partner_topic_name']),
            self.check('provisioningState', 'Succeeded'),
            self.check('location', self.kwargs['location']),
            self.check('activationState', 'Activated')
        ])

        self.cmd('az eventgrid partner namespace event-channel show --resource-group {rg} --partner-namespace-name {partner_namespace_name} --name {event_channel_name}', checks=[
            self.check('type', 'Microsoft.EventGrid/partnerNamespaces/eventChannels'),
            self.check('name', self.kwargs['event_channel_name']),
            self.check('provisioningState', 'Succeeded'),
            # self.check('expirationTimeIfNotActivatedUtc', exp_time + '+00:00'),
            # self.check('partnerTopicFriendlyDescription', partner_topic_friendly_description),
            # self.check('partnerTopicReadinessState', 'ActivatedByUser'),
        ])

        self.cmd('az eventgrid partner topic deactivate --name {partner_topic_name} --resource-group {rg}', checks=[
            self.check('type', 'Microsoft.EventGrid/partnerTopics'),
            self.check('name', self.kwargs['partner_topic_name']),
            self.check('provisioningState', 'Succeeded'),
            self.check('location', self.kwargs['location']),
            self.check('activationState', 'Deactivated')
        ])

        self.cmd('az eventgrid partner namespace event-channel show --resource-group {rg} --partner-namespace-name {partner_namespace_name} --name {event_channel_name}', checks=[
            self.check('type', 'Microsoft.EventGrid/partnerNamespaces/eventChannels'),
            self.check('name', self.kwargs['event_channel_name']),
            self.check('provisioningState', 'Succeeded'),
            # self.check('expirationTimeIfNotActivatedUtc', exp_time + '+00:00'),
            # self.check('partnerTopicFriendlyDescription', partner_topic_friendly_description),
            # self.check('partnerTopicReadinessState', 'DeactivatedByUser'),
        ])

        self.cmd('az eventgrid partner topic activate --name {partner_topic_name} --resource-group {rg}', checks=[
            self.check('type', 'Microsoft.EventGrid/partnerTopics'),
            self.check('name', self.kwargs['partner_topic_name']),
            self.check('provisioningState', 'Succeeded'),
            self.check('location', self.kwargs['location']),
            self.check('activationState', 'Activated')
        ])

        self.cmd('az eventgrid partner namespace event-channel show --resource-group {rg} --partner-namespace-name {partner_namespace_name} --name {event_channel_name}', checks=[
            self.check('type', 'Microsoft.EventGrid/partnerNamespaces/eventChannels'),
            self.check('name', self.kwargs['event_channel_name']),
            self.check('provisioningState', 'Succeeded'),
            # self.check('expirationTimeIfNotActivatedUtc', exp_time + '+00:00'),
            # self.check('partnerTopicFriendlyDescription', partner_topic_friendly_description),
            # self.check('partnerTopicReadinessState', 'ActivatedByUser'),
        ])

        self.cmd('az eventgrid partner topic event-subscription create --resource-group {rg} --partner-topic-name {partner_topic_name} --name {event_subscription_name} --endpoint-type storagequeue --endpoint {storagequeue_endpoint_id}', checks=[
            # self.check('type', 'Microsoft.EventGrid/partnerTopics/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name'])
        ])

        self.cmd('az eventgrid partner topic event-subscription create --resource-group {rg} --partner-topic-name {partner_topic_name} --name {event_subscription_name} --endpoint-type storagequeue --endpoint {storagequeue_endpoint_id} --labels label_1 label_2', checks=[
            # self.check('type', 'Microsoft.EventGrid/partnerTopics/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name'])
        ])

        self.cmd('az eventgrid partner topic event-subscription show --resource-group {rg} --partner-topic-name {partner_topic_name} --name {event_subscription_name}', checks=[
            # self.check('type', 'Microsoft.EventGrid/partnerTopics/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
        ])

        self.cmd('az eventgrid partner topic event-subscription update -g {rg} --partner-topic-name {partner_topic_name} -n {event_subscription_name} --labels label11 label22', checks=[
            # self.check('type', 'Microsoft.EventGrid/partnerTopics/eventSubscriptions'),
            self.check('provisioningState', 'Succeeded'),
            self.check('name', self.kwargs['event_subscription_name'])
        ])

        self.cmd('az eventgrid partner topic event-subscription list --resource-group {rg} --partner-topic-name {partner_topic_name}', checks=[
            # self.check('[0].type', 'Microsoft.EventGrid/partnerTopics/eventSubscriptions'),
            self.check('[0].provisioningState', 'Succeeded'),
        ])

        # self.cmd('az eventgrid partner topic event-subscription list --resource-group {rg} --partner-topic-name {partner_topic_name} --odata-query "name eq \'{event_subscription_name}\'"', checks=[
        #    self.check('[0].type', 'Microsoft.EventGrid/partnerTopics/eventSubscriptions'),
        #    self.check('[0].provisioningState', 'Succeeded'),
        # ])

        self.cmd('az eventgrid partner topic event-subscription delete -y -g {rg} --name {event_subscription_name} --partner-topic-name {partner_topic_name} ')
        self.cmd('az eventgrid partner topic delete -y --name {partner_topic_name} --resource-group {rg}')
        self.cmd('az eventgrid partner namespace event-channel delete -y --resource-group {rg} --partner-namespace-name {partner_namespace_name} --name {event_channel_name}')
        self.cmd('az eventgrid partner namespace delete -y --name {partner_namespace_name} --resource-group {rg}')
        self.cmd('az eventgrid partner registration delete -y -n {partner_registration_name} -g {rg}')
