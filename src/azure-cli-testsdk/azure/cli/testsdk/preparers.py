# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure_devtools.scenario_tests import AbstractPreparer, SingleValueReplacer

from .base import execute
from .exceptions import CliTestError


# Resource Group Preparer and its shorthand decorator

class ResourceGroupPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest.rg',
                 parameter_name='resource_group',
                 parameter_name_for_location='resource_group_location', location='westus',
                 dev_setting_name='AZURE_CLI_TEST_DEV_RESOURCE_GROUP_NAME',
                 dev_setting_location='AZURE_CLI_TEST_DEV_RESOURCE_GROUP_LOCATION',
                 random_name_length=75):
        super(ResourceGroupPreparer, self).__init__(name_prefix, random_name_length)
        self.location = location
        self.parameter_name = parameter_name
        self.parameter_name_for_location = parameter_name_for_location

        self.dev_setting_name = os.environ.get(dev_setting_name, None)
        self.dev_setting_location = os.environ.get(dev_setting_location, location)

    def create_resource(self, name, **kwargs):
        if self.dev_setting_name:
            return {self.parameter_name: self.dev_setting_name,
                    self.parameter_name_for_location: self.dev_setting_location}

        template = 'az group create --location {} --name {} --tag use=az-test'
        execute(template.format(self.location, name))
        return {self.parameter_name: name, self.parameter_name_for_location: self.location}

    def remove_resource(self, name, **kwargs):
        if not self.dev_setting_name:
            execute('az group delete --name {} --yes --no-wait'.format(name))


# Storage Account Preparer and its shorthand decorator

class StorageAccountPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest', sku='Standard_LRS', location='westus', parameter_name='storage_account',
                 resource_group_parameter_name='resource_group', skip_delete=True,
                 dev_setting_name='AZURE_CLI_TEST_DEV_STORAGE_ACCOUNT_NAME'):
        super(StorageAccountPreparer, self).__init__(name_prefix, 24)
        self.location = location
        self.sku = sku
        self.resource_group_parameter_name = resource_group_parameter_name
        self.skip_delete = skip_delete
        self.parameter_name = parameter_name

        self.dev_setting_name = os.environ.get(dev_setting_name, None)

    def create_resource(self, name, **kwargs):
        group = self._get_resource_group(**kwargs)

        if not self.dev_setting_name:
            template = 'az storage account create -n {} -g {} -l {} --sku {}'
            execute(template.format(name, group, self.location, self.sku))
        else:
            name = self.dev_setting_name

        account_key = execute('storage account keys list -n {} -g {} --query "[0].value" -otsv'
                              .format(name, group)).output
        return {self.parameter_name: name, self.parameter_name + '_info': (name, account_key)}

    def remove_resource(self, name, **kwargs):
        if not self.skip_delete and not self.dev_setting_name:
            group = self._get_resource_group(**kwargs)
            execute('az storage account delete -n {} -g {} --yes'.format(name, group))

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create a storage account a resource group is required. Please add ' \
                       'decorator @{} in front of this storage account preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__))


# KeyVault Preparer and its shorthand decorator

class KeyVaultPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest', sku='standard', location='westus', parameter_name='key_vault',
                 resource_group_parameter_name='resource_group', skip_delete=True,
                 dev_setting_name='AZURE_CLI_TEST_DEV_KEY_VAULT_NAME'):
        super(KeyVaultPreparer, self).__init__(name_prefix, 24)
        self.location = location
        self.sku = sku
        self.resource_group_parameter_name = resource_group_parameter_name
        self.skip_delete = skip_delete
        self.parameter_name = parameter_name

        self.dev_setting_name = os.environ.get(dev_setting_name, None)

    def create_resource(self, name, **kwargs):
        if not self.dev_setting_name:
            group = self._get_resource_group(**kwargs)
            template = 'az keyvault create -n {} -g {} -l {} --sku {}'
            execute(template.format(name, group, self.location, self.sku))
            return {self.parameter_name: name}

        return {self.parameter_name: self.dev_setting_name}

    def remove_resource(self, name, **kwargs):
        if not self.skip_delete and not self.dev_setting_name:
            group = self._get_resource_group(**kwargs)
            execute('az keyvault delete -n {} -g {} --yes'.format(name, group))

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create a KeyVault a resource group is required. Please add ' \
                       'decorator @{} in front of this KeyVault preparer.'
            raise CliTestError(template.format(KeyVaultPreparer.__name__))


# Role based access control service principal preparer

class RoleBasedServicePrincipalPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='http://clitest',
                 skip_assignment=True, parameter_name='sp_name', parameter_password='sp_password',
                 dev_setting_sp_name='AZURE_CLI_TEST_DEV_SP_NAME',
                 dev_setting_sp_password='AZURE_CLI_TEST_DEV_SP_PASSWORD'):
        super(RoleBasedServicePrincipalPreparer, self).__init__(name_prefix, 24)
        self.skip_assignment = skip_assignment
        self.result = {}
        self.parameter_name = parameter_name
        self.parameter_password = parameter_password
        self.dev_setting_sp_name = os.environ.get(dev_setting_sp_name, None)
        self.dev_setting_sp_password = os.environ.get(dev_setting_sp_password, None)

    def create_resource(self, name, **kwargs):
        if not self.dev_setting_sp_name:
            command = 'az ad sp create-for-rbac -n {}{}' \
                .format(name, ' --skip-assignment' if self.skip_assignment else '')
            self.result = execute(command).get_output_in_json()
            return {self.parameter_name: name, self.parameter_password: self.result['password']}

        return {self.parameter_name: self.dev_setting_sp_name,
                self.parameter_password: self.dev_setting_sp_password}

    def remove_resource(self, name, **kwargs):
        if not self.dev_setting_sp_name:
            execute('az ad sp delete --id {}'.format(self.result['appId']))


# Utility

def is_preparer_func(fn):
    return getattr(fn, '__is_preparer', False)
