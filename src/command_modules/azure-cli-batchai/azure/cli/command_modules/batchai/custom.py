# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import copy
import json
import os
import signal
import time
import requests

from knack.util import CLIError

from msrest.serialization import Deserializer

import azure.mgmt.batchai.models as models

from azure.cli.core.keys import is_valid_ssh_rsa_public_key
from azure.cli.core.util import should_disable_connection_verify, sdk_no_wait


# Environment variables for specifying azure storage account and key. We want the user to make explicit
# decision about which storage account to use instead of using his default account specified via AZURE_STORAGE_ACCOUNT
# and AZURE_STORAGE_KEY.
AZURE_BATCHAI_STORAGE_ACCOUNT = 'AZURE_BATCHAI_STORAGE_ACCOUNT'
AZURE_BATCHAI_STORAGE_KEY = 'AZURE_BATCHAI_STORAGE_KEY'
MSG_CONFIGURE_STORAGE_ACCOUNT = 'Please configure Azure Storage account name via AZURE_BATCHAI_STORAGE_ACCOUNT or ' \
                                'provide storage_account value in batchai section of your az configuration file.'
MSG_CONFIGURE_STORAGE_KEY = 'Please configure Azure Storage account key via AZURE_BATCHAI_STORAGE_KEY or ' \
                            'provide storage_key value in batchai section of your az configuration file.'

# Placeholders which customer may use in his config file for cluster creation.
AZURE_BATCHAI_STORAGE_KEY_PLACEHOLDER = '<{0}>'.format(AZURE_BATCHAI_STORAGE_KEY)
AZURE_BATCHAI_STORAGE_ACCOUNT_PLACEHOLDER = '<{0}>'.format(AZURE_BATCHAI_STORAGE_ACCOUNT)

# Supported images.
SUPPORTED_IMAGES = {
    "ubuntults": models.ImageReference(
        publisher='Canonical',
        offer='UbuntuServer',
        sku='16.04-LTS'
    ),
    "ubuntudsvm": models.ImageReference(
        publisher='microsoft-ads',
        offer='linux-data-science-vm-ubuntu',
        sku='linuxdsvmubuntu'
    )
}


def _get_deserializer():
    client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
    return Deserializer(client_models)


def _get_storage_account_key(cli_ctx, account_name, account_key):
    """Returns account key for the given storage account.

    :param str account_name: storage account name.
    :param str or None account_key: account key provide as command line argument.
    """
    if account_key:
        return account_key
    from azure.mgmt.storage import StorageManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    storage_client = get_mgmt_service_client(cli_ctx, StorageManagementClient)
    account = [a.id for a in list(storage_client.storage_accounts.list()) if a.name == account_name]
    if not account:
        raise CLIError('Cannot find "{0}" storage account.'.format(account_name))
    resource_group = account[0].split('/')[4]
    keys_list_result = storage_client.storage_accounts.list_keys(resource_group, account_name)
    if not keys_list_result or not keys_list_result.keys:
        raise CLIError('Cannot find a key for "{0}" storage account.'.format(account_name))
    return keys_list_result.keys[0].value


def _get_effective_storage_account_name_and_key(cli_ctx, account_name, account_key):
    """Returns storage account name and key to be used.

    :param str or None account_name: storage account name provided as command line argument.
    :param str or None account_key: storage account key provided as command line argument.
    """
    if account_name:
        return account_name, _get_storage_account_key(cli_ctx, account_name, account_key) or ''
    return cli_ctx.config.get('batchai', 'storage_account', ''), cli_ctx.config.get('batchai', 'storage_key', '')


def _update_cluster_create_parameters_with_env_variables(cli_ctx, params, account_name=None, account_key=None):
    """Replaces placeholders with information from the environment variables.

    Currently we support replacing of storage account name and key in mount volumes.

    :param models.ClusterCreateParameters params: cluster creation parameters to patch.
    :param str or None account_name: name of the storage account provided as command line argument.
    :param str or None account_key: storage account key provided as command line argument.
    :return models.ClusterCreateParameters: updated parameters.
    """
    result = copy.deepcopy(params)
    storage_account_name, storage_account_key = _get_effective_storage_account_name_and_key(
        cli_ctx, account_name, account_key)
    require_storage_account = False
    require_storage_account_key = False

    # Patch parameters of azure file share.
    if result.node_setup and \
            result.node_setup.mount_volumes and \
            result.node_setup.mount_volumes.azure_file_shares:
        for ref in result.node_setup.mount_volumes.azure_file_shares:
            if ref.account_name == AZURE_BATCHAI_STORAGE_ACCOUNT_PLACEHOLDER:
                require_storage_account = True
                ref.account_name = storage_account_name
            if ref.azure_file_url and AZURE_BATCHAI_STORAGE_ACCOUNT_PLACEHOLDER in ref.azure_file_url:
                require_storage_account = True
                ref.azure_file_url = ref.azure_file_url.replace(
                    AZURE_BATCHAI_STORAGE_ACCOUNT_PLACEHOLDER, storage_account_name)
            if ref.credentials and ref.credentials.account_key == AZURE_BATCHAI_STORAGE_KEY_PLACEHOLDER:
                require_storage_account_key = True
                ref.credentials.account_key = storage_account_key
            if not ref.credentials:
                require_storage_account_key = True
                ref.credentials = models.AzureStorageCredentialsInfo(account_key=storage_account_key)

    # Patch parameters of blob file system.
    if result.node_setup and \
            result.node_setup.mount_volumes and \
            result.node_setup.mount_volumes.azure_blob_file_systems:
        for ref in result.node_setup.mount_volumes.azure_blob_file_systems:
            if ref.account_name == AZURE_BATCHAI_STORAGE_ACCOUNT_PLACEHOLDER:
                require_storage_account = True
                ref.account_name = storage_account_name
            if ref.credentials and ref.credentials.account_key == AZURE_BATCHAI_STORAGE_KEY_PLACEHOLDER:
                require_storage_account_key = True
                ref.credentials.account_key = storage_account_key
            if not ref.credentials:
                require_storage_account_key = True
                ref.credentials = models.AzureStorageCredentialsInfo(account_key=storage_account_key)

    if require_storage_account and not storage_account_name:
        raise CLIError(MSG_CONFIGURE_STORAGE_ACCOUNT)
    if require_storage_account_key and not storage_account_key:
        raise CLIError(MSG_CONFIGURE_STORAGE_KEY)

    return result


def _update_user_account_settings(params, admin_user_name, ssh_key, password):
    """Update account settings of cluster or file server creation parameters

    :param models.ClusterCreateParameters or models.FileServerCreateParameters params: params to update
    :param str or None admin_user_name: name of admin user to create.
    :param str or None ssh_key: ssh public key value or path to the file containing the key.
    :param str or None password: password.
    :return models.ClusterCreateParameters: updated parameters.
    """
    result = copy.deepcopy(params)
    key = ssh_key
    if ssh_key:
        if os.path.exists(os.path.expanduser(ssh_key)):
            with open(os.path.expanduser(ssh_key)) as f:
                key = f.read()

        if not is_valid_ssh_rsa_public_key(key):
            raise CLIError('Incorrect ssh public key value.')

    if hasattr(result, 'user_account_settings'):
        parent = result
    else:
        if result.ssh_configuration is None:
            result.ssh_configuration = models.SshConfiguration(None)
        parent = result.ssh_configuration
    if parent.user_account_settings is None:
        parent.user_account_settings = models.UserAccountSettings(
            admin_user_name=admin_user_name, admin_user_ssh_public_key=key)
    if admin_user_name:
        parent.user_account_settings.admin_user_name = admin_user_name
    if key:
        parent.user_account_settings.admin_user_ssh_public_key = key
    if password:
        parent.user_account_settings.admin_user_password = password

    if not parent.user_account_settings.admin_user_name:
        raise CLIError('Please provide admin user name.')

    if (not parent.user_account_settings.admin_user_ssh_public_key and
            not parent.user_account_settings.admin_user_password):
        raise CLIError('Please provide admin user password or ssh key.')

    return result


def _add_nfs_to_cluster_create_parameters(params, file_server_id, mount_path):
    """Adds NFS to the cluster create parameters.

    :param model.ClusterCreateParameters params: cluster create parameters.
    :param str file_server_id: resource id of the file server.
    :param str mount_path: relative mount path for the file server.
    :return models.ClusterCreateParameters: updated parameters.
    """
    result = copy.deepcopy(params)
    if not mount_path:
        raise CLIError('File server relative mount path cannot be empty.')
    if result.node_setup is None:
        result.node_setup = models.NodeSetup()
    if result.node_setup.mount_volumes is None:
        result.node_setup.mount_volumes = models.MountVolumes()
    if result.node_setup.mount_volumes.file_servers is None:
        result.node_setup.mount_volumes.file_servers = []
    result.node_setup.mount_volumes.file_servers.append(models.FileServerReference(
        relative_mount_path=mount_path,
        file_server=models.ResourceId(file_server_id),
        mount_options="rw"))
    return result


def _add_azure_file_share_to_cluster_create_parameters(cli_ctx, params, azure_file_share, mount_path, account_name=None,
                                                       account_key=None):
    """Add Azure File share to the cluster create parameters.

    :param model.ClusterCreateParameters params: cluster create parameters.
    :param str azure_file_share: name of the azure file share.
    :param str mount_path: relative mount path for Azure File share.
    :param str or None account_name: storage account name provided as command line argument.
    :param str or None account_key: storage account key provided as command line argument.
    :return models.ClusterCreateParameters: updated parameters.
    """
    result = copy.deepcopy(params)
    if not mount_path:
        raise CLIError('Azure File share relative mount path cannot be empty.')
    if result.node_setup is None:
        result.node_setup = models.NodeSetup()
    if result.node_setup.mount_volumes is None:
        result.node_setup.mount_volumes = models.MountVolumes()
    if result.node_setup.mount_volumes.azure_file_shares is None:
        result.node_setup.mount_volumes.azure_file_shares = []
    storage_account_name, storage_account_key = _get_effective_storage_account_name_and_key(cli_ctx, account_name,
                                                                                            account_key)
    if not storage_account_name:
        raise CLIError(MSG_CONFIGURE_STORAGE_ACCOUNT)
    if not storage_account_key:
        raise CLIError(MSG_CONFIGURE_STORAGE_KEY)
    result.node_setup.mount_volumes.azure_file_shares.append(models.AzureFileShareReference(
        relative_mount_path=mount_path,
        account_name=storage_account_name,
        azure_file_url='https://{0}.file.core.windows.net/{1}'.format(storage_account_name, azure_file_share),
        credentials=models.AzureStorageCredentialsInfo(storage_account_key)))
    return result


def _add_azure_container_to_cluster_create_parameters(cli_ctx, params, container_name, mount_path, account_name=None,
                                                      account_key=None):
    """Add Azure Storage container to the cluster create parameters.

    :param model.ClusterCreateParameters params: cluster create parameters.
    :param str container_name: container name.
    :param str mount_path: relative mount path for the container.
    :param str or None account_name: storage account name provided as command line argument.
    :param str or None account_key: storage account key provided as command line argument.
    :return models.ClusterCreateParameters: updated parameters.
    """
    result = copy.deepcopy(params)
    if not mount_path:
        raise CLIError('Azure Storage container relative mount path cannot be empty.')
    if result.node_setup is None:
        result.node_setup = models.NodeSetup()
    if result.node_setup.mount_volumes is None:
        result.node_setup.mount_volumes = models.MountVolumes()
    if result.node_setup.mount_volumes.azure_blob_file_systems is None:
        result.node_setup.mount_volumes.azure_blob_file_systems = []
    storage_account_name, storage_account_key = _get_effective_storage_account_name_and_key(cli_ctx, account_name,
                                                                                            account_key)
    if not storage_account_name:
        raise CLIError(MSG_CONFIGURE_STORAGE_ACCOUNT)
    if not storage_account_key:
        raise CLIError(MSG_CONFIGURE_STORAGE_KEY)
    result.node_setup.mount_volumes.azure_blob_file_systems.append(models.AzureBlobFileSystemReference(
        relative_mount_path=mount_path,
        account_name=storage_account_name,
        container_name=container_name,
        credentials=models.AzureStorageCredentialsInfo(account_key=storage_account_key)))
    return result


def _get_image_reference_or_die(image):
    """Returns image reference for the given image alias.

    :param str image: image alias.
    :return models.ImageReference: the image reference.
    :raise CLIError: if the image with given alias was not found.
    """
    reference = SUPPORTED_IMAGES.get(image.lower(), None)
    if not reference:
        raise CLIError('Unsupported image alias "{0}"'.format(image))
    return reference


def _update_nodes_information(params, image, vm_size, min_nodes, max_nodes):
    """Updates cluster's nodes information.

    :param models.ClusterCreateParameters params: cluster create parameters.
    :param str or None image: image.
    :param str or None vm_size: VM size.
    :param int min_nodes: min number of nodes.
    :param int or None max_nodes: max number of nodes.
    :return models.ClusterCreateParameters: updated parameters.
    """
    result = copy.deepcopy(params)
    if vm_size:
        result.vm_size = vm_size
    if not result.vm_size:
        raise CLIError('Please provide VM size')
    if image:
        result.virtual_machine_configuration = models.VirtualMachineConfiguration(_get_image_reference_or_die(image))
    if min_nodes == max_nodes:
        result.scale_settings = models.ScaleSettings(manual=models.ManualScaleSettings(min_nodes))
    elif max_nodes is not None:
        result.scale_settings = models.ScaleSettings(auto_scale=models.AutoScaleSettings(min_nodes, max_nodes))
    if not result.scale_settings or (not result.scale_settings.manual and not result.scale_settings.auto_scale):
        raise CLIError('Please provide scale setting for the cluster via configuration file or via --min and --max '
                       'parameters.')
    return result


def create_cluster(cmd, client,  # pylint: disable=too-many-locals
                   resource_group, cluster_name, json_file=None, location=None, user_name=None,
                   ssh_key=None, password=None, image='UbuntuLTS', vm_size=None, min_nodes=0, max_nodes=None,
                   nfs_name=None, nfs_resource_group=None, nfs_mount_path='nfs', azure_file_share=None,
                   afs_mount_path='afs', container_name=None, container_mount_path='bfs', account_name=None,
                   account_key=None, no_wait=False):
    if json_file:
        with open(json_file) as f:
            json_obj = json.load(f)
            params = _get_deserializer()('ClusterCreateParameters', json_obj)
    else:
        params = models.ClusterCreateParameters(None, None, None)
    params = _update_cluster_create_parameters_with_env_variables(cmd.cli_ctx, params, account_name, account_key)
    params = _update_user_account_settings(params, user_name, ssh_key, password)
    if location:
        params.location = location
    if not params.location:
        raise CLIError('Please provide location for cluster creation.')
    params = _update_nodes_information(params, image, vm_size, min_nodes, max_nodes)
    if nfs_name:
        file_server = client.file_servers.get(nfs_resource_group if nfs_resource_group else resource_group, nfs_name)
        params = _add_nfs_to_cluster_create_parameters(params, file_server.id, nfs_mount_path)
    if azure_file_share:
        params = _add_azure_file_share_to_cluster_create_parameters(cmd.cli_ctx, params, azure_file_share,
                                                                    afs_mount_path, account_name, account_key)
    if container_name:
        params = _add_azure_container_to_cluster_create_parameters(cmd.cli_ctx, params, container_name,
                                                                   container_mount_path, account_name, account_key)

    return sdk_no_wait(no_wait, client.clusters.create, resource_group, cluster_name, params)


def list_clusters(client, resource_group=None):
    if resource_group:
        return list(client.list_by_resource_group(resource_group))
    return list(client.list())


def resize_cluster(client, resource_group, cluster_name, target):
    return client.update(resource_group, cluster_name, scale_settings=models.ScaleSettings(
        manual=models.ManualScaleSettings(target)))


def set_cluster_auto_scale_parameters(client, resource_group, cluster_name, min_nodes, max_nodes):
    return client.update(resource_group, cluster_name, scale_settings=models.ScaleSettings(
        auto_scale=models.AutoScaleSettings(min_nodes, max_nodes)))


def create_job(client, resource_group, job_name, json_file, location=None, cluster_name=None,
               cluster_resource_group=None, no_wait=False):
    with open(json_file) as f:
        json_obj = json.load(f)
        params = _get_deserializer()('JobCreateParameters', json_obj)
        if location:
            params.location = location
        if not params.location:
            raise CLIError('Please provide location for job creation.')
        # If cluster name is specified, find the cluster and use its resource id for the new job.
        if cluster_name is not None:
            if cluster_resource_group is None:  # The job must be created in the cluster's resource group.
                cluster_resource_group = resource_group
            cluster = client.clusters.get(cluster_resource_group, cluster_name)
            params.cluster = models.ResourceId(cluster.id)
        if params.cluster is None:
            raise CLIError('Please provide cluster information via command line or configuration file.')
        return sdk_no_wait(no_wait, client.jobs.create, resource_group, job_name, params)


def list_jobs(client, resource_group=None):
    if resource_group:
        return list(client.list_by_resource_group(resource_group))
    return list(client.list())


def list_files(client, resource_group, job_name, directory):
    options = models.JobsListOutputFilesOptions(directory)
    return list(client.list_output_files(resource_group, job_name, options))


def sigint_handler(*_):
    # Some libs do not handle KeyboardInterrupt nicely and print junk
    # messages. So, let's just exit without any cleanup.
    os._exit(0)  # pylint: disable=protected-access


def tail_file(client, resource_group, job_name, directory, file_name):
    """Output the current content of the file and outputs appended data as the file grows (similar to 'tail -f').

    Press Ctrl-C to interrupt the output.

    :param BatchAIClient client: the client.
    :param resource_group: name of the resource group.
    :param job_name: job's name.
    :param directory: job's output directory id.
    :param file_name: name of the file.
    """
    signal.signal(signal.SIGINT, sigint_handler)
    url = None
    # Wait until the file become available.
    while url is None:
        files = list_files(client, resource_group, job_name, directory)
        for f in files:
            if f.name == file_name:
                url = f.download_url
                break
        if url is None:
            time.sleep(1)
    # Stream the file
    downloaded = 0
    while True:
        r = requests.get(url, headers={'Range': 'bytes={0}-'.format(downloaded)},
                         verify=(not should_disable_connection_verify()))
        if int(r.status_code / 100) == 2:
            downloaded += len(r.content)
            print(r.content.decode(), end='')


def create_file_server(client, resource_group, file_server_name, json_file=None, vm_size=None, location=None,
                       user_name=None, ssh_key=None, password=None, disk_count=None, disk_size=None,
                       storage_sku='Premium_LRS', no_wait=False):
    if json_file:
        with open(json_file) as f:
            json_obj = json.load(f)
            parameters = _get_deserializer()('FileServerCreateParameters', json_obj)
    else:
        parameters = models.FileServerCreateParameters(None, None, None, None)

    parameters = _update_user_account_settings(parameters, user_name, ssh_key, password)
    if location:
        parameters.location = location
    if not parameters.location:
        raise CLIError('Please provide location for cluster creation.')
    if not parameters.data_disks:
        parameters.data_disks = models.DataDisks(None, None, None)
    if disk_size:
        parameters.data_disks.disk_size_in_gb = disk_size
    if not parameters.data_disks.disk_size_in_gb:
        raise CLIError('Please provide disk size in Gb.')
    if disk_count:
        parameters.data_disks.disk_count = disk_count
    if not parameters.data_disks.disk_count:
        raise CLIError('Please provide number of data disks (at least one disk is required).')
    if storage_sku:
        parameters.data_disks.storage_account_type = storage_sku
    if not parameters.data_disks.storage_account_type:
        raise CLIError('Please provide storage account type (storage sku).')
    if vm_size:
        parameters.vm_size = vm_size
    if not parameters.vm_size:
        raise CLIError('Please provide VM size.')
    return sdk_no_wait(no_wait, client.create, resource_group, file_server_name, parameters)


def list_file_servers(client, resource_group=None):
    if resource_group:
        return list(client.list_by_resource_group(resource_group))
    return list(client.list())
