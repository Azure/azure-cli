# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest

from azure.cli.command_modules.batchai.custom import (
    update_cluster_create_parameters_with_env_variables,
    update_nodes_information,
    update_user_account_settings,
    add_azure_container_to_cluster_create_parameters,
    add_azure_file_share_to_cluster_create_parameters,
    add_nfs_to_cluster_create_parameters)
from azure.cli.core.util import CLIError
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
    def __init__(self, method):
        super(TestBatchAICustom, self).__init__(method)
        pass

    def test_batchai_update_cluster_create_parameters_with_user_account_settings(self):
        """Test updating of user account settings."""
        params = ClusterCreateParameters(location='eastus', vm_size='STANDARD_D1',
                                         user_account_settings=UserAccountSettings(admin_user_name='name',
                                                                                   admin_user_password='password'))

        # No update.
        update_user_account_settings(params, None, None, None)
        self.assertEquals(params.user_account_settings.admin_user_name, 'name')
        self.assertEquals(params.user_account_settings.admin_user_password, 'password')
        self.assertIsNone(params.user_account_settings.admin_user_ssh_public_key)

        # Updating.
        params.user_account_settings = None
        update_user_account_settings(params, 'user', SSH_KEY, None)
        self.assertEquals(params.user_account_settings.admin_user_name, 'user')
        self.assertIsNone(params.user_account_settings.admin_user_password)
        self.assertEquals(params.user_account_settings.admin_user_ssh_public_key, SSH_KEY)

        # Incorrect ssh public key.
        params.user_account_settings = None  # user may emit user account settings in config file
        with self.assertRaises(CLIError):
            update_user_account_settings(params, 'user', 'wrong' + SSH_KEY, 'password')

        # No user account.
        params.user_account_settings = None
        with self.assertRaises(CLIError):
            update_user_account_settings(params, None, SSH_KEY, None)

        # No credentials.
        params.user_account_settings = None
        with self.assertRaises(CLIError):
            update_user_account_settings(params, 'user', None, None)

        # ssh public key from a file.
        update_user_account_settings(params, 'user', _data_file('key.txt'), None)
        self.assertEquals(params.user_account_settings.admin_user_ssh_public_key, SSH_KEY)

    def test_batchai_update_file_server_create_parameters_with_user_account_settings(self):
        """Test updating of user account settings."""
        params = FileServerCreateParameters(location='eastus', vm_size='STANDARD_D1',
                                            ssh_configuration=SshConfiguration(
                                                user_account_settings=UserAccountSettings(
                                                    admin_user_name='name', admin_user_password='password')),
                                            data_disks=DataDisks(10, 2, 'Standard_LRS'))

        # No update.
        update_user_account_settings(params, None, None, None)
        self.assertEquals(params.ssh_configuration.user_account_settings.admin_user_name, 'name')
        self.assertEquals(params.ssh_configuration.user_account_settings.admin_user_password, 'password')
        self.assertIsNone(params.ssh_configuration.user_account_settings.admin_user_ssh_public_key)

        # Updating when user_account_setting are omitted.
        params.ssh_configuration.user_account_settings = None
        update_user_account_settings(params, 'user', SSH_KEY, None)
        self.assertEquals(params.ssh_configuration.user_account_settings.admin_user_name, 'user')
        self.assertIsNone(params.ssh_configuration.user_account_settings.admin_user_password)
        self.assertEquals(params.ssh_configuration.user_account_settings.admin_user_ssh_public_key, SSH_KEY)

        # Updating when ssh_configuration is omitted.
        params.ssh_configuration = None
        update_user_account_settings(params, 'user', SSH_KEY, 'password')
        self.assertEquals(params.ssh_configuration.user_account_settings.admin_user_name, 'user')
        self.assertEquals(params.ssh_configuration.user_account_settings.admin_user_password, 'password')
        self.assertEquals(params.ssh_configuration.user_account_settings.admin_user_ssh_public_key, SSH_KEY)

        # Incorrect ssh public key.
        params.ssh_configuration.user_account_settings = None  # user may emit user account settings in config file
        with self.assertRaises(CLIError):
            update_user_account_settings(params, 'user', 'wrong' + SSH_KEY, None)

        # No user account.
        params.ssh_configuration.user_account_settings = None
        with self.assertRaises(CLIError):
            update_user_account_settings(params, None, SSH_KEY, None)

        # No credentials.
        params.ssh_configuration.user_account_settings = None
        with self.assertRaises(CLIError):
            update_user_account_settings(params, 'user', None, None)

        # Only password.
        params.ssh_configuration.user_account_settings = None
        update_user_account_settings(params, 'user', None, 'password')
        self.assertEquals(params.ssh_configuration.user_account_settings.admin_user_name, 'user')
        self.assertEquals(params.ssh_configuration.user_account_settings.admin_user_password, 'password')

        # ssh public key from a file.
        update_user_account_settings(params, 'user', _data_file('key.txt'), None)
        self.assertEquals(params.ssh_configuration.user_account_settings.admin_user_ssh_public_key, SSH_KEY)

    def test_batchai_cluster_parameter_update_with_environment_variables(self):
        """Test patching of cluster create parameters with environment variables."""
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

        # No environment variables provided.
        os.environ.pop('AZURE_BATCHAI_STORAGE_ACCOUNT', None)
        os.environ.pop('AZURE_BATCHAI_STORAGE_KEY', None)
        with self.assertRaises(CLIError):
            update_cluster_create_parameters_with_env_variables(params)

        # Set environment variables and check patching results.
        os.environ['AZURE_BATCHAI_STORAGE_ACCOUNT'] = 'account'
        os.environ['AZURE_BATCHAI_STORAGE_KEY'] = 'key'
        update_cluster_create_parameters_with_env_variables(params)
        self.assertEquals(params.node_setup.mount_volumes.azure_file_shares[0].account_name, 'account')
        self.assertEquals(params.node_setup.mount_volumes.azure_file_shares[0].credentials.account_key, 'key')
        self.assertEquals(params.node_setup.mount_volumes.azure_blob_file_systems[0].account_name, 'account')
        self.assertEquals(params.node_setup.mount_volumes.azure_blob_file_systems[0].credentials.account_key,
                          'key')

        # Test a case when no patching required.
        os.environ['AZURE_BATCHAI_STORAGE_ACCOUNT'] = 'another_account'
        os.environ['AZURE_BATCHAI_STORAGE_KEY'] = 'another_key'
        update_cluster_create_parameters_with_env_variables(params)

        # Check that no patching has been done.
        self.assertEquals(params.node_setup.mount_volumes.azure_file_shares[0].account_name, 'account')
        self.assertEquals(params.node_setup.mount_volumes.azure_file_shares[0].credentials.account_key, 'key')
        self.assertEquals(params.node_setup.mount_volumes.azure_blob_file_systems[0].account_name, 'account')
        self.assertEquals(params.node_setup.mount_volumes.azure_blob_file_systems[0].credentials.account_key,
                          'key')

    def test_batchai_add_nfs_to_cluster_create_parameters(self):
        """Test adding of nfs into cluster create parameters."""
        params = ClusterCreateParameters(location='eastus', vm_size='STANDARD_D1',
                                         user_account_settings=UserAccountSettings(admin_user_name='name',
                                                                                   admin_user_password='password'))

        # No relative mount path provided.
        with self.assertRaises(CLIError):
            add_nfs_to_cluster_create_parameters(params, 'id', '')

        # Check valid update.
        add_nfs_to_cluster_create_parameters(params, 'id', 'relative_path')
        self.assertEquals(params.node_setup.mount_volumes.file_servers[0].file_server.id, 'id')
        self.assertEquals(params.node_setup.mount_volumes.file_servers[0].relative_mount_path, 'relative_path')
        self.assertEquals(params.node_setup.mount_volumes.file_servers[0].mount_options, 'rw')

    def test_batchai_add_azure_file_share_to_cluster_create_parameters(self):
        """Test adding of azure file share into cluster create parameters."""
        params = ClusterCreateParameters(location='eastus', vm_size='STANDARD_D1',
                                         user_account_settings=UserAccountSettings(admin_user_name='name',
                                                                                   admin_user_password='password'))

        # No environment variables given.
        # No environment variables provided.
        os.environ.pop('AZURE_BATCHAI_STORAGE_ACCOUNT', None)
        os.environ.pop('AZURE_BATCHAI_STORAGE_KEY', None)
        with self.assertRaises(CLIError):
            add_azure_file_share_to_cluster_create_parameters(params, 'share', 'relative_path')

        os.environ['AZURE_BATCHAI_STORAGE_ACCOUNT'] = 'account'
        os.environ['AZURE_BATCHAI_STORAGE_KEY'] = 'key'

        # No relative mount path provided.
        with self.assertRaises(CLIError):
            add_azure_file_share_to_cluster_create_parameters(params, 'share', '')

        # Check valid update.
        add_azure_file_share_to_cluster_create_parameters(params, 'share', 'relative_path')
        self.assertEquals(params.node_setup.mount_volumes.azure_file_shares[0].account_name, 'account')
        self.assertEquals(params.node_setup.mount_volumes.azure_file_shares[0].azure_file_url,
                          'https://account.file.core.windows.net/share')
        self.assertEquals(params.node_setup.mount_volumes.azure_file_shares[0].relative_mount_path, 'relative_path')
        self.assertEquals(params.node_setup.mount_volumes.azure_file_shares[0].credentials.account_key, 'key')

    def test_batchai_add_azure_container_to_cluster_create_parameters(self):
        """Test adding of azure file share into cluster create parameters."""
        params = ClusterCreateParameters(location='eastus', vm_size='STANDARD_D1',
                                         user_account_settings=UserAccountSettings(admin_user_name='name',
                                                                                   admin_user_password='password'))

        # No environment variables given.
        os.environ.pop('AZURE_BATCHAI_STORAGE_ACCOUNT', None)
        os.environ.pop('AZURE_BATCHAI_STORAGE_KEY', None)
        with self.assertRaises(CLIError):
            add_azure_container_to_cluster_create_parameters(params, 'container', 'relative_path')

        os.environ['AZURE_BATCHAI_STORAGE_ACCOUNT'] = 'account'
        os.environ['AZURE_BATCHAI_STORAGE_KEY'] = 'key'

        # No relative mount path provided.
        with self.assertRaises(CLIError):
            add_azure_container_to_cluster_create_parameters(params, 'container', '')

        # Check valid update.
        add_azure_container_to_cluster_create_parameters(params, 'container', 'relative_path')
        self.assertEquals(params.node_setup.mount_volumes.azure_blob_file_systems[0].account_name, 'account')
        self.assertEquals(params.node_setup.mount_volumes.azure_blob_file_systems[0].container_name,
                          'container')
        self.assertEquals(params.node_setup.mount_volumes.azure_blob_file_systems[0].relative_mount_path,
                          'relative_path')
        self.assertEquals(params.node_setup.mount_volumes.azure_blob_file_systems[0].credentials.account_key,
                          'key')

    def test_batchai_update_nodes_information(self):
        """Test updating of nodes information."""
        params = ClusterCreateParameters(location='eastus', vm_size='STANDARD_D1',
                                         user_account_settings=UserAccountSettings(admin_user_name='name',
                                                                                   admin_user_password='password'))
        # Update to autoscale Ubuntu DSVM.
        update_nodes_information(params, 'ubuntudsvm', 'Standard_NC6', 1, 3)
        self.assertEquals(params.vm_size, 'Standard_NC6')
        self.assertEquals(params.virtual_machine_configuration.image_reference,
                          ImageReference('microsoft-ads', 'linux-data-science-vm-ubuntu', 'linuxdsvmubuntu'))
        self.assertEquals(params.scale_settings, ScaleSettings(auto_scale=AutoScaleSettings(1, 3)))

        # Update to manual scale Ubuntu LTS.
        update_nodes_information(params, 'UbuntuLTS', 'Standard_NC6', 2, 2)
        self.assertEquals(params.vm_size, 'Standard_NC6')
        self.assertEquals(params.virtual_machine_configuration.image_reference,
                          ImageReference('Canonical', 'UbuntuServer', '16.04-LTS'))
        self.assertEquals(params.scale_settings, ScaleSettings(manual=ManualScaleSettings(2)))

        # Update image.
        update_nodes_information(params, 'UbuntuDsvm', None, 0, None)
        self.assertEquals(params.vm_size, 'Standard_NC6')
        self.assertEquals(params.virtual_machine_configuration.image_reference,
                          ImageReference('microsoft-ads', 'linux-data-science-vm-ubuntu', 'linuxdsvmubuntu'))
        self.assertEquals(params.scale_settings, ScaleSettings(manual=ManualScaleSettings(2)))

        # Update nothing.
        update_nodes_information(params, None, None, 0, None)
        self.assertEquals(params.vm_size, 'Standard_NC6')
        self.assertEquals(params.virtual_machine_configuration.image_reference,
                          ImageReference('microsoft-ads', 'linux-data-science-vm-ubuntu', 'linuxdsvmubuntu'))
        self.assertEquals(params.scale_settings, ScaleSettings(manual=ManualScaleSettings(2)))

        # Wrong image.
        with self.assertRaises(CLIError):
            update_nodes_information(params, 'unsupported', None, 0, None)

        # No VM size.
        params.vm_size = None
        with self.assertRaises(CLIError):
            update_nodes_information(params, 'unsupported', None, 0, None)

        # No scale settings.
        params.vm_size = 'Standard_NC6'
        params.scale_settings = None
        with self.assertRaises(CLIError):
            update_nodes_information(params, None, None, 0, None)
