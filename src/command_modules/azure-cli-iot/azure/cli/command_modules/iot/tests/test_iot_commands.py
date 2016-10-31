#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.test_utils.vcr_test_base import (ResourceGroupVCRTestBase, JMESPathCheck)
import azure.cli.core._logging as _logging

logger = _logging.get_az_logger(__name__)


class IoTHubTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(IoTHubTest, self).__init__(__file__, test_method)
        self.resource_group = 'iot-hub-test-rg'
        self.hub_name = 'iot-hub-for-testing'
        self.device_id = 'iot-device-for-testing'

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
        connection_string = 'HostName=iot-hub-for-testing.azure-devices.net;SharedAccessKeyName=iothubowner;SharedAccessKey=cI+EYy448bmVabof54H7wiG0ntHwM9mqRL5rFOoBGj8='
        self.cmd('iot hub show-connection-string -n {0}'.format(hub), checks=[
            JMESPathCheck('connectionString', connection_string)
        ])

        self.cmd('iot hub show-connection-string -g {0}'.format(rg), checks=[
            JMESPathCheck('length([*])', 1),
            JMESPathCheck('[0].name', hub),
            JMESPathCheck('[0].connectionString', connection_string)
        ])

        # Test 'az iot hub show'
        self.cmd('iot hub show -g {0} -n {1}'.format(rg, hub), checks=[
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

        # Test 'az iot device create'
        device_id = self.device_id
        self.cmd('iot device create -n {0} -d {1}'.format(hub, device_id),
                 checks=[
                     JMESPathCheck('deviceId', device_id),
                     JMESPathCheck('status', 'enabled'),
                     JMESPathCheck('connectionState', 'Disconnected')
                 ])

        # Test 'az iot device show-connection-string'
        connection_string = 'HostName=iot-hub-for-testing.azure-devices.net;DeviceId=iot-device-for-testing;SharedAccessKey=dw93dOLBIxAcczUqoEDukwh1pVi7gzIQq65ahBS6qNw='
        self.cmd('iot device show-connection-string -n {0} -d {1}'.format(hub, device_id), checks=[
            JMESPathCheck('connectionString', connection_string)
        ])

        self.cmd('iot device show-connection-string -n {0}'.format(hub), checks=[
            JMESPathCheck('length([*])', 1),
            JMESPathCheck('[0].deviceId', device_id),
            JMESPathCheck('[0].connectionString', connection_string)
        ])

        # Test 'az iot device show'
        self.cmd('iot device show -n {0} -d {1}'.format(hub, device_id), checks=[
            JMESPathCheck('deviceId', device_id),
            JMESPathCheck('status', 'enabled'),
            JMESPathCheck('connectionState', 'Disconnected')
        ])

        # Test 'az iot device list'
        self.cmd('iot device list -n {0}'.format(hub), checks=[
            JMESPathCheck('length([*])', 1),
            JMESPathCheck('[0].deviceId', device_id),
            JMESPathCheck('[0].status', 'enabled'),
            JMESPathCheck('[0].connectionState', 'Disconnected')
        ])

        # Test 'az iot device delete'
        self.cmd('iot device delete -n {0} -d {1}'.format(hub, device_id))
