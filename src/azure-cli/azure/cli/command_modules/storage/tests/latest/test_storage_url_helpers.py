# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from knack import CLI
from knack.util import CLIError

from azure.cli.core._config import GLOBAL_CONFIG_DIR, ENV_VAR_PREFIX
from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.core.cloud import get_active_cloud

from azure.cli.command_modules.storage._client_factory import get_account_url
from azure.cli.command_modules.storage.storage_url_helpers import StorageResourceIdentifier, is_valid_hostname_label


class MockCLI(CLI):
    def __init__(self):
        super().__init__(cli_name='mock_cli', config_dir=GLOBAL_CONFIG_DIR,
                         config_env_var_prefix=ENV_VAR_PREFIX)
        self.cloud = get_active_cloud(self)


class TestStorageUrlHelpers(unittest.TestCase):
    def setUp(self):
        self.cli = MockCLI()

    def test_is_url(self):
        def _check_is_url(moniker, expectation):
            assert StorageResourceIdentifier(self.cli.cloud, moniker).is_url() == expectation

        _check_is_url('sample', False)
        _check_is_url('http://test.blob.core.windows.net/cont', True)
        _check_is_url('https://test.blob.core.windows.net/cont', True)
        _check_is_url('https://test.file.core.windows.net/cont', True)

    def test_container_parsing(self):
        def _test(moniker, expected_container=None, expected_blob=None, expected_snapshot=None):
            i = StorageResourceIdentifier(self.cli.cloud, moniker)

            if expected_container is not None:
                assert i.container == expected_container
                assert i.share is None
                assert i.directory is None
                assert i.filename is None
            else:
                assert i.container is None

            assert i.blob == expected_blob
            assert i.snapshot == expected_snapshot

        _test('sample')
        _test('https://momba.file.core.windows.net/snake')
        _test('http://momba.else.core.windows.net/snake')
        _test('http://momba.blob.core.windows.net/snake', 'snake')
        _test('https://momba.blob.core.windows.net/snake', 'snake')
        _test('https://momba.blob.core.windows.net/snake/blob', 'snake', 'blob')
        _test('https://momba.blob.core.windows.net/snake/blob/blob2', 'snake', 'blob/blob2')
        _test('https://momba.blob.core.windows.net/snake/blob?some=thing', 'snake', 'blob')

    def test_share_parsing(self):
        def _test(moniker, expected_share=None, expected_dir=None, expected_file=None):
            i = StorageResourceIdentifier(self.cli.cloud, moniker)

            if expected_share is not None:
                assert i.container is None
                assert i.blob is None
                assert i.snapshot is None
                assert i.share == expected_share
            else:
                assert i.share is None

            assert i.directory == expected_dir
            assert i.filename == expected_file

        _test('sample')
        _test('https://momba.blob.core.windows.net/snake')
        _test('http://momba.blob.core.windows.net/snake')
        _test('http://momba.else.core.windows.net/snake')
        _test('http://momba.file.core.windows.net/snake/d/f.txt', 'snake', 'd', 'f.txt')
        _test('http://momba.file.core.windows.net/snake/f.txt', 'snake', '', 'f.txt')
        _test('http://momba.file.core.windows.net/snake/d/e/f.txt', 'snake', 'd/e', 'f.txt')
        _test('http://momba.file.core.windows.net/snake/d/e/f.txt?s=t', 'snake', 'd/e', 'f.txt')

    def test_account_name(self):
        def _test(moniker, expected_account=None):
            i = StorageResourceIdentifier(self.cli.cloud, moniker)
            assert i.account_name == expected_account

        _test('sample')
        _test('https://momba.else.core.windows.net/snake')
        _test('https://momba.blob.core.windows.net/snake', 'momba')
        _test('http://momba.file.core.windows.net/snake', 'momba')
        _test('http://momba.file.core.windows.net/snake/d/e/f.txt?s=t', 'momba')
        _test('https://MomBa.blob.core.windows.net/snake', 'MomBa')
        _test('https://momba.BLOB.Core.Windows.Net/snake', 'momba')
        _test('https://momba.blob.core.windows.net:443/snake', 'momba')
        _test('https://user:pass@MomBa.blob.core.windows.net/snake', 'MomBa')
        # non-ASCII characters that lowercase to ASCII must not leak into the account name
        _test('https://\u212amomba.blob.core.windows.net/snake', 'kmomba')

    def test_unrecognized_hosts(self):
        monikers = [
            # backslash: urllib3/requests end the host at '\', so the request would go to 2130706433:8443
            'https://2130706433:8443\\.file.core.windows.net/myshare',
            'https://evil.example\\.file.core.windows.net/x',
            'https://evil.example\\.blob.core.windows.net/x/y',
            # host does not end with the storage endpoint suffix
            'https://momba.blob.core.windows.net.evil.example/snake',
            'https://momba.blob.evil.example/snake',
            'https://momba.blobcore.windows.net/snake',
            'https://blob.core.windows.net/snake',
            'https://.blob.core.windows.net/snake',
            # account name is not a single hostname label
            'https://evil.example.blob.core.windows.net/snake',
            'https://ev_il.blob.core.windows.net/snake',
            'https://evil%2Fx.blob.core.windows.net/snake',
            # port and userinfo pointing somewhere else
            'https://evil.example:443.blob.core.windows.net/snake',
            'https://momba.blob.core.windows.net:443@evil.example/snake',
            'https://momba.blob.core.windows.net@evil.example/snake',
            'https://user@evil.example/momba.blob.core.windows.net/snake',
        ]
        for moniker in monikers:
            with self.subTest(moniker=moniker):
                i = StorageResourceIdentifier(self.cli.cloud, moniker)
                self.assertTrue(i.is_url())
                self.assertIsNone(i.account_name)
                self.assertIsNone(i.container)
                self.assertIsNone(i.blob)
                self.assertIsNone(i.share)
                self.assertIsNone(i.directory)
                self.assertIsNone(i.filename)

    def test_unrecognized_host_keeps_query_handling(self):
        i = StorageResourceIdentifier(self.cli.cloud, 'https://evil.example\\.file.core.windows.net/x?sig=abc')
        self.assertIsNone(i.account_name)
        self.assertEqual(i.sas_token, 'sig=abc')

    def test_default_value(self):
        i = StorageResourceIdentifier(self.cli.cloud, '')
        assert not i.is_url()
        assert not i.is_valid
        assert i.account_name is None
        assert i.container is None
        assert i.blob is None
        assert i.share is None
        assert i.directory is None
        assert i.filename is None

    def test_get_sas_token(self):
        def _test(moniker, expected_sas=None):
            i = StorageResourceIdentifier(self.cli.cloud, moniker)
            assert i.sas_token == expected_sas

        _test('https://momba.blob.core.windows.net/blob?sv=2015-04-05&ss=bfqt&srt=sco&sp=rwdlacup&se='
              '2016-12-05T23:02:02Z&st=2016-12-05T15:02:02Z&spr=https&sig=e0xYWg%2F142F5uUsPBflsUVQqL'
              '33Pr0v3Fs5VIjsUL6A%3D',
              'sv=2015-04-05&ss=bfqt&srt=sco&sp=rwdlacup&se=2016-12-05T23:02:02Z&st=2016-12-05T15:02:'
              '02Z&spr=https&sig=e0xYWg%2F142F5uUsPBflsUVQqL33Pr0v3Fs5VIjsUL6A%3D')

        _test('https://momba.blob.core.windows.net/blob?sv=2015-04-05&ss=bfqt&srt=sco&sp=rwdlacup&se='
              '2016-12-05T23:02:02Z&st=2016-12-05T15:02:02Z&spr=https&sig=e0xYWg%2F142F5uUsPBflsUVQqL'
              '33Pr0v3Fs5VIjsUL6A%3D&snapshot=2016-12-05T23:12:03.1181304Z',
              'sv=2015-04-05&ss=bfqt&srt=sco&sp=rwdlacup&se=2016-12-05T23:02:02Z&st=2016-12-05T15:02:'
              '02Z&spr=https&sig=e0xYWg%2F142F5uUsPBflsUVQqL33Pr0v3Fs5VIjsUL6A%3D')


class TestHostnameLabelValidation(unittest.TestCase):
    def setUp(self):
        self.cli = MockCLI()

    def test_is_valid_hostname_label(self):
        for name in ('a', 'momba', 'MyAccount', 'my-account', 'momba-secondary', 'a' * 63, '123'):
            with self.subTest(name=name):
                self.assertTrue(is_valid_hostname_label(name))
        for name in (None, '', 'a' * 64, 'evil.example', 'evil/x', 'evil?', 'evil#', 'user@evil', 'evil:443',
                     'evil\\x', 'ev il', ' momba', 'momba\n', 'ev_il', '\u00e9vil', 123):
            with self.subTest(name=name):
                self.assertFalse(is_valid_hostname_label(name))

    def test_get_account_url(self):
        endpoint = self.cli.cloud.suffixes.storage_endpoint
        self.assertEqual(get_account_url(self.cli, 'momba', 'blob'), 'https://momba.blob.{}'.format(endpoint))
        self.assertEqual(get_account_url(self.cli, 'MyAccount', 'file'), 'https://MyAccount.file.{}'.format(endpoint))
        self.assertEqual(get_account_url(self.cli, 'momba-secondary', 'dfs'),
                         'https://momba-secondary.dfs.{}'.format(endpoint))

    def test_get_account_url_rejects_invalid_account_names(self):
        for name in ('evil.example/x?', 'evil.example', 'evil/x', 'evil?x', 'evil#x', 'user@evil', 'evil:443',
                     'evil\\x', 'ev il', '', ' '):
            with self.subTest(name=name):
                with self.assertRaisesRegex(InvalidArgumentValueError, 'Invalid storage account name'):
                    get_account_url(self.cli, name, 'file')

    def test_get_account_url_requires_account_name(self):
        with self.assertRaisesRegex(CLIError, 'Please provide storage account name'):
            get_account_url(self.cli, None, 'blob')

    def test_get_account_url_does_not_echo_invalid_account_name(self):
        name = 'https://myaccount.blob.core.windows.net/?sv=2025&sig=topsecret'
        with self.assertRaises(InvalidArgumentValueError) as ctx:
            get_account_url(self.cli, name, 'blob')
        self.assertNotIn('topsecret', str(ctx.exception))
