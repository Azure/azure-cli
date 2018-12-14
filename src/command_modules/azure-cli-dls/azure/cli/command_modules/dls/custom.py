# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError

from azure.mgmt.datalake.store.models import (
    UpdateDataLakeStoreAccountParameters,
    CreateDataLakeStoreAccountParameters,
    EncryptionConfigType,
    EncryptionIdentity,
    EncryptionConfig,
    EncryptionState,
    KeyVaultMetaInfo,
    UpdateEncryptionConfig,
    UpdateKeyVaultMetaInfo)

from azure.datalake.store.enums import ExpiryOptionType
from azure.datalake.store.multithread import (ADLUploader, ADLDownloader)
from azure.cli.command_modules.dls._client_factory import (cf_dls_filesystem)
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.profiles import ResourceType


logger = get_logger(__name__)


def get_update_progress(cli_ctx):

    def _update_progress(current, total):
        hook = cli_ctx.get_progress_controller(det=True)
        if total:
            hook.add(message='Alive', value=current, total_val=total)
            if total == current:
                hook.end()
    return _update_progress


# region account
def list_adls_account(client, resource_group_name=None):
    account_list = client.list_by_resource_group(resource_group_name=resource_group_name) \
        if resource_group_name else client.list()
    return list(account_list)


def create_adls_account(cmd, client, resource_group_name, account_name, location=None, default_group=None, tags=None,
                        encryption_type=EncryptionConfigType.service_managed.value, key_vault_id=None, key_name=None,
                        key_version=None, disable_encryption=False, tier=None):

    location = location or _get_resource_group_location(cmd.cli_ctx, resource_group_name)
    create_params = CreateDataLakeStoreAccountParameters(
        location=location,
        tags=tags,
        default_group=default_group,
        new_tier=tier)

    if not disable_encryption:
        identity = EncryptionIdentity()
        config = EncryptionConfig(type=encryption_type)
        if encryption_type == EncryptionConfigType.user_managed:
            if not key_name or not key_vault_id or not key_version:
                # pylint: disable=line-too-long
                raise CLIError('For user managed encryption, --key_vault_id, --key_name and --key_version are required parameters and must be supplied.')
            config.key_vault_meta_info = KeyVaultMetaInfo(
                key_vault_resource_id=key_vault_id,
                encryption_key_name=key_name,
                encryption_key_version=key_version)
        else:
            if key_name or key_vault_id or key_version:
                # pylint: disable=line-too-long
                logger.warning('User supplied Key Vault information. For service managed encryption user supplied Key Vault information is ignored.')

        create_params.encryption_config = config
        create_params.identity = identity
    else:
        create_params.encryption_state = EncryptionState.disabled
        create_params.identity = None
        create_params.encryption_config = None

    return client.create(resource_group_name, account_name, create_params).result()


def update_adls_account(client, account_name, resource_group_name, tags=None, default_group=None, firewall_state=None,
                        allow_azure_ips=None, trusted_id_provider_state=None, tier=None, key_version=None):
    update_params = UpdateDataLakeStoreAccountParameters(
        tags=tags,
        default_group=default_group,
        firewall_state=firewall_state,
        firewall_allow_azure_ips=allow_azure_ips,
        trusted_id_provider_state=trusted_id_provider_state,
        new_tier=tier)

    # this will fail if the encryption is not user managed, as service managed key rotation is not supported.
    if key_version:
        update_params.encryption_config = UpdateEncryptionConfig(
            key_vault_meta_info=UpdateKeyVaultMetaInfo(encryption_key_version=key_version))

    return client.update(resource_group_name, account_name, update_params).result()
# endregion


# region firewall
def add_adls_firewall_rule(client,
                           account_name,
                           firewall_rule_name,
                           start_ip_address,
                           end_ip_address,
                           resource_group_name):
    return client.create_or_update(resource_group_name,
                                   account_name,
                                   firewall_rule_name,
                                   start_ip_address,
                                   end_ip_address)
# endregion


# region virtual network
def add_adls_virtual_network_rule(client,
                                  account_name,
                                  virtual_network_rule_name,
                                  subnet,
                                  resource_group_name):
    return client.create_or_update(resource_group_name,
                                   account_name,
                                   virtual_network_rule_name,
                                   subnet)
# endregion


# region filesystem
def get_adls_item(cmd, account_name, path):
    return cf_dls_filesystem(cmd.cli_ctx, account_name).info(path)


def list_adls_items(cmd, account_name, path):
    return cf_dls_filesystem(cmd.cli_ctx, account_name).ls(path, detail=True)


def create_adls_item(cmd, account_name, path, content=None, folder=False, force=False):
    client = cf_dls_filesystem(cmd.cli_ctx, account_name)
    if client.exists(path):
        if force:
            # only recurse if the user wants this to be a folder
            # this prevents the user from unintentionally wiping out a folder
            # when trying to create a file.
            client.rm(path, recursive=folder)
        else:
            # pylint: disable=line-too-long
            raise CLIError('An item at path: \'{}\' already exists. To overwrite the existing item, specify --force'.format(path))

    if folder:
        return client.mkdir(path)

    if content:
        if isinstance(content, str):
            # turn content into bytes with UTF-8 encoding if it is just a string
            content = str.encode(content)
        with client.open(path, mode='wb') as f:
            return f.write(content)
    else:
        return client.touch(path)


def append_adls_item(cmd, account_name, path, content):
    client = cf_dls_filesystem(cmd.cli_ctx, account_name)
    if not client.exists(path):
        # pylint: disable=line-too-long
        raise CLIError('File at path: \'{}\' does not exist. Create the file before attempting to append to it.'.format(path))

    with client.open(path, mode='ab') as f:
        if isinstance(content, str):
            content = str.encode(content)
        f.write(content)


def upload_to_adls(cmd, account_name, source_path, destination_path, chunk_size, buffer_size, block_size,
                   thread_count=None, overwrite=False, progress_callback=None):
    client = cf_dls_filesystem(cmd.cli_ctx, account_name)
    ADLUploader(
        client,
        destination_path,
        source_path,
        thread_count,
        chunksize=chunk_size,
        buffersize=buffer_size,
        blocksize=block_size,
        overwrite=overwrite,
        progress_callback=progress_callback or get_update_progress(cmd.cli_ctx))


def remove_adls_item(cmd, account_name, path, recurse=False):
    cf_dls_filesystem(cmd.cli_ctx, account_name).rm(path, recurse)


def download_from_adls(cmd, account_name, source_path, destination_path, chunk_size, buffer_size, block_size,
                       thread_count=None, overwrite=False, progress_callback=None):
    client = cf_dls_filesystem(cmd.cli_ctx, account_name)
    ADLDownloader(
        client,
        source_path,
        destination_path,
        thread_count,
        chunksize=chunk_size,
        buffersize=buffer_size,
        blocksize=block_size,
        overwrite=overwrite,
        progress_callback=progress_callback or get_update_progress(cmd.cli_ctx))


def test_adls_item(cmd, account_name, path):
    return cf_dls_filesystem(cmd.cli_ctx, account_name).exists(path)


def preview_adls_item(cmd, account_name, path, length=None, offset=0, force=False):
    client = cf_dls_filesystem(cmd.cli_ctx, account_name)
    if length:
        try:
            length = long(length)
        except NameError:
            length = int(length)

    if offset:
        try:
            offset = long(offset)
        except NameError:
            offset = int(offset)

    if not length or length <= 0:
        length = client.info(path)['length'] - offset
        if length > 1 * 1024 * 1024 and not force:
            # pylint: disable=line-too-long
            raise CLIError('The remaining data to preview is greater than {} bytes. Please specify a length or use the --force parameter to preview the entire file. The length of the file that would have been previewed: {}'.format(str(1 * 1024 * 1024), str(length)))

    return client.read_block(path, offset, length)


def join_adls_items(cmd, account_name, source_paths, destination_path, force=False):
    client = cf_dls_filesystem(cmd.cli_ctx, account_name)
    if force and client.exists(destination_path):
        client.rm(destination_path)

    client.concat(destination_path, source_paths)


def move_adls_item(cmd, account_name, source_path, destination_path, force=False):
    client = cf_dls_filesystem(cmd.cli_ctx, account_name)
    if force and client.exists(destination_path):
        client.rm(destination_path)
    client.mv(source_path, destination_path)


def set_adls_item_expiry(cmd, account_name, path, expiration_time):
    client = cf_dls_filesystem(cmd.cli_ctx, account_name)
    if client.info(path)['type'] != 'FILE':
        # pylint: disable=line-too-long
        raise CLIError('The specified path does not exist or is not a file. Please ensure the path points to a file and it exists. Path supplied: {}'.format(path))

    expiration_time = float(expiration_time)
    try:
        expiration_time = long(expiration_time)
    except NameError:
        expiration_time = int(expiration_time)
    client.set_expiry(path, ExpiryOptionType.absolute.value, expiration_time)


def remove_adls_item_expiry(cmd, account_name, path):
    client = cf_dls_filesystem(cmd.cli_ctx, account_name)
    if client.info(path)['type'] != 'FILE':
        # pylint: disable=line-too-long
        raise CLIError('The specified path does not exist or is not a file. Please ensure the path points to a file and it exists. Path supplied: {}'.format(path))

    client.set_expiry(path, ExpiryOptionType.never_expire.value)
# endregion


# region filesystem permissions
def get_adls_item_acl(cmd, account_name, path):
    client = cf_dls_filesystem(cmd.cli_ctx, account_name)
    return client.get_acl_status(path)


def remove_adls_item_acl(cmd, account_name, path, default_acl=False):
    client = cf_dls_filesystem(cmd.cli_ctx, account_name)
    if default_acl:
        client.remove_default_acl(path)
    else:
        client.remove_acl(path)


def remove_adls_item_acl_entry(cmd, account_name, path, acl_spec):
    client = cf_dls_filesystem(cmd.cli_ctx, account_name)
    client.remove_acl_entries(path, acl_spec)


def set_adls_item_acl(cmd, account_name, path, acl_spec):
    client = cf_dls_filesystem(cmd.cli_ctx, account_name)
    client.set_acl(path, acl_spec)


def set_adls_item_acl_entry(cmd, account_name, path, acl_spec):
    client = cf_dls_filesystem(cmd.cli_ctx, account_name)
    client.modify_acl_entries(path, acl_spec)


def set_adls_item_owner(cmd, account_name, path, owner=None, group=None):
    cf_dls_filesystem(cmd.cli_ctx, account_name).chown(path, owner, group)


def set_adls_item_permissions(cmd, account_name, path, permission):
    cf_dls_filesystem(cmd.cli_ctx, account_name).chmod(path, permission)
# endregion


# helpers
def _get_resource_group_location(cli_ctx, resource_group_name):
    client = get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    # pylint: disable=no-member
    return client.resource_groups.get(resource_group_name).location
