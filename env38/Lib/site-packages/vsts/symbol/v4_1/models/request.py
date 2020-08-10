# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .resource_base import ResourceBase


class Request(ResourceBase):
    """Request.

    :param created_by: The ID of user who created this item. Optional.
    :type created_by: str
    :param created_date: The date time when this item is created. Optional.
    :type created_date: datetime
    :param id: An identifier for this item. Optional.
    :type id: str
    :param storage_eTag: An opaque ETag used to synchronize with the version stored at server end. Optional.
    :type storage_eTag: str
    :param url: A URI which can be used to retrieve this item in its raw format. Optional. Note this is distinguished from other URIs that are present in a derived resource.
    :type url: str
    :param description: An optional human-facing description.
    :type description: str
    :param expiration_date: An optional expiration date for the request. The request will become inaccessible and get deleted after the date, regardless of its status.  On an HTTP POST, if expiration date is null/missing, the server will assign a default expiration data (30 days unless overwridden in the registry at the account level). On PATCH, if expiration date is null/missing, the behavior is to not change whatever the request's current expiration date is.
    :type expiration_date: datetime
    :param name: A human-facing name for the request. Required on POST, ignored on PATCH.
    :type name: str
    :param status: The status for this request.
    :type status: object
    """

    _attribute_map = {
        'created_by': {'key': 'createdBy', 'type': 'str'},
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'id': {'key': 'id', 'type': 'str'},
        'storage_eTag': {'key': 'storageETag', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        'description': {'key': 'description', 'type': 'str'},
        'expiration_date': {'key': 'expirationDate', 'type': 'iso-8601'},
        'name': {'key': 'name', 'type': 'str'},
        'status': {'key': 'status', 'type': 'object'}
    }

    def __init__(self, created_by=None, created_date=None, id=None, storage_eTag=None, url=None, description=None, expiration_date=None, name=None, status=None):
        super(Request, self).__init__(created_by=created_by, created_date=created_date, id=id, storage_eTag=storage_eTag, url=url)
        self.description = description
        self.expiration_date = expiration_date
        self.name = name
        self.status = status
