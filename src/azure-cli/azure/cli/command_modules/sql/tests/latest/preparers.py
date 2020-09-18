# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
from datetime import datetime, timedelta

from azure.cli.testsdk import CliTestError, ResourceGroupPreparer
from azure.cli.testsdk.preparers import NoTrafficRecordingPreparer, SingleValueReplacer, KEY_RESOURCE_GROUP, KEY_VIRTUAL_NETWORK, get_dummy_cli
from azure.cli.testsdk.base import execute
# pylint: disable=line-too-long

class VNetPreparer(NoTrafficRecordingPreparer, SingleValueReplacer):  # pylint: disable=too-many-instance-attributes
    def __init__(self, name_prefix='clitest.vn',
                 parameter_name='virtual_network',
                 resource_group_parameter_name='resource_group',
                 resource_group_key=KEY_RESOURCE_GROUP,
                 dev_setting_name='AZURE_CLI_TEST_DEV_VIRTUAL_NETWORK_NAME',
                 random_name_length=24, key=KEY_VIRTUAL_NETWORK,
                 route_table_name='vcCliTestRouteTable', route_name_internet='vcCliTestRouteInternet',
                 route_name_vnetlocal='vcCliTestRouteVnetLoc', nsg_name='mynsg',
                 subnet_name='vcCliTestSubnet',
                 subnet_parameter_name='subnet_name',
                 subnet_key='subnet',
                 subnet_dev_setting_name='AZURE_CLI_TEST_DEV_SUBNET_NAME',
                 delegations='Microsoft.Sql/managedInstances',
                 vnet_address_prefix='10.0.0.0/16',
                 subnet_address_prefix='10.0.0.0/24',
                 location='westeurope'):
        if ' ' in name_prefix:
            raise CliTestError(
                'Error: Space character in name prefix \'%s\'' % name_prefix)
        super(VNetPreparer, self).__init__(
            name_prefix, random_name_length)
        self.cli_ctx = get_dummy_cli()
        self.parameter_name = parameter_name
        self.key = key
        self.resource_group_parameter_name = resource_group_parameter_name
        self.resource_group_key = resource_group_key
        self.dev_setting_name = os.environ.get(dev_setting_name, None)
        self.route_table_name = route_table_name
        self.route_name_internet = route_name_internet
        self.route_name_vnetlocal = route_name_vnetlocal
        self.nsg_name = nsg_name
        self.subnet_name = subnet_name
        self.subnet_parameter_name = subnet_parameter_name
        self.subnet_key = subnet_key
        self.subnet_dev_setting_name = os.environ.get(subnet_dev_setting_name, None)
        self.delegations = delegations
        self.vnet_address_prefix = vnet_address_prefix
        self.subnet_address_prefix = subnet_address_prefix
        self.location = location


    def create_resource(self, name, **kwargs):
        result = {}
        if self.dev_setting_name:
            self.test_class_instance.kwargs[self.key] = name
            result[self.parameter_name] = self.dev_setting_name
        if self.subnet_dev_setting_name:
            self.test_class_instance.kwargs[self.subnet_key] = self.subnet_name
            result[self.subnet_parameter_name] = self.subnet_dev_setting_name
        if self.dev_setting_name and self.subnet_dev_setting_name:
            return result

        tags = {'product': 'azurecli', 'cause': 'automation-sql',
                'date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}
        if 'ENV_JOB_NAME' in os.environ:
            tags['job'] = os.environ['ENV_JOB_NAME']
        tags = ' '.join(['{}={}'.format(key, value)
                         for key, value in tags.items()])
        template = 'az network route-table create --resource-group {} --name {}'
        self.live_only_execute(self.cli_ctx, template.format(self._get_resource_group(**kwargs), self.route_table_name))
        template = 'az network route-table route create --resource-group {} --route-table-name {} --name {} --next-hop-type Internet --address-prefix 0.0.0.0/0'
        self.live_only_execute(self.cli_ctx, template.format(self._get_resource_group(**kwargs), self.route_table_name, self.route_name_internet))
        template = 'az network route-table route create --resource-group {} --route-table-name {} -n {} --next-hop-type VnetLocal --address-prefix {}'
        self.live_only_execute(self.cli_ctx, template.format(self._get_resource_group(**kwargs), self.route_table_name, self.route_name_vnetlocal, self.subnet_address_prefix))
        template = 'az network vnet create --resource-group {} --name {} --location {} --address-prefix {} --tag ' + tags
        self.live_only_execute(self.cli_ctx, template.format(self._get_resource_group(**kwargs), name, self.location, self.vnet_address_prefix))
        template = 'az network nsg create --resource-group {} --name {}'
        self.live_only_execute(self.cli_ctx, template.format(self._get_resource_group(**kwargs), self.nsg_name))
        template = 'az network vnet subnet create --resource-group {} --vnet-name {} --name {} --address-prefix {} --route-table {}'
        self.live_only_execute(self.cli_ctx, template.format(self._get_resource_group(**kwargs), name, self.subnet_name, self.subnet_address_prefix, self.route_table_name))
        template = 'az network vnet subnet update --resource-group {} --vnet-name {} --name {} --delegations {} --network-security-group {}'
        self.live_only_execute(self.cli_ctx, template.format(self._get_resource_group(**kwargs), name, self.subnet_name, self.delegations, self.nsg_name))
        self.test_class_instance.kwargs[self.key] = name
        self.test_class_instance.kwargs[self.subnet_key] = self.subnet_name
        return {self.parameter_name: name, self.subnet_parameter_name: self.subnet_name}

    def remove_resource(self, name, **kwargs):
        if not self.dev_setting_name:
            from msrestazure.azure_exceptions import CloudError
            try:
                self.live_only_execute(
                    self.cli_ctx,
                    'az network vnet delete --name {} --resource-group {}'.format(name, self._get_resource_group(**kwargs)))
            except CloudError:
                # deletion of vnet may fail as service could create subresources like IPConfig. We could rely on the deletion of resource group to delete the vnet.
                pass

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create a VirtualNetwork a resource group is required. Please add ' \
                       'decorator @{} in front of this VirtualNetwork preparer.'
            raise CliTestError(template.format(VNetPreparer.__name__))
