#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.utils.vcr_test_base import (VCRTestBase, JMESPathCheck)


class IoTHubCreateTest(VCRTestBase):
    def __init__(self, test_method):
        super(IoTHubCreateTest, self).__init__(__file__, test_method)
        self.resource_group = 'iot-hub-test-rg'
        self.hub_name = 'iot-hub-for-testing'

    def test_iot_hub_create(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        hub = self.hub_name
        self.cmd('iot hub create -n {0} -g {1} --sku S1'.format(hub, rg),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('location', 'westus'),
                     JMESPathCheck('name', hub),
                     JMESPathCheck('sku.name', 'S1')
                 ])
        connection_string = 'HostName=iot-hub-for-testing.azure-devices.net;SharedAccessKeyName=iothubowner;SharedAccessKey=P80tG5ljXUHtGYyc+oP3GCAazRCq8d0VUtJ4RGrSru4='
        self.cmd('iot hub show-connection-string -n {0} -g {1}'.format(hub, rg),
                 checks=[
                     JMESPathCheck('connectionString', connection_string)
                 ])


class IoTDeviceCreateTest(VCRTestBase):
    def __init__(self, test_method):
        super(IoTDeviceCreateTest, self).__init__(__file__, test_method)
        self.resource_group = 'iot-hub-test-rg'
        self.hub_name = 'iot-hub-for-testing'
        self.device_id = 'iot-device-for-test'

    def test_iot_device_create(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        hub = self.hub_name
        device_id = self.device_id
        self.cmd('iot device create --hub {0} -g {1} -d {2}'.format(hub, rg, device_id),
                 checks=[
                     JMESPathCheck('deviceId', device_id),
                     JMESPathCheck('status', 'enabled'),
                     JMESPathCheck('connectionState', 'Disconnected')
                 ])
        connection_string = 'HostName=iot-hub-for-testing.azure-devices.net;DeviceId=iot-device-for-test;SharedAccessKey=fj6CZB/IrYJI3BOk8X0tzfABo/tsYZJ9boOr4SeG5YU='
        self.cmd('iot device show-connection-string --hub {0} -g {1} -d {2}'.format(hub, rg, device_id),
                 checks=[
                     JMESPathCheck('connectionString', connection_string)
                 ])
