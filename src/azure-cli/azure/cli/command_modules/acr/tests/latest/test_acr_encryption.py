# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from types import SimpleNamespace
from unittest import mock

from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.command_modules.acr import custom


class AcrEncryptionTests(unittest.TestCase):

    @mock.patch('azure.cli.core.commands.client_factory.get_subscription_id', return_value='subscription-id')
    @mock.patch.object(custom, '_ensure_identity_resource_id', return_value='identity-resource-id')
    @mock.patch.object(custom, 'resolve_identity_client_id', return_value='identity-client-id')
    def test_configure_cmk_preserves_managed_hsm_key_uri(
            self, resolve_identity_client_id, ensure_identity_resource_id, get_subscription_id):
        key_uri = 'https://myhsm.managedhsm.azure.net/keys/mykey'
        key_vault_properties = mock.Mock()
        encryption_property = mock.Mock()
        resource_identity_type = mock.Mock(user_assigned='UserAssigned')
        identity_properties = mock.Mock()
        cmd = mock.Mock()
        cmd.get_models.side_effect = [
            (key_vault_properties, encryption_property),
            (resource_identity_type, identity_properties),
        ]
        registry = mock.Mock()

        custom._configure_cmk(
            cmd,
            registry,
            'resource-group',
            'myidentity',
            key_uri)

        get_subscription_id.assert_called_once_with(cmd.cli_ctx)
        ensure_identity_resource_id.assert_called_once_with(
            subscription_id='subscription-id',
            resource_group='resource-group',
            resource='myidentity')
        resolve_identity_client_id.assert_called_once_with(
            cmd.cli_ctx,
            'identity-resource-id')
        key_vault_properties.assert_called_once_with(
            key_identifier=key_uri,
            identity='identity-client-id')
        encryption_property.assert_called_once_with(
            status='enabled',
            key_vault_properties=key_vault_properties.return_value)
        identity_properties.assert_called_once_with(
            type='UserAssigned',
            user_assigned_identities={'identity-resource-id': {}})
        self.assertIs(registry.encryption, encryption_property.return_value)
        self.assertIs(registry.identity, identity_properties.return_value)

    @mock.patch.object(custom, 'get_registry_by_name')
    def test_rotate_key_preserves_managed_hsm_key_uri(self, get_registry_by_name):
        registry = mock.Mock()
        registry.encryption = mock.Mock()
        registry.encryption.key_vault_properties = mock.Mock()
        get_registry_by_name.return_value = registry, 'resource-group'
        cmd = mock.Mock()
        client = mock.Mock()

        for key_uri in [
                'https://myhsm.managedhsm.azure.net/keys/mykey',
                'https://myhsm.managedhsm.azure.net/keys/mykey/00000000000000000000000000000000']:
            with self.subTest(key_uri=key_uri):
                custom.rotate_key(
                    cmd,
                    client,
                    'myregistry',
                    key_encryption_key=key_uri,
                    resource_group_name='resource-group')

                self.assertEqual(
                    registry.encryption.key_vault_properties.key_identifier,
                    key_uri)

        self.assertEqual(client.begin_update.call_count, 2)
        client.begin_update.assert_called_with(
            'resource-group',
            'myregistry',
            registry)


class AcrIdentityAssignmentTests(unittest.TestCase):

    @mock.patch('azure.cli.core.commands.client_factory.get_subscription_id',
                return_value='00000000-0000-0000-0000-000000000000')
    @mock.patch.object(custom, 'get_registry_by_name')
    def test_acr_identity_assignment_preserves_existing_types(self, get_registry_by_name, _get_subscription_id):
        from azure.mgmt.containerregistry.models import IdentityProperties, ResourceIdentityType

        identity_id = (
            '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/'
            'providers/Microsoft.ManagedIdentity/userAssignedIdentities/identity')
        cases = [
            ('systemAssigned', ['[system]'], 'SystemAssigned'),
            ('userAssigned', [identity_id], 'UserAssigned'),
            ('none', ['[system]'], 'SystemAssigned'),
            ('none', [identity_id], 'UserAssigned'),
            ('userAssigned', ['[system]'], 'SystemAssigned, UserAssigned'),
            ('systemAssigned', [identity_id], 'SystemAssigned, UserAssigned'),
            ('none', ['[system]', identity_id], 'SystemAssigned, UserAssigned'),
            ('systemAssigned, userAssigned', ['[system]', identity_id], 'SystemAssigned, UserAssigned'),
        ]
        cmd = mock.Mock()
        cmd.get_models.return_value = IdentityProperties, ResourceIdentityType
        for existing_type, identities, expected_type in cases:
            for identity_type in [existing_type, existing_type.upper(), existing_type[0].upper() + existing_type[1:]]:
                with self.subTest(identity_type=identity_type, identities=identities):
                    registry = SimpleNamespace(identity=IdentityProperties(
                        type=identity_type,
                        principal_id='system-principal',
                        tenant_id='tenant',
                        user_assigned_identities={identity_id: {}} if 'user' in existing_type else None))
                    client = mock.Mock()
                    get_registry_by_name.return_value = registry, 'rg'

                    for _ in range(2):
                        result = custom.assign_identity(cmd, client, 'registry', identities, 'rg')
                        self.assertEqual(registry.identity.type.lower(), expected_type.lower())
                        self.assertEqual(registry.identity.principal_id, 'system-principal')
                        if 'UserAssigned' in expected_type:
                            self.assertIn(identity_id, registry.identity.user_assigned_identities)
                        self.assertIs(result, client.begin_update.return_value)
                        client.begin_update.assert_called_with('rg', 'registry', registry)


class AcrIdentityRemovalTests(unittest.TestCase):

    def setUp(self):
        self.client = mock.Mock()
        self.cmd = mock.Mock()
        self.cmd.get_models.return_value = SimpleNamespace(
            none='None', system_assigned='SystemAssigned', user_assigned='UserAssigned')
        self.identity_prefix = (
            '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/'
            'providers/Microsoft.ManagedIdentity/userAssignedIdentities/')
        self.cmk_identity_id = self.identity_prefix + 'cmk'
        self.other_identity_id = self.identity_prefix + 'other'
        self.cmk_client_id = '11111111-aaaa-bbbb-cccc-111111111111'
        self.other_client_id = '22222222-dddd-eeee-ffff-222222222222'
        self.registry = SimpleNamespace(
            identity=SimpleNamespace(
                type='systemAssigned, userAssigned',
                principal_id='system-principal',
                tenant_id='tenant',
                user_assigned_identities={
                    self.cmk_identity_id: SimpleNamespace(client_id=self.cmk_client_id),
                    self.other_identity_id: SimpleNamespace(client_id=self.other_client_id),
                }),
            encryption=SimpleNamespace(
                status='enabled',
                key_vault_properties=SimpleNamespace(identity=self.cmk_client_id)))
        lookup_patch = mock.patch.object(
            custom, 'get_registry_by_name', return_value=(self.registry, 'rg'))
        lookup_patch.start()
        self.addCleanup(lookup_patch.stop)
        subscription_patch = mock.patch(
            'azure.cli.core.commands.client_factory.get_subscription_id',
            return_value='00000000-0000-0000-0000-000000000000')
        subscription_patch.start()
        self.addCleanup(subscription_patch.stop)

    def test_remove_identity_rejects_cmk_system_identity(self):
        self.registry.encryption.key_vault_properties.identity = 'SYSTEM'
        for identity_type in ['systemAssigned', 'systemAssigned, userAssigned']:
            with self.subTest(identity_type=identity_type):
                self.registry.identity.type = identity_type

                with self.assertRaisesRegex(InvalidArgumentValueError, 'used for customer-managed encryption'):
                    custom.remove_identity(self.cmd, self.client, 'registry', ['[system]'], 'rg')

                self.client.begin_create.assert_not_called()
                self.client.begin_update.assert_not_called()
                self.assertEqual(self.registry.identity.type, identity_type)
                self.assertEqual(self.registry.identity.principal_id, 'system-principal')

    def test_remove_identity_rejects_cmk_user_identity(self):
        self.registry.encryption.key_vault_properties.identity = self.cmk_client_id.upper()
        for identity in ['cmk', self.cmk_identity_id, self.cmk_identity_id.upper()]:
            with self.subTest(identity=identity):
                with self.assertRaisesRegex(InvalidArgumentValueError, 'used for customer-managed encryption'):
                    custom.remove_identity(self.cmd, self.client, 'registry', [identity], 'rg')

                self.client.begin_create.assert_not_called()
                self.client.begin_update.assert_not_called()
                self.assertIn(self.cmk_identity_id, self.registry.identity.user_assigned_identities)

    def test_remove_identity_rejects_cmk_identity_in_mixed_removal(self):
        with self.assertRaisesRegex(InvalidArgumentValueError, 'used for customer-managed encryption'):
            custom.remove_identity(
                self.cmd, self.client, 'registry',
                ['[system]', self.other_identity_id, self.cmk_identity_id], 'rg')

        self.client.begin_create.assert_not_called()
        self.client.begin_update.assert_not_called()

    def test_remove_identity_allows_unrelated_user_identity(self):
        result = custom.remove_identity(
            self.cmd, self.client, 'registry', [self.other_identity_id], 'rg')

        self.assertIs(result, self.client.begin_create.return_value)
        self.client.begin_create.assert_called_once_with('rg', 'registry', self.registry)
        self.assertEqual(
            list(self.registry.identity.user_assigned_identities), [self.cmk_identity_id])
        self.assertEqual(self.registry.encryption.key_vault_properties.identity, self.cmk_client_id)

    def test_remove_identity_allows_system_removal_when_cmk_uses_user_identity(self):
        custom.remove_identity(self.cmd, self.client, 'registry', ['[system]'], 'rg')

        self.client.begin_create.assert_called_once_with('rg', 'registry', self.registry)
        self.assertEqual(self.registry.identity.type, 'UserAssigned')
        self.assertIn(self.cmk_identity_id, self.registry.identity.user_assigned_identities)

    def test_remove_identity_allows_user_removal_when_cmk_uses_system_identity(self):
        self.registry.encryption.key_vault_properties.identity = 'system'
        self.registry.identity.user_assigned_identities[self.other_identity_id].client_id = None

        custom.remove_identity(self.cmd, self.client, 'registry', [self.other_identity_id], 'rg')

        self.client.begin_create.assert_called_once_with('rg', 'registry', self.registry)
        self.assertEqual(self.registry.identity.type, 'systemAssigned, userAssigned')
        self.assertEqual(self.registry.identity.principal_id, 'system-principal')

    def test_remove_identity_allows_unencrypted_registry(self):
        self.registry.encryption = None

        custom.remove_identity(self.cmd, self.client, 'registry', [self.cmk_identity_id], 'rg')

        self.client.begin_create.assert_called_once_with('rg', 'registry', self.registry)

    def test_remove_identity_allows_disabled_encryption(self):
        self.registry.encryption.status = 'disabled'

        custom.remove_identity(self.cmd, self.client, 'registry', [self.cmk_identity_id], 'rg')

        self.client.begin_create.assert_called_once_with('rg', 'registry', self.registry)

    def test_remove_identity_rejects_missing_encryption_identity(self):
        self.registry.encryption.key_vault_properties.identity = None

        with self.assertRaisesRegex(InvalidArgumentValueError, 'encryption identity is unavailable'):
            custom.remove_identity(self.cmd, self.client, 'registry', ['[system]'], 'rg')

        self.client.begin_create.assert_not_called()
        self.client.begin_update.assert_not_called()

    def test_remove_identity_rejects_missing_user_client_id(self):
        self.registry.identity.user_assigned_identities[self.cmk_identity_id].client_id = None

        with self.assertRaisesRegex(InvalidArgumentValueError, 'client ID is unavailable'):
            custom.remove_identity(self.cmd, self.client, 'registry', [self.cmk_identity_id], 'rg')

        self.client.begin_create.assert_not_called()
        self.client.begin_update.assert_not_called()
