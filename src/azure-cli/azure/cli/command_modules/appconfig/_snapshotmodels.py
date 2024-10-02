# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime
from enum import Enum

from ._constants import SnapshotFilterFields

# pylint: disable=too-few-public-methods
# pylint: disable=too-many-instance-attributes
# pylint: disable=line-too-long


class SnapshotQueryFields(Enum):
    NAME = 0x0001
    STATUS = 0x0002
    FILTERS = 0x0004
    COMPOSITION_TYPE = 0x0008
    CREATED = 0x0010
    EXPIRES = 0x0020
    SIZE = 0x0040
    ITEMS_COUNT = 0x0080
    TAGS = 0x0100
    ETAG = 0x0200
    RETENTION_PERIOD = 0x0400
    ALL = NAME | STATUS | FILTERS | COMPOSITION_TYPE | CREATED | EXPIRES | SIZE | ITEMS_COUNT | TAGS | ETAG | RETENTION_PERIOD


class Snapshot:
    '''
    Class used to represent the Snapshot entity returned from requests

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
    :ivar int retention_period:
        Number of seconds for which an archived snapshot will be kept before being deleted.
    '''

    def __init__(self,
                 name,
                 status,
                 filters,
                 etag=None,
                 composition_type=None,
                 created=None,
                 expires=None,
                 size=None,
                 items_count=None,
                 tags=None,
                 retention_period=None,
                 ):

        self.name = name
        self.status = status
        self.filters = filters
        self.etag = etag
        self.composition_type = composition_type
        self.created = created.isoformat() if isinstance(created, datetime) else str(created)
        self.expires = expires.isoformat() if isinstance(expires, datetime) else (str(expires) if expires else None)
        self.size = size
        self.items_count = items_count
        self.tags = tags
        self.retention_period = retention_period

    def __str__(self):
        return "\nEtag: " + self.etag + \
            "\nName: " + self.name + \
            "\nStatus: " + self.status + \
            "\nFilters: " + (str(self.filters) if self.filters else '[]') + \
            "\nComposition Type: " + self.composition_type + \
            "\nCreated: " + self.created + \
            "\nExpires: " + self.expires + \
            "\nSize: " + str(self.size) + \
            "\nItem count: " + str(self.items_count) + \
            "\nTags: " + (str(self.tags) if self.tags else '{}') + \
            "\nRetention Period: " + str(self.retention_period)

    @classmethod
    def from_configuration_snapshot(cls, config_snapshot):
        return cls(
            name=config_snapshot.name,
            status=config_snapshot.status,
            filters=[convert_configuration_setting_filter(setting_filter) for setting_filter in config_snapshot.filters],
            etag=config_snapshot.etag,
            composition_type=config_snapshot.composition_type,
            created=config_snapshot.created,
            expires=config_snapshot.expires,
            size=config_snapshot.size,
            items_count=config_snapshot.items_count,
            tags=config_snapshot.tags,
            retention_period=config_snapshot.retention_period
        )


def convert_configuration_setting_filter(configuration_setting_filter):
    result = {}

    if configuration_setting_filter.key is not None:
        result[SnapshotFilterFields.KEY] = configuration_setting_filter.key

    if configuration_setting_filter.label is not None:
        result[SnapshotFilterFields.LABEL] = configuration_setting_filter.label

    if configuration_setting_filter.tags is not None:
        result[SnapshotFilterFields.TAGS] = configuration_setting_filter.tags

    return result
