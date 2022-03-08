# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=too-many-statements

from azure.cli.testsdk import ResourceGroupPreparer, ScenarioTest, StorageAccountPreparer
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from .recording_processors import KeyReplacer
import unittest


class IoTHubTest(ScenarioTest):

    def __init__(self, method_name):
        super(IoTHubTest, self).__init__(
            method_name, recording_processors=[KeyReplacer()]
        )

    @AllowLargeResponse()
    @ResourceGroupPreparer(location='westus2')
    @StorageAccountPreparer()
    @unittest.skip('Need to try with passing SAS key in environment.')  # TODO
    def test_iot_hub(self, resource_group, resource_group_location, storage_account):
        hub = 'iot-hub-for-test-11'
        rg = resource_group
        location = resource_group_location
        containerName = 'iothubcontainer1'
        storageConnectionString = self._get_azurestorage_connectionstring(rg, containerName, storage_account)
        ehConnectionString = self._get_eventhub_connectionstring(rg)
        subscription_id = self._get_current_subscription()

        # Test hub life cycle in free tier
        self.cmd('iot hub create -n {0} -g {1} --sku F1'.format(hub, rg), expect_failure=True)
        self.cmd('iot hub create -n {0} -g {1} --sku F1 --partition-count 4'.format(hub, rg), expect_failure=True)
        self.cmd('iot hub create -n {0} -g {1} --sku F1 --partition-count 2'.format(hub, rg),
                 checks=[self.check('resourcegroup', rg),
                         self.check('name', hub),
                         self.check('sku.name', 'F1'),
                         self.check('properties.eventHubEndpoints.events.partitionCount', '2')])
        self.cmd('iot hub delete -n {0}'.format(hub), checks=self.is_empty())

        # Test 'az iot hub create'
        self.cmd('iot hub create -n {0} -g {1} --sku S1 --fn true'.format(hub, rg), expect_failure=True)
        self.cmd('iot hub create -n {0} -g {1} --sku S1 --fn true --fc containerName'
                 .format(hub, rg), expect_failure=True)
        self.cmd('iot hub create -n {0} -g {1} --retention-day 3'
                 ' --c2d-ttl 23 --c2d-max-delivery-count 89 --feedback-ttl 29 --feedback-lock-duration 35'
                 ' --feedback-max-delivery-count 40 --fileupload-notification-max-delivery-count 79'
                 ' --fileupload-notification-ttl 20'.format(hub, rg),
                 checks=[self.check('resourcegroup', rg),
                         self.check('location', location),
                         self.check('name', hub),
                         self.check('sku.name', 'S1'),
                         self.check('properties.eventHubEndpoints.events.partitionCount', '4'),
                         self.check('properties.eventHubEndpoints.events.retentionTimeInDays', '3'),
                         self.check('properties.cloudToDevice.feedback.maxDeliveryCount', '40'),
                         self.check('properties.cloudToDevice.feedback.lockDurationAsIso8601', '0:00:35'),
                         self.check('properties.cloudToDevice.feedback.ttlAsIso8601', '1 day, 5:00:00'),
                         self.check('properties.cloudToDevice.maxDeliveryCount', '89'),
                         self.check('properties.cloudToDevice.defaultTtlAsIso8601', '23:00:00'),
                         self.check('properties.messagingEndpoints.fileNotifications.ttlAsIso8601', '20:00:00'),
                         self.check('properties.messagingEndpoints.fileNotifications.maxDeliveryCount', '79')])

        # Test 'az iot hub show-connection-string'
        conn_str_pattern = r'^HostName={0}.azure-devices.net;SharedAccessKeyName=iothubowner;SharedAccessKey='.format(
            hub)
        self.cmd('iot hub show-connection-string -n {0}'.format(hub), checks=[
            self.check_pattern('connectionString', conn_str_pattern)
        ])

        self.cmd('iot hub show-connection-string -n {0} -g {1}'.format(hub, rg), checks=[
            self.check('length(@)', 1),
            self.check_pattern('connectionString', conn_str_pattern)
        ])

        self.cmd('iot hub show-connection-string -n {0} -g {1} --all'.format(hub, rg), checks=[
            self.check('length(connectionString[*])', 5),
            self.check_pattern('connectionString[0]', conn_str_pattern)
        ])

        # Storage Connection String Pattern
        storage_cs_pattern = 'DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName='
        # Test 'az iot hub update'
        updated_hub = self.cmd('iot hub update -n {0} --fnd 80 --rd 4 --ct 34 --cdd 46 --ft 43 --fld 10 --fd 76'
                               ' --fn true --fnt 32 --fst 3 --fcs {1} --fc {2}'
                               .format(hub, storageConnectionString, containerName)).get_output_in_json()

        assert updated_hub['properties']['eventHubEndpoints']['events']['partitionCount'] == 4
        assert updated_hub['properties']['eventHubEndpoints']['events']['retentionTimeInDays'] == 4
        assert updated_hub['properties']['cloudToDevice']['feedback']['maxDeliveryCount'] == 76
        assert updated_hub['properties']['cloudToDevice']['feedback']['lockDurationAsIso8601'] == '0:00:10'
        assert updated_hub['properties']['cloudToDevice']['feedback']['ttlAsIso8601'] == '1 day, 19:00:00'
        assert updated_hub['properties']['cloudToDevice']['maxDeliveryCount'] == 46
        assert updated_hub['properties']['cloudToDevice']['defaultTtlAsIso8601'] == '1 day, 10:00:00'
        assert updated_hub['properties']['messagingEndpoints']['fileNotifications']['ttlAsIso8601'] == '1 day, 8:00:00'
        assert updated_hub['properties']['messagingEndpoints']['fileNotifications']['maxDeliveryCount'] == 80
        assert storage_cs_pattern in updated_hub['properties']['storageEndpoints']['$default']['connectionString']
        assert updated_hub['properties']['storageEndpoints']['$default']['containerName'] == containerName
        assert updated_hub['properties']['storageEndpoints']['$default']['sasTtlAsIso8601'] == '3:00:00'

        # Test 'az iot hub show'
        self.cmd('iot hub show -n {0}'.format(hub), checks=[
            self.check('resourcegroup', rg),
            self.check('location', location),
            self.check('name', hub),
            self.check('sku.name', 'S1'),
            self.check('properties.eventHubEndpoints.events.partitionCount', '4'),
            self.check('properties.eventHubEndpoints.events.retentionTimeInDays', '4'),
            self.check('properties.cloudToDevice.feedback.maxDeliveryCount', '76'),
            self.check('properties.cloudToDevice.feedback.lockDurationAsIso8601', '0:00:10'),
            self.check('properties.cloudToDevice.feedback.ttlAsIso8601', '1 day, 19:00:00'),
            self.check('properties.cloudToDevice.maxDeliveryCount', '46'),
            self.check('properties.cloudToDevice.defaultTtlAsIso8601', '1 day, 10:00:00'),
            self.check('properties.messagingEndpoints.fileNotifications.ttlAsIso8601', '1 day, 8:00:00'),
            self.check('properties.messagingEndpoints.fileNotifications.maxDeliveryCount', '80')
        ])

        # Test 'az iot hub list'
        self.cmd('iot hub list -g {0}'.format(rg), checks=[
            self.check('length([*])', 1),
            self.check('[0].resourcegroup', rg),
            self.check('[0].location', location),
            self.check('[0].name', hub),
            self.check('[0].sku.name', 'S1')
        ])

        # Test 'az iot hub sku list'
        self.cmd('iot hub list-skus -n {0}'.format(hub), checks=[
            self.check('length([*])', 3),
            self.check('[0].sku.name', 'S1'),
            self.check('[1].sku.name', 'S2'),
            self.check('[2].sku.name', 'S3')
        ])

        # Test 'az iot hub policy create'
        policy_name = 'test_policy'
        permissions = 'RegistryWrite ServiceConnect DeviceConnect'
        self.cmd('iot hub policy create --hub-name {0} -n {1} --permissions {2}'.format(hub, policy_name, permissions),
                 checks=self.is_empty())

        # Test 'az iot hub policy list'
        self.cmd('iot hub policy list --hub-name {0}'.format(hub), checks=[
            self.check('length([*])', 6)
        ])

        # Test 'az iot hub policy show'
        self.cmd('iot hub policy show --hub-name {0} -n {1}'.format(hub, policy_name), checks=[
            self.check('keyName', policy_name),
            self.check('rights', 'RegistryWrite, ServiceConnect, DeviceConnect')
        ])

        # Test 'az iot hub policy renew-key'
        policy = self.cmd('iot hub policy renew-key --hub-name {0} -n {1} --renew-key Primary'.format(hub, policy_name),
                          checks=[self.check('keyName', policy_name)]).get_output_in_json()

        policy_name_conn_str_pattern = r'HostName={0}.azure-devices.net;SharedAccessKeyName={1};SharedAccessKey={2}'.format(
            hub, policy_name, policy['primaryKey'])

        # Test policy_name connection-string 'az iot hub show-connection-string'
        self.cmd('iot hub show-connection-string -n {0} --policy-name {1}'.format(hub, policy_name), checks=[
            self.check_pattern('connectionString', policy_name_conn_str_pattern)
        ])

        # Test swap keys 'az iot hub policy renew-key'
        self.cmd('iot hub policy renew-key --hub-name {0} -n {1} --renew-key Swap'.format(hub, policy_name),
                 checks=[self.check('primaryKey', policy['secondaryKey']),
                         self.check('secondaryKey', policy['primaryKey'])])

        # Test 'az iot hub policy delete'
        self.cmd('iot hub policy delete --hub-name {0} -n {1}'.format(hub, policy_name), checks=self.is_empty())
        self.cmd('iot hub policy list --hub-name {0}'.format(hub), checks=[
            self.check('length([*])', 5)
        ])

        # Test 'az iot hub consumer-group create'
        consumer_group_name = 'cg1'
        self.cmd('iot hub consumer-group create --hub-name {0} -n {1}'.format(hub, consumer_group_name), checks=[
            self.check('name', consumer_group_name)
        ])

        # Test 'az iot hub consumer-group show'
        self.cmd('iot hub consumer-group show --hub-name {0} -n {1}'.format(hub, consumer_group_name), checks=[
            self.check('name', consumer_group_name)
        ])

        # Test 'az iot hub consumer-group list'
        self.cmd('iot hub consumer-group list --hub-name {0}'.format(hub), checks=[
            self.check('length([*])', 2),
            self.check('[0].name', '$Default'),
            self.check('[1].name', consumer_group_name)
        ])

        # Test 'az iot hub consumer-group delete'
        self.cmd('iot hub consumer-group delete --hub-name {0} -n {1}'.format(hub, consumer_group_name),
                 checks=self.is_empty())

        self.cmd('iot hub consumer-group list --hub-name {0}'.format(hub), checks=[
            self.check('length([*])', 1),
            self.check('[0].name', '$Default')
        ])

        # Test 'az iot hub show-quota-metrics'
        self.cmd('iot hub show-quota-metrics -n {0}'.format(hub), checks=[
            self.check('length([*])', 2),
            self.check('[0].name', 'TotalMessages'),
            self.check('[0].maxValue', 400000),
            self.check('[1].name', 'TotalDeviceCount'),
            self.check('[1].maxValue', 'Unlimited')
        ])

        # Test 'az iot hub show-stats'
        device_count_pattern = r'^\d$'
        self.cmd('iot hub show-stats -n {0}'.format(hub), checks=[
            self.check_pattern('disabledDeviceCount', device_count_pattern),
            self.check_pattern('enabledDeviceCount', device_count_pattern),
            self.check_pattern('totalDeviceCount', device_count_pattern)
        ])

        endpoint_name = 'Event1'
        endpoint_type = 'EventHub'
        storage_endpoint_name = 'Storage1'
        storage_endpoint_type = 'azurestoragecontainer'
        storage_encoding_format = 'avro'
        storage_chunk_size = 150
        storage_batch_frequency = 100
        storage_file_name_format = '{iothub}/{partition}/{YYYY}/{MM}/{DD}/{HH}/{mm}'
        # Test 'az iot hub routing-endpoint create'
        self.cmd('iot hub routing-endpoint create --hub-name {0} -g {1} -n {2} -t {3} -r {4} -s {5} -c "{6}"'
                 .format(hub, rg, endpoint_name, endpoint_type, rg, subscription_id, ehConnectionString),
                 checks=[self.check('length(eventHubs[*])', 1),
                         self.check('eventHubs[0].resourceGroup', rg),
                         self.check('eventHubs[0].name', endpoint_name),
                         self.check('length(serviceBusQueues[*])', 0),
                         self.check('length(serviceBusTopics[*])', 0),
                         self.check('length(storageContainers[*])', 0)])

        # Test 'az iot hub routing-endpoint list'
        self.cmd('iot hub routing-endpoint list --hub-name {0} -g {1}'
                 .format(hub, rg),
                 checks=[self.check('length(eventHubs[*])', 1),
                         self.check('eventHubs[0].resourceGroup', rg),
                         self.check('eventHubs[0].name', endpoint_name)])

        self.cmd('iot hub routing-endpoint list --hub-name {0} -g {1} -t {2}'
                 .format(hub, rg, endpoint_type),
                 checks=[self.check('length([*])', 1),
                         self.check('[0].resourceGroup', rg),
                         self.check('[0].name', endpoint_name)])

        # Test 'az iot hub routing-endpoint show'
        self.cmd('iot hub routing-endpoint show --hub-name {0} -g {1} -n {2}'
                 .format(hub, rg, endpoint_name),
                 checks=[self.check('resourceGroup', rg),
                         self.check('name', endpoint_name)])

        # Test 'az iot hub routing-endpoint create' with storage endpoint
        endpoint = self.cmd('iot hub routing-endpoint create --hub-name {0} -g {1} -n {2} -t {3} -r {4} -s {5} '
                            '-c "{6}" --container-name {7} --encoding {8} -b {9} -w {10}'
                            .format(hub, rg, storage_endpoint_name, storage_endpoint_type, rg, subscription_id,
                                    storageConnectionString, containerName, storage_encoding_format,
                                    storage_batch_frequency, storage_chunk_size)).get_output_in_json()

        assert len(endpoint['storageContainers']) == 1
        assert endpoint["storageContainers"][0]["containerName"] == containerName
        assert endpoint["storageContainers"][0]["name"] == storage_endpoint_name
        assert endpoint["storageContainers"][0]["batchFrequencyInSeconds"] == storage_batch_frequency
        assert endpoint["storageContainers"][0]["maxChunkSizeInBytes"] == 1048576 * storage_chunk_size
        assert endpoint["storageContainers"][0]["fileNameFormat"] == storage_file_name_format
        assert len(endpoint['serviceBusQueues']) == 0
        assert len(endpoint['serviceBusTopics']) == 0
        assert len(endpoint['eventHubs']) == 1

        # Test 'az iot hub route create'
        route_name = 'route1'
        source_type = 'DeviceMessages'
        new_source_type = 'TwinChangeEvents'
        condition = 'true'
        enabled = True
        self.cmd('iot hub route create --hub-name {0} -g {1} -n {2} -s {3} --en {4} -c {5} -e {6}'
                 .format(hub, rg, route_name, source_type, endpoint_name, condition, enabled),
                 checks=[self.check('length([*])', 1),
                         self.check('[0].name', route_name),
                         self.check('[0].source', source_type),
                         self.check('[0].isEnabled', enabled),
                         self.check('[0].condition', condition),
                         self.check('length([0].endpointNames[*])', 1),
                         self.check('[0].endpointNames[0]', endpoint_name)])

        # Test 'az iot hub route list'
        self.cmd('iot hub route list --hub-name {0} -g {1}'.format(hub, rg),
                 checks=[self.check('length([*])', 1),
                         self.check('[0].name', route_name),
                         self.check('[0].source', source_type),
                         self.check('[0].isEnabled', enabled),
                         self.check('[0].condition', condition),
                         self.check('length([0].endpointNames[*])', 1),
                         self.check('[0].endpointNames[0]', endpoint_name)])

        # Test 'az iot hub route list'
        self.cmd('iot hub route list --hub-name {0} -g {1} -s {2}'.format(hub, rg, source_type),
                 checks=[self.check('length([*])', 1),
                         self.check('[0].name', route_name),
                         self.check('[0].source', source_type),
                         self.check('[0].isEnabled', enabled),
                         self.check('[0].condition', condition),
                         self.check('length([0].endpointNames[*])', 1),
                         self.check('[0].endpointNames[0]', endpoint_name)])

        # Test 'az iot hub route show'
        self.cmd('iot hub route show --hub-name {0} -g {1} -n {2}'.format(hub, rg, route_name),
                 checks=[self.check('name', route_name),
                         self.check('source', source_type),
                         self.check('isEnabled', enabled),
                         self.check('condition', condition),
                         self.check('length(endpointNames[*])', 1),
                         self.check('endpointNames[0]', endpoint_name)])

        # Test 'az iot hub route test'
        self.cmd('iot hub route test --hub-name {0} -g {1} -n {2}'.format(hub, rg, route_name),
                 checks=[self.check('result', 'true')])

        # Test 'az iot hub route test'
        self.cmd('iot hub route test --hub-name {0} -g {1} -s {2}'.format(hub, rg, source_type),
                 checks=[self.check('length(routes[*])', 1),
                         self.check('routes[0].properties.name', route_name),
                         self.check('routes[0].properties.source', source_type),
                         self.check('routes[0].properties.isEnabled', enabled),
                         self.check('routes[0].properties.condition', condition),
                         self.check('length(routes[0].properties.endpointNames[*])', 1),
                         self.check('routes[0].properties.endpointNames[0]', endpoint_name)])

        # Test 'az iot hub route update'
        self.cmd('iot hub route update --hub-name {0} -g {1} -n {2} -s {3}'.format(hub, rg, route_name, new_source_type),
                 checks=[self.check('length([*])', 1),
                         self.check('[0].name', route_name),
                         self.check('[0].source', new_source_type),
                         self.check('[0].isEnabled', enabled),
                         self.check('[0].condition', condition),
                         self.check('length([0].endpointNames[*])', 1),
                         self.check('[0].endpointNames[0]', endpoint_name)])

        # Test 'az iot hub route delete'
        self.cmd('iot hub route delete --hub-name {0} -g {1}'.format(hub, rg), checks=[
                 self.check('length([*])', 0)
                 ])

        # Test 'az iot hub routing-endpoint delete'
        self.cmd('iot hub routing-endpoint delete --hub-name {0} -g {1} -n {2}'.format(hub, rg, endpoint_name),
                 checks=[self.check('length(eventHubs[*])', 0),
                         self.check('length(serviceBusQueues[*])', 0),
                         self.check('length(serviceBusTopics[*])', 0),
                         self.check('length(storageContainers[*])', 1)])

        # Test 'az iot hub devicestream show'
        self.cmd('iot hub devicestream show -n {0} -g {1}'.format(hub, rg), checks=self.is_empty())

        # Test 'az iot hub message-enrichment create'
        real_endpoints = 'events'
        fake_endpoints = 'events fake_endpoint'
        key = 'key'
        fake_key = 'fake_key'
        value = 'value'

        self.cmd('iot hub message-enrichment create -n {0} -g {1} --key {2} --value {3} --endpoints {4}'
                 .format(hub, rg, key, value, fake_endpoints), expect_failure=True)
        self.cmd('iot hub message-enrichment create -n {0} -g {1} --key {2} --value {3} --endpoints {4}'
                 .format(hub, rg, key, value, real_endpoints), checks=[self.check('length(properties.routing.enrichments)', 1)])

        # Test 'az iot hub message-enrichment update'
        self.cmd('iot hub message-enrichment update -n {0} -g {1} --key {2} --value {3} --endpoints {4}'
                 .format(hub, rg, fake_key, value, real_endpoints), expect_failure=True)
        self.cmd('iot hub message-enrichment update -n {0} -g {1} --key {2} --value {3} --endpoints {4}'
                 .format(hub, rg, key, value, fake_endpoints), expect_failure=True)
        self.cmd('iot hub message-enrichment update -n {0} -g {1} --key {2} --value {3} --endpoints {4}'
                 .format(hub, rg, key, value, real_endpoints), checks=[self.check('length(properties.routing.enrichments)', 1)])

        # Test 'az iot hub message-enrichment list'
        self.cmd('iot hub message-enrichment list -n {0} -g {1}'.format(hub, rg),
                 checks=[self.check('length([*])', 1)])

        # Test 'az iot hub message-enrichment delete'
        self.cmd('iot hub message-enrichment delete -n {0} -g {1} --key {2}'.format(hub, rg, fake_key),
                 expect_failure=True)
        self.cmd('iot hub message-enrichment delete -n {0} -g {1} --key {2}'.format(hub, rg, key),
                 checks=[self.check('length(properties.routing.enrichments)', 0)])

        # Test 'az iot hub manual-failover'
        self.cmd('iot hub manual-failover -n {0} -g {1}'.format(hub, rg),
                 checks=[self.check('location', location)])
        # Test 'az iot hub delete'
        self.cmd('iot hub delete -n {0}'.format(hub), checks=self.is_empty())

    @AllowLargeResponse()
    @ResourceGroupPreparer(location='westus2')
    @StorageAccountPreparer()
    @unittest.skip('Need to try with passing SAS key in environment.')  # TODO
    def test_identity_hub(self, resource_group, resource_group_location, storage_account):
        # Test IoT Hub create with identity
        subscription_id = self._get_current_subscription()
        rg = resource_group
        location = resource_group_location

        private_endpoint_type = 'Microsoft.Devices/IoTHubs'
        identity_hub = 'identity-test-hub-cli'
        identity_based_auth = 'identityBased'
        event_hub_identity_endpoint_name = 'EventHubIdentityEndpoint'

        containerName = 'iothubcontainer'
        storageConnectionString = self._get_azurestorage_connectionstring(rg, containerName, storage_account)
        endpoint_name = 'Event1'
        endpoint_type = 'EventHub'
        eventhub_endpoint_uri = 'eh://test'
        storage_cs_pattern = 'DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName='
        entity_path = 'entity'

        # identity hub creation
        import os
        templateFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.pardir, 'templates', 'identity.json')
        self.cmd('deployment group create --name {0} -g {1} --template-file "{2}" --parameters name={3} --parameters location={4}'
                 .format("identity-hub-deployment", resource_group, templateFile, identity_hub, location))
        self.cmd('iot hub show --name {0}'.format(identity_hub), checks=[
                 self.check('properties.minTlsVersion', '1.2'),
                 self.check('identity.type', 'SystemAssigned')])

        # Test 'az iot hub update' with Identity-based fileUpload
        updated_hub = self.cmd('iot hub update -n {0} --fsa {1} --fcs {2} --fc {3} --fn true --fnt 32 --fnd 80 --rd 4 '
                               '--ct 34 --cdd 46 --ft 43 --fld 10 --fd 76'
                               .format(identity_hub, identity_based_auth, storageConnectionString, containerName)).get_output_in_json()
        assert updated_hub['properties']['storageEndpoints']['$default']['authenticationType'] == identity_based_auth
        assert storage_cs_pattern in updated_hub['properties']['storageEndpoints']['$default']['connectionString']
        # TODO - implement file upload container URI instead of connectionString once implemented in service

        # Test 'az iot hub routing-endpoint create' with Identity-based event hub endpoint
        self.cmd('iot hub routing-endpoint create --hub-name {0} -g {1} -n {2} -t {3} -r {4} -s {5} --auth-type {6} --endpoint-uri {7} --entity-path {8}'
                 .format(identity_hub, rg, event_hub_identity_endpoint_name, endpoint_type, rg, subscription_id, identity_based_auth, eventhub_endpoint_uri, entity_path),
                 checks=[self.check('length(eventHubs[*])', 1),
                         self.check('eventHubs[0].resourceGroup', rg),
                         self.check('eventHubs[0].name', event_hub_identity_endpoint_name),
                         self.check('eventHubs[0].authenticationType', identity_based_auth),
                         self.check('eventHubs[0].connectionString', None),
                         self.check('eventHubs[0].endpointUri', eventhub_endpoint_uri),
                         self.check('eventHubs[0].entityPath', entity_path),
                         self.check('length(serviceBusQueues[*])', 0),
                         self.check('length(serviceBusTopics[*])', 0),
                         self.check('length(storageContainers[*])', 0)])

        vnet = 'test-iot-vnet'
        subnet = 'subnet1'
        endpoint_name = 'iot-private-endpoint'
        connection_name = 'iot-private-endpoint-connection'

        # Test private endpoints
        # Prepare network
        self.cmd('network vnet create -n {0} -g {1} -l {2} --subnet-name {3}'
                 .format(vnet, rg, location, subnet),
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('network vnet subnet update -n {0} --vnet-name {1} -g {2} '
                 '--disable-private-endpoint-network-policies true'
                 .format(subnet, vnet, rg),
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Create a private endpoint connection
        pr = self.cmd('network private-link-resource list --type {0} -n {1} -g {2}'
                      .format(private_endpoint_type, identity_hub, rg)).get_output_in_json()
        group_id = pr[0]['properties']['groupId']

        hub = self.cmd('iot hub show -n {0} -g {1}'.format(identity_hub, rg)).get_output_in_json()
        hub_id = hub['id']

        private_endpoint = self.cmd(
            'network private-endpoint create -g {0} -n {1} --vnet-name {2} --subnet {3} -l {4} '
            '--connection-name {5} --private-connection-resource-id {6} --group-ids {7}'
            .format(rg, endpoint_name, vnet, subnet, location, connection_name, hub_id, group_id)
        ).get_output_in_json()

        self.assertEqual(private_endpoint['name'], endpoint_name)
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['name'], connection_name)
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['privateLinkServiceConnectionState']['status'], 'Approved')
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['provisioningState'], 'Succeeded')
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['groupIds'][0], group_id)

        hub = self.cmd('iot hub show -n {0} -g {1}'.format(identity_hub, rg)).get_output_in_json()
        endpoint_id = hub['properties']['privateEndpointConnections'][0]['id']
        private_endpoint_name = hub['properties']['privateEndpointConnections'][0]['name']

        # endpoint list
        self.cmd('network private-endpoint-connection list --type {0} -n {1} -g {2}'
                 .format(private_endpoint_type, identity_hub, rg),
                 checks=[self.check('length(@)', 1),
                         self.check('[0].id', endpoint_id),
                         self.check('[0].name', private_endpoint_name)])

        # endpoint connection approve by name
        approve_desc = 'Approving endpoint connection'
        self.cmd('network private-endpoint-connection approve --type {0} -n {1} --resource-name {2} -g {3} --description "{4}"'
                 .format(private_endpoint_type, private_endpoint_name, identity_hub, rg, approve_desc),
                 checks=[self.check('properties.privateLinkServiceConnectionState.status', 'Approved')])

        # endpoint approve by id
        self.cmd('network private-endpoint-connection approve --id {0} --description "{1}"'
                 .format(endpoint_id, approve_desc),
                 checks=[self.check('properties.privateLinkServiceConnectionState.status', 'Approved')])

        # endpoint connection reject by name
        reject_desc = 'Rejecting endpoint connection'
        self.cmd('network private-endpoint-connection reject --type {0} -n {1} --resource-name {2} -g {3} --description "{4}"'
                 .format(private_endpoint_type, private_endpoint_name, identity_hub, rg, reject_desc),
                 checks=[self.check('properties.privateLinkServiceConnectionState.status', 'Rejected')])

        # endpoint show
        self.cmd('network private-endpoint-connection show --type {0} -n {1} --resource-name {2} -g {3}'
                 .format(private_endpoint_type, private_endpoint_name, identity_hub, rg),
                 checks=self.check('id', endpoint_id))

        # endpoint delete
        self.cmd('network private-endpoint-connection delete --type {0} -n {1} --resource-name {2} -g {3} -y'
                 .format(private_endpoint_type, private_endpoint_name, identity_hub, rg))

    def _get_eventhub_connectionstring(self, rg):
        ehNamespace = 'ehNamespaceiothubfortest1'
        eventHub = 'eventHubiothubfortest'
        eventHubPolicy = 'eventHubPolicyiothubfortest'
        eventHubPolicyRight = 'Send'

        self.cmd('eventhubs namespace create --resource-group {0} --name {1}'
                 .format(rg, ehNamespace))

        self.cmd('eventhubs eventhub create --resource-group {0} --namespace-name {1} --name {2}'
                 .format(rg, ehNamespace, eventHub))

        self.cmd('eventhubs eventhub authorization-rule create --resource-group {0} --namespace-name {1} --eventhub-name {2} --name {3} --rights {4}'
                 .format(rg, ehNamespace, eventHub, eventHubPolicy, eventHubPolicyRight))

        output = self.cmd('eventhubs eventhub authorization-rule keys list --resource-group {0} --namespace-name {1} --eventhub-name {2} --name {3}'
                          .format(rg, ehNamespace, eventHub, eventHubPolicy))
        return output.get_output_in_json()['primaryConnectionString']

    def _get_azurestorage_connectionstring(self, rg, container_name, storage_name):

        self.cmd('storage container create --name {0} --account-name {1}'
                 .format(container_name, storage_name))

        output = self.cmd('storage account show-connection-string --resource-group {0} --name {1}'
                          .format(rg, storage_name))
        return output.get_output_in_json()['connectionString']

    def _get_current_subscription(self):
        output = self.cmd('account show')
        return output.get_output_in_json()['id']
