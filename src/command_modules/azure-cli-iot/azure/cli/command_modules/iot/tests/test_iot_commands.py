#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.utils.vcr_test_base import (ResourceGroupVCRTestBase, JMESPathCheck)
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
        connection_string = 'HostName=iot-hub-for-testing.azure-devices.net;SharedAccessKeyName=iothubowner;SharedAccessKey=fqS8+VBHmoLe/5/juDnt2LmnBF4DUkx6I87M7r5Jj3Y='
        self.cmd('iot hub show-connection-string -n {0}'.format(hub), checks=[
            JMESPathCheck('connectionString', connection_string),
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
        connection_string = 'HostName=iot-hub-for-testing.azure-devices.net;DeviceId=iot-device-for-testing;SharedAccessKey=qlhnBaWihYDHE/FlDZfngBTWfvwJ+BQbsmloLgl5+lU='
        self.cmd('iot device show-connection-string -n {0} -d {1}'.format(hub, device_id), checks=[
            JMESPathCheck('connectionString', connection_string),
        ])

        # Test 'az iot device list'
        self.cmd('iot device list -n {0}'.format(hub), checks=[
            JMESPathCheck('length([*])', 1),
            JMESPathCheck('[0].deviceId', device_id),
            JMESPathCheck('[0].status', 'enabled'),
            JMESPathCheck('[0].connectionState', 'Disconnected')
        ])
