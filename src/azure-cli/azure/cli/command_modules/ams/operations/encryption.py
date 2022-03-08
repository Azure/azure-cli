# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=redefined-builtin

from azure.core.exceptions import HttpResponseError
from azure.cli.core.azclierror import BadRequestError
from azure.mgmt.media.models import (MediaService, AccountEncryption, KeyVaultProperties)


def get_encryption(client, resource_group_name, account_name):
    account_info = client.get(resource_group_name,
                              account_name) if resource_group_name else client.get_by_subscription(account_name)
    return account_info.encryption


def set_encryption(client, resource_group_name, account_name, key_type=None,
                   current_key_id=None, key_identifier=None):
    try:
        account_info = client.get(resource_group_name,
                                  account_name) if resource_group_name else client.get_by_subscription(account_name)
        if key_type == 'CustomerKey':
            key_vault_props = KeyVaultProperties(key_identifier=key_identifier,
                                                 current_key_identifier=current_key_id)
        else:
            key_vault_props = None
        encryption = AccountEncryption(type=key_type, key_vault_properties=key_vault_props)
        media_service = MediaService(location=account_info.location, identity=account_info.identity,
                                     storage_accounts=account_info.storage_accounts, encryption=encryption)

        return client.create_or_update(resource_group_name, account_name, media_service)
    except HttpResponseError as ex:
        recommendation = ''
        if ex.message == '(BadRequest) Access to the Customer Key was forbidden.':
            recommendation = 'Please use the Azure Portal to grant the key vault access to the media account.'\
                             'For more information please visit https://aka.ms/keyvaultaccess'
        raise BadRequestError(ex, recommendation)
