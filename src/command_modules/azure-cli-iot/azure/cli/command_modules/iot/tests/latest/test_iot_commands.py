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

        # Test 'az iot hub create'
        self.cmd('iot hub create -n {0} -g {1} --sku S1 --partition-count 4'.format(hub, rg),
                 checks=[self.check('resourceGroup', rg),
                         self.check('location', location),
                         self.check('name', hub),
                         self.check('sku.name', 'S1'),
                         self.check('properties.eventHubEndpoints.events.partitionCount', '4')])

        # Test 'az iot hub show-connection-string'
        conn_str_pattern = r'^HostName={0}\.azure-devices\.net;SharedAccessKeyName=iothubowner;SharedAccessKey='.format(
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

        # Test 'az iot hub delete'
        self.cmd('iot hub delete -n {0}'.format(hub), checks=self.is_empty())
