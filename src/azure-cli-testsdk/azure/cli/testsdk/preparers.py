# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from datetime import datetime

from azure.cli.testsdk.base import execute
from azure.cli.core.mock import DummyCli

from .scenario_tests import AbstractPreparer, SingleValueReplacer
from .base import LiveScenarioTest
from .exceptions import CliTestError
from .reverse_dependency import get_dummy_cli
from .utilities import StorageAccountKeyReplacer, GraphClientPasswordReplacer

KEY_RESOURCE_GROUP = 'rg'
KEY_VIRTUAL_NETWORK = 'vnet'
KEY_VNET_NIC = 'nic'


# This preparer's traffic is not recorded.
# As a result when tests are run in record mode, sdk calls cannot be made to return the prepared resource group.
# Rather the deterministic prepared resource's information should be returned.
class NoTrafficRecordingPreparer(AbstractPreparer):
    from .base import execute as _raw_execute

    def __init__(self, *args, **kwargs):
        super(NoTrafficRecordingPreparer, self).__init__(disable_recording=True, *args, **kwargs)

    def live_only_execute(self, cli_ctx, command, expect_failure=False):
        # call AbstractPreparer.moniker to make resource counts and self.resource_moniker consistent between live and
        # play-back. see SingleValueReplacer.process_request, AbstractPreparer.__call__._preparer_wrapper
        # and ScenarioTest.create_random_name. This is so that when self.create_random_name is called for the
        # first time during live or playback, it would have the same value.
        _ = self.moniker

        try:
            if self.test_class_instance.in_recording:
                return self._raw_execute(cli_ctx, command, expect_failure)
        except AttributeError:
            # A test might not have an in_recording attribute. Run live if this is an instance of LiveScenarioTest
            if isinstance(self.test_class_instance, LiveScenarioTest):
                return self._raw_execute(cli_ctx, command, expect_failure)

        return None


# Resource Group Preparer and its shorthand decorator

class ResourceGroupPreparer(NoTrafficRecordingPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest.rg',
                 parameter_name='resource_group',
                 parameter_name_for_location='resource_group_location', location='westus',
                 dev_setting_name='AZURE_CLI_TEST_DEV_RESOURCE_GROUP_NAME',
                 dev_setting_location='AZURE_CLI_TEST_DEV_RESOURCE_GROUP_LOCATION',
                 random_name_length=75, key='rg', subscription=None, additional_tags=None):
        if ' ' in name_prefix:
            raise CliTestError('Error: Space character in resource group name prefix \'%s\'' % name_prefix)
        super(ResourceGroupPreparer, self).__init__(name_prefix, random_name_length)
        self.cli_ctx = get_dummy_cli()
        self.location = location
        self.subscription = subscription
        self.parameter_name = parameter_name
        self.parameter_name_for_location = parameter_name_for_location
        self.key = key
        self.additional_tags = additional_tags

        self.dev_setting_name = os.environ.get(dev_setting_name, None)
        self.dev_setting_location = os.environ.get(dev_setting_location, location)

    def create_resource(self, name, **kwargs):
        if self.dev_setting_name:
            self.test_class_instance.kwargs[self.key] = self.dev_setting_name
            return {self.parameter_name: self.dev_setting_name,
                    self.parameter_name_for_location: self.dev_setting_location}

        tags = {'product': 'azurecli', 'cause': 'automation', 'date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}
        if 'ENV_JOB_NAME' in os.environ:
            tags['job'] = os.environ['ENV_JOB_NAME']
        tags = ' '.join(['{}={}'.format(key, value) for key, value in tags.items()])
        if self.additional_tags is not None:
            tags = tags.join(['{}={}'.format(key, value) for key, value in self.additional_tags.items()])
        template = 'az group create --location {} --name {} --tag ' + tags
        if self.subscription:
            template += ' --subscription {} '.format(self.subscription)
        self.live_only_execute(self.cli_ctx, template.format(self.location, name))

        self.test_class_instance.kwargs[self.key] = name
        return {self.parameter_name: name, self.parameter_name_for_location: self.location}

    def remove_resource(self, name, **kwargs):
        # delete group if test is being recorded and if the group is not a dev rg
        if not self.dev_setting_name:
            template = 'az group delete --name {} --yes --no-wait '
            if self.subscription:
                template += ' --subscription {} '.format(self.subscription)
            self.live_only_execute(self.cli_ctx, template.format(name))


# Storage Account Preparer and its shorthand decorator

# pylint: disable=too-many-instance-attributes
class StorageAccountPreparer(NoTrafficRecordingPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest', sku='Standard_LRS', location='westus', kind='Storage', hns=False, length=24,
                 parameter_name='storage_account', resource_group_parameter_name='resource_group', skip_delete=True,
                 dev_setting_name='AZURE_CLI_TEST_DEV_STORAGE_ACCOUNT_NAME', key='sa'):
        super(StorageAccountPreparer, self).__init__(name_prefix, length)
        self.cli_ctx = get_dummy_cli()
        self.location = location
        self.sku = sku
        self.kind = kind
        self.hns = hns
        self.resource_group_parameter_name = resource_group_parameter_name
        self.skip_delete = skip_delete
        self.parameter_name = parameter_name
        self.key = key
        self.dev_setting_name = os.environ.get(dev_setting_name, None)

    def create_resource(self, name, **kwargs):
        group = self._get_resource_group(**kwargs)

        if not self.dev_setting_name:
            template = 'az storage account create -n {} -g {} -l {} --sku {} --kind {} --https-only '
            if self.hns:
                template += '--hns'
            self.live_only_execute(self.cli_ctx, template.format(
                name, group, self.location, self.sku, self.kind, self.hns))
        else:
            name = self.dev_setting_name

        try:
            account_key = self.live_only_execute(self.cli_ctx,
                                                 'storage account keys list -n {} -g {} --query "[0].value" -otsv'
                                                 .format(name, group)).output
        except AttributeError:  # live only execute returns None if playing from record
            account_key = None

        self.test_class_instance.kwargs[self.key] = name
        return {self.parameter_name: name,
                self.parameter_name + '_info': (name, account_key or StorageAccountKeyReplacer.KEY_REPLACEMENT)}

    def remove_resource(self, name, **kwargs):
        if not self.skip_delete and not self.dev_setting_name:
            group = self._get_resource_group(**kwargs)
            self.live_only_execute(self.cli_ctx, 'az storage account delete -n {} -g {} --yes'.format(name, group))

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create a storage account a resource group is required. Please add ' \
                       'decorator @{} in front of this storage account preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__))


# KeyVault Preparer and its shorthand decorator

# pylint: disable=too-many-instance-attributes
class KeyVaultPreparer(NoTrafficRecordingPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest', sku='standard', location='westus', enable_soft_delete=True,
                 parameter_name='key_vault', resource_group_parameter_name='resource_group', skip_delete=False,
                 dev_setting_name='AZURE_CLI_TEST_DEV_KEY_VAULT_NAME', key='kv', name_len=24, additional_params=None):
        super(KeyVaultPreparer, self).__init__(name_prefix, name_len)
        self.cli_ctx = get_dummy_cli()
        self.location = location
        self.sku = sku
        self.enable_soft_delete = enable_soft_delete
        self.resource_group_parameter_name = resource_group_parameter_name
        self.skip_delete = skip_delete
        self.parameter_name = parameter_name
        self.key = key
        self.additional_params = additional_params
        self.dev_setting_name = os.environ.get(dev_setting_name, None)

    def create_resource(self, name, **kwargs):
        if not self.dev_setting_name:
            group = self._get_resource_group(**kwargs)
            template = 'az keyvault create -n {} -g {} -l {} --sku {} '
            if self.enable_soft_delete:
                template += '--enable-soft-delete --retention-days 7 '
            if self.additional_params:
                template += self.additional_params
            self.live_only_execute(self.cli_ctx, template.format(name, group, self.location, self.sku))
            self.test_class_instance.kwargs[self.key] = name
            return {self.parameter_name: name}

        self.test_class_instance.kwargs[self.key] = self.dev_setting_name
        return {self.parameter_name: self.dev_setting_name}

    def remove_resource(self, name, **kwargs):
        if not self.skip_delete and not self.dev_setting_name:
            group = self._get_resource_group(**kwargs)
            self.live_only_execute(self.cli_ctx, 'az keyvault delete -n {} -g {}'.format(name, group))
            if self.enable_soft_delete:
                from azure.core.exceptions import HttpResponseError
                try:
                    self.live_only_execute(self.cli_ctx, 'az keyvault purge -n {} -l {}'.format(name, self.location))
                except HttpResponseError:
                    # purge operation will fail with HttpResponseError when --enable-purge-protection
                    pass

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create a KeyVault a resource group is required. Please add ' \
                       'decorator @{} in front of this KeyVault preparer.'
            raise CliTestError(template.format(KeyVaultPreparer.__name__))


# Role based access control service principal preparer

# pylint: disable=too-many-instance-attributes
class RoleBasedServicePrincipalPreparer(NoTrafficRecordingPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest',
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

            try:
                self.result = self.live_only_execute(self.cli_ctx, command).get_output_in_json()
            except AttributeError:  # live only execute returns None if playing from record
                pass

            self.test_class_instance.kwargs[self.key] = name
            self.test_class_instance.kwargs['{}_pass'.format(self.key)] = self.parameter_password
            return {self.parameter_name: name,
                    self.parameter_password: self.result.get('password') or GraphClientPasswordReplacer.PWD_REPLACEMENT}

        self.test_class_instance.kwargs[self.key] = self.dev_setting_sp_name
        self.test_class_instance.kwargs['{}_pass'.format(self.key)] = self.dev_setting_sp_password
        return {self.parameter_name: self.dev_setting_sp_name,
                self.parameter_password: self.dev_setting_sp_password}

    def remove_resource(self, name, **kwargs):
        if not self.dev_setting_sp_name:
            self.live_only_execute(self.cli_ctx, 'az ad sp delete --id {}'.format(self.result.get('appId')))


# Managed Application preparer

# pylint: disable=too-many-instance-attributes
class ManagedApplicationPreparer(AbstractPreparer, SingleValueReplacer):
    from .base import execute

    def __init__(self, name_prefix='clitest', parameter_name='aad_client_app_id',
                 parameter_secret='aad_client_app_secret', app_name='app_name',
                 dev_setting_app_name='AZURE_CLI_TEST_DEV_APP_NAME',
                 dev_setting_app_secret='AZURE_CLI_TEST_DEV_APP_SECRET', key='app'):
        super(ManagedApplicationPreparer, self).__init__(name_prefix, 24)
        self.cli_ctx = get_dummy_cli()
        self.parameter_name = parameter_name
        self.parameter_secret = parameter_secret
        self.result = {}
        self.app_name = app_name
        self.dev_setting_app_name = os.environ.get(dev_setting_app_name, None)
        self.dev_setting_app_secret = os.environ.get(dev_setting_app_secret, None)
        self.key = key

    def create_resource(self, name, **kwargs):
        if not self.dev_setting_app_name:
            template = 'az ad app create --display-name {} --key-type Password --password {} --identifier-uris ' \
                       'http://{}'
            self.result = self.execute(self.cli_ctx, template.format(name, name, name)).get_output_in_json()

            self.test_class_instance.kwargs[self.key] = name
            return {self.parameter_name: self.result['appId'], self.parameter_secret: name}
        self.test_class_instance.kwargs[self.key] = name
        return {self.parameter_name: self.dev_setting_app_name,
                self.parameter_secret: self.dev_setting_app_secret}

    def remove_resource(self, name, **kwargs):
        if not self.dev_setting_app_name:
            self.execute(self.cli_ctx, 'az ad app delete --id {}'.format(self.result['appId']))


# pylint: disable=too-many-instance-attributes
class VirtualNetworkPreparer(NoTrafficRecordingPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest.vn', location='westus',
                 parameter_name='virtual_network',
                 resource_group_parameter_name='resource_group',
                 resource_group_key=KEY_RESOURCE_GROUP,
                 dev_setting_name='AZURE_CLI_TEST_DEV_VIRTUAL_NETWORK_NAME',
                 random_name_length=24, key=KEY_VIRTUAL_NETWORK):
        if ' ' in name_prefix:
            raise CliTestError(
                'Error: Space character in name prefix \'%s\'' % name_prefix)
        super(VirtualNetworkPreparer, self).__init__(
            name_prefix, random_name_length)
        self.cli_ctx = get_dummy_cli()
        self.location = location
        self.parameter_name = parameter_name
        self.key = key
        self.resource_group_parameter_name = resource_group_parameter_name
        self.resource_group_key = resource_group_key
        self.dev_setting_name = os.environ.get(dev_setting_name, None)

    def create_resource(self, name, **kwargs):
        if self.dev_setting_name:
            self.test_class_instance.kwargs[self.key] = name
            return {self.parameter_name: self.dev_setting_name, }

        tags = {'product': 'azurecli', 'cause': 'automation',
                'date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}
        if 'ENV_JOB_NAME' in os.environ:
            tags['job'] = os.environ['ENV_JOB_NAME']
        tags = ' '.join(['{}={}'.format(key, value)
                         for key, value in tags.items()])
        template = 'az network vnet create --resource-group {} --location {} --name {} --subnet-name default --tag ' + tags
        self.live_only_execute(self.cli_ctx, template.format(self._get_resource_group(**kwargs), self.location, name))

        self.test_class_instance.kwargs[self.key] = name
        return {self.parameter_name: name}

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
            raise CliTestError(template.format(VirtualNetworkPreparer.__name__))


# pylint: disable=too-many-instance-attributes
class VnetNicPreparer(NoTrafficRecordingPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='clitest.nic',
                 parameter_name='subnet',
                 resource_group_parameter_name=KEY_RESOURCE_GROUP,
                 vnet_parameter_name=KEY_VIRTUAL_NETWORK,
                 dev_setting_name='AZURE_CLI_TEST_DEV_VNET_NIC_NAME',
                 key=KEY_VNET_NIC):
        if ' ' in name_prefix:
            raise CliTestError(
                'Error: Space character in name prefix \'%s\'' % name_prefix)
        super(VnetNicPreparer, self).__init__(name_prefix, 15)
        self.cli_ctx = get_dummy_cli()
        self.parameter_name = parameter_name
        self.key = key
        self.resource_group_parameter_name = resource_group_parameter_name
        self.vnet_parameter_name = vnet_parameter_name
        self.dev_setting_name = os.environ.get(dev_setting_name, None)

    def create_resource(self, name, **kwargs):
        if self.dev_setting_name:
            self.test_class_instance.kwargs[self.key] = name
            return {self.parameter_name: self.dev_setting_name, }

        template = 'az network nic create --resource-group {} --name {} --vnet-name {} --subnet default '
        self.live_only_execute(self.cli_ctx, template.format(
            self._get_resource_group(**kwargs), name, self._get_virtual_network(**kwargs)))

        self.test_class_instance.kwargs[self.key] = name
        return {self.parameter_name: name}

    def remove_resource(self, name, **kwargs):
        if not self.dev_setting_name:
            self.live_only_execute(
                self.cli_ctx,
                'az network nic delete --name {} --resource-group {}'.format(name, self._get_resource_group(**kwargs)))

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create a VirtualNetworkNic a resource group is required. Please add ' \
                       'decorator @{} in front of this VirtualNetworkNic preparer.'
            raise CliTestError(template.format(VnetNicPreparer.__name__))

    def _get_virtual_network(self, **kwargs):
        try:
            return kwargs.get(self.vnet_parameter_name)
        except KeyError:
            template = 'To create a VirtualNetworkNic a virtual network is required. Please add ' \
                       'decorator @{} in front of this VirtualNetworkNic preparer.'
            raise CliTestError(template.format(VnetNicPreparer.__name__))


class LogAnalyticsWorkspacePreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix='laworkspace', location='eastus2euap', parameter_name='laworkspace',
                 resource_group_parameter_name='resource_group', skip_delete=False):
        super(LogAnalyticsWorkspacePreparer, self).__init__(name_prefix, 15)
        self.location = location
        self.parameter_name = parameter_name
        self.resource_group_parameter_name = resource_group_parameter_name
        self.skip_delete = skip_delete

    def create_resource(self, name, **kwargs):
        group = self._get_resource_group(**kwargs)
        template = ('az monitor log-analytics workspace create -l {} -g {} -n {}')
        execute(DummyCli(), template.format(self.location, group, name))
        return {self.parameter_name: name}

    def remove_resource(self, name, **kwargs):
        if not self.skip_delete:
            group = self._get_resource_group(**kwargs)
            template = ('az monitor log-analytics workspace delete -g {} -n {} --yes')
            execute(DummyCli(), template.format(group, name))

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create a log analytics workspace a resource group is required. Please add ' \
                       'decorator @{} in front of this preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))

# Utility


def is_preparer_func(fn):
    return getattr(fn, '__is_preparer', False)
