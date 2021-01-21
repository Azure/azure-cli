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

from azure.cli.core.extension import WheelExtension
try:
    from azure.cli.core.extension.tests.latest import ExtensionTypeTestMixin, get_test_data_file
except ImportError:
    from . import ExtensionTypeTestMixin, get_test_data_file


class TestWheelTypeExtensionMetadata(ExtensionTypeTestMixin):

    def test_reading_wheel_type_0_30_0_extension_metadata(self):
        """
        Test wheel==0.30.0 containing metadata.json and we can handle it properly.
        For scenario like 'az extenion add'.
        """

        # this wheel contains metadata.json and METADATA
        wheel_0_30_0_packed = get_test_data_file('wheel_0_30_0_packed_extension-0.1.0-py3-none-any.whl')

        zf = zipfile.ZipFile(wheel_0_30_0_packed)
        zf.extractall(self.ext_dir)

        ext_name, ext_version = 'hello', '0.1.0'

        whl_extension = WheelExtension(ext_name, self.ext_dir)
        metadata = whl_extension.get_metadata()  # able to read metadata from wheel==0.30.0 built extension

        # wheel type extension generates .dist-info
        dist_info = ext_name + '-' + ext_version + '.dist-info'

        # assert Python metadata
        self.assertEqual(metadata['name'], ext_name)
        self.assertEqual(metadata['version'], ext_version)
        self.assertEqual(metadata['author'], 'Microsoft Corporation')
        self.assertIn('metadata.json', os.listdir(os.path.join(self.ext_dir, dist_info)))

        # assert Azure CLI extended metadata
        self.assertTrue(metadata['azext.isPreview'])
        self.assertTrue(metadata['azext.isExperimental'])
        self.assertEqual(metadata['azext.minCliCoreVersion'], '2.0.67')

    def test_reading_wheel_type_0_31_0_extension_metadata(self):
        """
        Test wheel>=0.31.0 not containing metadata.json but we can still handle it properly.
        For scenario like 'az extenion add'.
        """

        # this wheel contains METADATA only
        wheel_0_31_0_packed = get_test_data_file('wheel_0_31_0_packed_extension-0.1.0-py3-none-any.whl')

        zf = zipfile.ZipFile(wheel_0_31_0_packed)
        zf.extractall(self.ext_dir)

        ext_name, ext_version = 'hello', '0.1.0'

        whl_extension = WheelExtension(ext_name, self.ext_dir)
        metadata = whl_extension.get_metadata()  # able to read metadata from wheel==0.30.0 built extension

        # wheel type extension generates .dist-info
        dist_info = ext_name + '-' + ext_version + '.dist-info'

        # assert Python metadata
        self.assertEqual(metadata['name'], ext_name)
        self.assertEqual(metadata['version'], ext_version)
        self.assertEqual(metadata['author'], 'Microsoft Corporation')
        self.assertNotIn('metadata.json', os.listdir(os.path.join(self.ext_dir, dist_info)))

        # assert Azure CLI extended metadata
        self.assertTrue(metadata['azext.isPreview'])
        self.assertTrue(metadata['azext.isExperimental'])
        self.assertEqual(metadata['azext.minCliCoreVersion'], '2.0.67')

    def test_reading_wheel_type_extension_from_develop_mode(self):
        """
        Test wheel type extension but installing from source code.
        For scenario that user are developing extension via 'pip install -e' directlly
        and load it from _CUSTOM_EXT_DIR or GLOBAL_CONFIG_DIR
        """

        source_code_packaged = get_test_data_file('hello-0.1.0.tar.gz')

        with tarfile.open(source_code_packaged, 'r:gz') as tar:
            tar.extractall(self.ext_dir)

        ext_name, ext_version = 'hello', '0.1.0'

        ext_extension = WheelExtension(ext_name, os.path.join(self.ext_dir, ext_name + '-' + ext_version))
        metadata = ext_extension.get_metadata()  # able to read metadata from source code even in wheel type extension

        # assert Python metadata
        self.assertEqual(metadata['name'], ext_name)
        self.assertEqual(metadata['version'], ext_version)
        self.assertEqual(metadata['author'], 'Microsoft Corporation')
        self.assertNotIn('metadata.json', os.listdir(os.path.join(self.ext_dir, ext_name + '-' + ext_version)))

        # assert Azure CLI extended metadata
        self.assertTrue(metadata['azext.isPreview'])
        self.assertTrue(metadata['azext.isExperimental'])
        self.assertEqual(metadata['azext.minCliCoreVersion'], '2.0.67')
