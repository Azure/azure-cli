# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def create_streaming_locator(client, resource_group_name, account_name,
                             streaming_locator_name, streaming_policy_name,
                             asset_name, start_time=None, default_content_key_policy_name=None,
                             end_time=None):
    from azure.mgmt.media.models import StreamingLocator

    streaming_locator = StreamingLocator(asset_name=asset_name,
                                         start_time=start_time, end_time=end_time,
                                         streaming_policy_name=streaming_policy_name,
                                         default_content_key_policy_name=default_content_key_policy_name)

    return client.create(resource_group_name, account_name, streaming_locator_name, streaming_locator)


def create_streaming_policy(cmd, resource_group_name, account_name,
                            streaming_policy_name,
                            download=False, dash=False, hls=False, smooth_streaming=False,
                            default_content_key_policy_name=None):
    from azure.cli.command_modules.ams._client_factory import get_streaming_policies_client
    from azure.mgmt.media.models import (StreamingPolicy, NoEncryption, EnabledProtocols)

    enabled_protocols = EnabledProtocols(download=download, dash=dash, hls=hls, smooth_streaming=smooth_streaming)

    streaming_policy = StreamingPolicy(default_content_key_policy_name=default_content_key_policy_name,
                                       no_encryption=NoEncryption(enabled_protocols=enabled_protocols))

    return get_streaming_policies_client(cmd.cli_ctx).create(resource_group_name, account_name,
                                                             streaming_policy_name, streaming_policy)
