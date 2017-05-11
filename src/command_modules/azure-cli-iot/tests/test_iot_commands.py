# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long,too-many-statements

from azure.cli.testsdk.vcr_test_base import \
    ResourceGroupVCRTestBase, JMESPathCheck, JMESPathPatternCheck, NoneCheck


class IoTHubTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(IoTHubTest, self).__init__(__file__, test_method, resource_group='iot-hub-test-rg')
        self.hub_name = 'iot-hub-for-test'
        self.device_id_1 = 'test-device-1'
        self.device_id_2 = 'test-device-2'

    def test_iot_hub(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        location = self.location
        hub = self.hub_name

        # Test 'az iot hub create'
        self.cmd('iot hub create -n {0} -g {1} --sku S1'.format(hub, rg),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('location', location),
                     JMESPathCheck('name', hub),
                     JMESPathCheck('sku.name', 'S1')
                 ])

        # Test 'az iot hub show-connection-string'
        conn_str_pattern = r'^HostName={0}\.azure-devices\.net;SharedAccessKeyName=iothubowner;SharedAccessKey='.format(hub)
        self.cmd('iot hub show-connection-string -n {0}'.format(hub), checks=[
            JMESPathPatternCheck('connectionString', conn_str_pattern)
        ])

        self.cmd('iot hub show-connection-string -g {0}'.format(rg), checks=[
            JMESPathCheck('length([*])', 1),
            JMESPathCheck('[0].name', hub),
            JMESPathPatternCheck('[0].connectionString', conn_str_pattern)
        ])

        # Test 'az iot hub update'
        property_to_update = 'properties.operationsMonitoringProperties.events.DeviceTelemetry'
        updated_value = 'Error, Information'
        self.cmd('iot hub update -n {0} --set {1}="{2}"'.format(hub, property_to_update, updated_value),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('location', location),
                     JMESPathCheck('name', hub),
                     JMESPathCheck('sku.name', 'S1'),
                     JMESPathCheck(property_to_update, updated_value)
                 ])

        # Test 'az iot hub show'
        self.cmd('iot hub show -n {0}'.format(hub), checks=[
            JMESPathCheck('resourceGroup', rg),
            JMESPathCheck('location', location),
            JMESPathCheck('name', hub),
            JMESPathCheck('sku.name', 'S1'),
            JMESPathCheck(property_to_update, updated_value)
        ])

        # Test 'az iot hub list'
        self.cmd('iot hub list -g {0}'.format(rg), checks=[
            JMESPathCheck('length([*])', 1),
            JMESPathCheck('[0].resourceGroup', rg),
            JMESPathCheck('[0].location', location),
            JMESPathCheck('[0].name', hub),
            JMESPathCheck('[0].sku.name', 'S1')
        ])

        # Test 'az iot hub sku list'
        self.cmd('iot hub list-skus -n {0}'.format(hub), checks=[
            JMESPathCheck('length([*])', 3),
            JMESPathCheck('[0].sku.name', 'S1'),
            JMESPathCheck('[1].sku.name', 'S2'),
            JMESPathCheck('[2].sku.name', 'S3')
        ])

        # Test 'az iot hub policy create'
        policy_name = 'test_policy'
        permissions = 'RegistryWrite ServiceConnect DeviceConnect'
        self.cmd('iot hub policy create --hub-name {0} -n {1} --permissions {2}'.format(hub, policy_name, permissions),
                 checks=NoneCheck())

        # Test 'az iot hub policy list'
        self.cmd('iot hub policy list --hub-name {0}'.format(hub), checks=[
            JMESPathCheck('length([*])', 6)
        ])

        # Test 'az iot hub policy show'
        self.cmd('iot hub policy show --hub-name {0} -n {1}'.format(hub, policy_name), checks=[
            JMESPathCheck('keyName', policy_name),
            JMESPathCheck('rights', 'RegistryWrite, ServiceConnect, DeviceConnect')
        ])

        # Test 'az iot hub policy delete'
        self.cmd('iot hub policy delete --hub-name {0} -n {1}'.format(hub, policy_name), checks=NoneCheck())
        self.cmd('iot hub policy list --hub-name {0}'.format(hub), checks=[
            JMESPathCheck('length([*])', 5)
        ])

        # Test 'az iot hub consumer-group create'
        consumer_group_name = 'cg1'
        self.cmd('iot hub consumer-group create --hub-name {0} -n {1}'.format(hub, consumer_group_name), checks=[
            JMESPathCheck('name', consumer_group_name)
        ])

        # Test 'az iot hub consumer-group show'
        self.cmd('iot hub consumer-group show --hub-name {0} -n {1}'.format(hub, consumer_group_name), checks=[
            JMESPathCheck('name', consumer_group_name)
        ])

        # Test 'az iot hub consumer-group list'
        self.cmd('iot hub consumer-group list --hub-name {0}'.format(hub), checks=[
            JMESPathCheck('length([*])', 2),
            JMESPathCheck('[0]', '$Default'),
            JMESPathCheck('[1]', consumer_group_name)
        ])

        # Test 'az iot hub consumer-group delete'
        self.cmd('iot hub consumer-group delete --hub-name {0} -n {1}'.format(hub, consumer_group_name),
                 checks=NoneCheck())

        self.cmd('iot hub consumer-group list --hub-name {0}'.format(hub), checks=[
            JMESPathCheck('length([*])', 1),
            JMESPathCheck('[0]', '$Default')
        ])

        # Test 'az iot hub job list'
        self.cmd('iot hub job list --hub-name {0}'.format(hub), checks=NoneCheck())

        # Test 'az iot hub job show'
        job_id = 'fake-job'
        expected_exception = 'Job not found with ID'
        self.cmd('iot hub job show --hub-name {0} --job-id {1}'.format(hub, job_id),
                 allowed_exceptions=expected_exception)

        # Test 'az iot hub job cancel'
        expected_exception = 'JobNotFound'
        self.cmd('iot hub job cancel --hub-name {0} --job-id {1}'.format(hub, job_id),
                 allowed_exceptions=expected_exception)

        # Test 'az iot device create'
        device_1 = self.device_id_1
        self.cmd('iot device create --hub-name {0} -d {1}'.format(hub, device_1),
                 checks=[
                     JMESPathCheck('deviceId', device_1),
                     JMESPathCheck('status', 'enabled'),
                     JMESPathCheck('statusReason', None),
                     JMESPathCheck('connectionState', 'Disconnected')
                 ])

        device_2 = self.device_id_2
        primary_thumbprint = 'A361EA6A7119A8B0B7BBFFA2EAFDAD1F9D5BED8C'
        secondary_thumbprint = '14963E8F3BA5B3984110B3C1CA8E8B8988599087'
        self.cmd('iot device create --hub-name {0} -d {1} --x509 --primary-thumbprint {2} --secondary-thumbprint {3}'
                 .format(hub, device_2, primary_thumbprint, secondary_thumbprint),
                 checks=[
                     JMESPathCheck('deviceId', device_2),
                     JMESPathCheck('status', 'enabled'),
                     JMESPathCheck('statusReason', None),
                     JMESPathCheck('connectionState', 'Disconnected'),
                     JMESPathCheck('authentication.symmetricKey.primaryKey', None),
                     JMESPathCheck('authentication.symmetricKey.secondaryKey', None),
                     JMESPathCheck('authentication.x509Thumbprint.primaryThumbprint', primary_thumbprint),
                     JMESPathCheck('authentication.x509Thumbprint.secondaryThumbprint', secondary_thumbprint),
                 ])

        # Test 'az iot device show-connection-string'
        conn_str_pattern = r'^HostName={0}\.azure-devices\.net;DeviceId={1};SharedAccessKey='.format(hub, device_1)
        self.cmd('iot device show-connection-string --hub-name {0} -d {1}'.format(hub, device_1), checks=[
            JMESPathPatternCheck('connectionString', conn_str_pattern)
        ])

        connection_string = 'HostName={0}.azure-devices.net;DeviceId={1};x509=true'.format(hub, device_2)
        self.cmd('iot device show-connection-string --hub-name {0} -d {1}'.format(hub, device_2), checks=[
            JMESPathCheck('connectionString', connection_string)
        ])

        device_id_pattern = r'^test\-device\-\d$'
        self.cmd('iot device show-connection-string --hub-name {0}'.format(hub), checks=[
            JMESPathCheck('length([*])', 2),
            JMESPathPatternCheck('[0].deviceId', device_id_pattern),
            JMESPathPatternCheck('[1].deviceId', device_id_pattern)
        ])

        # Test 'az iot device show'
        self.cmd('iot device show --hub-name {0} -d {1}'.format(hub, device_1), checks=[
            JMESPathCheck('deviceId', device_1),
            JMESPathCheck('status', 'enabled'),
            JMESPathCheck('statusReason', None),
            JMESPathCheck('connectionState', 'Disconnected')
        ])

        # Test 'az iot device update'
        status_reason = 'TestReason'
        self.cmd('iot device update --hub-name {0} -d {1} --set statusReason={2}'.format(hub, device_2, status_reason),
                 checks=[
                     JMESPathCheck('deviceId', device_2),
                     JMESPathCheck('status', 'enabled'),
                     JMESPathCheck('statusReason', status_reason),
                     JMESPathCheck('connectionState', 'Disconnected'),
                     JMESPathCheck('authentication.symmetricKey.primaryKey', None),
                     JMESPathCheck('authentication.symmetricKey.secondaryKey', None),
                     JMESPathCheck('authentication.x509Thumbprint.primaryThumbprint', primary_thumbprint),
                     JMESPathCheck('authentication.x509Thumbprint.secondaryThumbprint', secondary_thumbprint),
                 ])

        # Test 'az iot device list'
        self.cmd('iot device list --hub-name {0}'.format(hub), checks=[
            JMESPathCheck('length([*])', 2),
            JMESPathPatternCheck('[0].deviceId', device_id_pattern),
            JMESPathPatternCheck('[1].deviceId', device_id_pattern)
        ])

        # Test 'az iot device message send'
        self.cmd('iot device message send --hub-name {0} -d {1}'.format(hub, device_1), checks=NoneCheck())

        # Test 'az iot device message receive'
        self.cmd('iot device message receive --hub-name {0} -d {1}'.format(hub, device_1), checks=NoneCheck())

        # Test 'az iot device message complete'
        lock_token = '00000000-0000-0000-0000-000000000000'
        expected_exception = 'PreconditionFailed'
        self.cmd('iot device message complete --hub-name {0} -d {1} --lock-token {2}'.format(hub, device_1, lock_token),
                 allowed_exceptions=expected_exception)

        # Test 'az iot device message reject'
        self.cmd('iot device message reject --hub-name {0} -d {1} --lock-token {2}'.format(hub, device_1, lock_token),
                 allowed_exceptions=expected_exception)

        # Test 'az iot device message abandon'
        self.cmd('iot device message abandon --hub-name {0} -d {1} --lock-token {2}'.format(hub, device_1, lock_token),
                 allowed_exceptions=expected_exception)

        # Test 'az iot hub show-quota-metrics'
        self.cmd('iot hub show-quota-metrics -n {0}'.format(hub), checks=[
            JMESPathCheck('length([*])', 2),
            JMESPathCheck('[0].name', 'TotalMessages'),
            JMESPathCheck('[0].maxValue', 400000),
            JMESPathCheck('[1].name', 'TotalDeviceCount'),
            JMESPathCheck('[1].maxValue', 500000)
        ])

        # Test 'az iot hub show-stats'
        device_count_pattern = r'^\d$'
        self.cmd('iot hub show-stats -n {0}'.format(hub), checks=[
            JMESPathPatternCheck('disabledDeviceCount', device_count_pattern),
            JMESPathPatternCheck('enabledDeviceCount', device_count_pattern),
            JMESPathPatternCheck('totalDeviceCount', device_count_pattern)
        ])

        # Test 'az iot device delete'
        self.cmd('iot device delete --hub-name {0} -d {1}'.format(hub, device_1), checks=NoneCheck())
        self.cmd('iot device delete --hub-name {0} -d {1}'.format(hub, device_2), checks=NoneCheck())

        # Test 'az iot hub delete'
        self.cmd('iot hub delete -n {0}'.format(hub), checks=NoneCheck())
