# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime
from enum import Enum
from azure.appconfiguration import ConfigurationSetting


# pylint: disable=too-few-public-methods
# pylint: disable=too-many-instance-attributes


class QueryFields(Enum):
    KEY = 0x001
    LABEL = 0x002
    VALUE = 0x004
    CONTENT_TYPE = 0x008
    ETAG = 0x010
    LAST_MODIFIED = 0x020
    LOCKED = 0x040
    TAGS = 0x080
    ALL = KEY | LABEL | VALUE | CONTENT_TYPE | ETAG | LAST_MODIFIED | LOCKED | TAGS


class KeyValue:
    '''
    We need to convert ConfigurationSetting returned by SDK to KeyValue object
    because ConfigurationSetting contains param 'read_only' instead of 'locked'.

    :ivar str key:
        Key of the entry.
    :ivar str value:
        Value of the entry.
    :ivar str label:
        Label of the entry.
    :ivar dict[str, str] tags:
        Dictionary of tags of the entry.
    :ivar str content_type:
        Content type of the entry.
    :ivar str etag:
        The ETag contains a value that you can use to perform operations.
    :ivar bool locked:
        Represents whether the key value entry is locked.
    :ivar str last_modified:
        A str representation of the datetime object representing the last time the key was modified.
    '''

    def __init__(self,
                 key,
                 value=None,
                 label=None,
                 tags=None,
                 content_type=None,
                 etag=None,
                 locked=False,
                 last_modified=None):
        self.key = key
        self.value = value
        self.label = label
        self.tags = tags
        self.content_type = content_type
        self.etag = etag
        self.last_modified = last_modified.isoformat() if isinstance(last_modified, datetime) else str(last_modified)
        self.locked = locked

    def __str__(self):
        return "\nKey: " + self.key + \
               "\nValue: " + self.value + \
               "\nLabel: " + (self.label if self.label else '') + \
               "\netag: " + self.etag + \
               "\nLast Modified: " + self.last_modified + \
               "\nLocked: " + self.locked + \
               "\nContent Type: " + self.content_type + \
               "\nTags: " + (str(self.tags) if self.tags else '')


def convert_configurationsetting_to_keyvalue(configuration_setting=None):

    if configuration_setting is None:
        return None
    return KeyValue(key=configuration_setting.key,
                    label=configuration_setting.label,
                    content_type=configuration_setting.content_type,
                    value=configuration_setting.value,
                    last_modified=configuration_setting.last_modified,
                    tags=configuration_setting.tags,
                    locked=configuration_setting.read_only,
                    etag=configuration_setting.etag)


def convert_keyvalue_to_configurationsetting(keyvalue=None):
    if keyvalue is None:
        return None
    return ConfigurationSetting(key=keyvalue.key,
                                label=keyvalue.label,
                                content_type=keyvalue.content_type,
                                value=keyvalue.value,
                                tags=keyvalue.tags,
                                read_only=keyvalue.locked,
                                etag=keyvalue.etag)
