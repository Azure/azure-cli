# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime
from enum import Enum
from typing import Optional
from msrest.serialization import Model

# pylint: disable=too-few-public-methods
# pylint: disable=too-many-instance-attributes


class SnapshotQueryFields(Enum):
    NAME = 0x001
    STATUS = 0x002
    FILTERS = 0x004
    COMPOSITION_TYPE = 0x008
    CREATED = 0x010
    EXPIRES = 0x020
    SIZE = 0x040
    ITEMS_COUNT = 0x080
    TAGS = 0x100
    ITEMS_LINK = 0x200
    RETENTION_PERIOD = 0x400
    ETAG = 0x800
    ALL = NAME | STATUS | FILTERS | COMPOSITION_TYPE | CREATED | EXPIRES | SIZE | ITEMS_COUNT | TAGS | RETENTION_PERIOD | ITEMS_LINK | ETAG


class Snapshot(Model):
    '''
    Class used to represent Snapshot entity returned from requests

    :ivar str name:
        Name of the snapshot.
    :ivar str status:
        Provisioning status of the snapshot.
    :ivar dict[str, str] filters:
        Dictionary of filters used in building snapshot.
    :ivar str etag:
        The ETag contains a value that you can use to perform operations.
    :ivar str composition_type:
        Choose how snapshot filters are applied in building snapshot.
    :ivar str created:
        Time of creation of snapshot.
    :ivar str expires:
        The time at which an archived snapshot will be deleted.
    :ivar int size:
        The size in bytes of the built snapshot.
    :ivar int items_count:
        The number of key-values in the built snapshot.
    :ivar dict[str, str] tags:
        Dictionary of tags of the snapshot.
    :ivar str items_link:
        Endpoint that can be used to query keys-values in a snapshot
    :ivar int retention_period:
        Number of days for which an archived snapshot will be kept before being deleted.
    '''

    _attribute_map = {
        'name': {'key': 'name', 'type': 'str'},
        'status': {'key': 'status', 'type': 'str'},
        'filters': {'key': 'content_type', 'type': '[Filter]'},
        'etag': {'key': 'etag', 'type': 'str'},
        'created': {'key': 'created', 'type': 'iso-8601'},
        'expires': {'key': 'expires', 'type': 'iso-8601'},
        'composition_type': {'key': 'composition_type', 'type': 'str'},
        'size': {'key': 'size', 'type': 'int'},
        'items_count': {'key': 'items_count', 'type': 'int'},
        'items_link': {'key': 'items_link', 'type': 'str'},
        'retention_period': {'key': 'retention_period', 'type': 'int'},
        'tags': {'key': 'tags', 'type': '{str}'}
    }

    def __init__(self,
                 *,
                 name,
                 status,
                 filters,
                 etag=None,
                 status_code=None,
                 composition_type=None,
                 created=None,
                 expires=None,
                 size=None,
                 items_count=None,
                 tags=None,
                 items_link=None,
                 retention_period=None,
                 **kwargs
                 ):

        super(Snapshot, self).__init__(**kwargs)
        self.name = name
        self.status = status
        self.filters = filters
        self.status_code = status_code
        self.etag = etag
        self.composition_type = composition_type
        self.created = created.isoformat() if isinstance(created, datetime) else str(created)
        self.expires = expires.isoformat() if isinstance(expires, datetime) else (str(expires) if expires else None)
        self.size = size
        self.items_count = items_count
        self.tags = tags
        self.items_link = items_link
        self.retention_period = retention_period

    def __str__(self):
        return "\netag: " + self.etag + \
            "\nName: " + self.name + \
            "\nStatus: " + self.status + \
            "\nFilters: " + (str(self.filters) if self.filters else '') + \
            "\nComposition Type: " + self.composition_type + \
            "\nCreated: " + self.created + \
            "\nExpires: " + self.expires + \
            "\nSize: " + str(self.size) + \
            "\nItem count: " + str(self.items_count) + \
            "\nTags: " + (str(self.tags) if self.tags else '{}') + \
            "\nItems Link: " + self.items_link + \
            "\nRetention Period: " + str(self.retention_period)

    @classmethod
    def from_json(cls, data_dict: any):
        return cls(
            name=data_dict.get("name", None),
            status=data_dict.get("status", None),
            filters=data_dict.get("filters", None),
            etag=data_dict.get("etag", None),
            composition_type=data_dict.get("composition_type", None),
            created=data_dict.get("created", None),
            expires=data_dict.get("expires", None),
            size=data_dict.get("size", 0),
            items_count=data_dict.get("items_count", 0),
            tags=data_dict.get("tags", {}),
            items_link=data_dict.get("items_link", None),
            retention_period=data_dict.get("retention_period", 0)
        )


class Filter(Model):
    _attribute_map = {
        'key': {'key': 'key', 'type': 'str'},
        'label': {'key': 'label', 'type': 'str'}
    }

    def __init__(self, *, key: Optional[str] = None, label: Optional[str] = None, **kwargs):
        super(Filter, self).__init__(**kwargs)
        self.key = key
        self.label = label


class SnapshotListResult:
    def __init__(self, items=None, next_link=None):
        self.items = items
        self.next_link = next_link

    def __str__(self):
        return str([str(i) for i in self.items])

    @classmethod
    def from_json(cls, data_dict: str):

        return cls(
            items=[Snapshot.from_json(snapshot) for snapshot in data_dict.get("items", [])],
            next_link=data_dict.get("next_link", None)
        )
