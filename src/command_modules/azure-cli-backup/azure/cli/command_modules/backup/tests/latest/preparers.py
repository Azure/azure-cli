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
        from azure.cli.core.mock import DummyCli
        self.cli_ctx = DummyCli()
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

            execute(self.cli_ctx, cmd)
            return {self.parameter_name: name}
        return {self.parameter_name: self.dev_setting_value}

    def remove_resource(self, name, **kwargs):
        self._cleanup(name, self.resource_group)

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

    def _cleanup(self, vault_name, resource_group):
        containers = execute(self.cli_ctx, 'az backup container list -v {} -g {} --query [].properties.friendlyName'
                             .format(vault_name, resource_group)).get_output_in_json()
        for container in containers:
            items = execute(self.cli_ctx, 'az backup item list -g {} -v {} -c {} --query [].properties.friendlyName'
                            .format(resource_group, vault_name, container)).get_output_in_json()
            for item in items:
                execute(self.cli_ctx,
                        'az backup protection disable -g {} -v {} -c {} -i {} --delete-backup-data true --yes'
                        .format(resource_group, vault_name, container, item))
        execute(self.cli_ctx, 'az backup vault delete -n {} -g {} --yes'.format(vault_name, resource_group))


class VMPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest-vm', parameter_name='vm_name',
                 resource_group_location_parameter_name='resource_group_location',
                 resource_group_parameter_name='resource_group', dev_setting_name='AZURE_CLI_TEST_DEV_BACKUP_VM_NAME'):
        super(VMPreparer, self).__init__(name_prefix, 15)
        from azure.cli.core.mock import DummyCli
        self.cli_ctx = DummyCli()
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
            param_format = '-n {} -g {} --image {} --admin-username {} --admin-password {}'
            param_string = param_format.format(name, self.resource_group, 'Win2012R2Datacenter', name,
                                               '%j^VYw9Q3Z@Cu$*h')
            cmd = 'az vm create {}'.format(param_string)
            execute(self.cli_ctx, cmd.format(name, self.resource_group, name))
            return {self.parameter_name: name}
        return {self.parameter_name: self.dev_setting_value}

    def remove_resource(self, name, **kwargs):
        # Resource group deletion will take care of this.
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
        super(ItemPreparer, self).__init__(name_prefix, 24)
        from azure.cli.core.mock import DummyCli
        self.cli_ctx = DummyCli()
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

            params_format = '-g {} -v {} --vm {} -p DefaultPolicy'
            param_string = params_format.format(self.resource_group, vault, vm)
            execute(self.cli_ctx, 'az backup protection enable-for-vm {}'.format(param_string))
            return {self.parameter_name: name}
        return {self.parameter_name: self.dev_setting_value}

    def remove_resource(self, name, **kwargs):
        # Vault deletion will take care of this.
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
        super(PolicyPreparer, self).__init__(name_prefix, 24)
        from azure.cli.core.mock import DummyCli
        self.cli_ctx = DummyCli()
        self.parameter_name = parameter_name
        self.resource_group = None
        self.resource_group_parameter_name = resource_group_parameter_name
        self.vault = None
        self.vault_parameter_name = vault_parameter_name
        self.dev_setting_value = os.environ.get(dev_setting_name, None)

    def create_resource(self, name, **kwargs):
        if not self.dev_setting_value:
            self.resource_group = self._get_resource_group(**kwargs)
            self.vault = self._get_vault(**kwargs)

            policy_json = execute(self.cli_ctx, 'az backup policy show -g {} -v {} -n {}'
                                  .format(self.resource_group, self.vault, 'DefaultPolicy')).get_output_in_json()
            policy_json['name'] = name
            policy_json = json.dumps(policy_json)

            execute(self.cli_ctx, 'az backup policy set -g {} -v {} --policy \'{}\''.format(self.resource_group,
                                                                                            self.vault,
                                                                                            policy_json))
            return {self.parameter_name: name}
        return {self.parameter_name: self.dev_setting_value}

    def remove_resource(self, name, **kwargs):
        # Vault deletion will take care of this.
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
        super(RPPreparer, self).__init__(name_prefix, 24)
        from azure.cli.core.mock import DummyCli
        self.cli_ctx = DummyCli()
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

            retain_date = datetime.utcnow() + timedelta(days=30)
            command_string = 'az backup protection backup-now -g {} -v {} -c {} -i {} --retain-until {} --query name'
            command_string = command_string.format(self.resource_group, vault, vm, vm,
                                                   retain_date.strftime('%d-%m-%Y'))
            backup_job = execute(self.cli_ctx, command_string).get_output_in_json()
            execute(self.cli_ctx, 'az backup job wait -g {} -v {} -n {}'.format(self.resource_group, vault, backup_job))
            return {self.parameter_name: name}
        return {self.parameter_name: self.dev_setting_value}

    def remove_resource(self, name, **kwargs):
        # Vault deletion will take care of this.
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
