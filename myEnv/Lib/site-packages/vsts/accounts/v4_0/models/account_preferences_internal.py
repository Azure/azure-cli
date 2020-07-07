# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AccountPreferencesInternal(Model):
    """AccountPreferencesInternal.

    :param culture:
    :type culture: object
    :param language:
    :type language: object
    :param time_zone:
    :type time_zone: object
    """

    _attribute_map = {
        'culture': {'key': 'culture', 'type': 'object'},
        'language': {'key': 'language', 'type': 'object'},
        'time_zone': {'key': 'timeZone', 'type': 'object'}
    }

    def __init__(self, culture=None, language=None, time_zone=None):
        super(AccountPreferencesInternal, self).__init__()
        self.culture = culture
        self.language = language
        self.time_zone = time_zone
