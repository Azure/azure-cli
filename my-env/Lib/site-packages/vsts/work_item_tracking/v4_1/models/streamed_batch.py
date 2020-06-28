# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class StreamedBatch(Model):
    """StreamedBatch.

    :param continuation_token:
    :type continuation_token: str
    :param is_last_batch:
    :type is_last_batch: bool
    :param next_link:
    :type next_link: str
    :param values:
    :type values: list of object
    """

    _attribute_map = {
        'continuation_token': {'key': 'continuationToken', 'type': 'str'},
        'is_last_batch': {'key': 'isLastBatch', 'type': 'bool'},
        'next_link': {'key': 'nextLink', 'type': 'str'},
        'values': {'key': 'values', 'type': '[object]'}
    }

    def __init__(self, continuation_token=None, is_last_batch=None, next_link=None, values=None):
        super(StreamedBatch, self).__init__()
        self.continuation_token = continuation_token
        self.is_last_batch = is_last_batch
        self.next_link = next_link
        self.values = values
