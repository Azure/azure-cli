# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

try:
    from unittest.mock import MagicMock
    from unittest.mock import patch
except ImportError:
    from mock import MagicMock
    from mock import patch

import unittest
import uuid
from azure.cli.command_modules.iot import custom as subject
from azure.cli.command_modules.iot.iot_sdk.utility import block_stdout
from azure.cli.core.util import CLIError
from iothub_service_client import IoTHubError
from iothub_client import IoTHubClientError

json = '{\"properties\":{\"desired\":{\"Awesome\":1}}}'
device_name = 'device'
hub_name = 'hub'
connstring = 'HostName=abcd;SharedAccessKeyName=name;SharedAccessKey=value'


class TwinTests(unittest.TestCase):
    @patch('azure.cli.command_modules.iot.custom.IoTHubDeviceTwin')
    @patch('azure.cli.command_modules.iot.custom.iot_hub_show_connection_string')
    def test_twin_show(self, mock_hub, mock_twin):
        mock_twin.return_value.get_twin.return_value = json
        result = subject.iot_twin_show(MagicMock(), device_name, hub_name)
        self.assertIsNot(result, None)
        mock_twin.return_value.get_twin.assert_called_with(device_name)
        self.assertIs(mock_twin.return_value.get_twin.call_count, 1)

    @patch('azure.cli.command_modules.iot.custom.IoTHubDeviceTwin')
    @patch('azure.cli.command_modules.iot.custom.iot_hub_show_connection_string')
    def test_twin_show_with_error(self, mock_hub, mock_twin):
        mock_twin.return_value.get_twin.side_effect = IoTHubError()
        with self.assertRaises(CLIError):
            subject.iot_twin_show(MagicMock(), device_name, hub_name)

    @patch('azure.cli.command_modules.iot.custom.IoTHubDeviceTwin')
    @patch('azure.cli.command_modules.iot.custom.iot_hub_show_connection_string')
    def test_twin_update(self, mock_hub, mock_twin):
        mock_twin.return_value.update_twin.return_value = json
        result = subject.iot_twin_update(MagicMock(), device_name, hub_name, json)
        self.assertIsNot(result, None)
        mock_twin.return_value.update_twin.assert_called_with(device_name, json)
        self.assertIs(mock_twin.return_value.update_twin.call_count, 1)

    @patch('azure.cli.command_modules.iot.custom.IoTHubDeviceTwin')
    @patch('azure.cli.command_modules.iot.custom.iot_hub_show_connection_string')
    def test_twin_update_invalidjson_error(self, mock_hub, mock_twin):
        with self.assertRaises(CLIError):
            subject.iot_twin_update(MagicMock(), device_name, hub_name, json + '}{')

    @patch('azure.cli.command_modules.iot.custom.IoTHubDeviceTwin')
    @patch('azure.cli.command_modules.iot.custom.iot_hub_show_connection_string')
    def test_twin_update_with_error(self, mock_hub, mock_twin):
        e = IoTHubError('errors')
        mock_twin.return_value.update_twin.side_effect = e
        with self.assertRaises(CLIError):
            subject.iot_twin_update(MagicMock(), device_name, hub_name, json)


class DeviceMethodTests(unittest.TestCase):
    @patch('azure.cli.command_modules.iot.custom.IoTHubDeviceMethod')
    @patch('azure.cli.command_modules.iot.custom.iot_hub_show_connection_string')
    def test_device_method(self, mock_hub, mock_devicemethod):
        mock_devicemethod.return_value.invoke.return_value = MagicMock(status=200, payload='awesome')
        response = subject.iot_device_method(MagicMock(), device_name, hub_name, 'method', json, 60)
        self.assertIs(response['status'], 200)
        self.assertIsNotNone(response['payload'])
        mock_devicemethod.return_value.invoke.assert_called_with(device_name, 'method', json, 60)
        self.assertIs(mock_devicemethod.return_value.invoke.call_count, 1)

    @patch('azure.cli.command_modules.iot.custom.IoTHubDeviceMethod')
    @patch('azure.cli.command_modules.iot.custom.iot_hub_show_connection_string')
    def test_device_method_error(self, mock_hub, mock_devicemethod):
        e = IoTHubError('errors')
        mock_devicemethod.return_value.invoke.side_effect = e
        with self.assertRaises(CLIError):
            subject.iot_device_method(MagicMock(), device_name, hub_name, 'method', json)


class HubMessageTests(unittest.TestCase):
    @patch('azure.cli.command_modules.iot.custom.IoTHubMessaging')
    @patch('azure.cli.command_modules.iot.custom.iot_hub_show_connection_string')
    def test_hub_send(self, mock_hub, mock_hubmsg):
        subject.iot_hub_message_send(MagicMock(), device_name, hub_name,
                                     str(uuid.uuid4()), str(uuid.uuid4()))
        self.assertIs(mock_hubmsg.return_value.open.call_count, 1)
        self.assertIs(mock_hubmsg.return_value.send_async.call_count, 1)
        self.assertIs(mock_hubmsg.return_value.close.call_count, 1)

    @patch('azure.cli.command_modules.iot.custom.IoTHubMessaging')
    @patch('azure.cli.command_modules.iot.custom.iot_hub_show_connection_string')
    def test_hub_send_error(self, mock_hub, mock_hubmsg):
        e = IoTHubError('errors')
        mock_hubmsg.return_value.send_async.side_effect = e
        with self.assertRaises(CLIError):
            subject.iot_hub_message_send(MagicMock(), device_name, hub_name,
                                         str(uuid.uuid4()), str(uuid.uuid4()))


class DeviceMessageTests(unittest.TestCase):
    @patch('azure.cli.command_modules.iot.iot_sdk.device_manager.DeviceManager.keep_alive')
    @patch('azure.cli.command_modules.iot.iot_sdk.device_manager.IoTHubClient')
    @patch('azure.cli.command_modules.iot.custom._get_single_device_connection_string')
    def test_device_msg(self, mock_hub, mock_deviceclient, keepalive):
        txt_protocol = 'http'
        mock_hub.return_value = connstring
        keepalive.return_value = False
        subject.iot_device_send_message_ext(MagicMock(), device_name, hub_name, txt_protocol)
        protocol = subject._iot_sdk_device_process_protocol(txt_protocol)
        mock_deviceclient.assert_called_with(connstring, protocol)

    @patch('azure.cli.command_modules.iot.iot_sdk.device_manager.DeviceManager.send_message')
    @patch('azure.cli.command_modules.iot.iot_sdk.device_manager.IoTHubClient')
    @patch('azure.cli.command_modules.iot.custom._get_single_device_connection_string')
    def test_device_msg_runtime_error(self, mock_hub, mock_deviceclient, mock_send):
        txt_protocol = 'mqtt'
        mock_hub.return_value = connstring
        e = RuntimeError('errors')
        mock_send.side_effect = e
        with self.assertRaises(CLIError):
            subject.iot_device_send_message_ext(MagicMock(), device_name, hub_name, txt_protocol)
            protocol = subject._iot_sdk_device_process_protocol(txt_protocol)
            mock_deviceclient.assert_called_with(connstring, protocol)

    @patch('azure.cli.command_modules.iot.iot_sdk.device_manager.DeviceManager.send_message')
    @patch('azure.cli.command_modules.iot.iot_sdk.device_manager.IoTHubClient')
    @patch('azure.cli.command_modules.iot.custom._get_single_device_connection_string')
    def test_device_msg_sdk_error(self, mock_hub, mock_deviceclient, mock_send):
        txt_protocol = 'mqtt'
        mock_hub.return_value = connstring
        e = IoTHubClientError('errors')
        mock_send.side_effect = e
        with self.assertRaises(CLIError):
            subject.iot_device_send_message_ext(MagicMock(), device_name, hub_name, txt_protocol)
            protocol = subject._iot_sdk_device_process_protocol(txt_protocol)
            mock_deviceclient.assert_called_with(connstring, protocol)


class SimulationTests(unittest.TestCase):
    @patch('azure.cli.command_modules.iot.iot_sdk.device_manager.DeviceManager.received')
    @patch('azure.cli.command_modules.iot.iot_sdk.device_manager.DeviceManager.configure_receive_settle')
    @patch('azure.cli.command_modules.iot.iot_sdk.device_manager.DeviceManager.keep_alive')
    @patch('azure.cli.command_modules.iot.iot_sdk.device_manager.IoTHubClient')
    @patch('azure.cli.command_modules.iot.custom._get_single_device_connection_string')
    def test_device_sim(self, mock_hub, mock_deviceclient, keepalive, crs, received):
        txt_protocol = 'amqp'
        txt_settle = 'reject'
        expected_msgs = 3
        receive_count = 2
        mock_hub.return_value = connstring
        keepalive.return_value = False
        mock_deviceclient.return_value.send_event_async.return_value = True
        received.side_effect = [0, 1, 2]
        with block_stdout():
            subject.iot_simulate_device(MagicMock(), device_name, hub_name, txt_settle, txt_protocol,
                                        'data', expected_msgs, 1, receive_count)
        protocol = subject._iot_sdk_device_process_protocol(txt_protocol)
        mock_deviceclient.assert_called_with(connstring, protocol)
        crs.assert_called_with(txt_settle)
        self.assertIs(mock_deviceclient.return_value.send_event_async.call_count, expected_msgs)
        self.assertIs(received.call_count, receive_count + 1)

    @patch('azure.cli.command_modules.iot.iot_sdk.device_manager.DeviceManager.send_message')
    @patch('azure.cli.command_modules.iot.iot_sdk.device_manager.IoTHubClient')
    @patch('azure.cli.command_modules.iot.custom._get_single_device_connection_string')
    def test_device_sim_error(self, mock_hub, mock_deviceclient, mock_send):
        txt_protocol = 'amqp'
        txt_settle = 'reject'
        expected_msgs = 3
        receive_count = 2
        mock_hub.return_value = connstring
        mock_deviceclient.return_value.send_event_async.return_value = True
        e = RuntimeError('errors')
        mock_send.side_effect = e
        with self.assertRaises(CLIError):
            with block_stdout():
                subject.iot_simulate_device(MagicMock(), device_name, hub_name, txt_settle, txt_protocol,
                                            'data', expected_msgs, 1, receive_count)


if __name__ == '__main__':
    unittest.main()
