# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=redefined-builtin

import json
import requests
from azure.cli.core.util import CLIError
from azure.cli.command_modules.ams._completers import get_mru_type_completion_list
from azure.cli.core.commands.client_factory import get_subscription_id, get_mgmt_service_client
from azure.mgmt.media.models import (MediaService, AccountEncryption, KeyVaultProperties)

def get_encryption(cmd, client, resource_group_name, account_name):
    account_info = client.get(resource_group_name,
                      account_name) if resource_group_name else client.get_by_subscription(account_name)
    return account_info.encryption

def set_encryption(cmd, client, resource_group_name, account_name, key_source=None, key_version=None, key_vault_id=None):
    account_info = client.get(resource_group_name,
                      account_name) if resource_group_name else client.get_by_subscription(account_name)
    if key_source == 'CustomerKey':
        key_vault_props = KeyVaultProperties(key_identifier = key_vault_id, current_key_identifier = key_version)
    else:
        key_vault_props = None
    encryption = AccountEncryption(type=key_source, key_vault_properties=key_vault_props)
    media_service = MediaService(location=account_info.location, identity=account_info.identity, storage_accounts=account_info.storage_accounts, encryption=encryption)

    result = client.create_or_update(resource_group_name, account_name, media_service)
    print("result is", result)
