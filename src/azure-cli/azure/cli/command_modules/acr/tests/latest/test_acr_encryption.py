# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

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
