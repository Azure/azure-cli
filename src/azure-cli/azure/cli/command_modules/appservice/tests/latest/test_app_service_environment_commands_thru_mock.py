# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-few-public-methods

import unittest
from unittest import mock
from azure.cli.core.azclierror import ValidationError


from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.web.models import HostingEnvironmentProfile, AseV3NetworkingConfiguration
from azure.mgmt.network.models import (Subnet, RouteTable, Route, NetworkSecurityGroup, SecurityRule, Delegation)

from azure.cli.command_modules.appservice.appservice_environment import (show_appserviceenvironment,
                                                                         list_appserviceenvironments,
                                                                         list_appserviceenvironment_plans,
                                                                         list_appserviceenvironment_addresses,
                                                                         create_appserviceenvironment_arm,
                                                                         update_appserviceenvironment,
                                                                         delete_appserviceenvironment)


class AppServiceEnvironmentScenarioMockTest(unittest.TestCase):
    def setUp(self):
        self.mock_logger = mock.MagicMock()
        self.mock_cmd = mock.MagicMock()
        self.mock_cmd.cli_ctx = mock.MagicMock()
        self.client = WebSiteManagementClient(mock.MagicMock(), '123455678')

    @mock.patch('azure.cli.command_modules.appservice.appservice_environment._get_ase_client_factory', autospec=True)
    def test_app_service_environment_show(self, ase_client_factory_mock):
        ase_name = 'mock_ase_name'
        rg_name = 'mock_rg_name'
        ase_client = mock.MagicMock()
        ase_client_factory_mock.return_value = ase_client
        host_env = HostingEnvironmentProfile(id='/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/mock_rg_name/Microsoft.Web/hostingEnvironments/mock_ase_name')
        host_env.name = ase_name        
        ase_client.get.return_value = host_env
        ase_client.list.return_value = [host_env]

        result = show_appserviceenvironment(self.mock_cmd, ase_name, None)

        # Assert same name
        self.assertEqual(result.name, ase_name)

    @mock.patch('azure.cli.command_modules.appservice.appservice_environment._get_ase_client_factory', autospec=True)
    def test_app_service_environment_list(self, ase_client_factory_mock):
        ase_name_1 = 'mock_ase_name_1'
        ase_name_2 = 'mock_ase_name_2'
        rg_name_1 = 'mock_rg_name_1'
        rg_name_2 = 'mock_rg_name_2'
        ase_client = mock.MagicMock()
        ase_client_factory_mock.return_value = ase_client
        host_env1 = HostingEnvironmentProfile(id='/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/mock_rg_name_1/Microsoft.Web/hostingEnvironments/mock_ase_name_1')
        host_env1.name = ase_name_1
        host_env1.kind = 'ASEv2'
        host_env2 = HostingEnvironmentProfile(id='/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/mock_rg_name_2/Microsoft.Web/hostingEnvironments/mock_ase_name_2')
        host_env2.name = ase_name_2
        host_env2.kind = 'ASEv3'
        ase_client.list.return_value = [host_env1, host_env2]

        ase_client.get.return_value = host_env1
        # Assert listvips is called (ASEv2)
        list_appserviceenvironment_addresses(self.mock_cmd, ase_name_1)
        ase_client.get_vip_info.assert_called_with(rg_name_1, ase_name_1)

        ase_client.get.return_value = host_env2
        # Assert get_ase_v3_networking_configuration is called (ASEv3)
        list_appserviceenvironment_addresses(self.mock_cmd, ase_name_2)
        ase_client.get_ase_v3_networking_configuration.assert_called_with(rg_name_2, ase_name_2)

        # Assert list_app_service_plans is called
        list_appserviceenvironment_plans(self.mock_cmd, ase_name_2)
        ase_client.list_app_service_plans.assert_called_with(rg_name_2, ase_name_2)

        # Assert list return two instances
        result = list_appserviceenvironments(self.mock_cmd, None)
        self.assertEqual(len(result), 2)

    @mock.patch('azure.cli.command_modules.appservice.appservice_environment._get_unique_deployment_name', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.appservice_environment._get_resource_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.appservice_environment._get_network_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.appservice_environment._get_ase_client_factory', autospec=True)
    def test_app_service_environment_create(self, ase_client_factory_mock, network_client_factory_mock,
                                            resource_client_factory_mock, deployment_name_mock):
        ase_name = 'mock_ase_name'
        rg_name = 'mock_rg_name'
        vnet_name = 'mock_vnet_name'
        subnet_name = 'mock_subnet_name'
        deployment_name = 'mock_deployment_name'

        ase_client = mock.MagicMock()
        ase_client_factory_mock.return_value = ase_client

        resource_client_mock = mock.MagicMock()
        resource_client_factory_mock.return_value = resource_client_mock

        deployment_name_mock.return_value = deployment_name

        network_client = mock.MagicMock()
        network_client_factory_mock.return_value = network_client

        subnet = Subnet(id=1, address_prefix='10.10.10.10/25')
        network_client.subnets.get.return_value = subnet

        # assert that ValidationError raised when called with small subnet
        with self.assertRaises(ValidationError):
            create_appserviceenvironment_arm(self.mock_cmd, resource_group_name=rg_name, name=ase_name,
                                             subnet=subnet_name, vnet_name=vnet_name,
                                             ignore_network_security_group=True, ignore_route_table=True,
                                             location='westeurope')

        subnet = Subnet(id=1, address_prefix='10.10.10.10/24')
        network_client.subnets.get.return_value = subnet
        create_appserviceenvironment_arm(self.mock_cmd, resource_group_name=rg_name, name=ase_name,
                                         subnet=subnet_name, vnet_name=vnet_name,
                                         ignore_network_security_group=True, ignore_route_table=True,
                                         location='westeurope')

        # Assert begin_create_or_update is called with correct rg and deployment name
        resource_client_mock.deployments.begin_create_or_update.assert_called_once()
        call_args = resource_client_mock.deployments.begin_create_or_update.call_args
        self.assertEqual(call_args[0][0], rg_name)
        self.assertEqual(call_args[0][1], deployment_name)

    @mock.patch('azure.cli.command_modules.appservice.appservice_environment._get_location_from_resource_group', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.appservice_environment._get_ase_client_factory', autospec=True)
    def test_app_service_environment_update(self, ase_client_factory_mock, resource_group_mock):
        ase_name = 'mock_ase_name'
        rg_name = 'mock_rg_name'

        ase_client = mock.MagicMock()
        ase_client_factory_mock.return_value = ase_client

        resource_group_mock.return_value = rg_name

        host_env = HostingEnvironmentProfile(id='/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/mock_rg_name/Microsoft.Web/hostingEnvironments/mock_ase_name')
        host_env.name = ase_name
        host_env.kind = 'ASEv2'
        ase_client.get.return_value = host_env
        ase_client.list.return_value = [host_env]

        update_appserviceenvironment(self.mock_cmd, ase_name, front_end_scale_factor=10)

        # Assert create_or_update is called with correct properties
        assert_host_env = HostingEnvironmentProfile(id='/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/mock_rg_name/Microsoft.Web/hostingEnvironments/mock_ase_name')
        assert_host_env.name = ase_name
        assert_host_env.kind = 'ASEv2'
        assert_host_env.internal_load_balancing_mode = None
        assert_host_env.front_end_scale_factor = 10
        ase_client.begin_create_or_update.assert_called_once_with(resource_group_name=rg_name, name=ase_name,
                                                                  hosting_environment_envelope=assert_host_env)

    @mock.patch('azure.cli.command_modules.appservice.appservice_environment._get_location_from_resource_group', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.appservice_environment._get_ase_client_factory', autospec=True)
    def test_app_service_environment_update_asev3(self, ase_client_factory_mock, resource_group_mock):
        ase_name = 'mock_ase_name'
        rg_name = 'mock_rg_name'

        ase_client = mock.MagicMock()
        ase_client_factory_mock.return_value = ase_client

        resource_group_mock.return_value = rg_name

        host_env = HostingEnvironmentProfile(id='/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/mock_rg_name/Microsoft.Web/hostingEnvironments/mock_ase_name')
        host_env.name = ase_name
        host_env.kind = 'ASEv3'
        ase_client.get.return_value = host_env
        ase_client.list.return_value = [host_env]
        ase_networking_conf = AseV3NetworkingConfiguration(allow_new_private_endpoint_connections=False)
        ase_client.get_ase_v3_networking_configuration.return_value = ase_networking_conf

        update_appserviceenvironment(self.mock_cmd, ase_name, allow_new_private_endpoint_connections=True)

        # Assert create_or_update is called with correct properties
        ase_client.update_ase_networking_configuration.assert_called_once_with(resource_group_name=rg_name,
                                                                               name=ase_name,
                                                                               ase_networking_configuration=ase_networking_conf)

    @mock.patch('azure.cli.command_modules.appservice.appservice_environment._get_location_from_resource_group', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.appservice_environment._get_ase_client_factory', autospec=True)
    def test_app_service_environment_delete(self, ase_client_factory_mock, resource_group_mock):
        ase_name = 'mock_ase_name'
        rg_name = 'mock_rg_name'

        ase_client = mock.MagicMock()
        ase_client_factory_mock.return_value = ase_client

        resource_group_mock.return_value = rg_name

        host_env = HostingEnvironmentProfile(id='/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/mock_rg_name/Microsoft.Web/hostingEnvironments/mock_ase_name')
        host_env.name = ase_name
        host_env.worker_pools = []
        ase_client.get.return_value = host_env
        ase_client.list.return_value = [host_env]

        delete_appserviceenvironment(self.mock_cmd, ase_name)

        # Assert delete is called with correct properties
        assert_host_env = HostingEnvironmentProfile(id='/subscriptions/11111111-1111-1111-1111-111111111111/resourceGroups/mock_rg_name/Microsoft.Web/hostingEnvironments/mock_ase_name')
        assert_host_env.name = ase_name
        ase_client.begin_delete.assert_called_once_with(name=ase_name, resource_group_name=rg_name)

    @mock.patch('azure.cli.command_modules.appservice.appservice_environment._get_unique_deployment_name', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.appservice_environment._get_resource_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.appservice_environment._get_network_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.appservice_environment._get_ase_client_factory', autospec=True)
    def test_app_service_environment_v3_create(self, ase_client_factory_mock, network_client_factory_mock,
                                               resource_client_factory_mock, deployment_name_mock):
        ase_name = 'mock_ase_name'
        rg_name = 'mock_rg_name'
        vnet_name = 'mock_vnet_name'
        subnet_name = 'mock_subnet_name'
        deployment_name = 'mock_deployment_name'

        ase_client = mock.MagicMock()
        ase_client_factory_mock.return_value = ase_client

        resource_client_mock = mock.MagicMock()
        resource_client_factory_mock.return_value = resource_client_mock

        deployment_name_mock.return_value = deployment_name

        network_client = mock.MagicMock()
        network_client_factory_mock.return_value = network_client

        subnet = Subnet(id=1, address_prefix='10.10.10.10/24')
        hosting_delegation = Delegation(id=1, service_name='Microsoft.Web/hostingEnvironments')
        subnet.delegations = [hosting_delegation]
        network_client.subnets.get.return_value = subnet
        create_appserviceenvironment_arm(self.mock_cmd, resource_group_name=rg_name, name=ase_name,
                                         subnet=subnet_name, vnet_name=vnet_name, kind='ASEv3',
                                         location='westeurope')

        # Assert begin_create_or_update is called with correct rg and deployment name
        resource_client_mock.deployments.begin_create_or_update.assert_called_once()
        call_args = resource_client_mock.deployments.begin_create_or_update.call_args
        self.assertEqual(call_args[0][0], rg_name)
        self.assertEqual(call_args[0][1], deployment_name)

    @mock.patch('azure.cli.command_modules.appservice.appservice_environment._get_unique_deployment_name', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.appservice_environment._get_resource_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.appservice_environment._get_network_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.appservice.appservice_environment._get_ase_client_factory', autospec=True)
    def test_app_service_environment_v3_zone_create(self, ase_client_factory_mock, network_client_factory_mock,
                                               resource_client_factory_mock, deployment_name_mock):
        ase_name = 'mock_ase_name'
        rg_name = 'mock_rg_name'
        vnet_name = 'mock_vnet_name'
        subnet_name = 'mock_subnet_name'
        deployment_name = 'mock_deployment_name'

        ase_client = mock.MagicMock()
        ase_client_factory_mock.return_value = ase_client

        resource_client_mock = mock.MagicMock()
        resource_client_factory_mock.return_value = resource_client_mock

        deployment_name_mock.return_value = deployment_name

        network_client = mock.MagicMock()
        network_client_factory_mock.return_value = network_client

        subnet = Subnet(id=1, address_prefix='10.10.10.10/24')
        hosting_delegation = Delegation(id=1, service_name='Microsoft.Web/hostingEnvironments')
        subnet.delegations = [hosting_delegation]
        network_client.subnets.get.return_value = subnet
        create_appserviceenvironment_arm(self.mock_cmd, resource_group_name=rg_name, name=ase_name,
                                         subnet=subnet_name, vnet_name=vnet_name, kind='ASEv3',
                                         location='westeurope', zone_redundant=True)

        # Assert begin_create_or_update is called with correct rg and deployment name
        resource_client_mock.deployments.begin_create_or_update.assert_called_once()
        call_args = resource_client_mock.deployments.begin_create_or_update.call_args
        self.assertEqual(call_args[0][0], rg_name)
        self.assertEqual(call_args[0][1], deployment_name)


if __name__ == '__main__':
    unittest.main()
