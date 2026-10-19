# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

from azure.cli.command_modules.storage.azcopy.util import client_auth_for_azcopy


class TestClientAuthForAzcopy(unittest.TestCase):
    def setUp(self):
        self.cmd = mock.Mock()

    def _assert_not_oauth(self, client):
        with mock.patch('azure.cli.command_modules.storage.azcopy.util.Profile') as profile_mock:
            result = client_auth_for_azcopy(self.cmd, client)
        profile_mock.assert_not_called()
        self.assertIsNone(result)

    def test_account_key_dict_credential_skips_oauth(self):
        client = mock.Mock(credential={"account_key": "fake_key"}, url="https://foo.blob.core.windows.net/c")
        self._assert_not_oauth(client)

    def test_account_key_object_credential_skips_oauth(self):
        credential = mock.Mock(spec=['account_key'], account_key='fake_key')
        client = mock.Mock(credential=credential, url="https://foo.blob.core.windows.net/c")
        self._assert_not_oauth(client)

    def test_sas_token_credential_string_skips_oauth(self):
        client = mock.Mock(credential="sv=2021-01-01&sig=abc", url="https://foo.blob.core.windows.net/c")
        self._assert_not_oauth(client)

    def test_sas_token_embedded_in_url_skips_oauth(self):
        # Reproduces #32284: azure-storage-blob SDK sets credential to None and appends the
        # SAS token to the client URL's query string instead of keeping it as client.credential.
        client = mock.Mock(
            credential=None,
            url="https://foo.blob.core.windows.net/c?sv=2021-01-01&sig=abc&se=2024-01-01")
        self._assert_not_oauth(client)

    def test_no_credential_and_no_sas_uses_oauth(self):
        client = mock.Mock(credential=None, url="https://foo.blob.core.windows.net/c")
        with mock.patch('azure.cli.command_modules.storage.azcopy.util.Profile') as profile_mock:
            profile_instance = profile_mock.return_value
            profile_instance.get_raw_token.return_value = (
                ('bearer', 'token', {'_authority': 'https://login.microsoftonline.com/tenant',
                                     'accessToken': 'token',
                                     'userId': 'user'}),
                None,
                'tenant-id',
            )
            with mock.patch(
                    'azure.cli.command_modules.storage.azcopy.util._unserialize_non_msi_token_payload',
                    return_value={'access_token': 'token'}):
                result = client_auth_for_azcopy(self.cmd, client)
        profile_instance.get_raw_token.assert_called_once()
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
