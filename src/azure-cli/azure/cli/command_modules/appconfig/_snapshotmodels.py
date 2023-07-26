# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime
from enum import Enum

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
            "\nFilters: " + (str(self.filters) if self.filters else '') + \
            "\nComposition Type: " + self.composition_type + \
            "\nCreated: " + self.created + \
            "\nExpires: " + self.expires + \
            "\nSize: " + str(self.size) + \
            "\nItem count: " + str(self.items_count) + \
            "\nTags: " + (str(self.tags) if self.tags else '{}') + \
            "\nRetention Period: " + str(self.retention_period)

    @classmethod
    def from_json(cls, data_dict):
        return cls(
            name=data_dict.get("name", None),
            status=data_dict.get("status", None),
            filters=data_dict.get("filters", None),
            etag=data_dict.get("etag", None),
            composition_type=data_dict.get("composition_type", None),
            created=data_dict.get("created", None),
            expires=data_dict.get("expires", None),
            size=data_dict.get("size", None),
            items_count=data_dict.get("items_count", None),
            tags=data_dict.get("tags", None),
            retention_period=data_dict.get("retention_period", None)
        )


class SnapshotListResult:
    '''
    Class representing a paginated list of snapshots.
    :ivar str next_link:
        Shows the link to the next page of snapshots
    :ivar [Snapshot] items:
        List of Snapshot entities in the current page.
    '''

    def __init__(self, items=None, next_link=None):
        self.items = items
        self.next_link = next_link

    def __str__(self):
        return str([str(i) for i in self.items])

    @classmethod
    def from_json(cls, data_dict):

        return cls(
            items=[Snapshot.from_json(snapshot) for snapshot in data_dict.get("items", [])],
            next_link=data_dict.get("@nextLink", None)
        )


class OperationStatus:
    '''
    Class representing the current create status of a snapshot
    :ivar str operation_id:
        Name of the Snapshot being created.
    :ivar str status:
        The creation status of the snapshot
    :ivar ErrorDetail error:
        The details of the error if any.
    '''

    def __init__(self,
                 operation_id,
                 status,
                 error=None):
        self.operation_id = operation_id
        self.status = status
        self.error = error

    @classmethod
    def from_json(cls, data_dict):
        return cls(
            operation_id=data_dict.get("id", None),
            status=data_dict.get("status", None),
            error=ErrorDetail.from_json(data_dict.get("error", None)),
        )


class ErrorDetail:
    '''
    Class representing the create error details for a failed snapshot.
    :ivar str code:
        Error status code.
    : ivar str message:
        Error message.
    '''

    def __init__(self,
                 code=None,
                 message=None):
        self.code = code
        self.message = message

    @classmethod
    def from_json(cls, data_dict):
        if not data_dict:
            return None

        return cls(
            code=data_dict.get("code", None),
            message=data_dict.get("message", None)
        )


class OperationStatusResponse:
    '''
    Class representing the required data needed in tracking snapshot creation
    :ivar OperationStatus operation_status:
        Status of the Snapshot being created.
    :ivar int retry_after:
        Number of seconds returned from the server in Retry-After header
    '''

    def __init__(self,
                 operation_status,
                 retry_after=None):
        self.operation_status = operation_status
        self.retry_after = retry_after

    @classmethod
    def from_response(cls, response):
        response_headers = response.headers
        retry_seconds = response_headers.pop('Retry-After', None)

        return cls(
            operation_status=OperationStatus.from_json(response.json()),
            retry_after=int(retry_seconds) if retry_seconds else None
        )
