# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock
from azure.core.exceptions import ResourceNotFoundError, HttpResponseError
from knack.util import CLIError

# Mock the logger to prevent actual logging during tests
with mock.patch('azure.cli.command_modules.keyvault.custom.logger'):
    from azure.cli.command_modules.keyvault.custom import copy_secret

class KeyVaultCopySecretTest(unittest.TestCase):
    def setUp(self):
        self.cmd = mock.MagicMock()
        self.cmd.cli_ctx = mock.MagicMock()
        self.cmd.cli_ctx.data = {
            'subscription_id': 'sub_id',
            'headers': {},
            'completer_active': False,
            'command': 'keyvault secret copy'
        }

        # Patches
        self.patcher_profile = mock.patch('azure.cli.core._profile.Profile')
        self.mock_profile = self.patcher_profile.start()
        self.mock_profile_instance = mock.MagicMock()
        self.mock_profile.return_value = self.mock_profile_instance
        self.mock_profile_instance.get_login_credentials.return_value = (mock.Mock(), mock.Mock(), mock.Mock())

        self.patcher_secret_client = mock.patch('azure.keyvault.secrets.SecretClient')
        self.mock_secret_client_cls = self.patcher_secret_client.start()
        
        # Source Client Mock (passed as argument)
        self.source_client = mock.MagicMock()
        self.source_client.vault_url = "https://source-kv.vault.azure.net/"
        
        # Dest Client Mock (instantiated inside function)
        self.dest_client = mock.MagicMock()
        self.mock_secret_client_cls.return_value = self.dest_client

    def tearDown(self):
        self.patcher_profile.stop()
        self.patcher_secret_client.stop()

    def test_copy_single_secret_success(self):
        # Setup
        secret_name = "mysecret"
        destination_vault = "https://dest-kv.vault.azure.net/"
        
        # Mocks for verification check
        # Dummy check raises 404 which is expected/success path for connectivity check
        not_found_error = HttpResponseError(message="Not Found")
        not_found_error.status_code = 404
        self.dest_client.get_secret.side_effect = [not_found_error, ResourceNotFoundError] 
        # First call is dummy check (fails with 404), second is check existence (fails with ResourceNotFoundError -> OK to copy)

        # Source secret
        secret_obj = mock.Mock()
        secret_obj.name = secret_name
        secret_obj.value = "secret_value"
        secret_obj.properties.content_type = "text/plain"
        secret_obj.properties.tags = {}
        secret_obj.properties.enabled = True
        secret_obj.properties.not_before = None
        secret_obj.properties.expires_on = None
        
        self.source_client.get_secret.return_value = secret_obj

        # Result of set_secret
        new_secret = mock.Mock()
        new_secret.name = secret_name
        new_secret.id = destination_vault + "/secrets/" + secret_name
        self.dest_client.set_secret.return_value = new_secret

        # Act
        result = copy_secret(self.cmd, self.source_client, destination_vault, name=secret_name)

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], secret_name)
        self.dest_client.set_secret.assert_called_with(
            secret_name, "secret_value", content_type="text/plain", tags={},
            enabled=True, not_before=None, expires_on=None
        )

    def test_copy_secret_already_exists_no_overwrite(self):
        # Setup
        secret_name = "mysecret"
        destination_vault = "https://dest-kv.vault.azure.net/"
        
        # Dummy check 404
        not_found_error = HttpResponseError(message="Not Found")
        not_found_error.status_code = 404
        
        # Pre-check existence returns Success (means it exists)
        self.dest_client.get_secret.side_effect = [not_found_error, mock.Mock()]

        # Act
        result = copy_secret(self.cmd, self.source_client, destination_vault, name=secret_name, overwrite=False)

        # Assert
        self.assertEqual(len(result), 0) # Should be empty list as it was skipped
        self.dest_client.set_secret.assert_not_called()

    def test_copy_secret_already_exists_with_overwrite(self):
        # Setup
        secret_name = "mysecret"
        destination_vault = "https://dest-kv.vault.azure.net/"
        
        # Dummy check 404
        not_found_error = HttpResponseError(message="Not Found")
        not_found_error.status_code = 404
        self.dest_client.get_secret.side_effect = [not_found_error] # No second call because overwrite=True skips check

        # Source secret
        secret_obj = mock.Mock()
        secret_obj.name = secret_name
        secret_obj.value = "val"
        secret_obj.properties.content_type = None
        secret_obj.properties.tags = None
        secret_obj.properties.enabled = True
        secret_obj.properties.not_before = None
        secret_obj.properties.expires_on = None
        self.source_client.get_secret.return_value = secret_obj

        new_secret = mock.Mock()
        new_secret.name = secret_name
        new_secret.id = destination_vault + "/secrets/" + secret_name
        self.dest_client.set_secret.return_value = new_secret

        # Act
        result = copy_secret(self.cmd, self.source_client, destination_vault, name=secret_name, overwrite=True)

        # Assert
        self.assertEqual(len(result), 1)
        self.dest_client.set_secret.assert_called()

    def test_copy_all_secrets(self):
        # Setup
        destination_vault = "https://dest-kv.vault.azure.net/"
        
        # Dummy check 404
        not_found_error = HttpResponseError(message="Not Found")
        not_found_error.status_code = 404
        # We have 2 secrets. For each, we check existence (fails -> copy). 
        # Side effect sequence: DummyCheck -> Check(sec1) -> Check(sec2)
        self.dest_client.get_secret.side_effect = [
            not_found_error, 
            ResourceNotFoundError, 
            ResourceNotFoundError
        ]

        # List secrets source
        s1 = mock.Mock(); s1.name = "sec1"; s1.managed = False
        s2 = mock.Mock(); s2.name = "sec2"; s2.managed = False
        s3 = mock.Mock(); s3.name = "mgd1"; s3.managed = True # Should be skipped
        self.source_client.list_properties_of_secrets.return_value = [s1, s2, s3]

        # Get secret details
        def get_secret_side_effect(name):
            m = mock.Mock()
            m.name = name
            m.value = "val"
            m.properties.content_type = None
            m.properties.tags = None
            m.properties.enabled = True
            m.properties.not_before = None
            m.properties.expires_on = None
            return m
        self.source_client.get_secret.side_effect = get_secret_side_effect

        new_secret = mock.Mock()
        new_secret.name = "sec"
        new_secret.id = "id"
        self.dest_client.set_secret.return_value = new_secret

        # Act
        result = copy_secret(self.cmd, self.source_client, destination_vault, all_secrets=True)

        # Assert
        self.assertEqual(len(result), 2)
        call_args = self.dest_client.set_secret.call_args_list
        self.assertEqual(call_args[0][0][0], "sec1")
        self.assertEqual(call_args[1][0][0], "sec2")

if __name__ == '__main__':
    unittest.main()
