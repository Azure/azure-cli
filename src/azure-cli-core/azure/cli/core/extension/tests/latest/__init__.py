# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
import tempfile
import shutil
from unittest import mock


def get_test_data_file(filename):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', filename)


class ExtensionTypeTestMixin(unittest.TestCase):

    def setUp(self):
        self.ext_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.ext_dir, ignore_errors=True)


class IndexPatch:
    def __init__(self, data=None):
        self.patcher = mock.patch('azure.cli.core.extension._resolve.get_index_extensions', return_value=data)

    def __enter__(self):
        self.patcher.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.patcher.stop()


def mock_ext(filename, version=None, download_url=None, digest=None, project_url=None):
    d = {
        'filename': filename,
        'metadata': {
            'version': version,
            'extensions': {
                'python.details': {
                    'project_urls': {
                        'Home': project_url or 'https://github.com/azure/some-extension'
                    }
                }
            }
        },
        'downloadUrl': download_url or 'http://contoso.com/{}'.format(filename),
        'sha256Digest': digest
    }
    return d
