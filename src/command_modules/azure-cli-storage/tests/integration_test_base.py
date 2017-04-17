# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from unittest import TestCase, skipIf
from datetime import datetime
from azure.cli.core.profiles import get_sdk, ResourceType

BaseBlobService, FileService = get_sdk(ResourceType.DATA_STORAGE,
                                       'blob.baseblobservice#BaseBlobService',
                                       'file.fileservice#FileService')


@skipIf(os.environ.get('Travis', 'false') == 'true', 'Integration tests are skipped in Travis CI')
class StorageIntegrationTestBase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generate_resource_files()

        cls._test_connection_string = os.environ['test_connection_string']
        assert cls._test_connection_string

        cls._blob_service = BaseBlobService(connection_string=cls._test_connection_string)
        assert cls._blob_service

        cls._file_service = FileService(connection_string=cls._test_connection_string)

        cls._test_account_key = cls._blob_service.account_key

    @classmethod
    def generate_resource_files(cls):
        cls._resource_folder = os.path.join(os.getcwd(), 'resources')
        if os.path.exists(cls._resource_folder):
            from shutil import rmtree
            rmtree(cls._resource_folder)

        os.makedirs(cls._resource_folder)

        with open(os.path.join(cls._resource_folder, 'sample_file.txt'), 'w') as f:
            f.write('storage blob test sample file')

        for folder_name in ['apple', 'butter', 'butter/charlie', 'duff/edward']:
            for file_index in range(10):
                file_path = os.path.join(cls._resource_folder, folder_name, 'file_%s' % file_index)
                if not os.path.exists(os.path.dirname(file_path)):
                    os.makedirs(os.path.dirname(file_path))
                with open(file_path, 'w') as f:
                    f.write('storage blob test sample file. origin: %s' % file_path)

    @classmethod
    def generate_new_container_name(cls):
        return 'blob-test-{}'.format(datetime.utcnow().strftime('%Y%m%d%H%M%S%f'))

    @classmethod
    def generate_new_share_name(cls):
        return 'file-test-{}'.format(datetime.utcnow().strftime('%Y%m%d%H%M%S%f'))

    @classmethod
    def _get_test_resource_file(cls, file_name):
        result = os.path.join(cls._resource_folder, file_name)
        assert os.path.exists(result)

        return result
