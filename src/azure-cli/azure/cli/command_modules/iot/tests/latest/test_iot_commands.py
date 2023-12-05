# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=too-many-statements
import json
from unittest import mock
from knack.util import CLIError

from azure.cli.testsdk import ResourceGroupPreparer, ScenarioTest, StorageAccountPreparer
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.mgmt.iothub.models import RoutingSource
from azure.cli.command_modules.iot.shared import IdentityType
from azure.core.exceptions import HttpResponseError
from .recording_processors import KeyReplacer


class IoTHubTest(ScenarioTest):

    def __init__(self, method_name):
        super(IoTHubTest, self).__init__(
            method_name, recording_processors=[KeyReplacer()]
        )

    @AllowLargeResponse(size_kb=4096)
    @ResourceGroupPreparer(location='westus2')
    @StorageAccountPreparer()
    def test_iot_hub(self, resource_group, resource_group_location, storage_account):
        # for some reason the recording is missing a ] and a } after the routing.endpoints.eventHubs
        hub = self.create_random_name(prefix='iot-hub-for-test-11', length=32)
        rg = resource_group
        location = resource_group_location
        containerName = self.create_random_name(prefix='iothubcontainer1', length=24)
        storageConnectionString = self._get_azurestorage_connectionstring(rg, containerName, storage_account)
        ehConnectionString = self._get_eventhub_connectionstring(rg)
        subscription_id = self.get_subscription_id()

        # Test 'az iot hub create'
        self.cmd('iot hub create -n {0} -g {1} --sku F1'.format(hub, rg), expect_failure=True)
        self.cmd('iot hub create -n {0} -g {1} --sku F1 --partition-count 4'.format(hub, rg), expect_failure=True)
        self.cmd('iot hub create -n {0} -g {1} --sku S1 --fn true'.format(hub, rg), expect_failure=True)
        self.cmd('iot hub create -n {0} -g {1} --sku S1 --fn true --fc containerName'
                 .format(hub, rg), expect_failure=True)
        self.cmd('iot hub create -n {0} -g {1} --sku S1 --mintls 2.5'.format(hub, rg), expect_failure=True)
        # qatar region data-residency enforcement must be enabled
        self.cmd('iot hub create -n {0} -g {1} --sku S1 --location qatarcentral --enforce-data-residency false'.format(hub, rg), expect_failure=True)
        self.cmd('iot hub create -n {0} -g {1} --sku S1 --location QATARCENTRAL'.format(hub, rg), expect_failure=True)
        self.cmd('iot hub create -n {0} -g {1} --retention-day 3'
                 ' --c2d-ttl 23 --c2d-max-delivery-count 89 --feedback-ttl 29 --feedback-lock-duration 35'
                 ' --feedback-max-delivery-count 40 --fileupload-notification-max-delivery-count 79'
                 ' --fileupload-notification-ttl 20 --min-tls-version 1.2 --fnld 15'.format(hub, rg),
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
                         self.check('properties.messagingEndpoints.fileNotifications.maxDeliveryCount', '79'),
                         self.check('properties.messagingEndpoints.fileNotifications.lockDurationAsIso8601', '0:00:15'),
                         self.check('properties.minTlsVersion', '1.2')])

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
        storage_cs_pattern = 'DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;'
        # Test 'az iot hub update'
        updated_hub = self.cmd('iot hub update -n {0} --fnd 80 --rd 4 --ct 34 --cdd 46 --ft 43 --fld 10 --fd 76'
                               ' --fn true --fnt 32 --fst 3 --fcs {1} --fc {2} --tags e=f g=h'
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
        assert updated_hub['tags'] == {'e': 'f', 'g': 'h'}

        # Test fileupload authentication type settings
        # No identity, setting identity-based file upload or managed identity for file upload should fail
        self.cmd('iot hub update -n {0} -g {1} --fsa identityBased'.format(hub, rg), expect_failure=True)
        self.cmd('iot hub update -n {0} -g {1} --fsi [system]'.format(hub, rg), expect_failure=True)
        self.cmd('iot hub update -n {0} -g {1} --fsi test/user/'.format(hub, rg), expect_failure=True)

        # Test auth config settings
        updated_hub = self.cmd('iot hub update -n {0} -g {1} --disable-local-auth --disable-module-sas'.format(hub, rg)).get_output_in_json()
        assert updated_hub['properties']['disableLocalAuth']
        assert not updated_hub['properties']['disableDeviceSas']
        assert updated_hub['properties']['disableModuleSas']

        updated_hub = self.cmd('iot hub update -n {0} -g {1} --disable-module-sas false  --disable-device-sas'.format(hub, rg)).get_output_in_json()
        assert updated_hub['properties']['disableLocalAuth']
        assert updated_hub['properties']['disableDeviceSas']
        assert not updated_hub['properties']['disableModuleSas']

        updated_hub = self.cmd('iot hub update -n {0} -g {1} --disable-local-auth false --disable-device-sas false'.format(hub, rg)).get_output_in_json()
        assert not updated_hub['properties']['disableLocalAuth']
        assert not updated_hub['properties']['disableDeviceSas']
        assert not updated_hub['properties']['disableModuleSas']

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

        policy_name_conn_str = r'HostName={0}.azure-devices.net;SharedAccessKeyName={1};SharedAccessKey={2}'.format(
            hub, policy_name, policy['primaryKey'])

        # Test policy_name connection-string 'az iot hub show-connection-string'
        self.cmd('iot hub show-connection-string -n {0} --policy-name {1}'.format(hub, policy_name), checks=[
            self.check('connectionString', policy_name_conn_str)
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
        device_count_pattern = r'\d$'
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
        self.kwargs["route_properties"] = json.dumps({"body": 4})
        props = "--sp '{route_properties}' --ap '{route_properties}'"
        self.cmd('iot hub route test --hub-name {0} -g {1} -n {2} {3}'.format(hub, rg, route_name, props),
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
        routing_sources = [source.value for source in RoutingSource if source != RoutingSource.Invalid]
        for new_source_type in routing_sources:
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

        # Data Residency tests
        dr_hub_name = self.create_random_name('dps-dr', 20)

        # Data residency not enabled in this region
        with self.assertRaises(HttpResponseError):
            self.cmd('az iot hub create -g {} -n {} --edr'.format(rg, dr_hub_name))

        # Successfully create in this region
        self.cmd('az iot hub create -g {} -n {} --location southeastasia --edr'.format(rg, dr_hub_name),
                 checks=[self.check('name', dr_hub_name),
                         self.check('location', 'southeastasia'),
                         self.check('properties.enableDataResidency', True)])
        self.cmd('az iot hub delete -n {}'.format(dr_hub_name))

    @AllowLargeResponse()
    @ResourceGroupPreparer(location='westus2')
    @StorageAccountPreparer()
    def test_identity_hub(self, resource_group, resource_group_location, storage_account):
        # Test IoT Hub create with identity
        from time import sleep

        subscription_id = self.get_subscription_id()
        rg = resource_group
        location = resource_group_location

        private_endpoint_type = 'Microsoft.Devices/IoTHubs'
        identity_hub = self.create_random_name(prefix='identitytesthub', length=32)
        identity_based_auth = 'identityBased'
        event_hub_system_identity_endpoint_name = self.create_random_name(prefix='EHSystemIdentityEndpoint', length=32)
        event_hub_user_identity_endpoint_name = self.create_random_name(prefix='EHUserIdentityEndpoint', length=32)

        containerName = 'iothubcontainer'
        storageConnectionString = self._get_azurestorage_connectionstring(rg, containerName, storage_account)
        endpoint_name = 'Event1'
        endpoint_type = 'EventHub'
        storage_cs_pattern = 'DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;'

        identity_storage_role = 'Storage Blob Data Contributor'
        storage_account_id = self.cmd('storage account show -n {0} -g {1}'.format(storage_account, rg)).get_output_in_json()['id']

        # identities
        user_identity_names = [
            self.create_random_name(prefix='iot-user-identity', length=32),
            self.create_random_name(prefix='iot-user-identity', length=32),
            self.create_random_name(prefix='iot-user-identity', length=32)
        ]

        # create user-assigned identity
        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            user_identity_1 = self.cmd('identity create -n {0} -g {1}'.format(user_identity_names[0], rg)).get_output_in_json()['id']
            user_identity_2 = self.cmd('identity create -n {0} -g {1}'.format(user_identity_names[1], rg)).get_output_in_json()['id']
            user_identity_3 = self.cmd('identity create -n {0} -g {1}'.format(user_identity_names[2], rg)).get_output_in_json()['id']

        # create hub with system-assigned identity, user-assigned identity, and assign storage roles
        with mock.patch('azure.cli.core.commands.arm._gen_guid', side_effect=self.create_guid):
            self.cmd('iot hub create -n {0} -g {1} --sku s1 --location {2} --mintls "1.2" --mi-system-assigned --mi-user-assigned {3} --role "{4}" --scopes "{5}"'
                     .format(identity_hub, rg, location, user_identity_1, identity_storage_role, storage_account_id))

        hub_props = self.cmd('iot hub show --name {0}'.format(identity_hub), checks=[
            self.check('properties.minTlsVersion', '1.2'),
            self.check('identity.type', 'SystemAssigned, UserAssigned')]).get_output_in_json()

        hub_object_id = hub_props['identity']['principalId']
        assert hub_object_id

        # Allow time for RBAC and Identity Service
        if self.is_live:
            sleep(60)

        # Test 'az iot hub update' with Identity-based fileUpload
        updated_hub = self.cmd('iot hub update -n {0} --fsa {1} --fsi [system] --fcs {2} --fc {3} --fnld 15'
                               .format(identity_hub, identity_based_auth, storageConnectionString, containerName)).get_output_in_json()
        assert updated_hub['properties']['storageEndpoints']['$default']['authenticationType'] == identity_based_auth
        assert updated_hub['properties']['messagingEndpoints']['fileNotifications']['lockDurationAsIso8601'] == '0:00:15'
        assert storage_cs_pattern in updated_hub['properties']['storageEndpoints']['$default']['connectionString']
        # Test fileupload authentication type settings
        # Setting key-based file upload (identity based commands should fail)
        updated_hub = self.cmd('iot hub update -n {0} -g {1} --fsa keyBased'.format(identity_hub, rg)).get_output_in_json()
        assert updated_hub['properties']['storageEndpoints']['$default']['authenticationType'] == 'keyBased'
        updated_hub = self.cmd('iot hub update -n {0} -g {1} --fsi test/user/'.format(identity_hub, rg), expect_failure=True)
        updated_hub = self.cmd('iot hub update -n {0} -g {1} --fsi [system]'.format(identity_hub, rg), expect_failure=True)

        # Back to identity-based file upload
        updated_hub = self.cmd('iot hub update -n {0} -g {1} --fsa {2}'.format(identity_hub, rg, identity_based_auth)).get_output_in_json()
        assert updated_hub['properties']['storageEndpoints']['$default']['authenticationType'] == identity_based_auth

        # Create EH and link identity
        eh_info = self._create_eventhub_and_link_identity(rg, hub_object_id, [user_identity_1])
        eventhub_endpoint_uri = eh_info[0]
        entity_path = eh_info[1]

        # Test 'az iot hub routing-endpoint create' with system-assigned identity and event hub endpoint
        self.cmd('iot hub routing-endpoint create --hub-name {0} -g {1} -n {2} -t {3} -r {4} -s {5} --auth-type {6} --endpoint-uri {7} --entity-path {8}'
                 .format(identity_hub, rg, event_hub_system_identity_endpoint_name, endpoint_type, rg, subscription_id, identity_based_auth, eventhub_endpoint_uri, entity_path),
                 checks=[self.check('length(eventHubs[*])', 1),
                         self.check('eventHubs[0].resourceGroup', rg),
                         self.check('eventHubs[0].name', event_hub_system_identity_endpoint_name),
                         self.check('eventHubs[0].authenticationType', identity_based_auth),
                         self.check('eventHubs[0].connectionString', None),
                         self.check('eventHubs[0].endpointUri', eventhub_endpoint_uri),
                         self.check('eventHubs[0].entityPath', entity_path),
                         self.check('length(serviceBusQueues[*])', 0),
                         self.check('length(serviceBusTopics[*])', 0),
                         self.check('length(storageContainers[*])', 0)])

        # Test routing-endpoint create with user-assigned identity and event hub endpoint
        self.cmd('iot hub routing-endpoint create --hub-name {0} -g {1} -n {2} -t {3} -r {4} -s {5} --auth-type {6} --identity {7} --endpoint-uri {8} --entity-path {9}'
                 .format(identity_hub, rg, event_hub_user_identity_endpoint_name, endpoint_type, rg, subscription_id, identity_based_auth, user_identity_1, eventhub_endpoint_uri, entity_path),
                 checks=[self.check('length(eventHubs[*])', 2),
                         self.check('eventHubs[1].resourceGroup', rg),
                         self.check('eventHubs[1].name', event_hub_user_identity_endpoint_name),
                         self.check('eventHubs[1].authenticationType', identity_based_auth),
                         self.check('eventHubs[1].connectionString', None),
                         self.check('eventHubs[1].endpointUri', eventhub_endpoint_uri),
                         self.check('eventHubs[1].entityPath', entity_path),
                         self.check('length(serviceBusQueues[*])', 0),
                         self.check('length(serviceBusTopics[*])', 0),
                         self.check('length(storageContainers[*])', 0)])

        # remove identity-based routing endpoints so we can remove user identity later
        self.cmd('iot hub routing-endpoint delete --hub-name {0} -g {1} -n {2}'.format(identity_hub, rg, event_hub_user_identity_endpoint_name))

        self.cmd('iot hub routing-endpoint delete --hub-name {0} -g {1} -n {2}'.format(identity_hub, rg, event_hub_system_identity_endpoint_name))

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

        # testing new identity namespace

        # show identity
        self.cmd('iot hub identity show -n {0} -g {1}'.format(identity_hub, rg),
                 checks=[
                     self.check('length(userAssignedIdentities)', 1),
                     self.check('type', IdentityType.system_assigned_user_assigned.value),
                     self.exists('userAssignedIdentities."{0}"'.format(user_identity_1))])

        # fix for hanging 'Transitioning' state from previous commands
        self._poll_for_hub_state(hub_name=identity_hub, resource_group_name=rg, desired_state='Active', polling_interval=10)

        # assign (user) add multiple user-assigned identities (2, 3)
        self.cmd('iot hub identity assign -n {0} -g {1} --user {2} {3}'
                 .format(identity_hub, rg, user_identity_2, user_identity_3),
                 checks=[
                     self.check('length(userAssignedIdentities)', 3),
                     self.check('type', IdentityType.system_assigned_user_assigned.value),
                     self.exists('userAssignedIdentities."{0}"'.format(user_identity_1)),
                     self.exists('userAssignedIdentities."{0}"'.format(user_identity_2)),
                     self.exists('userAssignedIdentities."{0}"'.format(user_identity_3))])

        # remove (system)
        self.cmd('iot hub identity remove -n {0} -g {1} --system'.format(identity_hub, rg),
                 checks=[
                     self.check('length(userAssignedIdentities)', 3),
                     self.check('type', IdentityType.user_assigned.value),
                     self.exists('userAssignedIdentities."{0}"'.format(user_identity_1)),
                     self.exists('userAssignedIdentities."{0}"'.format(user_identity_2)),
                     self.exists('userAssignedIdentities."{0}"'.format(user_identity_3))])

        # assign (system) re-add system identity
        self.cmd('iot hub identity assign -n {0} -g {1} --system'.format(identity_hub, rg),
                 checks=[
                     self.check('length(userAssignedIdentities)', 3),
                     self.exists('userAssignedIdentities."{0}"'.format(user_identity_1)),
                     self.exists('userAssignedIdentities."{0}"'.format(user_identity_2)),
                     self.exists('userAssignedIdentities."{0}"'.format(user_identity_3)),
                     self.check('type', IdentityType.system_assigned_user_assigned.value)])

        # remove (system) - remove system identity
        self.cmd('iot hub identity remove -n {0} -g {1} --system-assigned'.format(identity_hub, rg),
                 checks=[
                     self.check('type', IdentityType.user_assigned.value),
                     self.check('length(userAssignedIdentities)', 3),
                     self.exists('userAssignedIdentities."{0}"'.format(user_identity_1)),
                     self.exists('userAssignedIdentities."{0}"'.format(user_identity_2)),
                     self.exists('userAssignedIdentities."{0}"'.format(user_identity_3))])

        # remove (user) - remove single identity (2)
        self.cmd('iot hub identity remove -n {0} -g {1} --user {2}'.format(identity_hub, rg, user_identity_2),
                 checks=[
                     self.check('type', IdentityType.user_assigned.value),
                     self.check('length(userAssignedIdentities)', 2),
                     self.exists('userAssignedIdentities."{0}"'.format(user_identity_1)),
                     self.exists('userAssignedIdentities."{0}"'.format(user_identity_3))])

        # assign (system) re-add system identity
        self.cmd('iot hub identity assign -n {0} -g {1} --system'
                 .format(identity_hub, rg),
                 checks=[
                     self.check('length(userAssignedIdentities)', 2),
                     self.check('type', IdentityType.system_assigned_user_assigned.value)])

        # remove (--user-assigned)
        self.cmd('iot hub identity remove -n {0} -g {1} --user-assigned'
                 .format(identity_hub, rg),
                 checks=[
                     self.check('userAssignedIdentities', None),
                     self.check('type', IdentityType.system_assigned.value)])

        # remove (--system)
        self.cmd('iot hub identity remove -n {0} -g {1} --system'
                 .format(identity_hub, rg),
                 checks=[
                     self.check('userAssignedIdentities', None),
                     self.check('type', IdentityType.none.value)])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location='westus2')
    @StorageAccountPreparer()
    def test_hub_file_upload(self, resource_group, resource_group_location, storage_account):
        from time import sleep
        from azure.cli.core.azclierror import UnclassifiedUserFault
        hub = self.create_random_name(prefix='cli-file-upload-hub', length=32)
        user_identity_name = self.create_random_name(prefix='hub-user-identity', length=32)
        rg = resource_group
        containerName = self.create_random_name(prefix='iothubcontainer1', length=24)
        storageConnectionString = self._get_azurestorage_connectionstring(rg, containerName, storage_account)
        identity_based_auth = 'identityBased'
        key_based_auth = 'keyBased'
        storage_cs_pattern = 'DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;'

        # create user-assigned identity
        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            user_identity_obj = self.cmd('identity create -n {0} -g {1}'.format(user_identity_name, rg)).get_output_in_json()
        user_identity = user_identity_obj['id']
        user_identity_id = user_identity_obj['principalId']

        self.cmd('iot hub create -n {0} -g {1}'.format(hub, rg))

        # File upload - set to identity based (fail because no identity)
        self.cmd('iot hub update -n {0} -g {1} --fc {2} --fcs {3} --fsa {4}'
                 .format(hub, rg, containerName, storageConnectionString, identity_based_auth),
                 expect_failure=True)

        # File upload - set fileupload-identity /user/identity or [system] - fail
        self.cmd('iot hub update -n {0} -g {1} --fc {2} --fcs {3} --fsi /test/user/identity'
                 .format(hub, rg, containerName, storageConnectionString),
                 expect_failure=True)
        self.cmd('iot hub update -n {0} -g {1} --fc {2} --fcs {3} --fsi [system]'
                 .format(hub, rg, containerName, storageConnectionString),
                 expect_failure=True)

        # Testing hub update without $default storage endpoint
        self.kwargs.update({
            'hub': hub,
            'rg': rg
        })
        self.cmd('iot hub update -n {hub} -g {rg} --set "properties.storageEndpoints={{}}"',
                 checks=[self.not_exists('properties.storageEndpoints')])
        # update with fileUpload args (not container and cstring) should error
        with self.assertRaises(UnclassifiedUserFault) as ex:
            # configure fileupload SAS TTL
            self.cmd('iot hub update -n {hub} -g {rg} --fst 2')
        self.assertTrue('This hub has no default storage endpoint' in str(ex.exception))

        with self.assertRaises(UnclassifiedUserFault) as ex:
            # configure fileupload SAS TTL, with container name
            self.cmd('iot hub update -n {0} -g {1} --fst 2 --fc {2}'.format(hub, rg, containerName))
        self.assertTrue('This hub has no default storage endpoint' in str(ex.exception))

        # update with non-fileupload args should succeed (c2d TTL)
        self.cmd('iot hub update -n {hub} -g {rg} --ct 13',
                 checks=[self.check('properties.cloudToDevice.defaultTtlAsIso8601', '13:00:00')])
        # # --set identity
        self.cmd('iot hub update -n {hub} -g {rg} --set identity.type="SystemAssigned"',
                 checks=[self.check('identity.type', IdentityType.system_assigned.value)])

        # # reset identity for following tests
        self.cmd('iot hub identity remove -n {hub} -g {rg} --system',
                 checks=[self.check('type', IdentityType.none.value)])

        # File upload - add connection string and containername - keybased
        updated_hub = self.cmd('iot hub update -n {0} -g {1} --fc {2} --fcs {3}'
                 .format(hub, rg, containerName, storageConnectionString)).get_output_in_json()
        assert not updated_hub['properties']['storageEndpoints']['$default']['authenticationType']
        assert storage_cs_pattern in updated_hub['properties']['storageEndpoints']['$default']['connectionString']
        assert updated_hub['properties']['storageEndpoints']['$default']['containerName'] == containerName

        updated_hub = self.cmd('iot hub update -n {0} -g {1} --fsa {2}'
                 .format(hub, rg, key_based_auth)).get_output_in_json()
        assert updated_hub['properties']['storageEndpoints']['$default']['authenticationType'] == key_based_auth
        assert storage_cs_pattern in updated_hub['properties']['storageEndpoints']['$default']['connectionString']
        assert updated_hub['properties']['storageEndpoints']['$default']['containerName'] == containerName


        # Change to identity-based (with no identity) - fail
        self.cmd('iot hub update -n {0} -g {1} --fsa identitybased'.format(hub, rg), expect_failure=True)

        # change to use a user/identity or system identity - fail
        self.cmd('iot hub update -n {0} -g {1} --fsi [system]'.format(hub, rg), expect_failure=True)
        self.cmd('iot hub update -n {0} -g {1} --fsi /test/user/identity'.format(hub, rg), expect_failure=True)

        # add system identity, assign access to storage account
        hub_identity = self.cmd('iot hub identity assign --system -n {0} -g {1}'.format(hub, rg), checks=[
            self.check('type', IdentityType.system_assigned.value)
        ]).get_output_in_json()['principalId']

        storage_role = 'Storage Blob Data Contributor'
        storage_id = self.cmd('storage account show -n {0} -g {1}'.format(storage_account, rg)).get_output_in_json()['id']
        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            self.cmd('role assignment create --role "{0}" --assignee "{1}" --scope "{2}"'.format(storage_role, hub_identity, storage_id))
        if self.is_live:
            sleep(30)

        # change to system identity - fail (needs identityBased auth type)
        self.cmd('iot hub update -n {0} -g {1} --fsi [system]'.format(hub, rg), expect_failure=True)

        # change to identity-based
        updated_hub = self.cmd('iot hub update -n {0} -g {1} --fsa {2}'.format(hub, rg, identity_based_auth)).get_output_in_json()
        assert updated_hub['properties']['storageEndpoints']['$default']['authenticationType'] == identity_based_auth
        assert storage_cs_pattern in updated_hub['properties']['storageEndpoints']['$default']['connectionString']
        assert updated_hub['properties']['storageEndpoints']['$default']['containerName'] == containerName

        # explicitly assign to system identity
        updated_hub = self.cmd('iot hub update -n {0} -g {1} --fsi [system]'.format(hub, rg)).get_output_in_json()

        # explicit [system] should leave identity as null/None
        assert not updated_hub['properties']['storageEndpoints']['$default']['identity']
        assert storage_cs_pattern in updated_hub['properties']['storageEndpoints']['$default']['connectionString']
        assert updated_hub['properties']['storageEndpoints']['$default']['containerName'] == containerName

        # change to user-identity - fail
        updated_hub = self.cmd('iot hub update -n {0} -g {1} --fsi /test/user/identity'.format(hub, rg), expect_failure=True)

        # add a user identity, assign access to storage account
        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            self.cmd('role assignment create --role "{0}" --assignee "{1}" --scope "{2}"'.format(storage_role, user_identity_id, storage_id))
        if self.is_live:
            sleep(300)
        self.cmd('iot hub identity assign -n {0} -g {1} --user {2}'.format(hub, rg, user_identity), checks=[
            self.exists('userAssignedIdentities."{0}"'.format(user_identity)),
            self.check('type', IdentityType.system_assigned_user_assigned.value)])

        # change to user-identity
        updated_hub = self.cmd('iot hub update -n {0} -g {1} --fsi {2}'.format(hub, rg, user_identity)).get_output_in_json()
        assert updated_hub['properties']['storageEndpoints']['$default']['identity']['userAssignedIdentity'] == user_identity
        assert updated_hub['properties']['storageEndpoints']['$default']['authenticationType'] == identity_based_auth
        assert storage_cs_pattern in updated_hub['properties']['storageEndpoints']['$default']['connectionString']
        assert updated_hub['properties']['storageEndpoints']['$default']['containerName'] == containerName

        # change to key-based
        updated_hub = self.cmd('iot hub update -n {0} -g {1} --fsa {2}'.format(hub, rg, key_based_auth)).get_output_in_json()
        assert not updated_hub['properties']['storageEndpoints']['$default']['identity']
        assert updated_hub['properties']['storageEndpoints']['$default']['authenticationType'] == key_based_auth
        assert storage_cs_pattern in updated_hub['properties']['storageEndpoints']['$default']['connectionString']
        assert updated_hub['properties']['storageEndpoints']['$default']['containerName'] == containerName

    @AllowLargeResponse()
    @ResourceGroupPreparer(location='westus2')
    def test_hub_wait(self, resource_group, resource_group_location):
        hub = self.create_random_name(prefix='iot-hub-for-test-11', length=32)
        rg = resource_group

        # Create hub with no wait
        self.cmd('iot hub create -n {0} -g {1} --no-wait'.format(hub, rg))

        # Poll till hub is active
        self.cmd('iot hub wait -n {0} -g {1} --created'.format(hub, rg))

        # Delete hub with no wait
        self.cmd('iot hub delete -n {0} -g {1} --no-wait'.format(hub, rg))

        # Poll to make sure hub is deleted.
        try:
            self.cmd('iot hub wait -n {0} -g {1} --deleted'.format(hub, rg))
        except CLIError:
            pass

        # Final check and sleep to make sure lro poller thread is done
        self.cmd('iot hub show -n {0} -g {1}'.format(hub, rg), expect_failure=True)

    def _get_eventhub_connectionstring(self, rg):
        ehNamespace = self.create_random_name(prefix='ehNamespaceiothubfortest1', length=32)
        eventHub = self.create_random_name(prefix='eventHubiothubfortest', length=32)
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

    def _create_eventhub_and_link_identity(self, rg, hub_object_id, identities=None):
        ehNamespace = self.create_random_name(prefix='ehNamespaceiothubfortest1', length=32)
        eventHub = self.create_random_name(prefix='eventHubiothubfortest', length=32)
        role = 'Azure Event Hubs Data Sender'

        self.cmd('eventhubs namespace create --resource-group {0} --name {1}'
                 .format(rg, ehNamespace))

        eh = self.cmd('eventhubs eventhub create --resource-group {0} --namespace-name {1} --name {2}'
                      .format(rg, ehNamespace, eventHub)).get_output_in_json()
        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            self.cmd('role assignment create --role "{0}" --assignee "{1}" --scope "{2}"'.format(role, hub_object_id, eh['id']))
            if identities:
                for identity in identities:
                    identity_id = self.cmd('identity show --id "{}"'.format(identity)).get_output_in_json()['principalId']
                    self.cmd('role assignment create --role "{0}" --assignee "{1}" --scope "{2}"'.format(role, identity_id, eh['id']))

        # RBAC propogation
        if self.is_live:
            from time import sleep
            sleep(30)

        return ['sb://{0}.servicebus.windows.net'.format(ehNamespace), eventHub]

    # Polls and waits for hub to be in a desired state - may be temporary until we sort out LRO hub update issues
    def _poll_for_hub_state(self, hub_name, resource_group_name, desired_state, max_retries=10, polling_interval=5):
        from time import sleep
        attempts = 1
        hub_state = self.cmd('iot hub show --n {0} -g {1} --query="properties.state"'.format(hub_name, resource_group_name)).get_output_in_json()
        while hub_state != desired_state and attempts < max_retries:
            sleep(polling_interval)
            hub_state = self.cmd('iot hub show --n {0} -g {1} --query="properties.state"'.format(hub_name, resource_group_name)).get_output_in_json()
            attempts += 1
