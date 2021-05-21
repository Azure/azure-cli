# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime
import os

from azure.cli.testsdk.preparers import ResourceGroupPreparer, VirtualNetworkPreparer, KEY_RESOURCE_GROUP, KEY_VIRTUAL_NETWORK


class AKSCustomResourceGroupPreparer(ResourceGroupPreparer):
    def __init__(
            self,
            name_prefix='clitest.rg',
            parameter_name='resource_group',
            parameter_name_for_location='resource_group_location',
            location='westus',
            dev_setting_name='AZURE_CLI_TEST_DEV_RESOURCE_GROUP_NAME',
            dev_setting_location='AZURE_CLI_TEST_DEV_RESOURCE_GROUP_LOCATION',
            random_name_length=75,
            key='rg'):
        super(AKSCustomResourceGroupPreparer,
              self).__init__(name_prefix, parameter_name,
                             parameter_name_for_location, location,
                             dev_setting_name, dev_setting_location,
                             random_name_length, key)

        # use environment variable to modify the default value of location
        self.dev_setting_location = os.environ.get(dev_setting_location, None)
        if self.dev_setting_location:
            self.location = self.dev_setting_location
        else:
            self.dev_setting_location = location


class AKSCustomVirtualNetworkPreparer(VirtualNetworkPreparer):
    def __init__(
            self,
            name_prefix='clitest.vn',
            location='westus',
            parameter_name='virtual_network',
            resource_group_parameter_name='resource_group',
            resource_group_key=KEY_RESOURCE_GROUP,
            address_prefixes="10.128.0.0/24",
            address_prefixes_parameter_name='address_prefixes',
            dev_setting_name='AZURE_CLI_TEST_DEV_VIRTUAL_NETWORK_NAME',
            dev_setting_location='AZURE_CLI_TEST_DEV_RESOURCE_GROUP_LOCATION',
            random_name_length=24,
            key=KEY_VIRTUAL_NETWORK):
        super(AKSCustomVirtualNetworkPreparer,
              self).__init__(name_prefix, location, parameter_name,
                             resource_group_parameter_name, resource_group_key,
                             dev_setting_name, random_name_length, key)

        # use environment variable to modify the default value of location
        self.dev_setting_location = os.environ.get(dev_setting_location, None)
        if self.dev_setting_location:
            self.location = self.dev_setting_location
        else:
            self.dev_setting_location = location

        # get address_prefixes
        # custom address_prefixes to avoid conflict with aks cluster/service cidr
        self.address_prefixes = address_prefixes
        self.address_prefixes_parameter_name = address_prefixes_parameter_name

    def create_resource(self, name, **kwargs):
        if self.dev_setting_name:
            self.test_class_instance.kwargs[self.key] = name
            return {
                self.parameter_name: self.dev_setting_name,
            }

        tags = {
            'product': 'azurecli',
            'cause': 'automation',
            'date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        if 'ENV_JOB_NAME' in os.environ:
            tags['job'] = os.environ['ENV_JOB_NAME']
        tags = ' '.join(
            ['{}={}'.format(key, value) for key, value in tags.items()])
        template = 'az network vnet create --resource-group {} --location {} --name {} --subnet-name default --address-prefixes {} --tag ' + tags
        self._update_address_prefixes(**kwargs)
        self.live_only_execute(
            self.cli_ctx,
            template.format(self._get_resource_group(**kwargs), self.location,
                            name, self.address_prefixes))

        self.test_class_instance.kwargs[self.key] = name
        return {self.parameter_name: name}

    def remove_resource(self, name, **kwargs):
        if not self.dev_setting_name:
            from msrestazure.azure_exceptions import CloudError
            from azure.core.exceptions import HttpResponseError
            try:
                self.live_only_execute(
                    self.cli_ctx,
                    'az network vnet delete --name {} --resource-group {}'.
                    format(name, self._get_resource_group(**kwargs)))
            except CloudError:
                # deprecated since the SDK that network commands relies on has been migrated to track 2
                # deletion of vnet may fail as service could create subresources like IPConfig. We could rely on the deletion of resource group to delete the vnet.
                pass
            except HttpResponseError as ex:
                # new excetption class adopted by track 2 SDK
                # network resources are still used by other resources such as vm, and there is no clean way to delete these dependencies, rely on delete rg.
                if "(InUseSubnetCannotBeDeleted)" in ex.message:
                    pass
                else:
                    raise ex

    def _update_address_prefixes(self, **kwargs):
        if self.address_prefixes_parameter_name in kwargs:
            self.address_prefixes = kwargs.get(
                self.address_prefixes_parameter_name)
