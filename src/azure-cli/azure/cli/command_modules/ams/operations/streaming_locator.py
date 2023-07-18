# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json

from knack.util import CLIError

from azure.cli.command_modules.ams._utils import show_resource_not_found_message
from azure.mgmt.media.models import (StreamingLocator, StreamingLocatorContentKey)


def create_streaming_locator(client, resource_group_name, account_name,
                             streaming_locator_name, streaming_policy_name,
                             asset_name, start_time=None, default_content_key_policy_name=None,
                             end_time=None, streaming_locator_id=None, alternative_media_id=None,
                             content_keys=None,
                             filters=None):

    if not _valid_content_keys(content_keys):
        raise CLIError('Malformed content keys.')

    content_keys = _build_content_keys(content_keys)

    streaming_locator = StreamingLocator(asset_name=asset_name,
                                         start_time=start_time, end_time=end_time,
                                         streaming_policy_name=streaming_policy_name,
                                         default_content_key_policy_name=default_content_key_policy_name,
                                         streaming_locator_id=streaming_locator_id,
                                         alternative_media_id=alternative_media_id,
                                         content_keys=content_keys,
                                         filters=filters)

    return client.create(resource_group_name, account_name, streaming_locator_name, streaming_locator)


def list_content_keys(client, resource_group_name, account_name,
                      streaming_locator_name):
    return client.list_content_keys(resource_group_name, account_name,
                                    streaming_locator_name).content_keys


def _build_content_keys(content_keys):

    def __content_key_builder(key):
        return StreamingLocatorContentKey(
            id=key.get('id'),
            label_reference_in_streaming_policy=key.get('labelReferenceInStreamingPolicy'),
            value=key.get('value')
        )

    return None if content_keys is None else [__content_key_builder(k) for k in json.loads(content_keys)]


def _valid_content_keys(content_keys):
    if content_keys is None:
        return True

    def __valid_content_key(key):
        return key.get('id') and key.get('value') and key.get('labelReferenceInStreamingPolicy')

    obj = None

    try:
        obj = json.loads(content_keys)
    except ValueError as err:
        raise CLIError('Malformed JSON: ' + str(err))

    return isinstance(obj, list) and all(__valid_content_key(k) for k in obj)


def get_streaming_locator(client, resource_group_name, account_name,
                          streaming_locator_name):
    streaming_locator = client.get(resource_group_name, account_name, streaming_locator_name)
    if not streaming_locator:
        show_resource_not_found_message(resource_group_name, account_name, 'streamingLocators', streaming_locator_name)

    return streaming_locator
