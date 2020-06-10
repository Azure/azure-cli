# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from knack import CLI

from azure.cli.core._config import GLOBAL_CONFIG_DIR, ENV_VAR_PREFIX
from azure.cli.core.cloud import get_active_cloud

from azure.cli.command_modules.storage.storage_url_helpers import StorageResourceIdentifier


class MockCLI(CLI):
    def __init__(self):
        super(MockCLI, self).__init__(cli_name='mock_cli', config_dir=GLOBAL_CONFIG_DIR,
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
