# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import tempfile
import zipfile
import tarfile
import shutil
import unittest

from azure.cli.core.extension import DevExtension
try:
    from azure.cli.core.extension.tests.latest import ExtensionTypeTestMixin, get_test_data_file
except ImportError:
    from . import ExtensionTypeTestMixin, get_test_data_file


class TestWheelTypeExtensionMetadata(ExtensionTypeTestMixin):

    def test_reading_wheel_type_extension_from_develop_mode(self):
        """
        Test develop type extension.
        For scenario that user are developing extension via azdev
        """

        source_code_packaged = get_test_data_file('hello-0.1.0.tar.gz')

        with tarfile.open(source_code_packaged, 'r:gz') as tar:
            tar.extractall(self.ext_dir)

        ext_name, ext_version = 'hello', '0.1.0'

        ext_extension = DevExtension(ext_name, os.path.join(self.ext_dir, ext_name + '-' + ext_version))
        metadata = ext_extension.get_metadata()  # able to read metadata from source code

        # assert Python metadata
        self.assertEqual(metadata['name'], ext_name)
        self.assertEqual(metadata['version'], ext_version)
        self.assertEqual(metadata['author'], 'Microsoft Corporation')
        self.assertNotIn('metadata.json', os.listdir(os.path.join(self.ext_dir, ext_name + '-' + ext_version)))

        # assert Azure CLI extended metadata
        self.assertTrue(metadata['azext.isPreview'])
        self.assertTrue(metadata['azext.isExperimental'])
        self.assertEqual(metadata['azext.minCliCoreVersion'], '2.0.67')
