# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
from datetime import datetime, timedelta

from azure.cli.testsdk import CliTestError, ResourceGroupPreparer
from azure.cli.testsdk.preparers import AbstractPreparer, SingleValueReplacer
from azure.cli.testsdk.base import execute

class VaultPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest-vault', parameter_name='vault_name',
                 resource_group_location_parameter_name='resource_group_location',
                 resource_group_parameter_name='resource_group',
                 dev_setting_name='AZURE_CLI_TEST_DEV_BACKUP_ACCT_NAME'):
        super(VaultPreparer, self).__init__(name_prefix, 24)
        self.parameter_name = parameter_name
        self.resource_group = None
        self.resource_group_parameter_name = resource_group_parameter_name
        self.location = None
        self.resource_group_location_parameter_name = resource_group_location_parameter_name
        self.dev_setting_value = os.environ.get(dev_setting_name, None)

    def create_resource(self, name, **kwargs):
        if not self.dev_setting_value:
            self.resource_group = self._get_resource_group(**kwargs)
            self.location = self._get_resource_group_location(**kwargs)
            cmd = 'az backup vault create -n {} -g {} --location {}'.format(name, self.resource_group, self.location)

            execute(cmd)
            return {self.parameter_name: name}
        return {self.parameter_name: self.dev_setting_value}

    def remove_resource(self, name, **kwargs):
        #TODO: Preparer deletion order should be reversed - https://github.com/Azure/azure-python-devtools/issues/29
        pass

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create a vault, a resource group is required. Please add ' \
                       'decorator @{} in front of this Vault preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))

    def _get_resource_group_location(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_location_parameter_name)
        except KeyError:
            template = 'To create a vault, a resource group is required. Please add ' \
                       'decorator @{} in front of this Vault preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))

class VMPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest-vm', parameter_name='vm_name',
                 resource_group_location_parameter_name='resource_group_location',
                 resource_group_parameter_name='resource_group', dev_setting_name='AZURE_CLI_TEST_DEV_BACKUP_VM_NAME'):
        super(VMPreparer, self).__init__(name_prefix, 15)
        self.parameter_name = parameter_name
        self.resource_group = None
        self.resource_group_parameter_name = resource_group_parameter_name
        self.location = None
        self.resource_group_location_parameter_name = resource_group_location_parameter_name
        self.dev_setting_value = os.environ.get(dev_setting_name, None)

    def create_resource(self, name, **kwargs):
        if not self.dev_setting_value:
            self.resource_group = self._get_resource_group(**kwargs)
            self.location = self._get_resource_group_location(**kwargs)
            cmd = 'az vm create -n {} -g {} --image Win2012R2Datacenter --admin-password %j^VYw9Q3Z@Cu$*h'
            execute(cmd.format(name, self.resource_group))
            return {self.parameter_name: name}
        return {self.parameter_name: self.dev_setting_value}

    def remove_resource(self, name, **kwargs):
        #TODO: Preparer deletion order should be reversed - https://github.com/Azure/azure-python-devtools/issues/29
        pass

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create a vm, a resource group is required. Please add ' \
                       'decorator @{} in front of this VM preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))

    def _get_resource_group_location(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_location_parameter_name)
        except KeyError:
            template = 'To create a vm, a resource group is required. Please add ' \
                       'decorator @{} in front of this VM preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))

class ItemPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest-item', parameter_name='item_name', vm_parameter_name='vm_name',
                 vault_parameter_name='vault_name',
                 resource_group_parameter_name='resource_group',
                 dev_setting_name='AZURE_CLI_TEST_DEV_BACKUP_ITEM_NAME'):
        super().__init__(name_prefix, 24)
        self.parameter_name = parameter_name
        self.vm_parameter_name = vm_parameter_name
        self.resource_group = None
        self.resource_group_parameter_name = resource_group_parameter_name
        self.vault_parameter_name = vault_parameter_name
        self.dev_setting_value = os.environ.get(dev_setting_name, None)

    def create_resource(self, name, **kwargs):
        if not self.dev_setting_value:
            self.resource_group = self._get_resource_group(**kwargs)
            vault = self._get_vault(**kwargs)
            vm = self._get_vm(**kwargs)

            vault_json = json.dumps(execute('az backup vault show -n {} -g {}'
                                            .format(vault, self.resource_group)).get_output_in_json())
            policy_json = json.dumps(execute('az backup policy show --policy-name {} --vault \'{}\''
                                             .format('DefaultPolicy', vault_json)).get_output_in_json())
            vm_json = json.dumps(execute('az vm show -n {} -g {}'
                                         .format(vm, self.resource_group)).get_output_in_json())
            enable_protection_job_json = json.dumps(
                execute('az backup protection enable-for-vm --policy \'{}\' --vault \'{}\' --vm \'{}\''
                        .format(policy_json, vault_json, vm_json)).get_output_in_json())
            execute('az backup job wait --job \'{}\''.format(enable_protection_job_json))
            return {self.parameter_name: name}
        return {self.parameter_name: self.dev_setting_value}

    def remove_resource(self, name, **kwargs):
        #TODO: Preparer deletion order should be reversed - https://github.com/Azure/azure-python-devtools/issues/29
        pass

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create an item, a resource group is required. Please add ' \
                       'decorator @{} in front of this Item preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))

    def _get_vault(self, **kwargs):
        try:
            return kwargs.get(self.vault_parameter_name)
        except KeyError:
            template = 'To create an item, a vault is required. Please add ' \
                       'decorator @{} in front of this Item preparer.'
            raise CliTestError(template.format(VaultPreparer.__name__,
                                               self.vault_parameter_name))

    def _get_vm(self, **kwargs):
        try:
            return kwargs.get(self.vm_parameter_name)
        except KeyError:
            template = 'To create an item, a vm is required. Please add ' \
                       'decorator @{} in front of this Item preparer.'
            raise CliTestError(template.format(VMPreparer.__name__,
                                               self.vm_parameter_name))

class PolicyPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest-item', parameter_name='policy_name', vault_parameter_name='vault_name',
                 resource_group_parameter_name='resource_group',
                 dev_setting_name='AZURE_CLI_TEST_DEV_BACKUP_POLICY_NAME'):
        super().__init__(name_prefix, 24)
        self.parameter_name = parameter_name
        self.resource_group = None
        self.resource_group_parameter_name = resource_group_parameter_name
        self.vault = None
        self.vault_json = None
        self.vault_parameter_name = vault_parameter_name
        self.dev_setting_value = os.environ.get(dev_setting_name, None)

    def create_resource(self, name, **kwargs):
        if not self.dev_setting_value:
            self.resource_group = self._get_resource_group(**kwargs)
            self.vault = self._get_vault(**kwargs)

            self.vault_json = json.dumps(execute('az backup vault show -n {} -g {}'
                                                 .format(self.vault, self.resource_group)).get_output_in_json())
            policy_json = execute('az backup policy show --policy-name {} --vault \'{}\''
                                  .format('DefaultPolicy', self.vault_json)).get_output_in_json()
            policy_json['name'] = name
            policy_json = json.dumps(policy_json)

            execute('az backup policy update --policy \'{}\''.format(policy_json))
            return {self.parameter_name: name}
        return {self.parameter_name: self.dev_setting_value}

    def remove_resource(self, name, **kwargs):
        #TODO: Preparer deletion order should be reversed - https://github.com/Azure/azure-python-devtools/issues/29
        pass

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create an item, a resource group is required. Please add ' \
                       'decorator @{} in front of this Policy preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))

    def _get_vault(self, **kwargs):
        try:
            return kwargs.get(self.vault_parameter_name)
        except KeyError:
            template = 'To create an item, a vault is required. Please add ' \
                       'decorator @{} in front of this Policy preparer.'
            raise CliTestError(template.format(VaultPreparer.__name__,
                                               self.vault_parameter_name))

class RPPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest-rp', parameter_name='rp_name', vm_parameter_name='vm_name',
                 vault_parameter_name='vault_name',
                 resource_group_parameter_name='resource_group', dev_setting_name='AZURE_CLI_TEST_DEV_BACKUP_RP_NAME'):
        super().__init__(name_prefix, 24)
        self.parameter_name = parameter_name
        self.vm_parameter_name = vm_parameter_name
        self.resource_group = None
        self.resource_group_parameter_name = resource_group_parameter_name
        self.vault_parameter_name = vault_parameter_name
        self.dev_setting_value = os.environ.get(dev_setting_name, None)

    def create_resource(self, name, **kwargs):
        if not self.dev_setting_value:
            self.resource_group = self._get_resource_group(**kwargs)
            vault = self._get_vault(**kwargs)
            vm = self._get_vm(**kwargs)

            vault_json = json.dumps(execute('az backup vault show -n {} -g {}'
                                            .format(vault, self.resource_group)).get_output_in_json())
            container_json = json.dumps(execute('az backup container show --container-name \'{}\' --vault \'{}\''
                                                .format(vm, vault_json)).get_output_in_json())
            item_json = json.dumps(execute('az backup item show --item-name \'{}\' --container \'{}\''
                                           .format(vm, container_json)).get_output_in_json())
            retain_date = datetime.utcnow() + timedelta(days=30)
            backup_job_json = json.dumps(execute(
                'az backup protection backup-now --backup-item \'{}\' --retain-until {}'
                .format(item_json, retain_date.strftime('%d-%m-%Y'))).get_output_in_json())
            execute('az backup job wait --job \'{}\''.format(backup_job_json))
            return {self.parameter_name: name}
        return {self.parameter_name: self.dev_setting_value}

    def remove_resource(self, name, **kwargs):
        pass

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create an item, a resource group is required. Please add ' \
                       'decorator @{} in front of this RP preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))

    def _get_vault(self, **kwargs):
        try:
            return kwargs.get(self.vault_parameter_name)
        except KeyError:
            template = 'To create an item, a vault is required. Please add ' \
                       'decorator @{} in front of this RP preparer.'
            raise CliTestError(template.format(VaultPreparer.__name__,
                                               self.vault_parameter_name))

    def _get_vm(self, **kwargs):
        try:
            return kwargs.get(self.vm_parameter_name)
        except KeyError:
            template = 'To create an rp, a VM is required. Please add ' \
                       'decorator @{} in front of this RP preparer.'
            raise CliTestError(template.format(ItemPreparer.__name__, self.vm_parameter_name))
