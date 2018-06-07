# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError


def create_asset(client, account_name, resource_group_name, asset_name, alternate_id=None, description=None):
    from azure.mgmt.media.models import Asset

    asset = Asset(alternate_id=alternate_id, description=description)

    return client.create_or_update(resource_group_name, account_name, asset_name, asset)


def get_sas_urls(client, resource_group_name, account_name, asset_name, permissions=None, expiry_time=None):
    return client.list_container_sas(resource_group_name, account_name,
                                     asset_name, permissions, expiry_time).asset_container_sas_urls


def update_asset(instance, alternate_id=None, description=None):
    if not instance:
        raise CLIError('The asset resource was not found.')

    if alternate_id:
        instance.alternate_id = alternate_id

    if description:
        instance.description = description

    return instance
