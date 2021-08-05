# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

from azure.cli.command_modules.vm._template_builder import build_load_balancer_resource


class TestTemplateBuilder(unittest.TestCase):

    @mock.patch('azure.cli.command_modules.vm._template_builder.get_target_network_api', autospec=True)
    def test_build_load_balancer_resource(self, mock_get_api):
        mock_get_api.returtn_value = '1970-01-01'
        cmd_mock = mock.MagicMock()
        cmd_mock.supported_api_version.return_value = False

        result = build_load_balancer_resource(cmd_mock, 'lb1', 'westus', None, 'bepool1', 'natpool1', 'be_port',
                                              'frontip', 'pip_id1', 'subnet_id1', 'private_ip_address', 'dynamic',
                                              'basic', instance_count=1, disable_overprovision=False)
        self.assertEqual(result['properties']['inboundNatPools'][0]['properties']['frontendPortRangeEnd'], '50119')

        result = build_load_balancer_resource(cmd_mock, 'lb1', 'westus', None, 'bepool1', 'natpool1', 'be_port',
                                              'frontip', 'pip_id1', 'subnet_id1', 'private_ip_address', 'dynamic',
                                              'basic', instance_count=80, disable_overprovision=False)
        self.assertEqual(result['properties']['inboundNatPools'][0]['properties']['frontendPortRangeEnd'], '50159')

        result = build_load_balancer_resource(cmd_mock, 'lb1', 'westus', None, 'bepool1', 'natpool1', 'be_port',
                                              'frontip', 'pip_id1', 'subnet_id1', 'private_ip_address', 'dynamic',
                                              'basic', instance_count=80, disable_overprovision=True)
        self.assertEqual(result['properties']['inboundNatPools'][0]['properties']['frontendPortRangeEnd'], '50119')

        result = build_load_balancer_resource(cmd_mock, 'lb1', 'westus', None, 'bepool1', 'natpool1', 'be_port',
                                              'frontip', 'pip_id1', 'subnet_id1', 'private_ip_address', 'dynamic',
                                              'basic', instance_count=140, disable_overprovision=True)
        self.assertEqual(result['properties']['inboundNatPools'][0]['properties']['frontendPortRangeEnd'], '50139')
