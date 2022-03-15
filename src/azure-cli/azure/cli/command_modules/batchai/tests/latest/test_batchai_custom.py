# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import collections
import unittest
from contextlib import contextmanager

import os
# noinspection PyProtectedMember
from azure.cli.command_modules.batchai.custom import (
    _patch_mount_volumes,
    _update_nodes_information,
    _update_user_account_settings,
    _add_azure_container_to_mount_volumes,
    _add_azure_file_share_to_mount_volumes,
    _add_nfs_to_mount_volumes,
    _is_on_mount_point,
    _ensure_subnet_is_valid,
    _get_image_reference,
    _list_node_setup_files_for_cluster,
    _generate_auto_storage_account_name,
    _add_setup_task,
    _get_effective_resource_parameters)
from azure.cli.core.util import CLIError
from azure.cli.core.mock import DummyCli
from azure.mgmt.batchai.models import (
    Cluster, ClusterCreateParameters, UserAccountSettings, MountVolumes, NodeSetup, FileServer,
    FileServerCreateParameters, AzureFileShareReference, AzureBlobFileSystemReference, AzureStorageCredentialsInfo,
    SshConfiguration, ImageReference, ScaleSettings, ManualScaleSettings, AutoScaleSettings, ResourceId, SetupTask
)
# Some valid ssh public key value.
from unittest.mock import MagicMock, patch

SSH_KEY = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDKUDnWeK6rx36apNE9ij1iAXn68FKXLTW0009XK/7dyMewlNfXi6Z2opnxHDD' \
          'YWucMluU0dsvBR22OuYH2RHriPJTi1jN3aZ0zZSrlH/W4MSNQKlG/AnrjJPA3xfYjIKLGuKBqSIvMsmrkuDfIfMaDnPcxb+GzM1' \
          '0L5epRhoP5FwqaQbLqp640YzFSLqMChz7E6RG54CpEm+MRvA7lj9nD9AlYnfRQAKj2thsFrkz7AlYLQ1ug8vV+1Y3xSKDbo5vy6' \
          'oqM3QKeLiUiyN9Ff1Rq4uYnrqJqcWN1ADfiPGZZjEStOkRgG3V6JrpIN+z0Zl3n+sjrH+CKwrYmyni6D41L'


@contextmanager
def _given_env_variable(name, value):
    os.environ[name] = value
    try:
        yield
    finally:
        os.environ.pop(name, None)


def _get_mock_storage_accounts_and_keys(accounts_and_keys):
    """Creates a mock storage client which knows about given storage accounts and keys"""
    Endpoints = collections.namedtuple('Endpoints', 'file')
    Account = collections.namedtuple('Account', 'id name primary_endpoints')
    mock_storage_client = MagicMock()
    mock_storage_client.storage_accounts.list = MagicMock(
        return_value=[Account(
            '/subscriptions/000/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/{0}'.format(a),
            a, Endpoints('https://{0}.file.core.windows.net/'.format(a)))
            for a in accounts_and_keys.keys()])
    Keys = collections.namedtuple('Keys', 'keys')
    Key = collections.namedtuple('Key', 'value')
    mock_storage_client.storage_accounts.list_keys = MagicMock(
        side_effect=lambda _, account: Keys([Key(accounts_and_keys.get(account, None))]))
    return mock_storage_client


def _data_file(filename):
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', filename)
    return path.replace('\\', '\\\\')


class TestBatchAICustom(unittest.TestCase):

    def test_batchai_update_cluster_user_account_settings_using_config(self):
        params = ClusterCreateParameters(
            vm_size=None,
            user_account_settings=UserAccountSettings(
                admin_user_name='name',
                admin_user_password='password'))
        actual = _update_user_account_settings(params, None, None, None)
        self.assertEqual(params, actual)

    def test_batchai_update_cluster_user_account_settings_using_command_line(self):
        params = ClusterCreateParameters(vm_size=None, user_account_settings=None)
        actual = _update_user_account_settings(params, 'name', SSH_KEY, 'password')
        self.assertEqual(actual.user_account_settings,
                         UserAccountSettings(
                             admin_user_name='name',
                             admin_user_ssh_public_key=SSH_KEY,
                             admin_user_password='password'))

    def test_batchai_update_cluster_user_account_settings_using_command_line_overriding_config(self):
        params = ClusterCreateParameters(
            vm_size=None,
            user_account_settings=UserAccountSettings(
                admin_user_name='old_name',
                admin_user_ssh_public_key='old key',
                admin_user_password='old_password'))
        actual = _update_user_account_settings(params, 'name', SSH_KEY, 'password')
        self.assertEqual(actual.user_account_settings,
                         UserAccountSettings(
                             admin_user_name='name',
                             admin_user_ssh_public_key=SSH_KEY,
                             admin_user_password='password'))

    def test_batchai_update_cluster_user_account_settings_using_command_line_when_key_is_path(self):
        params = ClusterCreateParameters(vm_size=None, user_account_settings=None)
        actual = _update_user_account_settings(params, 'user', _data_file('key.txt'), None)
        self.assertEqual(actual.user_account_settings,
                         UserAccountSettings(
                             admin_user_name='user',
                             admin_user_ssh_public_key=SSH_KEY))

    def test_batchai_update_cluster_user_account_settings_using_command_line_when_key_is_wrong(self):
        params = ClusterCreateParameters(vm_size=None, user_account_settings=None)
        with self.assertRaisesRegex(CLIError, 'Incorrect ssh public key value'):
            _update_user_account_settings(params, 'user', 'my key', None)

    @patch('getpass.getuser')
    def test_batchai_update_cluster_user_account_settings_using_current_user(self, getuser):
        getuser.return_value = 'current_user'
        params = ClusterCreateParameters(vm_size=None, user_account_settings=None)
        actual = _update_user_account_settings(params, None, None, 'password')
        self.assertEqual(actual.user_account_settings,
                         UserAccountSettings(
                             admin_user_name='current_user',
                             admin_user_password='password'))

    @patch('getpass.getuser')
    @patch('azure.cli.command_modules.batchai.custom._get_default_ssh_public_key_location')
    def test_batchai_update_cluster_user_account_settings_using_current_user_and_default_ssh_key(
            self, get_default_ssh_public_key_location, getuser):
        get_default_ssh_public_key_location.return_value = _data_file('key.txt')
        getuser.return_value = 'current_user'
        params = ClusterCreateParameters(vm_size=None, user_account_settings=None)
        actual = _update_user_account_settings(params, None, None, None)
        self.assertEqual(actual.user_account_settings,
                         UserAccountSettings(
                             admin_user_name='current_user',
                             admin_user_ssh_public_key=SSH_KEY))

    def test_batchai_update_file_server_user_account_settings_using_config(self):
        params = FileServerCreateParameters(
            vm_size=None,
            data_disks=None,
            ssh_configuration=SshConfiguration(
                user_account_settings=UserAccountSettings(
                    admin_user_name='name', admin_user_password='password')))
        actual = _update_user_account_settings(params, None, None, None)
        self.assertEqual(params, actual)

    def test_batchai_update_file_server_user_account_settings_using_command_line(self):
        params = FileServerCreateParameters(vm_size=None, data_disks=None, ssh_configuration=None)
        actual = _update_user_account_settings(params, 'name', SSH_KEY, 'password')
        self.assertEqual(actual.ssh_configuration.user_account_settings,
                         UserAccountSettings(
                             admin_user_name='name',
                             admin_user_ssh_public_key=SSH_KEY,
                             admin_user_password='password'))

    def test_batchai_update_file_server_user_account_settings_using_command_line_overriding_config(self):
        params = FileServerCreateParameters(
            vm_size=None,
            data_disks=None,
            ssh_configuration=SshConfiguration(
                user_account_settings=UserAccountSettings(
                    admin_user_name='old_name',
                    admin_user_ssh_public_key='old_key',
                    admin_user_password='old_password')))
        actual = _update_user_account_settings(params, 'name', SSH_KEY, 'password')
        self.assertEqual(actual.ssh_configuration.user_account_settings,
                         UserAccountSettings(
                             admin_user_name='name',
                             admin_user_ssh_public_key=SSH_KEY,
                             admin_user_password='password'))

    def test_batchai_update_file_server_user_account_settings_using_command_line_when_key_is_path(self):
        params = FileServerCreateParameters(vm_size=None, data_disks=None, ssh_configuration=None)
        actual = _update_user_account_settings(params, 'user', _data_file('key.txt'), None)
        self.assertEqual(actual.ssh_configuration.user_account_settings,
                         UserAccountSettings(
                             admin_user_name='user',
                             admin_user_ssh_public_key=SSH_KEY))

    def test_batchai_update_fileserver_user_account_settings_using_command_line_when_key_is_wrong(self):
        params = FileServerCreateParameters(vm_size=None, data_disks=None, ssh_configuration=None)
        with self.assertRaisesRegex(CLIError, 'Incorrect ssh public key value'):
            _update_user_account_settings(params, 'user', 'my key', None)

    @patch('getpass.getuser')
    def test_batchai_update_file_server_user_account_settings_using_current_user(self, getuser):
        getuser.return_value = 'current_user'
        params = FileServerCreateParameters(vm_size=None, data_disks=None, ssh_configuration=None)
        actual = _update_user_account_settings(params, None, None, 'password')
        self.assertEqual(actual.ssh_configuration.user_account_settings,
                         UserAccountSettings(
                             admin_user_name='current_user',
                             admin_user_password='password'))

    @patch('getpass.getuser')
    @patch('azure.cli.command_modules.batchai.custom._get_default_ssh_public_key_location')
    def test_batchai_update_file_server_user_account_settings_using_current_user_and_default_ssh_key(
            self, get_default_ssh_public_key_location, getuser):
        get_default_ssh_public_key_location.return_value = _data_file('key.txt')
        getuser.return_value = 'current_user'
        params = FileServerCreateParameters(vm_size=None, data_disks=None, ssh_configuration=None)
        actual = _update_user_account_settings(params, None, None, None)
        self.assertEqual(actual.ssh_configuration.user_account_settings,
                         UserAccountSettings(
                             admin_user_name='current_user',
                             admin_user_ssh_public_key=SSH_KEY))

    def test_batchai_patch_mount_volumes_no_volumes(self):
        self.assertIsNone(_patch_mount_volumes(DummyCli(), None))

    def test_batchai_patch_mount_volumes_empty_volumes(self):
        self.assertEqual(MountVolumes(), _patch_mount_volumes(DummyCli(), MountVolumes()))

    def test_batchai_patch_mount_volumes_with_templates_via_command_line_args(self):
        # noinspection PyTypeChecker
        mount_volumes = MountVolumes(
            azure_file_shares=[
                AzureFileShareReference(
                    relative_mount_path='azfiles',
                    account_name='<AZURE_BATCHAI_STORAGE_ACCOUNT>',
                    azure_file_url='https://<AZURE_BATCHAI_STORAGE_ACCOUNT>.file.core.windows.net/share',
                    credentials=AzureStorageCredentialsInfo(account_key='<AZURE_BATCHAI_STORAGE_KEY>')
                ),
                AzureFileShareReference(
                    relative_mount_path='azfiles2',
                    account_name=None,
                    azure_file_url='https://<AZURE_BATCHAI_STORAGE_ACCOUNT>.file.core.windows.net/share2',
                    credentials=None
                )
            ],
            azure_blob_file_systems=[
                AzureBlobFileSystemReference(
                    relative_mount_path='blobfs',
                    container_name='container',
                    account_name='<AZURE_BATCHAI_STORAGE_ACCOUNT>',
                    credentials=AzureStorageCredentialsInfo(account_key='<AZURE_BATCHAI_STORAGE_KEY>')
                ),
                AzureBlobFileSystemReference(
                    relative_mount_path='blobfs2',
                    container_name='container2',
                    account_name='<AZURE_BATCHAI_STORAGE_ACCOUNT>',
                    credentials=None
                ),
            ]
        )
        actual = _patch_mount_volumes(DummyCli(), mount_volumes, 'account', 'key')
        expected = MountVolumes(
            azure_file_shares=[
                AzureFileShareReference(
                    relative_mount_path='azfiles',
                    account_name='account',
                    azure_file_url='https://account.file.core.windows.net/share',
                    credentials=AzureStorageCredentialsInfo(account_key='key')
                ),
                AzureFileShareReference(
                    relative_mount_path='azfiles2',
                    account_name='account',
                    azure_file_url='https://account.file.core.windows.net/share2',
                    credentials=AzureStorageCredentialsInfo(account_key='key')
                ),
            ],
            azure_blob_file_systems=[
                AzureBlobFileSystemReference(
                    relative_mount_path='blobfs',
                    container_name='container',
                    account_name='account',
                    credentials=AzureStorageCredentialsInfo(account_key='key')
                ),
                AzureBlobFileSystemReference(
                    relative_mount_path='blobfs2',
                    container_name='container2',
                    account_name='account',
                    credentials=AzureStorageCredentialsInfo(account_key='key')
                )
            ]
        )
        self.assertEqual(expected, actual)

    def test_batchai_patch_mount_volumes_with_templates_via_env_variables(self):
        # noinspection PyTypeChecker
        mount_volumes = MountVolumes(
            azure_file_shares=[
                AzureFileShareReference(
                    relative_mount_path='azfiles',
                    account_name='<AZURE_BATCHAI_STORAGE_ACCOUNT>',
                    azure_file_url='https://<AZURE_BATCHAI_STORAGE_ACCOUNT>.file.core.windows.net/share',
                    credentials=AzureStorageCredentialsInfo(account_key='<AZURE_BATCHAI_STORAGE_KEY>')
                ),
                AzureFileShareReference(
                    relative_mount_path='azfiles2',
                    account_name=None,
                    azure_file_url='https://<AZURE_BATCHAI_STORAGE_ACCOUNT>.file.core.windows.net/share2',
                    credentials=None
                )
            ],
            azure_blob_file_systems=[
                AzureBlobFileSystemReference(
                    relative_mount_path='blobfs',
                    container_name='container',
                    account_name='<AZURE_BATCHAI_STORAGE_ACCOUNT>',
                    credentials=AzureStorageCredentialsInfo(account_key='<AZURE_BATCHAI_STORAGE_KEY>')
                ),
                AzureBlobFileSystemReference(
                    relative_mount_path='blobfs2',
                    container_name='container2',
                    account_name='<AZURE_BATCHAI_STORAGE_ACCOUNT>',
                    credentials=None
                ),
            ]
        )
        with _given_env_variable('AZURE_BATCHAI_STORAGE_ACCOUNT', 'account'):
            with _given_env_variable('AZURE_BATCHAI_STORAGE_KEY', 'key'):
                actual = _patch_mount_volumes(DummyCli(), mount_volumes)
        expected = MountVolumes(
            azure_file_shares=[
                AzureFileShareReference(
                    relative_mount_path='azfiles',
                    account_name='account',
                    azure_file_url='https://account.file.core.windows.net/share',
                    credentials=AzureStorageCredentialsInfo(account_key='key')
                ),
                AzureFileShareReference(
                    relative_mount_path='azfiles2',
                    account_name='account',
                    azure_file_url='https://account.file.core.windows.net/share2',
                    credentials=AzureStorageCredentialsInfo(account_key='key')
                ),
            ],
            azure_blob_file_systems=[
                AzureBlobFileSystemReference(
                    relative_mount_path='blobfs',
                    container_name='container',
                    account_name='account',
                    credentials=AzureStorageCredentialsInfo(account_key='key')
                ),
                AzureBlobFileSystemReference(
                    relative_mount_path='blobfs2',
                    container_name='container2',
                    account_name='account',
                    credentials=AzureStorageCredentialsInfo(account_key='key')
                )
            ]
        )
        self.assertEqual(expected, actual)

    @patch('azure.cli.command_modules.batchai.custom._get_storage_management_client')
    def test_batchai_patch_mount_volumes_with_credentials(self, get_storage_client):
        # noinspection PyTypeChecker
        mount_volumes = MountVolumes(
            azure_file_shares=[
                AzureFileShareReference(
                    relative_mount_path='azfiles',
                    account_name=None,
                    azure_file_url='https://account1.file.core.windows.net/share',
                    credentials=None
                )
            ],
            azure_blob_file_systems=[
                AzureBlobFileSystemReference(
                    relative_mount_path='blobfs',
                    container_name='container',
                    account_name='account2',
                    credentials=None
                ),
            ]
        )
        get_storage_client.return_value = \
            _get_mock_storage_accounts_and_keys({'account1': 'key1', 'account2': 'key2'})
        actual = _patch_mount_volumes(DummyCli(), mount_volumes)
        expected = MountVolumes(
            azure_file_shares=[
                AzureFileShareReference(
                    relative_mount_path='azfiles',
                    account_name='account1',
                    azure_file_url='https://account1.file.core.windows.net/share',
                    credentials=AzureStorageCredentialsInfo(account_key='key1')
                )
            ],
            azure_blob_file_systems=[
                AzureBlobFileSystemReference(
                    relative_mount_path='blobfs',
                    container_name='container',
                    account_name='account2',
                    credentials=AzureStorageCredentialsInfo(account_key='key2')
                )
            ]
        )
        self.assertEqual(expected, actual)

    @patch('azure.cli.command_modules.batchai.custom._get_storage_management_client')
    def test_batchai_patch_mount_volumes_with_credentials_no_account_found(self, get_storage_client):
        get_storage_client.return_value = _get_mock_storage_accounts_and_keys({})
        # noinspection PyTypeChecker
        mount_volumes = MountVolumes(
            azure_file_shares=[
                AzureFileShareReference(
                    relative_mount_path='azfiles',
                    account_name=None,
                    azure_file_url='https://account1.file.core.windows.net/share',
                    credentials=None
                )
            ]
        )
        with self.assertRaisesRegex(CLIError, 'Cannot find "account1" storage account'):
            _patch_mount_volumes(DummyCli(), mount_volumes)

    @patch('azure.cli.command_modules.batchai.custom._get_storage_management_client')
    def test_batchai_patch_mount_volumes_with_credentials_no_account_given(
            self, get_storage_client):
        get_storage_client.return_value = _get_mock_storage_accounts_and_keys(
            {})
        # noinspection PyTypeChecker
        mount_volumes = MountVolumes(
            azure_file_shares=[
                AzureFileShareReference(
                    relative_mount_path='azfiles',
                    account_name=None,
                    azure_file_url='https://<AZURE_BATCHAI_STORAGE_ACCOUNT>.file.core.windows.net/share',
                    credentials=None
                )
            ]
        )
        with self.assertRaisesRegex(CLIError, 'Please configure Azure Storage account name'):
            _patch_mount_volumes(DummyCli(), mount_volumes)

    @patch('azure.cli.command_modules.batchai.custom._get_storage_management_client')
    def test_batchai_patch_mount_volumes_when_no_patching_required(
            self, get_storage_client):
        get_storage_client.return_value = _get_mock_storage_accounts_and_keys(
            {})
        # noinspection PyTypeChecker
        mount_volumes = MountVolumes(
            azure_file_shares=[
                AzureFileShareReference(
                    relative_mount_path='azfiles',
                    account_name='account1',
                    azure_file_url='https://account1.file.core.windows.net/share',
                    credentials=AzureStorageCredentialsInfo(account_key='key')
                )
            ]
        )
        actual = _patch_mount_volumes(DummyCli(), mount_volumes)
        self.assertEqual(mount_volumes, actual)

    def test_batchai_patch_mount_volumes_no_azure_file_url(self):
        # noinspection PyTypeChecker
        mount_volumes = MountVolumes(
            azure_file_shares=[
                AzureFileShareReference(
                    relative_mount_path='azfiles',
                    account_name=None,
                    azure_file_url=None,
                    credentials=None
                )
            ]
        )
        with self.assertRaisesRegex(CLIError, 'Azure File URL cannot absent or be empty'):
            _patch_mount_volumes(DummyCli(), mount_volumes)

    def test_batchai_patch_mount_volumes_ill_formed_azure_file_url(self):
        # noinspection PyTypeChecker
        mount_volumes = MountVolumes(
            azure_file_shares=[
                AzureFileShareReference(
                    relative_mount_path='azfiles',
                    account_name=None,
                    azure_file_url='http://http://something/is/wrong',
                    credentials=None
                )
            ]
        )
        with self.assertRaisesRegex(CLIError, 'Ill-formed Azure File URL'):
            _patch_mount_volumes(DummyCli(), mount_volumes)

    def test_batchai_add_nfs_to_mount_volumes_no_relative_mount_path(self):
        with self.assertRaisesRegex(CLIError, 'File server relative mount path cannot be empty'):
            _add_nfs_to_mount_volumes(MountVolumes(), 'id', '')

    def test_batchai_add_nfs_to_empty_mount_volumes(self):
        mount_volumes = _add_nfs_to_mount_volumes(MountVolumes(), 'id', 'relative_path')
        self.assertEqual('id', mount_volumes.file_servers[0].file_server.id)
        self.assertEqual('relative_path', mount_volumes.file_servers[0].relative_mount_path)
        self.assertEqual('rw', mount_volumes.file_servers[0].mount_options)

    def test_batchai_add_nfs_to_absent_mount_volumes(self):
        mount_volumes = _add_nfs_to_mount_volumes(None, 'id', 'relative_path')
        self.assertEqual('id', mount_volumes.file_servers[0].file_server.id)
        self.assertEqual('relative_path', mount_volumes.file_servers[0].relative_mount_path)
        self.assertEqual('rw', mount_volumes.file_servers[0].mount_options)

    def test_batchai_add_nfs_to_non_empty_mount_volumes(self):
        mount_volumes = _add_nfs_to_mount_volumes(MountVolumes(), 'id0', 'relative_path0')
        mount_volumes = _add_nfs_to_mount_volumes(mount_volumes, 'id1', 'relative_path1')
        for i in range(2):
            self.assertEqual('id{0}'.format(i), mount_volumes.file_servers[i].file_server.id)
            self.assertEqual('relative_path{0}'.format(i), mount_volumes.file_servers[i].relative_mount_path)
            self.assertEqual('rw', mount_volumes.file_servers[i].mount_options)

    def test_batchai_add_azure_file_share_to_mount_volumes_no_account_info(self):
        with self.assertRaisesRegex(CLIError, 'Please configure Azure Storage account name'):
            _add_azure_file_share_to_mount_volumes(DummyCli(), MountVolumes(), 'share', 'relative_path')

    def test_batchai_add_azure_file_share_to_mount_volumes_no_relative_mount_path(self):
        with self.assertRaisesRegex(CLIError, 'Azure File share relative mount path cannot be empty'):
            _add_azure_file_share_to_mount_volumes(DummyCli(), MountVolumes(), 'share', '')

    @patch('azure.cli.command_modules.batchai.custom._get_storage_management_client')
    def test_batchai_add_azure_file_share_to_mount_volumes_account_and_key_via_env_variables(
            self, get_storage_client):
        get_storage_client.return_value = _get_mock_storage_accounts_and_keys({'account': 'key'})
        with _given_env_variable('AZURE_BATCHAI_STORAGE_ACCOUNT', 'account'):
            with _given_env_variable('AZURE_BATCHAI_STORAGE_KEY', 'key'):
                actual = _add_azure_file_share_to_mount_volumes(DummyCli(), MountVolumes(), 'share', 'relative_path')
        expected = MountVolumes(azure_file_shares=[
            AzureFileShareReference(
                account_name='account',
                azure_file_url='https://account.file.core.windows.net/share',
                relative_mount_path='relative_path',
                credentials=AzureStorageCredentialsInfo(
                    account_key='key'
                )
            )]
        )
        self.assertEqual(expected, actual)

    @patch('azure.cli.command_modules.batchai.custom._get_storage_management_client')
    def test_batchai_add_azure_file_share_to_mount_volumes_account_and_key_via_command_line_args(
            self, get_storage_client):
        get_storage_client.return_value = \
            _get_mock_storage_accounts_and_keys({'account': 'key'})
        actual = _add_azure_file_share_to_mount_volumes(DummyCli(), MountVolumes(), 'share', 'relative_path',
                                                        'account', 'key')
        expected = MountVolumes(azure_file_shares=[
            AzureFileShareReference(
                account_name='account',
                azure_file_url='https://account.file.core.windows.net/share',
                relative_mount_path='relative_path',
                credentials=AzureStorageCredentialsInfo(
                    account_key='key'
                )
            )]
        )
        self.assertEqual(expected, actual)

    @patch('azure.cli.command_modules.batchai.custom._get_storage_management_client')
    def test_batchai_add_azure_file_share_to_mount_volumes_account_via_command_line_args(self, get_storage_client):
        get_storage_client.return_value = _get_mock_storage_accounts_and_keys({'account': 'key'})
        actual = _add_azure_file_share_to_mount_volumes(DummyCli(), MountVolumes(), 'share', 'relative_path', 'account')
        expected = MountVolumes(azure_file_shares=[
            AzureFileShareReference(
                account_name='account',
                azure_file_url='https://account.file.core.windows.net/share',
                relative_mount_path='relative_path',
                credentials=AzureStorageCredentialsInfo(
                    account_key='key'
                )
            )]
        )
        self.assertEqual(expected, actual)

    @patch('azure.cli.command_modules.batchai.custom._get_storage_management_client')
    def test_batchai_add_azure_file_share_to_absent_mount_volumes(self, get_storage_client):
        get_storage_client.return_value = _get_mock_storage_accounts_and_keys({'account': 'key'})
        actual = _add_azure_file_share_to_mount_volumes(DummyCli(), None, 'share', 'relative_path', 'account')
        expected = MountVolumes(azure_file_shares=[
            AzureFileShareReference(
                account_name='account',
                azure_file_url='https://account.file.core.windows.net/share',
                relative_mount_path='relative_path',
                credentials=AzureStorageCredentialsInfo(
                    account_key='key'
                )
            )]
        )
        self.assertEqual(expected, actual)

    def test_batchai_add_azure_container_mount_volumes_no_account(self):
        with self.assertRaisesRegex(CLIError, 'Please configure Azure Storage account name'):
            _add_azure_container_to_mount_volumes(DummyCli(), MountVolumes(), 'container', 'relative_path')

    def test_batchai_add_azure_container_mount_volumes_no_relative_path(self):
        with self.assertRaisesRegex(CLIError, 'Azure Storage Container relative mount path cannot be empty'):
            _add_azure_container_to_mount_volumes(DummyCli(), MountVolumes(), 'container', '')

    def test_batchai_add_azure_container_to_absent_mount_volumes(self):
        with _given_env_variable('AZURE_BATCHAI_STORAGE_ACCOUNT', 'account'):
            with _given_env_variable('AZURE_BATCHAI_STORAGE_KEY', 'key'):
                actual = _add_azure_container_to_mount_volumes(DummyCli(), None, 'container', 'relative_path')
        expected = MountVolumes(azure_blob_file_systems=[
            AzureBlobFileSystemReference(
                account_name='account',
                container_name='container',
                relative_mount_path='relative_path',
                credentials=AzureStorageCredentialsInfo(account_key='key'))])
        self.assertEqual(expected, actual)

    def test_batchai_add_azure_container_mount_volumes_account_and_key_via_env_variables(self):
        with _given_env_variable('AZURE_BATCHAI_STORAGE_ACCOUNT', 'account'):
            with _given_env_variable('AZURE_BATCHAI_STORAGE_KEY', 'key'):
                actual = _add_azure_container_to_mount_volumes(DummyCli(), MountVolumes(), 'container', 'relative_path')
        expected = MountVolumes(azure_blob_file_systems=[
            AzureBlobFileSystemReference(
                account_name='account',
                container_name='container',
                relative_mount_path='relative_path',
                credentials=AzureStorageCredentialsInfo(account_key='key'))])
        self.assertEqual(expected, actual)

    def test_batchai_add_azure_container_mount_volumes_account_and_key_via_cmd_line_args(self):
        actual = _add_azure_container_to_mount_volumes(
            DummyCli(), MountVolumes(), 'container', 'relative_path', 'account', 'key')
        expected = MountVolumes(azure_blob_file_systems=[
            AzureBlobFileSystemReference(
                account_name='account',
                container_name='container',
                relative_mount_path='relative_path',
                credentials=AzureStorageCredentialsInfo(account_key='key'))])
        self.assertEqual(expected, actual)

    @patch('azure.cli.command_modules.batchai.custom._get_storage_management_client')
    def test_batchai_add_azure_container_mount_volumes_account_via_cmd_line_args(self, get_storage_client):
        get_storage_client.return_value = _get_mock_storage_accounts_and_keys({'account': 'key'})
        actual = _add_azure_container_to_mount_volumes(
            DummyCli(), MountVolumes(), 'container', 'relative_path', 'account')
        expected = MountVolumes(azure_blob_file_systems=[
            AzureBlobFileSystemReference(
                account_name='account',
                container_name='container',
                relative_mount_path='relative_path',
                credentials=AzureStorageCredentialsInfo(account_key='key'))])
        self.assertEqual(expected, actual)

    def test_batchai_update_nodes_information(self):
        params = ClusterCreateParameters(location='southcentralus', vm_size='STANDARD_D1',
                                         user_account_settings=UserAccountSettings(admin_user_name='name',
                                                                                   admin_user_password='password'))
        # Update to autoscale Ubuntu DSVM.
        result = _update_nodes_information(params, 'ubuntudsvm', None, 'Standard_NC6', 'dedicated', None, 1, 3)
        self.assertEqual(result.vm_size, 'Standard_NC6')
        self.assertEqual(result.vm_priority, 'dedicated')
        self.assertEqual(
            ImageReference(publisher='microsoft-ads', offer='linux-data-science-vm-ubuntu', sku='linuxdsvmubuntu'),
            result.virtual_machine_configuration.image_reference)
        self.assertEqual(result.scale_settings,
                         ScaleSettings(auto_scale=AutoScaleSettings(minimum_node_count=1, maximum_node_count=3)))

        # Update to manual scale Ubuntu LTS.
        result = _update_nodes_information(params, 'UbuntuLTS', None, 'Standard_NC6', '', None, 2, 2)
        self.assertEqual(result.vm_size, 'Standard_NC6')
        self.assertEqual(result.vm_priority, None)
        self.assertEqual(ImageReference(
            publisher='Canonical', offer='UbuntuServer', sku='16.04-LTS'),
            result.virtual_machine_configuration.image_reference
        )
        self.assertEqual(result.scale_settings, ScaleSettings(
            manual=ManualScaleSettings(target_node_count=2)))

        # Update to manual scale Ubuntu LTS.
        result = _update_nodes_information(params, 'UbuntuLTS', None, 'Standard_NC6', '', 2, 2, 2)
        self.assertEqual(result.vm_size, 'Standard_NC6')
        self.assertEqual(result.vm_priority, None)
        self.assertEqual(
            ImageReference(publisher='Canonical', offer='UbuntuServer', sku='16.04-LTS'),
            result.virtual_machine_configuration.image_reference)
        self.assertEqual(result.scale_settings, ScaleSettings(manual=ManualScaleSettings(target_node_count=2)))

        # Update to manual scale Ubuntu LTS.
        result = _update_nodes_information(params, 'UbuntuLTS', None, 'Standard_NC6', '', 2, None, None)
        self.assertEqual(result.vm_size, 'Standard_NC6')
        self.assertEqual(result.vm_priority, None)
        self.assertEqual(
            ImageReference(publisher='Canonical', offer='UbuntuServer', sku='16.04-LTS'),
            result.virtual_machine_configuration.image_reference
        )
        self.assertEqual(result.scale_settings, ScaleSettings(manual=ManualScaleSettings(target_node_count=2)))

        # Update to auto-scale with initial count Ubuntu LTS.
        result = _update_nodes_information(params, 'UbuntuLTS', None, 'Standard_NC6', '', 1, 0, 2)
        self.assertEqual(result.vm_size, 'Standard_NC6')
        self.assertEqual(result.vm_priority, None)
        self.assertEqual(
            ImageReference(publisher='Canonical', offer='UbuntuServer', sku='16.04-LTS'),
            result.virtual_machine_configuration.image_reference)
        self.assertEqual(
            ScaleSettings(
                auto_scale=AutoScaleSettings(minimum_node_count=0, maximum_node_count=2, initial_node_count=1)),
            result.scale_settings)

        # Update image.
        params.scale_settings = ScaleSettings(manual=ManualScaleSettings(target_node_count=2))
        result = _update_nodes_information(params, 'UbuntuDsvm', None, None, '', None, None, None)
        self.assertEqual(
            ImageReference(publisher='microsoft-ads', offer='linux-data-science-vm-ubuntu', sku='linuxdsvmubuntu'),
            result.virtual_machine_configuration.image_reference)
        self.assertEqual(result.scale_settings, ScaleSettings(manual=ManualScaleSettings(target_node_count=2)))

        # Update nothing.
        result = _update_nodes_information(params, None, None, None, '', None, None, None)
        self.assertEqual(params, result)

        # Wrong image.
        with self.assertRaisesRegex(CLIError, 'Unsupported image alias'):
            _update_nodes_information(params, 'unsupported', None, None, '', None, None, None)

        # No VM size.
        params.vm_size = None
        with self.assertRaisesRegex(CLIError, 'Please provide VM size'):
            _update_nodes_information(params, 'unsupported', None, None, '', None, None, None)

        # No scale settings.
        params.vm_size = 'Standard_NC6'
        params.scale_settings = None
        with self.assertRaisesRegex(CLIError, 'Please provide scale setting for the cluster'):
            _update_nodes_information(params, None, None, None, '', None, None, None)

        # Error if only min is specified
        with self.assertRaisesRegex(CLIError, 'You need to either provide both min and max node'):
            _update_nodes_information(params, 'UbuntuLTS', None, 'Standard_NC6', '', 2, 2, None)

    def test_get_image_or_die_supported_aliases(self):
        self.assertEqual(
            ImageReference(publisher='Canonical', offer='UbuntuServer', sku='16.04-LTS'),
            _get_image_reference('ubuntults', None))
        self.assertEqual(
            ImageReference(publisher='microsoft-ads', offer='linux-data-science-vm-ubuntu', sku='linuxdsvmubuntu'),
            _get_image_reference('ubuntudsvm', None))

    def test_get_image_or_die_unsupported_alias(self):
        with self.assertRaisesRegex(CLIError, 'Unsupported image alias "ubuntu", supported aliases are'):
            _get_image_reference('ubuntu', None)

    def test_get_image_or_die_with_valid_spec(self):
        self.assertEqual(
            ImageReference(publisher='Canonical', offer='UbuntuServer', sku='16.04-LTS'),
            _get_image_reference('Canonical:UbuntuServer:16.04-LTS:', None))
        self.assertEqual(
            ImageReference(publisher='Canonical', offer='UbuntuServer', sku='16.04-LTS', version='latest'),
            _get_image_reference('Canonical:UbuntuServer:16.04-LTS:latest', None))

    def test_get_image_or_die_with_invalid_spec(self):
        with self.assertRaisesRegex(CLIError, "--image must have format"):
            _get_image_reference('Canonical:UbuntuServer:16.04-LTS', None)
        with self.assertRaisesRegex(CLIError, "--image must have format"):
            _get_image_reference('Canonical:UbuntuServer:16.04-LTS:latest:', None)
        with self.assertRaisesRegex(CLIError, "Image publisher must be provided in --image argument"):
            _get_image_reference(':UbuntuServer:16.04-LTS:latest', None)
        with self.assertRaisesRegex(CLIError, "Image offer must be provided in --image argument"):
            _get_image_reference('Canonical::16.04-LTS:latest', None)
        with self.assertRaisesRegex(CLIError, "Image sku must be provided in --image argument"):
            _get_image_reference('Canonical:Offer::latest', None)

    def test_get_image_or_die_with_custom_image_without_version(self):
        # noinspection PyTypeChecker
        self.assertEqual(
            ImageReference(
                publisher='Canonical',
                offer='UbuntuServer',
                sku='16.04-LTS',
                version=None,
                virtual_machine_image_id='/subscriptions/00/resourceGroups/gr/providers/Microsoft.Compute/images/img'
            ),
            _get_image_reference(
                'ubuntults', '/subscriptions/00/resourceGroups/gr/providers/Microsoft.Compute/images/img')
        )

    def test_get_image_or_die_with_custom_image_with_version(self):
        self.assertEqual(
            ImageReference(
                publisher='Canonical',
                offer='UbuntuServer',
                sku='16.04-LTS',
                version='latest',
                virtual_machine_image_id='/subscriptions/00/resourceGroups/gr/providers/Microsoft.Compute/images/img'
            ),
            _get_image_reference(
                'Canonical:UbuntuServer:16.04-LTS:latest',
                '/subscriptions/00/resourceGroups/gr/providers/Microsoft.Compute/images/img'),
        )

    def test_get_image_or_die_with_invalid_custom_image(self):
        with self.assertRaisesRegex(CLIError, 'Ill-formed custom image resource id'):
            _get_image_reference('ubuntults', 'bla-bla')

    def test_get_image_or_die_with_custom_image_but_without_image(self):
        with self.assertRaisesRegex(CLIError, 'You need to specify --image argument'):
            _get_image_reference(
                None, '/subscriptions/00/resourceGroups/gr/providers/Microsoft.Compute/images/img')

    def test_validate_subnet_no_subnet(self):
        _ensure_subnet_is_valid(None, None, 'mockrg', 'mockws', 'mocknfs')

    def test_validate_subnet_no_nfs(self):
        _ensure_subnet_is_valid(
            None,
            '/subscriptions/000/resourceGroups/gr/providers/Microsoft.Network/virtualNetworks/vn/subnets/subnet',
            'mockrg', 'mockws', None)

    def test_validate_subnet_wrong_resource_id(self):
        with self.assertRaisesRegex(CLIError, 'Ill-formed subnet resource id'):
            _ensure_subnet_is_valid(None, 'bla-bla', 'mockrg', 'mockws', 'mocknfs')

    def test_validate_subnet_no_conflicts(self):
        mock_client = MagicMock()
        mock_client.file_servers.get = MagicMock(
            return_value=FileServer(subnet=ResourceId(
                id='/subscriptions/000/resourceGroups/gr/providers/Microsoft.Network/virtualNetworks/vn/subnets/subnet')
            ))
        _ensure_subnet_is_valid(
            mock_client,
            '/subscriptions/000/resourceGroups/gr/providers/Microsoft.Network/virtualNetworks/vn/subnets/subnet',
            'mockrg', 'mockws', 'mocknfs')

    def test_validate_subnet_when_conflict(self):
        mock_client = MagicMock()
        mock_client.file_servers.get = MagicMock(
            return_value=FileServer(
                subnet=ResourceId(id='conflict')
            ))
        with self.assertRaisesRegex(CLIError, 'Cluster and mounted NFS must be in the same subnet'):
            _ensure_subnet_is_valid(
                mock_client,
                '/subscriptions/000/resourceGroups/gr/providers/Microsoft.Network/virtualNetworks/vn/subnets/subnet',
                'mockrg', 'mockws', 'mocknfs')

    def test_is_on_mount_point_yes(self):
        self.assertTrue(_is_on_mount_point('afs', 'afs'))
        self.assertTrue(_is_on_mount_point('afs/', 'afs'))
        self.assertTrue(_is_on_mount_point('afs', 'afs/'))
        self.assertTrue(_is_on_mount_point('afs/', 'afs/'))
        self.assertTrue(_is_on_mount_point('afs/logs', 'afs'))
        self.assertTrue(_is_on_mount_point('afs/logs/', 'afs'))
        self.assertTrue(_is_on_mount_point('afs/logs', 'afs/'))
        self.assertTrue(_is_on_mount_point('afs/logs/', 'afs'))
        self.assertTrue(_is_on_mount_point('folder/afs/logs', 'folder/afs'))

    def test_is_on_mount_point_no(self):
        self.assertFalse(_is_on_mount_point('somewhere', 'afs'))
        self.assertFalse(_is_on_mount_point('af', 'afs'))
        self.assertFalse(_is_on_mount_point('afs', 'af'))

    def test_list_setup_task_files_for_cluster_when_no_node_setup(self):
        self.assertEqual(_list_node_setup_files_for_cluster(DummyCli(), Cluster(), '.', 60), [])

    def test_list_setup_task_files_for_cluster_when_output_not_on_mounts_root(self):
        with self.assertRaisesRegex(CLIError, 'List files is supported only for clusters with startup task'):
            cluster = Cluster(
                node_setup=NodeSetup(
                    setup_task=SetupTask(
                        command_line='true',
                        std_out_err_path_prefix='/somewhere')))
            _list_node_setup_files_for_cluster(DummyCli(), cluster, '.', 60)

    def test_list_setup_task_files_for_cluster_when_cluster_doesnt_support_suffix(self):
        with self.assertRaisesRegex(CLIError, 'List files is not supported for this cluster'):
            cluster = Cluster(
                node_setup=NodeSetup(
                    setup_task=SetupTask(
                        command_line='true',
                        std_out_err_path_prefix='$AZ_BATCHAI_MOUNT_ROOT/nfs')))
            _list_node_setup_files_for_cluster(DummyCli(), cluster, '.', 60)

    def test_list_setup_task_files_for_cluster_when_cluster_has_not_mount_volumes(self):
        with self.assertRaisesRegex(CLIError, 'List files is supported only for clusters with startup task'):
            cluster = Cluster(
                node_setup=NodeSetup(
                    setup_task=SetupTask(
                        command_line='true',
                        std_out_err_path_prefix='$AZ_BATCHAI_MOUNT_ROOT/nfs')))
            cluster.node_setup.setup_task.std_out_err_path_suffix = 'path/segment'
            _list_node_setup_files_for_cluster(DummyCli(), cluster, '.', 60)

    def test_list_setup_task_files_for_cluster_when_output_not_on_afs_or_bfs(self):
        with self.assertRaisesRegex(CLIError, 'List files is supported only for clusters with startup task'):
            cluster = Cluster(
                vm_size=None,
                user_account_settings=None,
                node_setup=NodeSetup(
                    setup_task=SetupTask(
                        command_line='true',
                        std_out_err_path_prefix='$AZ_BATCHAI_MOUNT_ROOT/nfs')),
                mount_volumes=MountVolumes(
                    azure_file_shares=[
                        AzureFileShareReference(
                            azure_file_url='https://account.file.core.windows.net/share',
                            relative_mount_path='afs',
                            account_name='some',
                            credentials=None
                        )]
                ))
            cluster.node_setup.setup_task.std_out_err_path_suffix = 'path/segment'
            _list_node_setup_files_for_cluster(DummyCli(), cluster, '.', 60)

    @patch('azure.cli.command_modules.batchai.custom._get_files_from_afs')
    def test_list_setup_task_files_for_cluster_when_output_on_afs(self, get_files_from_afs):
        cluster = Cluster(
            node_setup=NodeSetup(
                setup_task=SetupTask(
                    command_line='true',
                    std_out_err_path_prefix='$AZ_BATCHAI_MOUNT_ROOT/afs')))
        cluster.node_setup.setup_task.std_out_err_path_suffix = 'path/segment'
        cluster.node_setup.mount_volumes = MountVolumes(
            azure_file_shares=[
                AzureFileShareReference(
                    relative_mount_path='afs',
                    account_name='some',
                    azure_file_url='some url',
                    credentials=None)])
        cli_ctx = DummyCli()
        _list_node_setup_files_for_cluster(cli_ctx, cluster, '.', 60)
        get_files_from_afs.assert_called_once_with(
            cli_ctx,
            AzureFileShareReference(
                relative_mount_path='afs',
                account_name='some',
                azure_file_url='some url',
                credentials=None),
            os.path.join('path/segment', '.'), 60)

    @patch('azure.cli.command_modules.batchai.custom._get_files_from_bfs')
    def test_list_setup_task_files_for_cluster_when_output_on_bfs(self, get_files_from_bfs):
        cluster = Cluster(
            node_setup=NodeSetup(
                setup_task=SetupTask(
                    command_line='true',
                    std_out_err_path_prefix='$AZ_BATCHAI_MOUNT_ROOT/bfs')))
        cluster.node_setup.setup_task.std_out_err_path_suffix = os.path.join('path', 'segment')
        cluster.node_setup.mount_volumes = MountVolumes(
            azure_blob_file_systems=[
                AzureBlobFileSystemReference(
                    relative_mount_path='bfs',
                    account_name='some',
                    container_name='container',
                    credentials=None)])
        cli_ctx = DummyCli()
        _list_node_setup_files_for_cluster(cli_ctx, cluster, '.', 60)
        get_files_from_bfs.assert_called_once_with(
            cli_ctx,
            AzureBlobFileSystemReference(
                account_name='some',
                relative_mount_path='bfs',
                container_name='container',
                credentials=None),
            os.path.join('path', 'segment', '.'), 60)

    def test_generate_auto_storage_account_name(self):
        names = {_generate_auto_storage_account_name() for i in range(100)}
        # at least 90% of names must be unique
        self.assertTrue(len(names) > 90)

    def test_setup_task_no_output(self):
        with self.assertRaisesRegex(CLIError, '--setup-task requires providing of --setup-task-output'):
            _add_setup_task('echo hi', None, ClusterCreateParameters(vm_size=None, user_account_settings=None))

    def test_setup_task_added_to_cluster_without_node_setup(self):
        actual = _add_setup_task('echo hi', '/tmp', ClusterCreateParameters(vm_size=None, user_account_settings=None))
        self.assertEqual(actual,
                         ClusterCreateParameters(
                             vm_size=None,
                             user_account_settings=None,
                             node_setup=NodeSetup(
                                 setup_task=SetupTask(
                                     command_line='echo hi',
                                     std_out_err_path_prefix='/tmp',
                                     run_elevated=False
                                 ))))

    def test_setup_task_added_to_cluster_without_setup_task(self):
        actual = _add_setup_task('echo hi', '/tmp', ClusterCreateParameters(
            vm_size=None, user_account_settings=None, node_setup=NodeSetup()))
        self.assertEqual(actual,
                         ClusterCreateParameters(
                             vm_size=None,
                             user_account_settings=None,
                             node_setup=NodeSetup(
                                 setup_task=SetupTask(
                                     command_line='echo hi',
                                     std_out_err_path_prefix='/tmp',
                                     run_elevated=False
                                 ))))

    def test_setup_task_overwrite(self):
        # Should overwrite setup task but keep other parameters of node setup (here we use mount_volumes to check it)
        actual = _add_setup_task('echo hi', '/tmp',
                                 ClusterCreateParameters(
                                     vm_size=None,
                                     user_account_settings=None,
                                     node_setup=NodeSetup(
                                         setup_task=SetupTask(
                                             command_line='different', std_out_err_path_prefix=None),
                                         mount_volumes=[]
                                     )))
        self.assertEqual(actual,
                         ClusterCreateParameters(
                             vm_size=None,
                             user_account_settings=None,
                             node_setup=NodeSetup(
                                 setup_task=SetupTask(
                                     command_line='echo hi',
                                     std_out_err_path_prefix='/tmp',
                                     run_elevated=False
                                 ),
                                 mount_volumes=[])))

    def test_get_effective_resource_parameters_when_resource_id_given(self):
        rg, ws, name = _get_effective_resource_parameters(
            '/subscriptions/xxx/resourceGroups/rg/providers/Microsoft.BatchAI/workspaces/ws/clusters/cl',
            'other_rg', 'other_ws')
        self.assertEqual([rg, ws, name], ['rg', 'ws', 'cl'])

    def test_get_effective_resource_parameters_when_name_given(self):
        rg, ws, name = _get_effective_resource_parameters('cl', 'rg', 'ws')
        self.assertEqual([rg, ws, name], ['rg', 'ws', 'cl'])

    def test_get_effective_resource_parameters_when_none_given(self):
        rg, ws, name = _get_effective_resource_parameters(None, 'rg', 'ws')
        self.assertEqual([rg, ws, name], [None, None, None])
