# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import codecs
import os
import re
import time
import uuid

from OpenSSL import crypto

from msrestazure.azure_exceptions import CloudError
from azure.mgmt.datalake.store.models import (DataLakeStoreAccountUpdateParameters,
                                        FirewallRule,
                                        DataLakeStoreAccount,
                                        EncryptionConfigType,
                                        EncryptionIdentity,
                                        EncryptionConfig,
                                        EncryptionState,
                                        KeyVaultMetaInfo)

from azure.datalake.store.multithread import (ADLUploader, ADLDownloader)
from azure.cli.command_modules.datalake.store._client_factory import (cf_datalake_store_filesystem)

import azure.cli.core.telemetry as telemetry
from azure.cli.core._util import CLIError
import azure.cli.core.azlogging as azlogging

logger = azlogging.get_az_logger(__name__)
# account customiaztions
def list_adls_account(client, resource_group_name=None):
    account_list = client.list_by_resource_group(resource_group_name=resource_group_name) \
        if resource_group_name else client.list()
    return list(account_list)

def create_adls_account(client, 
                        resource_group_name,
                        account_name,
                        location = None,
                        default_group = None,
                        tags = None,
                        encryption_type = EncryptionConfigType.service_managed,
                        key_vault_id = None,
                        key_name = None,
                        key_version = None,
                        disable_encryption = False,
                        tier = None):
    
    location = location or get_resource_group_location(resource_group_name)
    create_params = DataLakeStoreAccount(location)
    if tags:
        create_params.tags = tags

    if default_group:
        create_params.default_group = default_group

    if tier:
        create_params.new_tier = tier
    if not disable_encryption:
        identity = EncryptionIdentity()
        config = EncryptionConfig(type=encryption_type)
        if encryption_type == EncryptionConfigType.user_managed:
            if not key_name or not key_vault_id or not key_version:
                raise CLIError('For user managed encryption, --key_vault_id, --key_name and --key_version are required parameters and must be supplied.')
            config.key_vault_meta_info = KeyVaultMetaInfo(key_vault_id, key_name, key_version)
        else:
            if key_name or key_vault_id or key_version:
                logger.warning('User supplied Key Vault information. For service managed encryption user supplied Key Vault information is ignored.')
        
        create_params.encryption_config = config
        create_params.identity = identity
    else:
        create_params.encryption_state = EncryptionState.disabled
        create_params.identity = None
        create_params.encryption_config = None

    return client.create(resource_group_name, account_name, create_params)

def update_adls_account(client,
                        account_name,
                        tags = None,
                        resource_group_name = None,
                        default_group = None,
                        firewall_state = None,
                        allow_azure_ips = None,
                        trusted_id_provider_state = None,
                        tier = None):
    if not resource_group_name:
        resource_group_name = _get_resource_group_by_account_name(client, account_name)

    update_params = DataLakeStoreAccountUpdateParameters(
        tags=tags,
        default_group=default_group,
        firewall_state=firewall_state,
        firewall_allow_azure_ips=allow_azure_ips,
        trusted_id_provider_state=trusted_id_provider_state,
        new_tier=tier)

    return client.update(resource_group_name, account_name, update_params)

# firewall customizations
def add_adls_firewall_rule(client,
                           account_name,
                           firewall_rule_name,
                           start_ip_address,
                           end_ip_address,
                           resource_group_name = None):
    if not resource_group_name:
        resource_group_name = _get_resource_group_by_account_name(client, account_name)

    create_params = FirewallRule(start_ip_address, end_ip_address)
    return client.create_or_update(resource_group_name,
                            account_name,
                            firewall_rule_name,
                            create_params)

# filesystem customizations
def get_adls_item(account_name,
                  path):
    return cf_datalake_store_filesystem(account_name).info(path)

def list_adls_items(account_name,
                    path):
    return cf_datalake_store_filesystem(account_name).ls(path, detail=True)
def create_adls_item(account_name,
                     path,
                     content=None,
                     folder=False,
                     force=False):
    client = cf_datalake_store_filesystem(account_name)
    if client.exists(path):
        if force:
            # only recurse if the user wants this to be a folder
            # this prevents the user from unintentionally wiping out a folder
            # when trying to create a file.
            client.rm(path, recursive=folder)
        else:
            raise CLIError('An item at path: \'{}\' already exists. To overwrite the existing item, specify --force'.format(path))
    
    if folder:
        return client.mkdir(path)

    if content:
        if type(content) is str:
            content = str.encode(content) # turn content into bytes with UTF-8 encoding if it is just a string
        with client.open(path, mode='wb') as f:
            return f.write(content)
    else:
        return client.touch(path)

def append_adls_item(account_name,
                     path,
                     content):
    client = cf_datalake_store_filesystem(account_name)
    if not client.exists(path):
        raise CLIError('File at path: \'{}\' does not exist. Create the file before attempting to append to it.'.format(path))
    
    with client.open(path, mode='ab') as f:
        if type(content) is str:
            content = str.encode(content)
        f.write(content)

def remove_adls_item(account_name,
                     path,
                     recurse=False):
    cf_datalake_store_filesystem(account_name).rm(path, recurse)

def upload_to_adls(account_name,
                   source_path,
                   destination_path,
                   thread_count=None,
                   overwrite=False):
    client = cf_datalake_store_filesystem(account_name)
    upload = ADLUploader(client, destination_path, source_path, thread_count, overwrite=overwrite)

def download_from_adls(account_name,
                   source_path,
                   destination_path,
                   thread_count=None,
                   overwrite=False):
    client = cf_datalake_store_filesystem(account_name)
    download = ADLDownloader(client, source_path, destination_path, thread_count, overwrite=overwrite)

def test_adls_item(account_name,
                   path):
    return cf_datalake_store_filesystem(account_name).exists(path)

def preview_adls_item(account_name,
                      path,
                      length=None,
                      offset=0,
                      force=False):
    client = cf_datalake_store_filesystem(account_name)
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
        if length > 1*1024*1024 and not force:
            raise CLIError('The remaining data to preview is greater than {} bytes. Please specify a length or use the --force parameter to preview the entire file. The length of the file that would have been previewed: {}'.format(str(1*1024*1024), str(length)))

    return client.read_block(path, offset, length)

def join_adls_items(account_name,
                    source_paths,
                    destination_path,
                    force=False):
    client = cf_datalake_store_filesystem(account_name)
    if force and client.exists(destination_path):
        client.rm(destination_path)

    client.concat(destination_path, source_paths)

def move_adls_item(account_name,
                   source_path,
                   destination_path,
                   force=False):
    client = cf_datalake_store_filesystem(account_name)
    if force and client.exists(destination_path):
        client.rm(destination_path)
    client.mv(source_path,destination_path)

def set_adls_item_expiry(account_name,
                         path,
                         expiration_time):
    client = cf_datalake_store_filesystem(account_name)
    if client.info(path)['type'] != 'FILE':
        raise CLIError('The specified path does not exist or is not a file. Please ensure the path points to a file and it exists. Path supplied: {}'.format(path))
    print('todo')

# filesystem permissions customizations
def get_adls_item_acl():
    print('todo')
def remove_adls_item_acl():
    print('todo')
def remove_adls_item_acl_entry():
    print('todo')
def set_adls_item_acl():
    print('todo')
def set_adls_item_acl_entry():
    print('todo')
def set_adls_item_owner(account_name,
                        path,
                        owner=None,
                        group=None):
    cf_datalake_store_filesystem(account_name).chown(path, owner, group)

def set_adls_item_permissions(account_name,
                              path,
                              permission):
    cf_datalake_store_filesystem(account_name).chmod(path, permission)

# helpers
def _get_resource_group_by_account_name(client, account_name):
    accts = list_adla_account(client)
    for item in accts:
        if item.name.lower() == account_name.lower():
            item_id = item.id
            rg_start = item_id.lower().index('resourcegroups/') + len('resourcegroups/')
            rg_length = item_id.lower().index('/providers/') - rg_start
            return item_id[rg_start:rg_length + rg_start]
    
    raise CLIError(
        'Could not find account: \'{}\' in any resource group in the currently selected subscription: {}. Please ensure this account exists and that the current user has access to it.'
        .format(account_name, client.subscription_id))

def get_resource_group_location(resource_group_name):
    from azure.mgmt.resource.resources import ResourceManagementClient
    client = get_mgmt_service_client(ResourceManagementClient)
    # pylint: disable=no-member
    return client.resource_groups.get(resource_group_name).location