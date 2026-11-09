# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.command_modules.storage.operations.blob import incremental_copy_start
from azure.storage.blob import BlobClient

START = 'azure.cli.command_modules.storage.aaz.latest.storage.blob.incremental_copy.Start'


class TestStorageBlobIncrementalCopy(unittest.TestCase):

    @staticmethod
    def _client(account_url):
        return BlobClient(account_url, container_name='container', blob_name='blob', credential=None)

    def test_rejects_account_names_that_change_the_request_host(self):
        for account_url in ('https://evil.example\\x.blob.core.windows.net',
                            'https://a@evil.example:1.blob.core.example.test',
                            'https://evil.example%2Fx.blob.core.example.test',
                            'https://custom.example.test'):
            with self.subTest(account_url=account_url):
                with mock.patch(START) as start, \
                        self.assertRaisesRegex(InvalidArgumentValueError, 'valid storage account name'):
                    incremental_copy_start(self._client(account_url), mock.Mock(),
                                           copy_source='https://src.blob.core.windows.net/c/b?snapshot=1')
                start.assert_not_called()

    def test_error_does_not_include_credentials(self):
        for account_url, credential in (('https://evil.example\\x.blob.core.windows.net', 'sig=secret'),
                                        ('https://user:secret@myaccount.blob.core.windows.net', None)):
            with self.subTest(account_url=account_url):
                client = BlobClient(account_url, container_name='container', blob_name='blob', credential=credential)
                with mock.patch(START) as start, self.assertRaises(InvalidArgumentValueError) as ctx:
                    incremental_copy_start(client, mock.Mock(), copy_source='https://src.blob.core.windows.net/c/b')
                start.assert_not_called()
                self.assertNotIn('secret', str(ctx.exception))
                self.assertNotIn('secret', str(ctx.exception.recommendations))

    def test_passes_valid_account_name_to_request(self):
        for account_url, account_name in (('https://myaccount.blob.core.windows.net', 'myaccount'),
                                          ('https://MyAccount.blob.core.windows.net', 'MyAccount')):
            with self.subTest(account_url=account_url):
                with mock.patch(START) as start:
                    start.return_value.ctx.vars._output = {'status': 'pending'}
                    result = incremental_copy_start(self._client(account_url), mock.Mock(),
                                                    copy_source='https://src.blob.core.windows.net/c/b?snapshot=1')
                self.assertEqual(result, {'status': 'pending'})
                command_args = start.return_value.call_args.kwargs['command_args']
                self.assertEqual(command_args['account_name'], account_name)
                self.assertEqual(command_args['destination_container'], 'container')
                self.assertEqual(command_args['destination_blob'], 'blob')


if __name__ == '__main__':
    unittest.main()
