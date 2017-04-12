# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from datetime import datetime, timedelta
from .integration_test_base import StorageIntegrationTestBase
from ..util import glob_files_remotely
from azure.cli.core.profiles import get_sdk, ResourceType

BlobPermissions, FilePermissions = get_sdk(ResourceType.DATA_STORAGE,
                                           'blob.models#BlobPermissions',
                                           'file.models#FilePermissions')


def _cli_main(command, *args):
    from azure.cli.main import main as azure_cli_main
    if isinstance(command, str):
        return azure_cli_main(command.split(), *args)
    elif isinstance(command, list):
        return azure_cli_main(command, *args)
    else:
        raise ValueError('command should be either string or a list')


class StorageFileCopyIntegrationTests(StorageIntegrationTestBase):
    @classmethod
    def setUpClass(cls):
        StorageIntegrationTestBase.setUpClass()

        # set up sample container
        cls._test_source_container = os.environ.get('TEST_SAMPLE_CONTAINER', None)
        if not cls._test_source_container:
            cls._test_source_container = cls.generate_new_container_name()
            assert cls._blob_service.create_container(cls._test_source_container)

            _cli_main('storage blob upload-batch -s {} -d {} --connection-string {}'
                      .format(cls._resource_folder, cls._test_source_container,
                              cls._test_connection_string))
            cls._clear_test_source_container = True
        else:
            cls._clear_test_source_container = False

        test_blobs = [b.name for b in cls._blob_service.list_blobs(cls._test_source_container)]
        assert len(test_blobs) == 41

        # set up sample file share
        cls._test_source_share = os.environ.get('TEST_SAMPLE_SHARE', None)
        if not cls._test_source_share:
            cls._test_source_share = cls.generate_new_share_name()
            assert cls._file_service.create_share(cls._test_source_share)

            _cli_main('storage file upload-batch -s {} -d {} --connection-string {}'
                      .format(cls._resource_folder, cls._test_source_share,
                              cls._test_connection_string))

            cls._clear_test_source_share = True
        else:
            cls._clear_test_source_share = False

        test_files = [f for f in glob_files_remotely(cls._file_service, cls._test_source_share,
                                                     pattern=None)]
        assert len(test_files) == 41

    @classmethod
    def tearDownClass(cls):
        if cls._clear_test_source_container:
            cls._blob_service.delete_container(cls._test_source_container)

        if cls._clear_test_source_share:
            cls._file_service.delete_share(cls._test_source_share)

    def setUp(self):
        self._test_target_share = self.generate_new_share_name()
        assert self._file_service.create_share(self._test_target_share)

    def tearDown(self):
        self._file_service.delete_share(self._test_target_share)

    def test_batch_copy_blob_with_sas(self):
        # create sas token for read permission on the source blob container
        sas_token = self._blob_service.generate_container_shared_access_signature(
            self._test_source_container,
            BlobPermissions(read=True),
            datetime.utcnow() + timedelta(minutes=15))

        cmd_template = 'storage file copy start-batch' \
                       ' --source-container {}' \
                       ' --destination-share {}' \
                       ' --account-name {}' \
                       ' --account-key {}' \
                       ' --source-sas {}'

        _cli_main(cmd_template.format(self._test_source_container,
                                      self._test_target_share,
                                      self._file_service.account_name,
                                      self._file_service.account_key,
                                      sas_token))

        files = list(glob_files_remotely(self._file_service, self._test_target_share, pattern=None))
        assert len(files) == 41

    def test_batch_copy_blob_without_sas(self):
        cmd_template = 'storage file copy start-batch' \
                       ' --source-container {}' \
                       ' --destination-share {}' \
                       ' --account-name {}' \
                       ' --account-key {}'

        _cli_main(cmd_template.format(self._test_source_container,
                                      self._test_target_share,
                                      self._file_service.account_name,
                                      self._file_service.account_key))

        files = list(glob_files_remotely(self._file_service, self._test_target_share, pattern=None))
        assert len(files) == 0

    def test_batch_copy_blob_with_pattern(self):
        # create sas token for read permission on the source blob container
        sas_token = self._blob_service.generate_container_shared_access_signature(
            self._test_source_container,
            BlobPermissions(read=True),
            datetime.utcnow() + timedelta(minutes=15))

        cmd_template = 'storage file copy start-batch' \
                       ' --source-container {}' \
                       ' --destination-share {}' \
                       ' --account-name {}' \
                       ' --account-key {}' \
                       ' --source-sas {}' \
                       ' --pattern apple/*'

        _cli_main(cmd_template.format(self._test_source_container,
                                      self._test_target_share,
                                      self._file_service.account_name,
                                      self._file_service.account_key,
                                      sas_token))

        files = list(glob_files_remotely(self._file_service, self._test_target_share, pattern=None))
        assert len(files) == 10

    def test_batch_copy_files_without_sas(self):
        cmd_template = 'storage file copy start-batch' \
                       ' --source-share {}' \
                       ' --destination-share {}' \
                       ' --account-name {}' \
                       ' --account-key {}'

        _cli_main(cmd_template.format(self._test_source_share,
                                      self._test_target_share,
                                      self._file_service.account_name,
                                      self._file_service.account_key))

        files = list(glob_files_remotely(self._file_service, self._test_target_share, pattern=None))
        assert len(files) == 41

    def test_batch_copy_files_with_sas(self):
        sas = self._create_read_sas(self._file_service, share=self._test_source_share)
        cmd_template = 'storage file copy start-batch' \
                       ' --source-share {}' \
                       ' --destination-share {}' \
                       ' --account-name {}' \
                       ' --account-key {}' \
                       ' --source-sas {}'

        _cli_main(cmd_template.format(self._test_source_share,
                                      self._test_target_share,
                                      self._file_service.account_name,
                                      self._file_service.account_key,
                                      sas))

        files = list(glob_files_remotely(self._file_service, self._test_target_share, pattern=None))
        assert len(files) == 41

    @classmethod
    def _create_read_sas(cls, client, share=None, container=None):
        if (share and container) or (not share and not container):
            raise ValueError('set either share or container')

        if share:
            return client.generate_share_shared_access_signature(
                share,
                FilePermissions(read=True),
                datetime.utcnow() + timedelta(minutes=15))
        elif container:
            return client.generate_container_shared_access_signature(
                container,
                BlobPermissions(read=True),
                datetime.utcnow() + timedelta(minutes=15))
