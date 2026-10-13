import unittest
from argparse import Namespace
from unittest import mock

from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.command_modules.storage import _validators
from azure.cli.command_modules.storage.operations import blob


class StorageBlobSourceOAuthTests(unittest.TestCase):
    def setUp(self):
        self.cmd = mock.MagicMock()
        self.cmd.cli_ctx.cloud.suffixes.storage_endpoint = 'core.windows.net'
        self.cmd.cli_ctx.cloud.endpoints.storage_resource_id = 'https://storage.azure.com/'
        self.namespace = Namespace(
            account_name='destination', source_account_name='source',
            source_container='states', source_blob='folder/state file.tfstate',
            token_credential=mock.Mock(), source_auth_mode='login', requires_sync=True)

    @mock.patch.object(_validators, 'validate_client_parameters')
    @mock.patch.object(_validators, 'cf_blob_service')
    @mock.patch.object(_validators, '_query_account_key')
    def test_named_source_uses_no_account_key_or_delegation_sas(self, query_key, source_client, validate_client):
        with mock.patch('azure.cli.command_modules.storage.util.create_short_lived_blob_sas_v2') as sas:
            _validators.validate_source_url(self.cmd, self.namespace)
        self.assertEqual(self.namespace.source_url,
                         'https://source.blob.core.windows.net/states/folder/state%20file.tfstate')
        query_key.assert_not_called()
        source_client.assert_not_called()
        sas.assert_not_called()
        validate_client.assert_called_once()

    def test_source_login_rejects_unsupported_combinations(self):
        for changes in (
                {'requires_sync': False}, {'token_credential': None},
                {'source_url': 'https://untrusted.example/blob'}, {'source_sas': 'sig=value'},
                {'source_account_key': 'key'}, {'destination_blob_type': 'BlockBlob'},
                {'source_account_name': 'source.blob.core.windows.net@untrusted.example'},
                {'source_share': 'share', 'source_path': 'file'}):
            with self.subTest(changes=changes):
                namespace = Namespace(**{**vars(self.namespace), **changes})
                with self.assertRaises(InvalidArgumentValueError):
                    _validators.validate_source_url(self.cmd, namespace)

    @mock.patch.object(_validators, 'validate_client_parameters')
    @mock.patch.object(_validators, 'cf_blob_service')
    def test_default_source_login_preserves_delegation_sas(self, source_client, validate_client):
        self.namespace.source_auth_mode = None
        with mock.patch('azure.cli.command_modules.storage.util.create_short_lived_blob_sas_v2',
                        return_value='sig=test') as sas:
            _validators.validate_source_url(self.cmd, self.namespace)
        source_client.return_value.get_user_delegation_key.assert_called_once()
        sas.assert_called_once()
        self.assertTrue(self.namespace.source_url.endswith('?sig=test'))

    @mock.patch.object(_validators, 'validate_client_parameters')
    def test_source_login_uses_cloud_endpoint_and_same_account_default(self, validate_client):
        self.namespace.source_account_name = None
        self.namespace.source_snapshot = 'snapshot-value'
        self.cmd.cli_ctx.cloud.suffixes.storage_endpoint = 'core.usgovcloudapi.net'
        _validators.validate_source_url(self.cmd, self.namespace)
        self.assertEqual(self.namespace.source_url,
                         'https://destination.blob.core.usgovcloudapi.net/states/'
                         'folder/state%20file.tfstate?snapshot=snapshot-value')

    def test_synchronous_copy_passes_source_bearer_token(self):
        client = mock.MagicMock()
        client.url = 'https://destination.blob.core.windows.net/backups/state.tfstate'
        client.credential.get_token.return_value.token = 'test-token'
        source_url = 'https://source.blob.core.windows.net/states/state.tfstate'
        blob.copy_blob(self.cmd, client, source_url, source_auth_mode='login', requires_sync=True)
        client.credential.get_token.assert_called_once_with('https://storage.azure.com/.default')
        client.start_copy_from_url.assert_called_once_with(
            source_url=source_url, metadata=None, incremental_copy=False,
            requires_sync=True, source_authorization='Bearer test-token')

    def test_source_login_uses_cloud_token_scope(self):
        self.cmd.cli_ctx.cloud.endpoints.storage_resource_id = 'https://storage.azure.us/'
        client = mock.MagicMock()
        client.url = 'https://destination.blob.core.usgovcloudapi.net/container/example.txt'
        client.credential.get_token.return_value.token = 'test-token'
        blob.copy_blob(self.cmd, client,
                       'https://source.blob.core.usgovcloudapi.net/container/example.txt',
                       source_auth_mode='login', requires_sync=True)
        client.credential.get_token.assert_called_once_with('https://storage.azure.us/.default')

    def test_default_copy_does_not_request_source_bearer_token(self):
        client = mock.MagicMock()
        client.url = 'https://destination.blob.core.windows.net/container/example.txt'
        source_url = 'https://source.blob.core.windows.net/container/example.txt?sig=test'
        blob.copy_blob(self.cmd, client, source_url, source_auth_mode=None, requires_sync=False)
        client.credential.get_token.assert_not_called()
        client.start_copy_from_url.assert_called_once_with(
            source_url=source_url, metadata=None, incremental_copy=False)


if __name__ == '__main__':
    unittest.main()