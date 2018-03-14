# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def create_asset(client, account_name, resource_group_name, asset_name, alternate_id=None, description=None):
    from azure.mediav3.models import Asset

    asset = Asset(alternate_id=alternate_id, description=description)

    return client.create_or_update(resource_group_name, account_name, asset_name, asset)
