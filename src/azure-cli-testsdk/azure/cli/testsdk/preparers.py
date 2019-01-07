# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from datetime import datetime

from azure_devtools.scenario_tests import AbstractPreparer, SingleValueReplacer

from .base import execute
from .exceptions import CliTestError
from .reverse_dependency import get_dummy_cli


# Resource Group Preparer and its shorthand decorator

class ResourceGroupPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest.rg',
                 parameter_name='resource_group',
                 parameter_name_for_location='resource_group_location', location='westus',
                 dev_setting_name='AZURE_CLI_TEST_DEV_RESOURCE_GROUP_NAME',
                 dev_setting_location='AZURE_CLI_TEST_DEV_RESOURCE_GROUP_LOCATION',
                 random_name_length=75, key='rg'):
        super(ResourceGroupPreparer, self).__init__(name_prefix, random_name_length)
        self.cli_ctx = get_dummy_cli()
        self.location = location
        self.parameter_name = parameter_name
        self.parameter_name_for_location = parameter_name_for_location
        self.key = key

        self.dev_setting_name = os.environ.get(dev_setting_name, None)
        self.dev_setting_location = os.environ.get(dev_setting_location, location)

    def create_resource(self, name, **kwargs):
        if self.dev_setting_name:
            return {self.parameter_name: self.dev_setting_name,
                    self.parameter_name_for_location: self.dev_setting_location}

        tags = {'product': 'azurecli', 'cause': 'automation', 'date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}
        if 'ENV_JOB_NAME' in os.environ:
            tags['job'] = os.environ['ENV_JOB_NAME']
        tags = ' '.join(['{}={}'.format(key, value) for key, value in tags.items()])

        template = 'az group create --location {} --name {} --tag ' + tags
        execute(self.cli_ctx, template.format(self.location, name))
        self.test_class_instance.kwargs[self.key] = name
        return {self.parameter_name: name, self.parameter_name_for_location: self.location}

    def remove_resource(self, name, **kwargs):
        if not self.dev_setting_name:
            execute(self.cli_ctx, 'az group delete --name {} --yes --no-wait'.format(name))


# Storage Account Preparer and its shorthand decorator

# pylint: disable=too-many-instance-attributes
class StorageAccountPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest', sku='Standard_LRS', location='westus', parameter_name='storage_account',
                 resource_group_parameter_name='resource_group', skip_delete=True,
                 dev_setting_name='AZURE_CLI_TEST_DEV_STORAGE_ACCOUNT_NAME', key='sa'):
        super(StorageAccountPreparer, self).__init__(name_prefix, 24)
        self.cli_ctx = get_dummy_cli()
        self.location = location
        self.sku = sku
        self.resource_group_parameter_name = resource_group_parameter_name
        self.skip_delete = skip_delete
        self.parameter_name = parameter_name
        self.key = key
        self.dev_setting_name = os.environ.get(dev_setting_name, None)

    def create_resource(self, name, **kwargs):
        group = self._get_resource_group(**kwargs)

        if not self.dev_setting_name:
            template = 'az storage account create -n {} -g {} -l {} --sku {}'
            execute(self.cli_ctx, template.format(name, group, self.location, self.sku))
        else:
            name = self.dev_setting_name

        account_key = execute(self.cli_ctx, 'storage account keys list -n {} -g {} --query "[0].value" -otsv'
                              .format(name, group)).output
        self.test_class_instance.kwargs[self.key] = name
        return {self.parameter_name: name, self.parameter_name + '_info': (name, account_key)}

    def remove_resource(self, name, **kwargs):
        if not self.skip_delete and not self.dev_setting_name:
            group = self._get_resource_group(**kwargs)
            execute(self.cli_ctx, 'az storage account delete -n {} -g {} --yes'.format(name, group))

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create a storage account a resource group is required. Please add ' \
                       'decorator @{} in front of this storage account preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__))


# KeyVault Preparer and its shorthand decorator

# pylint: disable=too-many-instance-attributes
class KeyVaultPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest', sku='standard', location='westus', parameter_name='key_vault',
                 resource_group_parameter_name='resource_group', skip_delete=True,
                 dev_setting_name='AZURE_CLI_TEST_DEV_KEY_VAULT_NAME', key='kv'):
        super(KeyVaultPreparer, self).__init__(name_prefix, 24)
        self.cli_ctx = get_dummy_cli()
        self.location = location
        self.sku = sku
        self.resource_group_parameter_name = resource_group_parameter_name
        self.skip_delete = skip_delete
        self.parameter_name = parameter_name
        self.key = key
        self.dev_setting_name = os.environ.get(dev_setting_name, None)

    def create_resource(self, name, **kwargs):
        if not self.dev_setting_name:
            group = self._get_resource_group(**kwargs)
            template = 'az keyvault create -n {} -g {} -l {} --sku {}'
            execute(self.cli_ctx, template.format(name, group, self.location, self.sku))
            return {self.parameter_name: name}

        self.test_class_instance.kwargs[self.key] = name
        return {self.parameter_name: self.dev_setting_name}

    def remove_resource(self, name, **kwargs):
        if not self.skip_delete and not self.dev_setting_name:
            group = self._get_resource_group(**kwargs)
            execute(self.cli_ctx, 'az keyvault delete -n {} -g {} --yes'.format(name, group))

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create a KeyVault a resource group is required. Please add ' \
                       'decorator @{} in front of this KeyVault preparer.'
            raise CliTestError(template.format(KeyVaultPreparer.__name__))


# Role based access control service principal preparer

# pylint: disable=too-many-instance-attributes
class RoleBasedServicePrincipalPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='http://clitest',
                 skip_assignment=True, parameter_name='sp_name', parameter_password='sp_password',
                 dev_setting_sp_name='AZURE_CLI_TEST_DEV_SP_NAME',
                 dev_setting_sp_password='AZURE_CLI_TEST_DEV_SP_PASSWORD', key='sp'):
        super(RoleBasedServicePrincipalPreparer, self).__init__(name_prefix, 24)
        self.cli_ctx = get_dummy_cli()
        self.skip_assignment = skip_assignment
        self.result = {}
        self.parameter_name = parameter_name
        self.parameter_password = parameter_password
        self.dev_setting_sp_name = os.environ.get(dev_setting_sp_name, None)
        self.dev_setting_sp_password = os.environ.get(dev_setting_sp_password, None)
        self.key = key

    def create_resource(self, name, **kwargs):
        if not self.dev_setting_sp_name:
            command = 'az ad sp create-for-rbac -n {}{}' \
                .format(name, ' --skip-assignment' if self.skip_assignment else '')
            self.result = execute(self.cli_ctx, command).get_output_in_json()
            self.test_class_instance.kwargs[self.key] = name
            self.test_class_instance.kwargs['{}_pass'.format(self.key)] = self.parameter_password
            return {self.parameter_name: name, self.parameter_password: self.result['password']}
        self.test_class_instance.kwargs[self.key] = self.dev_setting_sp_name
        self.test_class_instance.kwargs['{}_pass'.format(self.key)] = self.dev_setting_sp_password
        return {self.parameter_name: self.dev_setting_sp_name,
                self.parameter_password: self.dev_setting_sp_password}

    def remove_resource(self, name, **kwargs):
        if not self.dev_setting_sp_name:
            execute(self.cli_ctx, 'az ad sp delete --id {}'.format(self.result['appId']))


class AADGraphUserReplacer:
    def __init__(self, test_user, mock_user):
        self.test_user = test_user
        self.mock_user = mock_user

    def process_request(self, request):
        test_user_encoded = self.test_user.replace('@', '%40')
        if test_user_encoded in request.uri:
            request.uri = request.uri.replace(test_user_encoded, self.mock_user.replace('@', '%40'))

        if request.body:
            body = str(request.body)
            if self.test_user in body:
                request.body = body.replace(self.test_user, self.mock_user)

        return request

    def process_response(self, response):
        if response['body']['string']:
            response['body']['string'] = response['body']['string'].replace(self.test_user,
                                                                            self.mock_user)

        return response
# Utility


def is_preparer_func(fn):
    return getattr(fn, '__is_preparer', False)
