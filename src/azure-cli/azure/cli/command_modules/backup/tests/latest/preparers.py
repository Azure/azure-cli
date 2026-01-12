# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
from datetime import datetime, timedelta

from azure.cli.testsdk import CliTestError, ResourceGroupPreparer
from azure.cli.testsdk.preparers import AbstractPreparer, SingleValueReplacer, KeyVaultPreparer
from azure.cli.testsdk.base import execute
# pylint: disable=line-too-long

from knack.log import get_logger
logger = get_logger(__name__)


# Temporary Resource Group Preparer for testing while we update the RecoveryServices SDK to deal with new Soft Delete rules
class RGPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest.rg',
                 parameter_name='resource_group',
                 parameter_name_for_location='resource_group_location', location='westus',
                 dev_setting_name='AZURE_CLI_TEST_DEV_RESOURCE_GROUP_NAME',
                 dev_setting_location='AZURE_CLI_TEST_DEV_RESOURCE_GROUP_LOCATION',
                 random_name_length=75, key='rg', subscription=None, additional_tags=None):
        if ' ' in name_prefix:
            raise CliTestError('Error: Space character in resource group name prefix \'%s\'' % name_prefix)
        super().__init__(name_prefix, random_name_length)
        from azure.cli.core.mock import DummyCli
        self.cli_ctx = DummyCli()
        self.location = location
        self.subscription = subscription
        self.parameter_name = parameter_name
        self.parameter_name_for_location = parameter_name_for_location
        self.key = key
        self.additional_tags = additional_tags
 
        self.dev_setting_name = os.environ.get(dev_setting_name, None)
        self.dev_setting_location = os.environ.get(dev_setting_location, location)

    def create_resource(self, name, **kwargs):
        cmd = 'az group create --location {} --name {}'.format(self.location, name)
        execute(self.cli_ctx, cmd)
        return {self.parameter_name: name, self.parameter_name_for_location: self.location}
 
    def remove_resource(self, name, **kwargs):
        pass


class VaultPreparer(AbstractPreparer, SingleValueReplacer):  # pylint: disable=too-many-instance-attributes
    def __init__(self, name_prefix='clitest-vault', parameter_name='vault_name',
                 resource_group_location_parameter_name='resource_group_location',
                 resource_group_parameter_name='resource_group',
                 dev_setting_name='AZURE_CLI_TEST_DEV_BACKUP_ACCT_NAME', storageRedundancy=None):
        super().__init__(name_prefix, 24)
        from azure.cli.core.mock import DummyCli
        self.cli_ctx = DummyCli()
        self.parameter_name = parameter_name
        self.resource_group = None
        self.resource_group_parameter_name = resource_group_parameter_name
        self.location = None
        self.resource_group_location_parameter_name = resource_group_location_parameter_name
        self.dev_setting_value = os.environ.get(dev_setting_name, None)
        self.storageRedundancy = storageRedundancy

    def create_resource(self, name, **kwargs):
        if not self.dev_setting_value:
            self.resource_group = self._get_resource_group(**kwargs)
            self.location = self._get_resource_group_location(**kwargs)

            # Soft delete cannnot be disabled anymore.
            cmd = 'az backup vault create -n {} -g {} --location {}'.format(name, self.resource_group, self.location)
            execute(self.cli_ctx, cmd)

            if self.storageRedundancy:
                cmd = 'az backup vault update -n {} -g {} --backup-storage-redundancy {}'.format(name, self.resource_group, self.storageRedundancy)
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
        print(vault_name, resource_group)
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
            logger.warning('Unable to delete the vault. Please delete it manually.')


class VMPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest-vm', parameter_name='vm_name',
                 resource_group_location_parameter_name='resource_group_location',
                 resource_group_parameter_name='resource_group', dev_setting_name='AZURE_CLI_TEST_DEV_BACKUP_VM_NAME', image = "Win2022Datacenter"):
        super().__init__(name_prefix, 15)
        from azure.cli.core.mock import DummyCli
        self.cli_ctx = DummyCli()
        self.parameter_name = parameter_name
        self.resource_group = None
        self.resource_group_parameter_name = resource_group_parameter_name
        self.location = None
        self.resource_group_location_parameter_name = resource_group_location_parameter_name
        self.dev_setting_value = os.environ.get(dev_setting_name, None)
        self.image = image

    def create_resource(self, name, **kwargs):
        if not self.dev_setting_value:
            self.resource_group = self._get_resource_group(**kwargs)
            self.location = self._get_resource_group_location(**kwargs)
            param_format = '-n {} -g {} --image {} --admin-username {} --admin-password {} '
            param_format += '--tags {} --nsg-rule None'
            # param_format += '--tags {} --size {} --nsg-rule None'
            param_tags = 'MabUsed=Yes Owner=sisi Purpose=CLITest DeleteBy=12-2099 AutoShutdown=No'
            param_string = param_format.format(name, self.resource_group, self.image, name,
                                               '%j^VYw9Q3Z@Cu$*h', param_tags)  #, 'Standard_D2a_v4')
            cmd = 'az vm create {}'.format(param_string)
            execute(self.cli_ctx, cmd)
            return {self.parameter_name: name}
        return {self.parameter_name: self.dev_setting_value}

    def remove_resource(self, name, **kwargs):
        # Resource group deletion will take care of this.
        cmd = 'az vm delete -g {} -n {} --yes'.format(self.resource_group, name)
        try:
            execute(self.cli_ctx, cmd)
        except:
            logger.warning("Unable to delete the Virtual Machine. Please delete it manually.")
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
        super().__init__(name_prefix, 24)
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
        super().__init__(name_prefix, 24)
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


class KeyPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest-key', parameter_name='key_url', keyvault_parameter_name='key_vault',
                 dev_setting_name='AZURE_CLI_TEST_DEV_BACKUP_KEY_NAME'):
        super().__init__(name_prefix, 24)
        from azure.cli.core.mock import DummyCli
        self.cli_ctx = DummyCli()
        self.parameter_name = parameter_name
        self.key_vault = keyvault_parameter_name
        self.dev_setting_value = os.environ.get(dev_setting_name, None)
    
    def create_resource(self, name, **kwargs):
        if not self.dev_setting_value:
            keyvault = self._get_keyvault(**kwargs)

            command_string = 'az keyvault key create --vault-name {} -n {}'
            command_string = command_string.format(keyvault, name)
            key_job = execute(self.cli_ctx, command_string).get_output_in_json()
            return {self.parameter_name: key_job["key"]["kid"]}
        return {self.parameter_name: self.dev_setting_value}
    
    def remove_resource(self, name, **kwargs):
        # Keyvault deletion will take care of this.
        pass

    def _get_keyvault(self, **kwargs):
        try:
            return kwargs.get(self.key_vault)
        except KeyError:
            template = 'To create a Key, a keyvault is required. Please add ' \
                        'decorator @{}} in front of this Key Preparer.'
            raise CliTestError(template.format(KeyVaultPreparer.__name__,
                                                self.keyvault_parameter_name))
    

class DESPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest-des', parameter_name='des_name', key_parameter_name='key_url',
                 resource_group_parameter_name='resource_group', dev_setting_name='AZURE_CLI_TEST_DEV_BACKUP_DES_NAME'):
        super().__init__(name_prefix, 24)
        from azure.cli.core.mock import DummyCli
        self.cli_ctx = DummyCli()
        self.resource_group = None
        self.parameter_name = parameter_name
        self.key_url = key_parameter_name
        self.resource_group_parameter_name = resource_group_parameter_name
        self.dev_setting_value = os.environ.get(dev_setting_name, None)

    def create_resource(self, name, **kwargs):
        if not self.dev_setting_value:
            self.resource_group = self._get_resource_group(**kwargs)
            key_url = self._get_key_url(**kwargs)

            command_string = 'az disk-encryption-set create -g {} -n {} --key-url {}'
            command_string = command_string.format(self.resource_group, name, key_url)
            execute(self.cli_ctx, command_string)
            return {self.parameter_name: name}
        return {self.parameter_name: self.dev_setting_value}

    def remove_resource(self, name, **kwargs):
        # Resource group deletion will take care of this.
        pass

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create a Disk encryption set, a resource group is required. Please add ' \
                       'decorator @{} in front of this DES preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))

    def _get_key_url(self, **kwargs):
        try:
            return kwargs.get(self.key_url)
        except KeyError:
            template = 'To create a Disk Encryption Set, a key is required. Please add ' \
                        'decorator @{}} in front of this DES Preparer.'
            raise CliTestError(template.format(KeyPreparer.__name__,
                                               self.key_url))


class AFSPolicyPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest-item', parameter_name='policy_name', vault_parameter_name='vault_name',
                 resource_group_parameter_name='resource_group',
                 backup_tier="Snapshot"):
        super().__init__(name_prefix, 24)
        from azure.cli.core.mock import DummyCli
        self.cli_ctx = DummyCli()
        self.parameter_name = parameter_name
        self.resource_group = None
        self.resource_group_parameter_name = resource_group_parameter_name
        self.vault = None
        self.vault_parameter_name = vault_parameter_name
        self.backup_tier = backup_tier

    def create_resource(self, name, **kwargs):
        if not os.environ.get('AZURE_CLI_TEST_DEV_BACKUP_POLICY_NAME', None):
            self.resource_group = self._get_resource_group(**kwargs)
            self.vault = self._get_vault(**kwargs)

            policy_json = execute(self.cli_ctx, 'az backup policy show -g {} -v {} -n {}'
                                  .format(self.resource_group, self.vault, 'DefaultPolicy')).get_output_in_json()
            
            # Remove unwanted keys from default AzureVM policy
            keys_to_remove = [
                'instantRpDetails',
                'instantRpRetentionRangeInDays',
                'policyType',
                'snapshotConsistencyType',
                'tieringPolicy'
            ]

            for key in keys_to_remove:
                policy_json['properties'].pop(key, None)

            policy_json['name'] = name
           
            policy_json['properties']['backupManagementType'] = "AzureStorage"
            policy_json['properties']['workLoadType'] = "AzureFileShare"

            # Modify the policy based on the backup tier
            if self.backup_tier.lower() == 'vaultstandard':
                # Set retentionPolicy to null
                policy_json['properties'].pop('retentionPolicy', None)

                # Add vaultRetentionPolicy with the required properties
                policy_json['properties']['vaultRetentionPolicy'] = {
                    "snapshotRetentionInDays": 5,
                    "vaultRetention": {
                        "dailySchedule": {
                            "retentionDuration": {
                                "count": 30,
                                "durationType": "Days"
                            },
                            "retentionTimes": policy_json['properties']['schedulePolicy']['scheduleRunTimes']
                        },
                        "monthlySchedule": None,
                        "retentionPolicyType": "LongTermRetentionPolicy",
                        "weeklySchedule": None,
                        "yearlySchedule": None
                    }
                }
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
        super().__init__(name_prefix, 24)
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
        super().__init__(name_prefix, 24)
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
        resource_group = self._get_resource_group(**kwargs)
        storage_account = self._get_storage_account(**kwargs)
        vault = self._get_vault(**kwargs)
        afs = self._get_file_share(**kwargs)
        self._cleanup(resource_group, storage_account, vault, afs)

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

    def _delete_lock(self, lock):
        lock_id = lock["id"]
        print("deleting lock ID: ", lock_id)
        try:
            command_string = 'az lock delete --ids {}'.format(lock_id)
            execute(self.cli_ctx, command_string)
        except Exception:
            logger.warning('Unable to delete the lock with ID {}, please delete it manually'.format(lock_id))

    def _cleanup(self, resource_group, storage_account, vault, afs):
        # Need to remove any resource locks on the Storage Account, and also manually delete the item
        command_string = 'az lock list -g {}'.format(resource_group)
        list_of_locks = execute(self.cli_ctx, command_string).get_output_in_json()
        for lock in list_of_locks:
            self._delete_lock(lock)
        
        # Cleaning up Storage account locks
        command_string = 'az lock list -g {} --resource-name {} --resource-type {}'.format(
            resource_group, storage_account, 'Microsoft.Storage/storageAccounts')
        list_of_locks = execute(self.cli_ctx, command_string).get_output_in_json()
        for lock in list_of_locks:
            self._delete_lock(lock)

        command_string = 'az backup protection disable'
        command_string += ' -g {} -v {} --container-name {} --item-name {}'
        command_string += ' --backup-management-type AzureStorage --workload-type AzureFileShare --delete-backup-data true --yes'
        command_string = command_string.format(resource_group, vault, storage_account, afs)
        try:
            execute(self.cli_ctx, command_string)
        except Exception:
            logger.warning('Warning: Unable to unregister AFS item during AFS Item test cleanup.')

        command_string = 'az backup container unregister'
        command_string += ' --vault-name {} --resource-group {} --container-name {} --backup-management-type AzureStorage --yes'
        command_string = command_string.format(vault, resource_group, storage_account)
        try:
            execute(self.cli_ctx, command_string)
        except Exception:
            logger.warning('Warning: Unable to unregister storage container during AFS Item test cleanup.')


class AFSRPPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest-item', storage_account_parameter_name='storage_account',
                 resource_group_parameter_name='resource_group', vault_parameter_name='vault_name',
                 parameter_name='rp_name', afs_parameter_name='afs_name'):
        super().__init__(name_prefix, 24)
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
        super().__init__(name_prefix, 24)
        self.parameter_name = parameter_name

    def create_resource(self, name, **kwargs):
        if not os.environ.get('AZURE_CLI_TEST_DEV_BACKUP_RP_NAME', None):
            f = open(name, "a")
            f.close()
            return {self.parameter_name: name}
        return {self.parameter_name: os.environ.get('AZURE_CLI_TEST_DEV_BACKUP_RP_NAME', None)}

    def remove_resource(self, name, **kwargs):
        os.remove(name)
