#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.test_utils.vcr_test_base import (ResourceGroupVCRTestBase, JMESPathCheck, JMESPathPatternCheck)


class IoTHubTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(IoTHubTest, self).__init__(__file__, test_method)
        self.resource_group = 'iot-hub-test-rg'
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
        connection_string_pattern = r'^HostName={0}\.azure-devices\.net;SharedAccessKeyName=iothubowner;SharedAccessKey='.format(hub)
        self.cmd('iot hub show-connection-string -n {0}'.format(hub), checks=[
            JMESPathPatternCheck('connectionString', connection_string_pattern)
        ])

        self.cmd('iot hub show-connection-string -g {0}'.format(rg), checks=[
            JMESPathCheck('length([*])', 1),
            JMESPathCheck('[0].name', hub),
            JMESPathPatternCheck('[0].connectionString', connection_string_pattern)
        ])

        # Test 'az iot hub show'
        self.cmd('iot hub show -n {0}'.format(hub), checks=[
            JMESPathCheck('resourceGroup', rg),
            JMESPathCheck('location', location),
            JMESPathCheck('name', hub),
            JMESPathCheck('sku.name', 'S1')
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

        # Test 'az iot hub key list'
        self.cmd('iot hub key list --hub-name {0}'.format(hub), checks=[
            JMESPathCheck('length([*])', 5)
        ])

        # Test 'az iot hub key show'
        key_name = 'service'
        self.cmd('iot hub key show --hub-name {0} -n {1}'.format(hub, key_name), checks=[
            JMESPathCheck('keyName', key_name),
            JMESPathCheck('rights', 'ServiceConnect')
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
        self.cmd('iot hub consumer-group delete --hub-name {0} -n {1}'.format(hub, consumer_group_name))

        self.cmd('iot hub consumer-group list --hub-name {0}'.format(hub), checks=[
            JMESPathCheck('length([*])', 1),
            JMESPathCheck('[0]', '$Default'),
        ])

        # Test 'az iot device create'
        device_1 = self.device_id_1
        self.cmd('iot device create --hub-name {0} -d {1}'.format(hub, device_1),
                 checks=[
                     JMESPathCheck('deviceId', device_1),
                     JMESPathCheck('status', 'enabled'),
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
                     JMESPathCheck('connectionState', 'Disconnected'),
                     JMESPathCheck('authentication.symmetricKey.primaryKey', None),
                     JMESPathCheck('authentication.symmetricKey.secondaryKey', None),
                     JMESPathCheck('authentication.x509Thumbprint.primaryThumbprint', primary_thumbprint),
                     JMESPathCheck('authentication.x509Thumbprint.secondaryThumbprint', secondary_thumbprint),
                 ])

        # Test 'az iot device show-connection-string'
        connection_string_pattern = r'^HostName={0}\.azure-devices\.net;DeviceId={1};SharedAccessKey='.format(hub, device_1)
        self.cmd('iot device show-connection-string --hub-name {0} -d {1}'.format(hub, device_1), checks=[
            JMESPathPatternCheck('connectionString', connection_string_pattern)
        ])

        connection_string = 'HostName={0}.azure-devices.net;DeviceId={1};x509=true'.format(hub, device_2)
        self.cmd('iot device show-connection-string --hub-name {0} -d {1}'.format(hub, device_2), checks=[
            JMESPathCheck('connectionString', connection_string)
        ])

        self.cmd('iot device show-connection-string --hub-name {0}'.format(hub), checks=[
            JMESPathCheck('length([*])', 2),
            JMESPathCheck('[0].deviceId', device_1),
            JMESPathCheck('[1].deviceId', device_2),
        ])

        # Test 'az iot device show'
        self.cmd('iot device show --hub-name {0} -d {1}'.format(hub, device_1), checks=[
            JMESPathCheck('deviceId', device_1),
            JMESPathCheck('status', 'enabled'),
            JMESPathCheck('connectionState', 'Disconnected')
        ])

        # Test 'az iot device list'
        self.cmd('iot device list --hub-name {0}'.format(hub), checks=[
            JMESPathCheck('length([*])', 2),
            JMESPathCheck('[0].deviceId', device_1),
            JMESPathCheck('[1].deviceId', device_2),
        ])

        # Test 'az iot device delete'
        self.cmd('iot device delete --hub-name {0} -d {1}'.format(hub, device_1))
        self.cmd('iot device delete --hub-name {0} -d {1}'.format(hub, device_2))
