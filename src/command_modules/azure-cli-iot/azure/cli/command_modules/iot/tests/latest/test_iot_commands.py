# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=too-many-statements

from azure.cli.testsdk import ResourceGroupPreparer, ScenarioTest


class IoTHubTest(ScenarioTest):

    @ResourceGroupPreparer()
    def test_iot_hub(self, resource_group, resource_group_location):
        hub = 'iot-hub-for-test'
        rg = resource_group
        location = resource_group_location
        ehConnectionString = self._get_eventhub_connectionstring(rg)
        subscription_id = self._get_current_subscription()

        # Test 'az iot hub create'
        self.cmd('iot hub create -n {0} -g {1} --sku S1 --partition-count 4'.format(hub, rg),
                 checks=[self.check('resourceGroup', rg),
                         self.check('location', location),
                         self.check('name', hub),
                         self.check('sku.name', 'S1'),
                         self.check('properties.eventHubEndpoints.events.partitionCount', '4')])

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

        # Test 'az iot hub update'
        property_to_update = 'properties.operationsMonitoringProperties.events.DeviceTelemetry'
        updated_value = 'Error, Information'
        self.cmd('iot hub update -n {0} --set {1}="{2}"'.format(hub, property_to_update, updated_value),
                 checks=[self.check('resourceGroup', rg),
                         self.check('location', location),
                         self.check('name', hub),
                         self.check('sku.name', 'S1'),
                         self.check(property_to_update, updated_value)])

        # Test 'az iot hub show'
        self.cmd('iot hub show -n {0}'.format(hub), checks=[
            self.check('resourceGroup', rg),
            self.check('location', location),
            self.check('name', hub),
            self.check('sku.name', 'S1'),
            self.check(property_to_update, updated_value)
        ])

        # Test 'az iot hub list'
        self.cmd('iot hub list -g {0}'.format(rg), checks=[
            self.check('length([*])', 1),
            self.check('[0].resourceGroup', rg),
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

        # Test 'az iot hub job list'
        self.cmd('iot hub job list --hub-name {0}'.format(hub), checks=self.is_empty())

        # Test 'az iot hub job show'
        job_id = 'fake-job'
        self.cmd('iot hub job show --hub-name {0} --job-id {1}'.format(hub, job_id),
                 expect_failure=True)

        # Test 'az iot hub job cancel'
        self.cmd('iot hub job cancel --hub-name {0} --job-id {1}'.format(hub, job_id),
                 expect_failure=True)

        # Test 'az iot hub show-quota-metrics'
        self.cmd('iot hub show-quota-metrics -n {0}'.format(hub), checks=[
            self.check('length([*])', 2),
            self.check('[0].name', 'TotalMessages'),
            self.check('[0].maxValue', 400000),
            self.check('[1].name', 'TotalDeviceCount'),
            self.check('[1].maxValue', 500000)
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
                         self.check('length(storageContainers[*])', 0)])

        # Test 'az iot hub delete'
        self.cmd('iot hub delete -n {0}'.format(hub), checks=self.is_empty())

    def _get_eventhub_connectionstring(self, rg):
        ehNamespace = 'ehNamespaceiothubfortest'
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

    def _get_current_subscription(self):
        output = self.cmd('account show')
        return output.get_output_in_json()['id']
