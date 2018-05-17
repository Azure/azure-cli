# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines
from __future__ import print_function

import string
from random import shuffle

import collections
import copy
import datetime
import getpass
import json
import os
import signal
import sys
import time
from six.moves import urllib_parse

import requests

from knack.log import get_logger
from knack.util import CLIError
from msrest.serialization import Deserializer
from msrestazure.azure_exceptions import CloudError
from msrestazure.tools import is_valid_resource_id

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core import keys
from azure.cli.core.profiles import ResourceType, get_sdk

import azure.mgmt.batchai.models as models


# Environment variables for specifying azure storage account and key. We want the user to make explicit
# decision about which storage account to use instead of using his default account specified via AZURE_STORAGE_ACCOUNT
# and AZURE_STORAGE_KEY.
AZURE_BATCHAI_STORAGE_ACCOUNT = 'AZURE_BATCHAI_STORAGE_ACCOUNT'
AZURE_BATCHAI_STORAGE_KEY = 'AZURE_BATCHAI_STORAGE_KEY'
MSG_CONFIGURE_STORAGE_ACCOUNT = 'Please configure Azure Storage account name via AZURE_BATCHAI_STORAGE_ACCOUNT or ' \
                                'provide storage_account value in batchai section of your az configuration file.'
MSG_CONFIGURE_STORAGE_KEY = 'Please configure Azure Storage account key via AZURE_BATCHAI_STORAGE_KEY or ' \
                            'provide storage_key value in batchai section of your az configuration file.'
STANDARD_OUTPUT_DIRECTORY_ID = 'stdouterr'

# Parameters of auto storage
AUTO_STORAGE_RESOURCE_GROUP = 'batchaiautostorage'
AUTO_STORAGE_CONTAINER_NAME = 'batchaicontainer'
AUTO_STORAGE_SHARE_NAME = 'batchaishare'
AUTO_STORAGE_ACCOUNT_PREFIX = 'bai'
AUTO_STORAGE_CONTAINER_PATH = 'autobfs'
AUTO_STORAGE_SHARE_PATH = 'autoafs'

# Placeholders which customer may use in his config file for cluster creation.
AZURE_BATCHAI_STORAGE_KEY_PLACEHOLDER = '<{0}>'.format(AZURE_BATCHAI_STORAGE_KEY)
AZURE_BATCHAI_STORAGE_ACCOUNT_PLACEHOLDER = '<{0}>'.format(AZURE_BATCHAI_STORAGE_ACCOUNT)

# Default expiration time for file download URLs.
DEFAULT_URL_EXPIRY_MIN = 60

# Supported images.
SUPPORTED_IMAGE_ALIASES = {
    "UbuntuLTS": models.ImageReference(
        publisher='Canonical',
        offer='UbuntuServer',
        sku='16.04-LTS'
    ),
    "UbuntuDSVM": models.ImageReference(
        publisher='microsoft-ads',
        offer='linux-data-science-vm-ubuntu',
        sku='linuxdsvmubuntu'
    )
}

# Type of entries reported by list startup files.
LogFile = collections.namedtuple('LogFile', 'name download_url is_directory size')

logger = get_logger(__name__)


def _get_resource_group_location(cli_ctx, resource_group):
    client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    return client.resource_groups.get(resource_group).location


def _get_default_ssh_public_key_location():
    path = os.path.join(os.path.expanduser('~'), '.ssh', 'id_rsa.pub')
    if os.path.exists(path):
        return path
    return None


def _get_deserializer():
    client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
    return Deserializer(client_models)


def _ensure_resource_not_exist(client, resource_group, name):
    try:
        client.get(resource_group, name)
        raise CLIError('"{0}" already exists in "{1}" resource group'.format(name, resource_group))
    except CloudError as e:
        if e.status_code != 404:
            raise


def _verify_subnet(client, subnet, nfs_name, nfs_resource_group):
    if not subnet:
        return
    if not is_valid_resource_id(subnet):
        raise CLIError('Ill-formed subnet resource id')

    # check there are no conflicts between provided subnet and mounted nfs
    if not nfs_name:
        return
    nfs = None  # type: models.FileServer
    try:
        nfs = client.file_servers.get(nfs_name, nfs_resource_group)
    except CloudError as e:
        if e.status_code != 404:
            raise
    if not nfs:
        # CLI will return the error during nfs validation
        return
    if nfs.subnet.id != subnet:
        raise CLIError('Cluster and mounted NFS must be in the same subnet.')


def _get_storage_management_client(cli_ctx):
    from azure.mgmt.storage import StorageManagementClient
    return get_mgmt_service_client(cli_ctx, StorageManagementClient)


def _get_storage_account_key(cli_ctx, account_name, account_key):
    """Returns account key for the given storage account.

    :param str account_name: storage account name.
    :param str or None account_key: account key provide as command line argument.
    """
    if account_key:
        return account_key
    storage_client = _get_storage_management_client(cli_ctx)
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


def _get_account_name_from_azure_file_url(azure_file_url):
    """Extracts account name from Azure File URL

    :param str azure_file_url: Azure File URL
    :return str: account name
    """
    if not azure_file_url:
        raise CLIError('Azure File URL cannot absent or be empty')
    o = urllib_parse.urlparse(azure_file_url)
    try:
        account, _ = o.netloc.split('.', 1)
        return account
    except ValueError:
        raise CLIError('Ill-formed Azure File URL "{0}"'.format(azure_file_url))


def _get_effective_credentials(cli_ctx, existing_credentials, account_name):
    """Returns AzureStorageCredentialInfo for the account

    :param models.AzureStorageCredentialsInfo existing_credentials: known credentials
    :param str account_name: storage account name
    :return models.AzureStorageCredentialsInfo: credentials to be used
    """
    if existing_credentials and (existing_credentials.account_key or existing_credentials.account_key_secret_reference):
        return existing_credentials
    return models.AzureStorageCredentialsInfo(
        account_key=_get_storage_account_key(cli_ctx, account_name, account_key=None))


def _patch_mount_volumes(cli_ctx, volumes, account_name=None, account_key=None):
    """Patches mount volumes by replacing placeholders and adding credentials information.

    :param models.MountVolumes or None volumes: mount volumes.
    :param str or None account_name: name of the storage account provided as command line argument.
    :param str or None account_key: storage account key provided as command line argument.
    :return models.ClusterCreateParameters: updated parameters.
    """
    if volumes is None:
        return None
    result = copy.deepcopy(volumes)  # type: models.MountVolumes
    storage_account_name, storage_account_key = _get_effective_storage_account_name_and_key(
        cli_ctx, account_name, account_key)
    require_storage_account = False
    require_storage_account_key = False

    # Patch parameters of azure file share.
    if result.azure_file_shares:
        for ref in result.azure_file_shares:
            # Populate account name if it was not provided
            if not ref.account_name:
                ref.account_name = _get_account_name_from_azure_file_url(ref.azure_file_url)
            # Replace placeholders
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
            if not ref.credentials and ref.account_name == storage_account_name:
                require_storage_account_key = True
                ref.credentials = models.AzureStorageCredentialsInfo(account_key=storage_account_key)
            if ref.account_name:
                ref.credentials = _get_effective_credentials(cli_ctx, ref.credentials, ref.account_name)

    # Patch parameters of blob file systems.
    if result.azure_blob_file_systems:
        for ref in result.azure_blob_file_systems:
            # Replace placeholders
            if ref.account_name == AZURE_BATCHAI_STORAGE_ACCOUNT_PLACEHOLDER:
                require_storage_account = True
                ref.account_name = storage_account_name
            if ref.credentials and ref.credentials.account_key == AZURE_BATCHAI_STORAGE_KEY_PLACEHOLDER:
                require_storage_account_key = True
                ref.credentials.account_key = storage_account_key
            if not ref.credentials and ref.account_name == storage_account_name:
                require_storage_account_key = True
                ref.credentials = models.AzureStorageCredentialsInfo(account_key=storage_account_key)
            # Populate the rest of credentials based on the account name
            if not ref.account_name:
                raise CLIError('Ill-formed Azure Blob File System reference in the configuration file - no account '
                               'name provided.')
            if ref.account_name:
                ref.credentials = _get_effective_credentials(cli_ctx, ref.credentials, ref.account_name)

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
    if hasattr(result, 'user_account_settings'):
        parent = result
    else:
        if result.ssh_configuration is None:
            result.ssh_configuration = models.SshConfiguration(user_account_settings=None)
        parent = result.ssh_configuration
    if parent.user_account_settings is None:
        parent.user_account_settings = models.UserAccountSettings()
    # Get effective user name, password and key trying them in the following order: provided via command line,
    # provided in the config file, current user name and his default public ssh key.
    effective_user_name = admin_user_name or parent.user_account_settings.admin_user_name or getpass.getuser()
    effective_password = password or parent.user_account_settings.admin_user_password
    # Use default ssh public key only if no password is configured.
    effective_key = (ssh_key or parent.user_account_settings.admin_user_ssh_public_key or
                     (None if effective_password else _get_default_ssh_public_key_location()))
    if effective_key:
        if os.path.exists(os.path.expanduser(effective_key)):
            with open(os.path.expanduser(effective_key)) as f:
                effective_key = f.read()
    try:
        if effective_key and not keys.is_valid_ssh_rsa_public_key(effective_key):
            raise CLIError('Incorrect ssh public key value.')
    except Exception:
        raise CLIError('Incorrect ssh public key value.')

    parent.user_account_settings.admin_user_name = effective_user_name
    parent.user_account_settings.admin_user_ssh_public_key = effective_key
    parent.user_account_settings.admin_user_password = effective_password

    if not parent.user_account_settings.admin_user_name:
        raise CLIError('Please provide admin user name.')

    if (not parent.user_account_settings.admin_user_ssh_public_key and
            not parent.user_account_settings.admin_user_password):
        raise CLIError('Please provide admin user password or ssh key.')

    return result


def _add_nfs_to_mount_volumes(volumes, file_server_id, mount_path):
    """Adds NFS to the mount volumes.

    :param models.MountVolumes or None volumes: existing mount volumes.
    :param str file_server_id: resource id of the file server.
    :param str mount_path: relative mount path for the file server.
    :return models.ClusterCreateParameters: updated parameters.
    """
    result = copy.deepcopy(volumes) if volumes else models.MountVolumes()
    if not mount_path:
        raise CLIError('File server relative mount path cannot be empty.')
    if result.file_servers is None:
        result.file_servers = []
    result.file_servers.append(models.FileServerReference(
        relative_mount_path=mount_path,
        file_server=models.ResourceId(id=file_server_id),
        mount_options="rw"))
    return result


def _get_azure_file_url(cli_ctx, account_name, azure_file_share):
    """Returns Azure File URL for the given account

    :param str account_name: account name
    :param str azure_file_share: name of the share
    :return str: Azure File URL to be used in mount volumes
    """
    return 'https://{0}.file.{1}/{2}'.format(account_name, cli_ctx.cloud.suffixes.storage_endpoint, azure_file_share)


def _add_azure_file_share_to_mount_volumes(cli_ctx, volumes, azure_file_share, mount_path, account_name=None,
                                           account_key=None):
    """Add Azure File share to the mount volumes.

    :param model.MountVolumes volumes: existing mount volumes.
    :param str azure_file_share: name of the azure file share.
    :param str mount_path: relative mount path for Azure File share.
    :param str or None account_name: storage account name provided as command line argument.
    :param str or None account_key: storage account key provided as command line argument.
    :return models.ClusterCreateParameters: updated parameters.
    """
    result = copy.deepcopy(volumes) if volumes else models.MountVolumes()
    if not mount_path:
        raise CLIError('Azure File share relative mount path cannot be empty.')
    if result.azure_file_shares is None:
        result.azure_file_shares = []
    effective_account_name, effective_account_key = _get_effective_storage_account_name_and_key(cli_ctx, account_name,
                                                                                                account_key)
    if not effective_account_name:
        raise CLIError(MSG_CONFIGURE_STORAGE_ACCOUNT)
    if not effective_account_key:
        raise CLIError(MSG_CONFIGURE_STORAGE_KEY)
    result.azure_file_shares.append(models.AzureFileShareReference(
        relative_mount_path=mount_path,
        account_name=effective_account_name,
        azure_file_url=_get_azure_file_url(cli_ctx, effective_account_name, azure_file_share),
        credentials=models.AzureStorageCredentialsInfo(account_key=effective_account_key)))
    return result


def _add_azure_container_to_mount_volumes(cli_ctx, volumes, container_name, mount_path, account_name=None,
                                          account_key=None):
    """Add Azure Storage container to the mount volumes.

    :param model.MountVolumes: existing mount volumes.
    :param str container_name: container name.
    :param str mount_path: relative mount path for the container.
    :param str or None account_name: storage account name provided as command line argument.
    :param str or None account_key: storage account key provided as command line argument.
    :return models.ClusterCreateParameters: updated parameters.
    """
    result = copy.deepcopy(volumes) if volumes else models.MountVolumes()
    if not mount_path:
        raise CLIError('Azure Storage Container relative mount path cannot be empty.')
    if result.azure_blob_file_systems is None:
        result.azure_blob_file_systems = []
    storage_account_name, storage_account_key = _get_effective_storage_account_name_and_key(cli_ctx, account_name,
                                                                                            account_key)
    if not storage_account_name:
        raise CLIError(MSG_CONFIGURE_STORAGE_ACCOUNT)
    if not storage_account_key:
        raise CLIError(MSG_CONFIGURE_STORAGE_KEY)
    result.azure_blob_file_systems.append(models.AzureBlobFileSystemReference(
        relative_mount_path=mount_path,
        account_name=storage_account_name,
        container_name=container_name,
        credentials=models.AzureStorageCredentialsInfo(account_key=storage_account_key)))
    return result


def _get_image_reference(image, custom_image):
    """Returns image reference for the given image and custom image.

    :param str image or None: image alias or full spec.
    :param str custom_image or None: resource id of the custom image.
    :raise CLIError: if the image with given alias was not found.
    """
    if custom_image and not image:
        raise CLIError('You need to specify --image argument with information about the custom image')
    if custom_image and not is_valid_resource_id(custom_image):
        raise CLIError('Ill-formed custom image resource id')
    if ':' in image:
        # full image specification is provided
        try:
            publisher, offer, sku, version = image.split(':')
            if not publisher:
                raise CLIError('Image publisher must be provided in --image argument')
            if not offer:
                raise CLIError('Image offer must be provided in --image argument')
            if not sku:
                raise CLIError('Image sku must be provided in --image argument')
            return models.ImageReference(
                publisher=publisher,
                offer=offer,
                sku=sku,
                version=version or None,
                virtual_machine_image_id=custom_image
            )
        except ValueError:
            raise CLIError('--image must have format "publisher:offer:sku:version" or "publisher:offer:sku:"')

    # image alias is used
    reference = None
    for alias, value in SUPPORTED_IMAGE_ALIASES.items():
        if alias.lower() == image.lower():
            reference = value
    if not reference:
        raise CLIError('Unsupported image alias "{0}", supported aliases are {1}'.format(
            image, ', '.join(SUPPORTED_IMAGE_ALIASES.keys())))
    result = copy.deepcopy(reference)
    result.virtual_machine_image_id = custom_image
    return result


def _get_scale_settings(initial_count, min_count, max_count):
    """Returns scale settings for a cluster with gine parameters"""
    if not initial_count and not min_count and not max_count:
        # Get from the config file
        return None
    if sum([1 if v is not None else 0 for v in (min_count, max_count)]) == 1:
        raise CLIError('You need to either provide both min and max node counts or not provide any of them')
    if min_count is not None and max_count is not None and min_count > max_count:
        raise CLIError('Maximum nodes count must be greater or equal to minimum nodes count')
    if min_count == max_count:
        if min_count is None or initial_count == min_count:
            return models.ScaleSettings(
                manual=models.ManualScaleSettings(target_node_count=initial_count))
        if initial_count is None:
            return models.ScaleSettings(
                manual=models.ManualScaleSettings(target_node_count=min_count)
            )
    return models.ScaleSettings(
        auto_scale=models.AutoScaleSettings(
            minimum_node_count=min_count,
            maximum_node_count=max_count,
            initial_node_count=initial_count or 0))


def _update_nodes_information(params, image, custom_image, vm_size, vm_priority, target, min_nodes, max_nodes):
    """Updates cluster's nodes information.

    :param models.ClusterCreateParameters params: cluster create parameters.
    :param str or None image: image.
    :param str or None custom_image: custom image resource id.
    :param str or None vm_size: VM size.
    :param str vm_priority: Priority.
    :param int or None target: initial number of nodes.
    :param int or None min_nodes: min number of nodes.
    :param int or None max_nodes: max number of nodes.
    :return models.ClusterCreateParameters: updated parameters.
    """
    result = copy.deepcopy(params)
    if vm_size:
        result.vm_size = vm_size
    if not result.vm_size:
        raise CLIError('Please provide VM size')
    if vm_priority:
        result.vm_priority = vm_priority
    if image or custom_image:
        result.virtual_machine_configuration = models.VirtualMachineConfiguration(
            image_reference=_get_image_reference(image, custom_image))
    scale_settings = _get_scale_settings(target, min_nodes, max_nodes)
    if scale_settings:
        result.scale_settings = scale_settings
    if not result.scale_settings or (not result.scale_settings.manual and not result.scale_settings.auto_scale):
        raise CLIError('Please provide scale setting for the cluster via command line or configuration file')
    return result


def _get_auto_storage_resource_group():
    return AUTO_STORAGE_RESOURCE_GROUP


def _configure_auto_storage(cli_ctx, location):
    """Configures auto storage account for the cluster

    :param str location: location for the auto-storage account.
    :return (str, str): a tuple with auto storage account name and key.
    """
    from azure.mgmt.resource.resources.models import ResourceGroup
    BlockBlobService, FileService = get_sdk(cli_ctx, ResourceType.DATA_STORAGE,
                                            'blob#BlockBlobService', 'file#FileService')
    resource_group = _get_auto_storage_resource_group()
    resource_client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    if resource_client.resource_groups.check_existence(resource_group):
        logger.warning('BatchAI will use existing %s resource group for auto-storage account',
                       resource_group)
    else:
        logger.warning('Creating %s resource for auto-storage account', resource_group)
        resource_client.resource_groups.create_or_update(
            resource_group, ResourceGroup(location=location))
    storage_client = _get_storage_management_client(cli_ctx)
    account = None
    for a in storage_client.storage_accounts.list_by_resource_group(resource_group):
        if a.primary_location == location.lower().replace(' ', ''):
            account = a.name
            logger.warning('Using existing %s storage account as an auto-storage account', account)
            break
    if account is None:
        account = _create_auto_storage_account(storage_client, resource_group, location)
        logger.warning('Created auto storage account %s', account)
    key = _get_storage_account_key(cli_ctx, account, None)
    file_service = FileService(account, key)
    file_service.create_share(AUTO_STORAGE_SHARE_NAME, fail_on_exist=False)
    blob_service = BlockBlobService(account, key)
    blob_service.create_container(AUTO_STORAGE_CONTAINER_NAME, fail_on_exist=False)
    return account, key


def _generate_auto_storage_account_name():
    """Generates unique name for auto storage account"""
    characters = list(string.ascii_lowercase * 12)
    shuffle(characters)
    return AUTO_STORAGE_ACCOUNT_PREFIX + ''.join(characters[:12])


def _create_auto_storage_account(storage_client, resource_group, location):
    """Creates new auto storage account in the given resource group and location

    :param StorageManagementClient storage_client: storage client.
    :param str resource_group: name of the resource group.
    :param str location: location.
    :return str: name of the created storage account.
    """
    from azure.mgmt.storage.models import Kind, Sku, SkuName
    name = _generate_auto_storage_account_name()
    check = storage_client.storage_accounts.check_name_availability(name)
    while not check.name_available:
        name = _generate_auto_storage_account_name()
        check = storage_client.storage_accounts.check_name_availability(name).name_available
    storage_client.storage_accounts.create(resource_group, name, {
        'sku': Sku(SkuName.standard_lrs),
        'kind': Kind.storage,
        'location': location}).result()
    return name


def _add_setup_task(cmd_line, output, cluster):
    """Adds a setup task with given command line and output destination to the cluster.

    :param str cmd_line: node setup command line.
    :param str output: output destination.
    :param models.ClusterCreateParameters cluster: cluster creation parameters.
    """
    if cmd_line is None:
        return cluster
    if output is None:
        raise CLIError('--setup-task requires providing of --setup-task-output')
    cluster = copy.deepcopy(cluster)
    cluster.node_setup = cluster.node_setup or models.NodeSetup()
    cluster.node_setup.setup_task = models.SetupTask(
        command_line=cmd_line,
        std_out_err_path_prefix=output,
        run_elevated=False)
    return cluster


def _generate_ssh_keys():
    """Generates ssh keys pair"""
    private_key_path = os.path.join(os.path.expanduser('~'), '.ssh', 'id_rsa')
    public_key_path = os.path.join(os.path.expanduser('~'), '.ssh', 'id_rsa.pub')
    if os.path.exists(private_key_path) and os.path.exists(public_key_path):
        logger.warning('Reusing existing ssh public key from ~/.ssh')
        return
    if os.path.exists(private_key_path):
        logger.warning('SSH private key id_rsa exists but public key is missing. Please export the public key.')
        return
    keys.generate_ssh_keys(private_key_path, public_key_path)
    logger.warning('SSH key files id_rsa and id_rsa.pub have been generated under ~/.ssh to allow SSH access to the '
                   'nodes. If using machines without permanent storage, back up your keys to a safe location.')


def create_cluster(cmd, client,  # pylint: disable=too-many-locals
                   resource_group, cluster_name, json_file=None, location=None, user_name=None,
                   ssh_key=None, password=None, generate_ssh_keys=None, image=None, custom_image=None,
                   use_auto_storage=False, vm_size=None, vm_priority=None, target=None, min_nodes=None,
                   max_nodes=None, subnet=None, nfs_name=None, nfs_resource_group=None, nfs_mount_path='nfs',
                   azure_file_share=None, afs_mount_path='afs', container_name=None, container_mount_path='bfs',
                   account_name=None, account_key=None, setup_task=None, setup_task_output=None):
    if generate_ssh_keys:
        _generate_ssh_keys()
        if ssh_key is None:
            ssh_key = _get_default_ssh_public_key_location()
    _ensure_resource_not_exist(client.clusters, resource_group, cluster_name)
    _verify_subnet(client, subnet, nfs_name, nfs_resource_group or resource_group)
    if json_file:
        with open(json_file) as f:
            json_obj = json.load(f)
            params = _get_deserializer()('ClusterCreateParameters', json_obj)
    else:
        # noinspection PyTypeChecker
        params = models.ClusterCreateParameters()
    if params.node_setup:
        params.node_setup.mount_volumes = _patch_mount_volumes(
            cmd.cli_ctx, params.node_setup.mount_volumes, account_name, account_key)
    params = _update_user_account_settings(params, user_name, ssh_key, password)
    params.location = location or _get_resource_group_location(cmd.cli_ctx, resource_group)
    params = _update_nodes_information(params, image, custom_image, vm_size, vm_priority, target, min_nodes, max_nodes)
    if nfs_name or azure_file_share or container_name:
        params.node_setup = params.node_setup or models.NodeSetup()
    mount_volumes = params.node_setup.mount_volumes if params.node_setup else None
    if nfs_name:
        file_server = client.file_servers.get(nfs_resource_group or resource_group, nfs_name)
        mount_volumes = _add_nfs_to_mount_volumes(mount_volumes, file_server.id, nfs_mount_path)
    if azure_file_share:
        mount_volumes = _add_azure_file_share_to_mount_volumes(cmd.cli_ctx, mount_volumes, azure_file_share,
                                                               afs_mount_path, account_name, account_key)
    if container_name:
        mount_volumes = _add_azure_container_to_mount_volumes(cmd.cli_ctx, mount_volumes, container_name,
                                                              container_mount_path, account_name, account_key)
    if use_auto_storage:
        auto_storage_account, auto_storage_key = _configure_auto_storage(cmd.cli_ctx, params.location)
        mount_volumes = _add_azure_file_share_to_mount_volumes(
            cmd.cli_ctx, mount_volumes, AUTO_STORAGE_SHARE_NAME, AUTO_STORAGE_SHARE_PATH,
            auto_storage_account, auto_storage_key)
        mount_volumes = _add_azure_container_to_mount_volumes(
            cmd.cli_ctx, mount_volumes, AUTO_STORAGE_CONTAINER_NAME, AUTO_STORAGE_CONTAINER_PATH,
            auto_storage_account, auto_storage_key)
    if mount_volumes:
        if params.node_setup is None:
            params.node_setup = models.NodeSetup()
        params.node_setup.mount_volumes = mount_volumes
    if subnet:
        params.subnet = models.ResourceId(id=subnet)
    if setup_task:
        params = _add_setup_task(setup_task, setup_task_output, params)
    return client.clusters.create(resource_group, cluster_name, params)


def list_clusters(client, resource_group=None):
    if resource_group:
        return list(client.list_by_resource_group(resource_group))
    return list(client.list())


def resize_cluster(client, resource_group, cluster_name, target):
    return client.update(resource_group, cluster_name, scale_settings=models.ScaleSettings(
        manual=models.ManualScaleSettings(target_node_count=target)))


def set_cluster_auto_scale_parameters(client, resource_group, cluster_name, min_nodes, max_nodes):
    return client.update(resource_group, cluster_name, scale_settings=models.ScaleSettings(
        auto_scale=models.AutoScaleSettings(minimum_node_count=min_nodes, maximum_node_count=max_nodes)))


def _is_on_mount_point(path, mount_path):
    """Checks if path is on mount_path"""
    path = os.path.normpath(path).replace('\\', '/')
    mount_path = os.path.normpath(mount_path).replace('\\', '/')
    return path == mount_path or os.path.commonprefix([path, mount_path + '/']) == mount_path + '/'


def list_node_setup_files(cmd, client, resource_group, cluster_name, path='.', expiry=DEFAULT_URL_EXPIRY_MIN):
    cluster = client.get(resource_group, cluster_name)  # type: models.Cluster
    return _list_node_setup_files_for_cluster(cmd.cli_ctx, cluster, path, expiry)


def _list_node_setup_files_for_cluster(cli_ctx, cluster, path, expiry):
    """Lists node setup task's log files for the given cluster.

    :param models.Cluster cluster: the cluster.
    :param str path: relative path under cluster node setup task's output directory.
    :param int expiry: time in seconds for how long generated SASes will remain valid.
    """
    unsupported_location = 'List files is supported only for clusters with startup task configure to store its ' \
                           'output on Azure File Share or Azure Blob Container'
    if cluster.node_setup is None or cluster.node_setup.setup_task is None:
        # Nothing to check or return if there is no setup task.
        return []
    prefix = cluster.node_setup.setup_task.std_out_err_path_prefix
    if not _is_on_mount_point(prefix, '$AZ_BATCHAI_MOUNT_ROOT'):
        # The stdouterr directory must be on $AZ_BATCHAI_MOUNT_ROOT
        raise CLIError(unsupported_location)
    suffix = cluster.node_setup.setup_task.std_out_err_path_suffix
    if not suffix:
        # Clusters created with older API version do not report the path suffix, so we cannot find their files.
        raise CLIError('List files is not supported for this cluster')
    relative_mount_path = prefix[len('$AZ_BATCHAI_MOUNT_ROOT/'):]
    if cluster.node_setup.mount_volumes is None:
        # If nothing is mounted, the files were stored somewhere else and we cannot find them.
        raise CLIError(unsupported_location)
    # try mounted Azure file shares
    for afs in cluster.node_setup.mount_volumes.azure_file_shares or []:
        if _is_on_mount_point(relative_mount_path, afs.relative_mount_path):
            return _get_files_from_afs(cli_ctx, afs, os.path.join(suffix, path), expiry)
    # try mounted blob containers
    for bfs in cluster.node_setup.mount_volumes.azure_blob_file_systems or []:
        if _is_on_mount_point(relative_mount_path, bfs.relative_mount_path):
            return _get_files_from_bfs(cli_ctx, bfs, os.path.join(suffix, path), expiry)
    # the folder on some other file system or on local disk
    raise CLIError(unsupported_location)


def _get_files_from_bfs(cli_ctx, bfs, path, expiry):
    """Returns a list of files and directories under given path on mounted blob container.

    :param models.AzureBlobFileSystemReference bfs: blob file system reference.
    :param str path: path to list files from.
    :param int expiry: SAS expiration time in minutes.
    """
    from azure.storage.blob import BlockBlobService
    from azure.storage.blob.models import Blob, BlobPermissions
    result = []
    service = BlockBlobService(bfs.account_name, _get_storage_account_key(cli_ctx, bfs.account_name, None))
    effective_path = _get_path_for_storage(path)
    folders = set()
    for b in service.list_blobs(bfs.container_name, effective_path + '/', delimiter='/'):
        if isinstance(b, Blob):
            name = os.path.basename(b.name)
            sas = service.generate_blob_shared_access_signature(
                bfs.container_name, b.name, BlobPermissions(read=True),
                expiry=datetime.datetime.utcnow() + datetime.timedelta(minutes=expiry))
            result.append(
                LogFile(
                    name, service.make_blob_url(bfs.container_name, b.name, 'https', sas),
                    False, b.properties.content_length))
        else:
            name = b.name.split('/')[-2]
            folders.add(name)
            result.append(LogFile(name, None, True, None))
    result = [f for f in result if f.is_directory or f.name not in folders]
    return result


def _get_path_for_storage(path):
    """Returns a path in format acceptable for passing to storage"""
    result = os.path.normpath(path).replace('\\', '/')
    if result.endswith('/.'):
        result = result[:-2]
    return result


def _get_files_from_afs(cli_ctx, afs, path, expiry):
    """Returns a list of files and directories under given path on mounted Azure File share.

    :param models.AzureFileShareReference afs: Azure file share reference.
    :param str path: path to list files from.
    :param int expiry: SAS expiration time in minutes.
    """
    FileService, File, FilePermissions = get_sdk(cli_ctx, ResourceType.DATA_STORAGE,
                                                 'file#FileService', 'file.models#File', 'file.models#FilePermissions')
    result = []
    service = FileService(afs.account_name, _get_storage_account_key(cli_ctx, afs.account_name, None))
    share_name = afs.azure_file_url.split('/')[-1]
    effective_path = _get_path_for_storage(path)
    if not service.exists(share_name, effective_path):
        return result
    for f in service.list_directories_and_files(share_name, effective_path):
        if isinstance(f, File):
            sas = service.generate_file_shared_access_signature(
                share_name, effective_path, f.name, permission=FilePermissions(read=True),
                expiry=datetime.datetime.utcnow() + datetime.timedelta(minutes=expiry))
            result.append(
                LogFile(
                    f.name, service.make_file_url(share_name, effective_path, f.name, 'https', sas),
                    False, f.properties.content_length))
        else:
            result.append(LogFile(f.name, None, True, None))
    return result


def create_job(cmd, client, resource_group, job_name, json_file, location=None, cluster_name=None,
               cluster_resource_group=None, nfs_name=None, nfs_resource_group=None, nfs_mount_path='nfs',
               azure_file_share=None, afs_mount_path='afs', container_name=None, container_mount_path='bfs',
               account_name=None, account_key=None):
    _ensure_resource_not_exist(client.jobs, resource_group, job_name)
    with open(json_file) as f:
        json_obj = json.load(f)
        params = _get_deserializer()('JobCreateParameters', json_obj)  # type: models.JobCreateParameters
        params.location = location or _get_resource_group_location(cmd.cli_ctx, resource_group)
        # If cluster name is specified, find the cluster and use its resource id for the new job.
        if cluster_name is not None:
            if cluster_resource_group is None:  # The job must be created in the cluster's resource group.
                cluster_resource_group = resource_group
            cluster = client.clusters.get(cluster_resource_group, cluster_name)
            params.cluster = models.ResourceId(id=cluster.id)
        if params.cluster is None:
            raise CLIError('Please provide cluster information via command line or configuration file.')
        if params.mount_volumes:
            params.mount_volumes = _patch_mount_volumes(
                cmd.cli_ctx, params.mount_volumes, account_name, account_key)
        # Add file systems specified via command line into mount volumes
        if nfs_name or azure_file_share or container_name:
            params.mount_volumes = params.mount_volumes or models.MountVolumes()
        mount_volumes = params.mount_volumes
        if nfs_name:
            file_server = client.file_servers.get(nfs_resource_group or resource_group, nfs_name)
            mount_volumes = _add_nfs_to_mount_volumes(mount_volumes, file_server.id, nfs_mount_path)
        if azure_file_share:
            mount_volumes = _add_azure_file_share_to_mount_volumes(cmd.cli_ctx, mount_volumes, azure_file_share,
                                                                   afs_mount_path, account_name, account_key)
        if container_name:
            mount_volumes = _add_azure_container_to_mount_volumes(cmd.cli_ctx, mount_volumes, container_name,
                                                                  container_mount_path, account_name, account_key)
        if mount_volumes:
            params.mount_volumes = mount_volumes
        return client.jobs.create(resource_group, job_name, params)


def list_jobs(client, resource_group=None):
    if resource_group:
        return list(client.list_by_resource_group(resource_group))
    return list(client.list())


def list_files(client, resource_group, job_name, output_directory_id=STANDARD_OUTPUT_DIRECTORY_ID, path='.',
               expiry=DEFAULT_URL_EXPIRY_MIN):
    options = models.JobsListOutputFilesOptions(
        outputdirectoryid=output_directory_id,
        directory=path,
        linkexpiryinminutes=expiry)
    return list(client.list_output_files(resource_group, job_name, options))


def sigint_handler(*_):
    # Some libs do not handle KeyboardInterrupt nicely and print junk
    # messages. So, let's just exit without any cleanup.
    # noinspection PyProtectedMember
    os._exit(0)  # pylint: disable=protected-access


def tail_file(client, resource_group, job_name, file_name, output_directory_id=STANDARD_OUTPUT_DIRECTORY_ID, path='.'):
    """Output the current content of the file and outputs appended data as the file grows (similar to 'tail -f').

    The output will be interrupted as soon as job is completed.

    :param BatchAIClient client: the client.
    :param resource_group: name of the resource group.
    :param job_name: job's name.
    :param output_directory_id: job's output directory id.
    :param path: path to the file.
    :param file_name: name of the file.
    """
    signal.signal(signal.SIGINT, sigint_handler)
    url = None
    # Wait until the file become available.
    reported_absence_of_file = False
    while url is None:
        files = list_files(client, resource_group, job_name, output_directory_id, path)
        for f in files:
            if f.name == file_name:
                url = f.download_url
                logger.warning('File found with URL "%s". Start streaming', url)
                break
        if url is None:
            job = client.get(resource_group, job_name)
            if job.execution_state in [models.ExecutionState.succeeded, models.ExecutionState.failed]:
                break
            if not reported_absence_of_file:
                logger.warning('The file "%s" not found. Waiting for the job to generate it.', file_name)
                reported_absence_of_file = True
            time.sleep(1)
    if url is None:
        logger.warning('The file "%s" not found for the completed job.', file_name)
        return
    # Stream the file
    downloaded = 0
    while True:
        r = requests.get(url, headers={'Range': 'bytes={0}-'.format(downloaded)})
        if int(r.status_code / 100) == 2:
            downloaded += len(r.content)
            print(r.content.decode(), end='')
        job = client.get(resource_group, job_name)
        if job.execution_state in [models.ExecutionState.succeeded, models.ExecutionState.failed]:
            break
        time.sleep(1)


def wait_for_job_completion(client, resource_group, job_name, check_interval_sec=15):
    """Waits for specified job completion and setups the exit code to the code of the job.

    :param azure.mgmt.batchai.BatchAIManagementClient client: Batch AI client.
    :param str resource_group: name of the resource group.
    :param str job_name: name of the job.
    :param int check_interval_sec: how often to check the job state.
    """
    job = client.jobs.get(resource_group_name=resource_group, job_name=job_name)  # type: models.Job
    logger.warning('Job submitted at %s', str(job.creation_time))
    last_state = None
    reported_job_start_time = False
    while True:
        info = job.execution_info  # type: models.JobPropertiesExecutionInfo
        if info and not reported_job_start_time:
            logger.warning('Job started execution at %s', str(info.start_time))
            reported_job_start_time = True
        if job.execution_state != last_state:
            logger.warning('Job state: %s', job.execution_state.name)
            last_state = job.execution_state
        if job.execution_state == models.ExecutionState.succeeded:
            logger.warning('Job completed at %s; execution took %s', str(info.end_time),
                           str(info.end_time - info.start_time))
            return
        if job.execution_state == models.ExecutionState.failed:
            _log_failed_job(resource_group, job)
            sys.exit(-1)
        time.sleep(check_interval_sec)
        job = client.jobs.get(resource_group_name=resource_group, job_name=job_name)


def _log_failed_job(resource_group, job):
    """Logs information about failed job

    :param str resource_group: resource group name
    :param models.Job job: failed job.
    """
    logger.warning('The job "%s" in resource group "%s" failed.', job.name, resource_group)
    info = job.execution_info  # type: models.JobPropertiesExecutionInfo
    if info:
        logger.warning('Job failed with exit code %d at %s; execution took %s', info.exit_code,
                       str(info.end_time), str(info.end_time - info.start_time))
        errors = info.errors
        if errors:
            for e in errors:
                details = '<none>'
                if e.details:
                    details = '\n' + '\n'.join(['{0}: {1}'.format(d.name, d.value) for d in e.details])
                logger.warning('Error message: %s\nDetails:\n %s', e.message, details)
        sys.exit(info.exit_code)
    logger.warning('Failed job has no execution info')


def create_file_server(cmd, client, resource_group, file_server_name, json_file=None, vm_size=None, location=None,
                       user_name=None, ssh_key=None, password=None, generate_ssh_keys=None,
                       disk_count=None, disk_size=None, caching_type=None, storage_sku=None, subnet=None,
                       raw=False):
    if generate_ssh_keys:
        _generate_ssh_keys()
        if ssh_key is None:
            ssh_key = _get_default_ssh_public_key_location()
    _ensure_resource_not_exist(client, resource_group, file_server_name)
    if json_file:
        with open(json_file) as f:
            json_obj = json.load(f)
            params = _get_deserializer()('FileServerCreateParameters', json_obj)
    else:
        # noinspection PyTypeChecker
        params = models.FileServerCreateParameters()
    params = _update_user_account_settings(params, user_name, ssh_key, password)
    params.location = location or _get_resource_group_location(cmd.cli_ctx, resource_group)
    if not params.data_disks:
        # noinspection PyTypeChecker
        params.data_disks = models.DataDisks()
    if disk_size:
        params.data_disks.disk_size_in_gb = disk_size
    if not params.data_disks.disk_size_in_gb:
        raise CLIError('Please provide disk size in Gb.')
    if disk_count:
        params.data_disks.disk_count = disk_count
    if not params.data_disks.disk_count:
        raise CLIError('Please provide number of data disks (at least one disk is required).')
    if caching_type:
        params.data_disks.caching_type = caching_type
    if storage_sku:
        params.data_disks.storage_account_type = storage_sku
    if not params.data_disks.storage_account_type:
        raise CLIError('Please provide storage account type (storage sku).')
    if vm_size:
        params.vm_size = vm_size
    if not params.vm_size:
        raise CLIError('Please provide VM size.')
    if subnet:
        if not is_valid_resource_id(subnet):
            raise CLIError('Ill-formed subnet resource id')
        params.subnet = models.ResourceId(id=subnet)

    return client.create(resource_group, file_server_name, params, raw=raw)


def list_file_servers(client, resource_group=None):
    if resource_group:
        return list(client.list_by_resource_group(resource_group))
    return list(client.list())
