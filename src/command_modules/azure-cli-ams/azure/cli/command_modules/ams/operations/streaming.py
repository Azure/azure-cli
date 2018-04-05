# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def create_streaming_locator(client, resource_group_name, account_name,
                             streaming_locator_name, asset_name=None,
                             streaming_policy_name=None, default_content_key_policy_name=None):
    from azure.mediav3.models import StreamingLocator

    streaming_locator = StreamingLocator(asset_name=asset_name,
                                         streaming_policy_name=streaming_policy_name,
                                         default_content_key_policy_name=default_content_key_policy_name)

    return client.create(resource_group_name, account_name, streaming_locator_name, streaming_locator)
