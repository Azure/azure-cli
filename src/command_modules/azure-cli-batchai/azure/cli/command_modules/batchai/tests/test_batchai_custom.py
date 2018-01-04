# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import uuid

import os
import unittest

from azure.cli.command_modules.batchai.custom import (
    _update_cluster_create_parameters_with_env_variables,
    _update_nodes_information,
    _update_user_account_settings,
    _add_azure_container_to_cluster_create_parameters,
    _add_azure_file_share_to_cluster_create_parameters,
    _add_nfs_to_cluster_create_parameters)
from azure.cli.core.util import CLIError

from azure.cli.testsdk import TestCli

from azure.mgmt.batchai.models import (
    ClusterCreateParameters, UserAccountSettings, NodeSetup, MountVolumes, FileServerCreateParameters,
    AzureFileShareReference, AzureBlobFileSystemReference, AzureStorageCredentialsInfo, SshConfiguration, DataDisks,
    ImageReference, ScaleSettings, ManualScaleSettings, AutoScaleSettings
)

# Some valid ssh public key value.
SSH_KEY = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDKUDnWeK6rx36apNE9ij1iAXn68FKXLTW0009XK/7dyMewlNfXi6Z2opnxHDD' \
          'YWucMluU0dsvBR22OuYH2RHriPJTi1jN3aZ0zZSrlH/W4MSNQKlG/AnrjJPA3xfYjIKLGuKBqSIvMsmrkuDfIfMaDnPcxb+GzM1' \
          '0L5epRhoP5FwqaQbLqp640YzFSLqMChz7E6RG54CpEm+MRvA7lj9nD9AlYnfRQAKj2thsFrkz7AlYLQ1ug8vV+1Y3xSKDbo5vy6' \
          'oqM3QKeLiUiyN9Ff1Rq4uYnrqJqcWN1ADfiPGZZjEStOkRgG3V6JrpIN+z0Zl3n+sjrH+CKwrYmyni6D41L'


def _data_file(filename):
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', filename)
    return filepath.replace('\\', '\\\\')


class TestBatchAICustom(unittest.TestCase):

    def test_batchai_update_cluster_create_parameters_with_user_account_settings(self):
        params = ClusterCreateParameters(location='eastus', vm_size='STANDARD_D1',
                                         user_account_settings=UserAccountSettings(admin_user_name='name',
                                                                                   admin_user_password='password'))

        # No update.
        result = _update_user_account_settings(params, None, None, None)
        self.assertEquals(result.user_account_settings.admin_user_name, 'name')
        self.assertEquals(result.user_account_settings.admin_user_password, 'password')
        self.assertIsNone(result.user_account_settings.admin_user_ssh_public_key)

        # Updating.
        params.user_account_settings = None
        result = _update_user_account_settings(params, 'user', SSH_KEY, None)
        self.assertEquals(result.user_account_settings.admin_user_name, 'user')
        self.assertIsNone(result.user_account_settings.admin_user_password)
        self.assertEquals(result.user_account_settings.admin_user_ssh_public_key, SSH_KEY)

        # Incorrect ssh public key.
        params.user_account_settings = None  # user may emit user account settings in config file
        with self.assertRaises(CLIError):
            _update_user_account_settings(params, 'user', 'wrong' + SSH_KEY, 'password')

        # No user account.
        params.user_account_settings = None
        with self.assertRaises(CLIError):
            _update_user_account_settings(params, None, SSH_KEY, None)

        # No credentials.
        params.user_account_settings = None
        with self.assertRaises(CLIError):
            _update_user_account_settings(params, 'user', None, None)

        # ssh public key from a file.
        result = _update_user_account_settings(params, 'user', _data_file('key.txt'), None)
        self.assertEquals(result.user_account_settings.admin_user_ssh_public_key, SSH_KEY)

    def test_batchai_update_file_server_create_parameters_with_user_account_settings(self):
        params = FileServerCreateParameters(location='eastus', vm_size='STANDARD_D1',
                                            ssh_configuration=SshConfiguration(
                                                user_account_settings=UserAccountSettings(
                                                    admin_user_name='name', admin_user_password='password')),
                                            data_disks=DataDisks(10, 2, 'Standard_LRS'))

        # No update.
        result = _update_user_account_settings(params, None, None, None)
        self.assertEqual(params, result)

        # Updating when user_account_setting are omitted.
        params.ssh_configuration.user_account_settings = None
        result = _update_user_account_settings(params, 'user', SSH_KEY, None)
        self.assertEquals(result.ssh_configuration.user_account_settings.admin_user_name, 'user')
        self.assertIsNone(result.ssh_configuration.user_account_settings.admin_user_password)
        self.assertEquals(result.ssh_configuration.user_account_settings.admin_user_ssh_public_key, SSH_KEY)

        # Updating when ssh_configuration is omitted.
        params.ssh_configuration = None
        result = _update_user_account_settings(params, 'user', SSH_KEY, 'password')
        self.assertEquals(result.ssh_configuration.user_account_settings.admin_user_name, 'user')
        self.assertEquals(result.ssh_configuration.user_account_settings.admin_user_password, 'password')
        self.assertEquals(result.ssh_configuration.user_account_settings.admin_user_ssh_public_key, SSH_KEY)

        # Incorrect ssh public key.
        params.ssh_configuration = SshConfiguration(None)  # user may emit user account settings in config file
        with self.assertRaises(CLIError):
            _update_user_account_settings(params, 'user', 'wrong' + SSH_KEY, None)

        # No user account.
        params.ssh_configuration.user_account_settings = None
        with self.assertRaises(CLIError):
            _update_user_account_settings(params, None, SSH_KEY, None)

        # No credentials.
        params.ssh_configuration.user_account_settings = None
        with self.assertRaises(CLIError):
            _update_user_account_settings(params, 'user', None, None)

        # Only password.
        params.ssh_configuration.user_account_settings = None
        result = _update_user_account_settings(params, 'user', None, 'password')
        self.assertEquals(result.ssh_configuration.user_account_settings.admin_user_name, 'user')
        self.assertEquals(result.ssh_configuration.user_account_settings.admin_user_password, 'password')

        # ssh public key from a file.
        result = _update_user_account_settings(params, 'user', _data_file('key.txt'), None)
        self.assertEquals(result.ssh_configuration.user_account_settings.admin_user_ssh_public_key, SSH_KEY)

    def test_batchai_cluster_parameter_update_with_environment_variables(self):
        cli_ctx = TestCli()
        params = ClusterCreateParameters(
            location='eastus', vm_size='STANDARD_D1',
            user_account_settings=UserAccountSettings(admin_user_name='name',
                                                      admin_user_password='password'),
            node_setup=NodeSetup(mount_volumes=MountVolumes(
                azure_file_shares=[AzureFileShareReference(
                    relative_mount_path='azfiles',
                    account_name='<AZURE_BATCHAI_STORAGE_ACCOUNT>',
                    azure_file_url='https://<AZURE_BATCHAI_STORAGE_ACCOUNT>.file.core.windows.net/share',
                    credentials=AzureStorageCredentialsInfo(account_key='<AZURE_BATCHAI_STORAGE_KEY>')
                )],
                azure_blob_file_systems=[AzureBlobFileSystemReference(
                    relative_mount_path='blobfs',
                    container_name='container',
                    account_name='<AZURE_BATCHAI_STORAGE_ACCOUNT>',
                    credentials=AzureStorageCredentialsInfo(account_key='<AZURE_BATCHAI_STORAGE_KEY>')
                )]
            )))

        # No environment variables and no command line parameters provided.
        os.environ.pop('AZURE_BATCHAI_STORAGE_ACCOUNT', None)
        os.environ.pop('AZURE_BATCHAI_STORAGE_KEY', None)
        with self.assertRaises(CLIError):
            _update_cluster_create_parameters_with_env_variables(cli_ctx, params)

        # Set environment variables and check patching results.
        os.environ['AZURE_BATCHAI_STORAGE_ACCOUNT'] = 'account'
        os.environ['AZURE_BATCHAI_STORAGE_KEY'] = 'key'
        result = _update_cluster_create_parameters_with_env_variables(cli_ctx, params)
        self.assertEquals(result.node_setup.mount_volumes.azure_file_shares[0].account_name, 'account')
        self.assertEquals(result.node_setup.mount_volumes.azure_file_shares[0].credentials.account_key, 'key')
        self.assertEquals(result.node_setup.mount_volumes.azure_blob_file_systems[0].account_name, 'account')
        self.assertEquals(result.node_setup.mount_volumes.azure_blob_file_systems[0].credentials.account_key, 'key')

        # Test a case when no patching required.
        params.node_setup.mount_volumes.azure_file_shares[0].account_name = 'some_account'
        params.node_setup.mount_volumes.azure_file_shares[0].credentials.account_key = 'some_key'
        params.node_setup.mount_volumes.azure_blob_file_systems[0].account_name = 'some_other_account'
        params.node_setup.mount_volumes.azure_blob_file_systems[0].credentials.account_key = 'some_other_key'
        os.environ['AZURE_BATCHAI_STORAGE_ACCOUNT'] = 'account'
        os.environ['AZURE_BATCHAI_STORAGE_KEY'] = 'key'
        result = _update_cluster_create_parameters_with_env_variables(cli_ctx, params)
        self.assertEquals(result.node_setup.mount_volumes.azure_file_shares[0].account_name, 'some_account')
        self.assertEquals(result.node_setup.mount_volumes.azure_file_shares[0].credentials.account_key, 'some_key')
        self.assertEquals(result.node_setup.mount_volumes.azure_blob_file_systems[0].account_name,
                          'some_other_account')
        self.assertEquals(result.node_setup.mount_volumes.azure_blob_file_systems[0].credentials.account_key,
                          'some_other_key')

        # Storage account and key provided as command line args.
        params.node_setup.mount_volumes.azure_file_shares[0].account_name = '<AZURE_BATCHAI_STORAGE_ACCOUNT>'
        params.node_setup.mount_volumes.azure_file_shares[0].credentials.account_key = '<AZURE_BATCHAI_STORAGE_KEY>'
        params.node_setup.mount_volumes.azure_blob_file_systems[0].account_name = '<AZURE_BATCHAI_STORAGE_ACCOUNT>'
        params.node_setup.mount_volumes.azure_blob_file_systems[0].credentials.account_key = \
            '<AZURE_BATCHAI_STORAGE_KEY>'
        result = _update_cluster_create_parameters_with_env_variables(cli_ctx, params, 'account_from_cmd', 'key_from_cmd')
        self.assertEquals(result.node_setup.mount_volumes.azure_file_shares[0].account_name, 'account_from_cmd')
        self.assertEquals(result.node_setup.mount_volumes.azure_file_shares[0].credentials.account_key, 'key_from_cmd')
        self.assertEquals(result.node_setup.mount_volumes.azure_blob_file_systems[0].account_name, 'account_from_cmd')
        self.assertEquals(result.node_setup.mount_volumes.azure_blob_file_systems[0].credentials.account_key,
                          'key_from_cmd')

        # Non existing storage account provided as command line arg.
        params.node_setup.mount_volumes.azure_file_shares[0].account_name = '<AZURE_BATCHAI_STORAGE_ACCOUNT>'
        params.node_setup.mount_volumes.azure_file_shares[0].credentials.account_key = '<AZURE_BATCHAI_STORAGE_KEY>'
        with self.assertRaises(CLIError):
            _update_cluster_create_parameters_with_env_variables(cli_ctx, params, str(uuid.uuid4()), None)

    def test_batchai_add_nfs_to_cluster_create_parameters(self):
        params = ClusterCreateParameters(location='eastus', vm_size='STANDARD_D1',
                                         user_account_settings=UserAccountSettings(admin_user_name='name',
                                                                                   admin_user_password='password'))

        # No relative mount path provided.
        with self.assertRaises(CLIError):
            _add_nfs_to_cluster_create_parameters(params, 'id', '')

        # Check valid update.
        result = _add_nfs_to_cluster_create_parameters(params, 'id', 'relative_path')
        self.assertEquals(result.node_setup.mount_volumes.file_servers[0].file_server.id, 'id')
        self.assertEquals(result.node_setup.mount_volumes.file_servers[0].relative_mount_path, 'relative_path')
        self.assertEquals(result.node_setup.mount_volumes.file_servers[0].mount_options, 'rw')

    def test_batchai_add_azure_file_share_to_cluster_create_parameters(self):
        cli_ctx = TestCli()
        params = ClusterCreateParameters(location='eastus', vm_size='STANDARD_D1',
                                         user_account_settings=UserAccountSettings(admin_user_name='name',
                                                                                   admin_user_password='password'))

        # No environment variables given.
        # No environment variables provided.
        os.environ.pop('AZURE_BATCHAI_STORAGE_ACCOUNT', None)
        os.environ.pop('AZURE_BATCHAI_STORAGE_KEY', None)
        with self.assertRaises(CLIError):
            _add_azure_file_share_to_cluster_create_parameters(cli_ctx, params, 'share', 'relative_path')

        os.environ['AZURE_BATCHAI_STORAGE_ACCOUNT'] = 'account'
        os.environ['AZURE_BATCHAI_STORAGE_KEY'] = 'key'

        # No relative mount path provided.
        with self.assertRaises(CLIError):
            _add_azure_file_share_to_cluster_create_parameters(cli_ctx, params, 'share', '')

        # Check valid update.
        result = _add_azure_file_share_to_cluster_create_parameters(cli_ctx, params, 'share', 'relative_path')
        self.assertEquals(result.node_setup.mount_volumes.azure_file_shares[0].account_name, 'account')
        self.assertEquals(result.node_setup.mount_volumes.azure_file_shares[0].azure_file_url,
                          'https://account.file.core.windows.net/share')
        self.assertEquals(result.node_setup.mount_volumes.azure_file_shares[0].relative_mount_path, 'relative_path')
        self.assertEquals(result.node_setup.mount_volumes.azure_file_shares[0].credentials.account_key, 'key')

        # Account name and key provided via command line args.
        os.environ.pop('AZURE_BATCHAI_STORAGE_ACCOUNT', None)
        os.environ.pop('AZURE_BATCHAI_STORAGE_KEY', None)
        result = _add_azure_file_share_to_cluster_create_parameters(cli_ctx, params, 'share', 'relative_path', 'account', 'key')
        self.assertEquals(result.node_setup.mount_volumes.azure_file_shares[0].account_name, 'account')
        self.assertEquals(result.node_setup.mount_volumes.azure_file_shares[0].azure_file_url,
                          'https://account.file.core.windows.net/share')
        self.assertEquals(result.node_setup.mount_volumes.azure_file_shares[0].relative_mount_path, 'relative_path')
        self.assertEquals(result.node_setup.mount_volumes.azure_file_shares[0].credentials.account_key, 'key')

    def test_batchai_add_azure_container_to_cluster_create_parameters(self):
        cli_ctx = TestCli()
        params = ClusterCreateParameters(location='eastus', vm_size='STANDARD_D1',
                                         user_account_settings=UserAccountSettings(admin_user_name='name',
                                                                                   admin_user_password='password'))

        # No environment variables given.
        os.environ.pop('AZURE_BATCHAI_STORAGE_ACCOUNT', None)
        os.environ.pop('AZURE_BATCHAI_STORAGE_KEY', None)
        with self.assertRaises(CLIError):
            _add_azure_container_to_cluster_create_parameters(cli_ctx, params, 'container', 'relative_path')

        os.environ['AZURE_BATCHAI_STORAGE_ACCOUNT'] = 'account'
        os.environ['AZURE_BATCHAI_STORAGE_KEY'] = 'key'

        # No relative mount path provided.
        with self.assertRaises(CLIError):
            _add_azure_container_to_cluster_create_parameters(cli_ctx, params, 'container', '')

        # Check valid update.
        result = _add_azure_container_to_cluster_create_parameters(cli_ctx, params, 'container', 'relative_path')
        self.assertEquals(result.node_setup.mount_volumes.azure_blob_file_systems[0].account_name, 'account')
        self.assertEquals(result.node_setup.mount_volumes.azure_blob_file_systems[0].container_name,
                          'container')
        self.assertEquals(result.node_setup.mount_volumes.azure_blob_file_systems[0].relative_mount_path,
                          'relative_path')
        self.assertEquals(result.node_setup.mount_volumes.azure_blob_file_systems[0].credentials.account_key,
                          'key')

        # Account name and key provided via command line args.
        os.environ.pop('AZURE_BATCHAI_STORAGE_ACCOUNT', None)
        os.environ.pop('AZURE_BATCHAI_STORAGE_KEY', None)
        result = _add_azure_container_to_cluster_create_parameters(cli_ctx, params, 'container', 'relative_path',
                                                                   'account', 'key')
        self.assertEquals(result.node_setup.mount_volumes.azure_blob_file_systems[0].account_name, 'account')
        self.assertEquals(result.node_setup.mount_volumes.azure_blob_file_systems[0].container_name,
                          'container')
        self.assertEquals(result.node_setup.mount_volumes.azure_blob_file_systems[0].relative_mount_path,
                          'relative_path')
        self.assertEquals(result.node_setup.mount_volumes.azure_blob_file_systems[0].credentials.account_key,
                          'key')

    def test_batchai_update_nodes_information(self):
        params = ClusterCreateParameters(location='eastus', vm_size='STANDARD_D1',
                                         user_account_settings=UserAccountSettings(admin_user_name='name',
                                                                                   admin_user_password='password'))
        # Update to autoscale Ubuntu DSVM.
        result = _update_nodes_information(params, 'ubuntudsvm', 'Standard_NC6', 1, 3)
        self.assertEquals(result.vm_size, 'Standard_NC6')
        self.assertEquals(result.virtual_machine_configuration.image_reference,
                          ImageReference('microsoft-ads', 'linux-data-science-vm-ubuntu', 'linuxdsvmubuntu'))
        self.assertEquals(result.scale_settings, ScaleSettings(auto_scale=AutoScaleSettings(1, 3)))

        # Update to manual scale Ubuntu LTS.
        result = _update_nodes_information(params, 'UbuntuLTS', 'Standard_NC6', 2, 2)
        self.assertEquals(result.vm_size, 'Standard_NC6')
        self.assertEquals(result.virtual_machine_configuration.image_reference,
                          ImageReference('Canonical', 'UbuntuServer', '16.04-LTS'))
        self.assertEquals(result.scale_settings, ScaleSettings(manual=ManualScaleSettings(2)))

        # Update image.
        params.scale_settings = ScaleSettings(manual=ManualScaleSettings(2))
        result = _update_nodes_information(params, 'UbuntuDsvm', None, 0, None)
        self.assertEquals(result.virtual_machine_configuration.image_reference,
                          ImageReference('microsoft-ads', 'linux-data-science-vm-ubuntu', 'linuxdsvmubuntu'))
        self.assertEquals(result.scale_settings, ScaleSettings(manual=ManualScaleSettings(2)))

        # Update nothing.
        result = _update_nodes_information(params, None, None, 0, None)
        self.assertEqual(params, result)

        # Wrong image.
        with self.assertRaises(CLIError):
            _update_nodes_information(params, 'unsupported', None, 0, None)

        # No VM size.
        params.vm_size = None
        with self.assertRaises(CLIError):
            _update_nodes_information(params, 'unsupported', None, 0, None)

        # No scale settings.
        params.vm_size = 'Standard_NC6'
        params.scale_settings = None
        with self.assertRaises(CLIError):
            _update_nodes_information(params, None, None, 0, None)
