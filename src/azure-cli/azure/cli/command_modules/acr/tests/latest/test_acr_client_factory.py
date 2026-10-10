# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

from azure.cli.core.azclierror import ArgumentUsageError, ValidationError
from azure.cli.command_modules.acr import _client_factory


class AcrClientFactoryTests(unittest.TestCase):

    @mock.patch.object(_client_factory, 'get_mgmt_service_client')
    def test_acr_service_client_uses_auxiliary_tenants(self, get_mgmt_service_client):
        _client_factory.get_acr_service_client(
            mock.sentinel.cli_ctx, aux_tenants=['source-tenant'])

        _, kwargs = get_mgmt_service_client.call_args
        self.assertEqual(kwargs['aux_tenants'], ['source-tenant'])

    @mock.patch.object(_client_factory, 'get_acr_service_client')
    @mock.patch('azure.cli.core._profile.Profile')
    def test_import_client_uses_registry_tenant(self, profile, get_acr_service_client):
        registries = mock.sentinel.registries
        get_acr_service_client.return_value.registries = registries
        profile.return_value.get_subscription.return_value = {'user': {'type': 'user'}}
        command_args = {
            'source_registry': (
                '/subscriptions/source-subscription/resourceGroups/source-rg/providers/'
                'Microsoft.ContainerRegistry/registries/source-registry'),
            'registry_tenant': 'source-tenant'
        }

        result = _client_factory.cf_acr_import(mock.sentinel.cli_ctx, command_args)

        self.assertIs(result, registries)
        get_acr_service_client.assert_called_once_with(
            mock.sentinel.cli_ctx, aux_tenants=['source-tenant'])
        self.assertNotIn('registry_tenant', command_args)

    @mock.patch.object(_client_factory, 'get_acr_service_client')
    def test_import_client_rejects_registry_name_with_registry_tenant(self, get_acr_service_client):
        command_args = {
            'source_registry': 'source-registry',
            'registry_tenant': 'source-tenant'
        }

        with self.assertRaisesRegex(
                ArgumentUsageError,
                '--registry-tenant can only be used when --registry is a container registry resource ID'):
            _client_factory.cf_acr_import(mock.sentinel.cli_ctx, command_args)

        get_acr_service_client.assert_not_called()

    @mock.patch.object(_client_factory, 'get_acr_service_client')
    def test_import_client_rejects_missing_registry_with_registry_tenant(self, get_acr_service_client):
        command_args = {'registry_tenant': 'source-tenant'}

        with self.assertRaisesRegex(
                ArgumentUsageError,
                '--registry-tenant can only be used when --registry is a container registry resource ID'):
            _client_factory.cf_acr_import(mock.sentinel.cli_ctx, command_args)

        get_acr_service_client.assert_not_called()

    @mock.patch.object(_client_factory, 'get_acr_service_client')
    def test_import_client_rejects_non_registry_resource_id(self, get_acr_service_client):
        command_args = {
            'source_registry': (
                '/subscriptions/source-subscription/resourceGroups/source-rg/providers/'
                'Microsoft.Storage/storageAccounts/source-storage'),
            'registry_tenant': 'source-tenant'
        }

        with self.assertRaisesRegex(
                ArgumentUsageError,
                '--registry-tenant can only be used when --registry is a container registry resource ID'):
            _client_factory.cf_acr_import(mock.sentinel.cli_ctx, command_args)

        get_acr_service_client.assert_not_called()

    @mock.patch.object(_client_factory, 'get_acr_service_client')
    @mock.patch('azure.cli.core._profile.Profile')
    def test_import_client_rejects_managed_identity(self, profile, get_acr_service_client):
        profile.return_value.get_subscription.return_value = {
            'user': {'name': 'systemAssignedIdentity'}
        }
        command_args = {
            'source_registry': (
                '/subscriptions/source-subscription/resourceGroups/source-rg/providers/'
                'Microsoft.ContainerRegistry/registries/source-registry'),
            'registry_tenant': 'source-tenant'
        }

        with self.assertRaisesRegex(
                ValidationError,
                '--registry-tenant is not supported when signed in with managed identity'):
            _client_factory.cf_acr_import(mock.sentinel.cli_ctx, command_args)

        get_acr_service_client.assert_not_called()

    @mock.patch.object(_client_factory, 'get_acr_service_client')
    @mock.patch('azure.cli.core._profile.Profile')
    def test_import_client_rejects_cloud_shell(self, profile, get_acr_service_client):
        profile.return_value.get_subscription.return_value = {'user': {'cloudShellID': True}}
        command_args = {
            'source_registry': (
                '/subscriptions/source-subscription/resourceGroups/source-rg/providers/'
                'Microsoft.ContainerRegistry/registries/source-registry'),
            'registry_tenant': 'source-tenant'
        }

        with self.assertRaisesRegex(
                ValidationError,
                '--registry-tenant is not supported when signed in with managed identity or Cloud Shell'):
            _client_factory.cf_acr_import(mock.sentinel.cli_ctx, command_args)

        get_acr_service_client.assert_not_called()

    @mock.patch.object(_client_factory, 'get_acr_service_client')
    def test_import_client_without_registry_tenant(self, get_acr_service_client):
        registries = mock.sentinel.registries
        get_acr_service_client.return_value.registries = registries
        command_args = {'source_registry': 'source-registry'}

        result = _client_factory.cf_acr_import(mock.sentinel.cli_ctx, command_args)

        self.assertIs(result, registries)
        get_acr_service_client.assert_called_once_with(mock.sentinel.cli_ctx, aux_tenants=None)


if __name__ == '__main__':
    unittest.main()
