# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class IdentityKeyMap(Model):
    """IdentityKeyMap.

    :param cuid:
    :type cuid: str
    :param storage_key:
    :type storage_key: str
    :param subject_type:
    :type subject_type: str
    """

    _attribute_map = {
        'cuid': {'key': 'cuid', 'type': 'str'},
        'storage_key': {'key': 'storageKey', 'type': 'str'},
        'subject_type': {'key': 'subjectType', 'type': 'str'}
    }

    def __init__(self, cuid=None, storage_key=None, subject_type=None):
        super(IdentityKeyMap, self).__init__()
        self.cuid = cuid
        self.storage_key = storage_key
        self.subject_type = subject_type
