# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def create_streaming_locator(client, resource_group_name, account_name,
                             streaming_locator_name, streaming_policy_name,
                             asset_name, start_time=None, default_content_key_policy_name=None,
                             end_time=None, streaming_locator_id=None, alternative_media_id=None):
    from azure.mgmt.media.models import StreamingLocator

    streaming_locator = StreamingLocator(asset_name=asset_name,
                                         start_time=start_time, end_time=end_time,
                                         streaming_policy_name=streaming_policy_name,
                                         default_content_key_policy_name=default_content_key_policy_name,
                                         streaming_locator_id=streaming_locator_id,
                                         alternative_media_id=alternative_media_id)

    return client.create(resource_group_name, account_name, streaming_locator_name, streaming_locator)


def list_content_keys(client, resource_group_name, account_name,
                      streaming_locator_name):
    return client.list_content_keys(resource_group_name, account_name, 
                                    streaming_locator_name).content_keys
