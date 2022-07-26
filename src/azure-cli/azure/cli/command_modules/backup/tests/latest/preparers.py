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
# pylint: disable=line-too-long


class VaultPreparer(AbstractPreparer, SingleValueReplacer):  # pylint: disable=too-many-instance-attributes
    def __init__(self, name_prefix='clitest-vault', parameter_name='vault_name',
                 resource_group_location_parameter_name='resource_group_location',
                 resource_group_parameter_name='resource_group',
                 dev_setting_name='AZURE_CLI_TEST_DEV_BACKUP_ACCT_NAME', soft_delete=True):
        super(VaultPreparer, self).__init__(name_prefix, 24)
        from azure.cli.core.mock import DummyCli
        self.cli_ctx = DummyCli()
        self.parameter_name = parameter_name
        self.resource_group = None
        self.resource_group_parameter_name = resource_group_parameter_name
        self.location = None
        self.resource_group_location_parameter_name = resource_group_location_parameter_name
        self.dev_setting_value = os.environ.get(dev_setting_name, None)
        self.soft_delete = soft_delete

    def create_resource(self, name, **kwargs):
        if not self.dev_setting_value:
            self.resource_group = self._get_resource_group(**kwargs)
            self.location = self._get_resource_group_location(**kwargs)
            cmd = 'az backup vault create -n {} -g {} --location {}'.format(name, self.resource_group, self.location)
            execute(self.cli_ctx, cmd)
            if not self.soft_delete:
                cmd = 'az backup vault backup-properties set -n {} -g {} --soft-delete-feature-state Disable'.format(name, self.resource_group)
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
        containers = execute(self.cli_ctx, 'az backup container list --backup-management-type AzureIaasVM -v {} -g {} --query [].properties.friendlyName'
                             .format(vault_name, resource_group)).get_output_in_json()
        for container in containers:
            items = execute(self.cli_ctx, 'az backup item list --backup-management-type AzureIaasVM --workload-type VM -g {} -v {} -c {} --query [].properties.friendlyName'
                            .format(resource_group, vault_name, container)).get_output_in_json()
            for item in items:
                execute(self.cli_ctx,
                        'az backup protection disable --backup-management-type AzureIaasVM --workload-type VM -g {} -v {} -c {} -i {} --delete-backup-data true --yes'
                        .format(resource_group, vault_name, container, item))
        from azure.core.exceptions import HttpResponseError
        try:
            execute(self.cli_ctx, 'az backup vault delete -n {} -g {} --yes'.format(vault_name, resource_group))
        except HttpResponseError as ex:
            if "Operation returned an invalid status 'Bad Request'" not in str(ex):
                raise ex


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
            param_format = '-n {} -g {} --image {} --admin-username {} --admin-password {} --tags {} --nsg-rule None'
            param_tags = 'MabUsed=Yes Owner=sisi Purpose=CLITest DeleteBy=12-2099 AutoShutdown=No'
            param_string = param_format.format(name, self.resource_group, 'Win2012R2Datacenter', name,
                                               '%j^VYw9Q3Z@Cu$*h', param_tags)
            cmd = 'az vm create {}'.format(param_string)
            execute(self.cli_ctx, cmd)
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
                 instant_rp_days=None):
        super(PolicyPreparer, self).__init__(name_prefix, 24)
        from azure.cli.core.mock import DummyCli
        self.cli_ctx = DummyCli()
        self.parameter_name = parameter_name
        self.resource_group = None
        self.resource_group_parameter_name = resource_group_parameter_name
        self.vault = None
        self.vault_parameter_name = vault_parameter_name
        self.instant_rp_days = instant_rp_days

    def create_resource(self, name, **kwargs):
        if not os.environ.get('AZURE_CLI_TEST_DEV_BACKUP_POLICY_NAME', None):
            self.resource_group = self._get_resource_group(**kwargs)
            self.vault = self._get_vault(**kwargs)

            policy_json = execute(self.cli_ctx, 'az backup policy show -g {} -v {} -n {}'
                                  .format(self.resource_group, self.vault, 'DefaultPolicy')).get_output_in_json()
            policy_json['name'] = name
            if self.instant_rp_days:
                policy_json['properties']['instantRpRetentionRangeInDays'] = self.instant_rp_days
            policy_json = json.dumps(policy_json)

            execute(self.cli_ctx, 'az backup policy set -g {} -v {} --policy \'{}\''.format(self.resource_group,
                                                                                            self.vault,
                                                                                            policy_json))
            return {self.parameter_name: name}
        return {self.parameter_name: os.environ.get('AZURE_CLI_TEST_DEV_BACKUP_POLICY_NAME', None)}

    def remove_resource(self, name, **kwargs):
        # Vault deletion will take care of this.
        pass

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create a Policy, a resource group is required. Please add ' \
                       'decorator @{} in front of this Policy preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))

    def _get_vault(self, **kwargs):
        try:
            return kwargs.get(self.vault_parameter_name)
        except KeyError:
            template = 'To create a Policy, a vault is required. Please add ' \
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
            command_string = 'az backup protection backup-now --backup-management-type AzureIaasVM --workload-type VM -g {} -v {} -c {} -i {} --retain-until {} --query name'
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
            template = 'To create an RP, a resource group is required. Please add ' \
                       'decorator @{} in front of this RP preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))

    def _get_vault(self, **kwargs):
        try:
            return kwargs.get(self.vault_parameter_name)
        except KeyError:
            template = 'To create an RP, a vault is required. Please add ' \
                       'decorator @{} in front of this RP preparer.'
            raise CliTestError(template.format(VaultPreparer.__name__,
                                               self.vault_parameter_name))

    def _get_vm(self, **kwargs):
        try:
            return kwargs.get(self.vm_parameter_name)
        except KeyError:
            template = 'To create an RP, a VM is required. Please add ' \
                       'decorator @{} in front of this RP preparer.'
            raise CliTestError(template.format(ItemPreparer.__name__, self.vm_parameter_name))


class AFSPolicyPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest-item', parameter_name='policy_name', vault_parameter_name='vault_name',
                 resource_group_parameter_name='resource_group',
                 instant_rp_days=None):
        super(AFSPolicyPreparer, self).__init__(name_prefix, 24)
        from azure.cli.core.mock import DummyCli
        self.cli_ctx = DummyCli()
        self.parameter_name = parameter_name
        self.resource_group = None
        self.resource_group_parameter_name = resource_group_parameter_name
        self.vault = None
        self.vault_parameter_name = vault_parameter_name
        self.instant_rp_days = instant_rp_days

    def create_resource(self, name, **kwargs):
        if not os.environ.get('AZURE_CLI_TEST_DEV_BACKUP_POLICY_NAME', None):
            self.resource_group = self._get_resource_group(**kwargs)
            self.vault = self._get_vault(**kwargs)

            policy_json = execute(self.cli_ctx, 'az backup policy show -g {} -v {} -n {}'
                                  .format(self.resource_group, self.vault, 'DefaultPolicy')).get_output_in_json()
            policy_json['name'] = name
            if self.instant_rp_days:
                policy_json['properties']['instantRpRetentionRangeInDays'] = self.instant_rp_days
            policy_json['properties']['backupManagementType'] = "AzureStorage"
            policy_json = json.dumps(policy_json)

            command_string = 'az backup policy create -g {} -v {} --policy \'{}\' -n {} --backup-management-type {}'
            command_string = command_string.format(self.resource_group, self.vault, policy_json, name, "AzureStorage")
            execute(self.cli_ctx, command_string)
            return {self.parameter_name: name}
        return {self.parameter_name: os.environ.get('AZURE_CLI_TEST_DEV_BACKUP_POLICY_NAME', None)}

    def remove_resource(self, name, **kwargs):
        # Vault deletion will take care of this.
        pass

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create a Policy, a resource group is required. Please add ' \
                       'decorator @{} in front of this Policy preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))

    def _get_vault(self, **kwargs):
        try:
            return kwargs.get(self.vault_parameter_name)
        except KeyError:
            template = 'To create a Policy, a vault is required. Please add ' \
                       'decorator @{} in front of this Policy preparer.'
            raise CliTestError(template.format(VaultPreparer.__name__,
                                               self.vault_parameter_name))


class FileSharePreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest-item', storage_account_parameter_name='storage_account',
                 resource_group_parameter_name='resource_group', file_parameter_name=None,
                 parameter_name='afs_name', file_upload=False):
        super(FileSharePreparer, self).__init__(name_prefix, 24)
        from azure.cli.core.mock import DummyCli
        self.cli_ctx = DummyCli()
        self.parameter_name = parameter_name
        self.resource_group = None
        self.resource_group_parameter_name = resource_group_parameter_name
        self.storage_account_parameter_name = storage_account_parameter_name
        self.file_parameter_name = file_parameter_name
        self.file_upload = file_upload

    def create_resource(self, name, **kwargs):
        if not os.environ.get('AZURE_CLI_TEST_DEV_BACKUP_POLICY_NAME', None):
            self.resource_group = self._get_resource_group(**kwargs)
            storage_account = self._get_storage_account(**kwargs)

            storage_keys_command = 'az storage account keys list --resource-group {} --account-name {} --query [0].value'
            storage_keys_command = storage_keys_command.format(self.resource_group, storage_account)
            if self.file_upload:
                storage_key = execute(self.cli_ctx, storage_keys_command).get_output_in_json()
            connection_string_command = 'az storage account show-connection-string -n {} -g {}'
            connection_string_command = connection_string_command.format(storage_account, self.resource_group)
            connection_string = execute(self.cli_ctx, connection_string_command).get_output_in_json()
            connection_string = connection_string['connectionString']
            command_string = 'az storage share create --name {} --quota 1 --connection-string {}'
            command_string = command_string.format(name, connection_string)
            execute(self.cli_ctx, command_string)
            file_upload_command_format = 'az storage file upload --account-name {} --account-key {} --share-name {} --source {}'
            if self.file_upload:
                file_param_names = self.file_parameter_name
                for file_param_name in file_param_names:
                    self.file_parameter_name = file_param_name
                    file = self._get_file(**kwargs)
                    file_upload_command = file_upload_command_format.format(storage_account, storage_key, name, file)
                    execute(self.cli_ctx, file_upload_command)
            return {self.parameter_name: name}
        return {self.parameter_name: os.environ.get('AZURE_CLI_TEST_DEV_BACKUP_POLICY_NAME', None)}

    def remove_resource(self, name, **kwargs):
        # Vault deletion will take care of this.
        pass

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create a Fileshare, a resource group is required. Please add ' \
                       'decorator @{} in front of this Fileshare preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))

    def _get_file(self, **kwargs):
        try:
            return kwargs.get(self.file_parameter_name)
        except KeyError:
            raise CliTestError("File not Found")

    def _get_storage_account(self, **kwargs):
        try:
            return kwargs.get(self.storage_account_parameter_name)
        except KeyError:
            template = 'To create a Fileshare, a storage_account is required. Please add ' \
                       'decorator @StorageAccountPreparer in front of this Fileshare preparer.'
            raise CliTestError(template)


class AFSItemPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest-item', storage_account_parameter_name='storage_account',
                 resource_group_parameter_name='resource_group', vault_parameter_name='vault_name',
                 parameter_name='item_name', afs_parameter_name='afs_name',
                 policy_parameter_name='policy_name'):
        super(AFSItemPreparer, self).__init__(name_prefix, 24)
        from azure.cli.core.mock import DummyCli
        self.cli_ctx = DummyCli()
        self.parameter_name = parameter_name
        self.resource_group_parameter_name = resource_group_parameter_name
        self.storage_account_parameter_name = storage_account_parameter_name
        self.vault_parameter_name = vault_parameter_name
        self.afs_parameter_name = afs_parameter_name
        self.policy_parameter_name = policy_parameter_name

    def create_resource(self, name, **kwargs):
        if not os.environ.get('AZURE_CLI_TEST_DEV_BACKUP_ITEM_NAME', None):
            resource_group = self._get_resource_group(**kwargs)
            storage_account = self._get_storage_account(**kwargs)
            vault = self._get_vault(**kwargs)
            afs = self._get_file_share(**kwargs)
            policy = self._get_policy(**kwargs)

            command_string = 'az backup protection enable-for-azurefileshare'
            command_string += ' -g {} -v {} --azure-file-share {} --storage-account {} -p {}'
            command_string = command_string.format(resource_group, vault, afs, storage_account, policy)
            execute(self.cli_ctx, command_string)
            return {self.parameter_name: name}
        return {self.parameter_name: os.environ.get('AZURE_CLI_TEST_DEV_BACKUP_ITEM_NAME', None)}

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

    def _get_storage_account(self, **kwargs):
        try:
            return kwargs.get(self.storage_account_parameter_name)
        except KeyError:
            template = 'To create an item, a storage_account is required. Please add ' \
                       'decorator @StorageAccountPreparer in front of this Item preparer.'
            raise CliTestError(template)

    def _get_file_share(self, **kwargs):
        try:
            return kwargs.get(self.afs_parameter_name)
        except KeyError:
            template = 'To create an item, a fileshare is required. Please add ' \
                       'decorator @FileSharePreparer in front of this Item preparer.'
            raise CliTestError(template)

    def _get_policy(self, **kwargs):
        try:
            return kwargs.get(self.policy_parameter_name)
        except KeyError:
            template = 'To create an item, a policy is required. Please add ' \
                       'decorator @AFSPolicyPreparer in front of this Item preparer.'
            raise CliTestError(template)


class AFSRPPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest-item', storage_account_parameter_name='storage_account',
                 resource_group_parameter_name='resource_group', vault_parameter_name='vault_name',
                 parameter_name='rp_name', afs_parameter_name='afs_name'):
        super(AFSRPPreparer, self).__init__(name_prefix, 24)
        from azure.cli.core.mock import DummyCli
        self.cli_ctx = DummyCli()
        self.parameter_name = parameter_name
        self.resource_group = None
        self.resource_group_parameter_name = resource_group_parameter_name
        self.storage_account_parameter_name = storage_account_parameter_name
        self.vault_parameter_name = vault_parameter_name
        self.afs_parameter_name = afs_parameter_name

    def create_resource(self, name, **kwargs):
        if not os.environ.get('AZURE_CLI_TEST_DEV_BACKUP_RP_NAME', None):
            self.resource_group = self._get_resource_group(**kwargs)
            storage_account = self._get_storage_account(**kwargs)
            vault = self._get_vault(**kwargs)
            afs = self._get_file_share(**kwargs)

            retain_date = datetime.utcnow() + timedelta(days=30)
            retain_date = retain_date.strftime('%d-%m-%Y')
            command_string = 'az backup protection backup-now'
            command_string += ' -g {} -v {} -i {} -c {} --backup-management-type AzureStorage --retain-until {} --query name'
            command_string = command_string.format(self.resource_group, vault, afs, storage_account, retain_date)
            backup_job = execute(self.cli_ctx, command_string).get_output_in_json()
            execute(self.cli_ctx, 'az backup job wait -g {} -v {} -n {}'.format(self.resource_group, vault, backup_job))
            return {self.parameter_name: name}
        return {self.parameter_name: os.environ.get('AZURE_CLI_TEST_DEV_BACKUP_RP_NAME', None)}

    def remove_resource(self, name, **kwargs):
        # Vault deletion will take care of this.
        pass

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create an RP, a resource group is required. Please add ' \
                       'decorator @{} in front of this RP preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))

    def _get_vault(self, **kwargs):
        try:
            return kwargs.get(self.vault_parameter_name)
        except KeyError:
            template = 'To create an RP, a vault is required. Please add ' \
                       'decorator @{} in front of this RP preparer.'
            raise CliTestError(template.format(VaultPreparer.__name__,
                                               self.vault_parameter_name))

    def _get_storage_account(self, **kwargs):
        try:
            return kwargs.get(self.storage_account_parameter_name)
        except KeyError:
            template = 'To create an RP, a storage_account is required. Please add ' \
                       'decorator @AFSItemPreparer in front of this RP preparer.'
            raise CliTestError(template)

    def _get_file_share(self, **kwargs):
        try:
            return kwargs.get(self.afs_parameter_name)
        except KeyError:
            template = 'To create an RP, a fileshare is required. Please add ' \
                       'decorator @FileSharePreparer in front of this RP preparer.'
            raise CliTestError(template)


class FilePreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest-file', parameter_name='file_name'):
        super(FilePreparer, self).__init__(name_prefix, 24)
        self.parameter_name = parameter_name

    def create_resource(self, name, **kwargs):
        if not os.environ.get('AZURE_CLI_TEST_DEV_BACKUP_RP_NAME', None):
            f = open(name, "a")
            f.close()
            return {self.parameter_name: name}
        return {self.parameter_name: os.environ.get('AZURE_CLI_TEST_DEV_BACKUP_RP_NAME', None)}

    def remove_resource(self, name, **kwargs):
        os.remove(name)
