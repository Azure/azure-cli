# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .resource_base import ResourceBase


class DebugEntry(ResourceBase):
    """DebugEntry.

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
    :param blob_details:
    :type blob_details: :class:`JsonBlobIdentifierWithBlocks <symbol.v4_1.models.JsonBlobIdentifierWithBlocks>`
    :param blob_identifier: A blob identifier of the symbol file to upload to this debug entry. This property is mostly used during creation of debug entry (a.k.a. symbol publishing) to allow the server to query the existence of the blob.
    :type blob_identifier: :class:`JsonBlobIdentifier <symbol.v4_1.models.JsonBlobIdentifier>`
    :param blob_uri: The URI to get the symbol file. Provided by the server, the URI contains authentication information and is readily accessible by plain HTTP GET request. The client is recommended to retrieve the file as soon as it can since the URI will expire in a short period.
    :type blob_uri: str
    :param client_key: A key the client (debugger, for example) uses to find the debug entry. Note it is not unique for each different symbol file as it does not distinguish between those which only differ by information level.
    :type client_key: str
    :param information_level: The information level this debug entry contains.
    :type information_level: object
    :param request_id: The identifier of symbol request to which this debug entry belongs.
    :type request_id: str
    :param status: The status of debug entry.
    :type status: object
    """

    _attribute_map = {
        'created_by': {'key': 'createdBy', 'type': 'str'},
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'id': {'key': 'id', 'type': 'str'},
        'storage_eTag': {'key': 'storageETag', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'},
        'blob_details': {'key': 'blobDetails', 'type': 'JsonBlobIdentifierWithBlocks'},
        'blob_identifier': {'key': 'blobIdentifier', 'type': 'JsonBlobIdentifier'},
        'blob_uri': {'key': 'blobUri', 'type': 'str'},
        'client_key': {'key': 'clientKey', 'type': 'str'},
        'information_level': {'key': 'informationLevel', 'type': 'object'},
        'request_id': {'key': 'requestId', 'type': 'str'},
        'status': {'key': 'status', 'type': 'object'}
    }

    def __init__(self, created_by=None, created_date=None, id=None, storage_eTag=None, url=None, blob_details=None, blob_identifier=None, blob_uri=None, client_key=None, information_level=None, request_id=None, status=None):
        super(DebugEntry, self).__init__(created_by=created_by, created_date=created_date, id=id, storage_eTag=storage_eTag, url=url)
        self.blob_details = blob_details
        self.blob_identifier = blob_identifier
        self.blob_uri = blob_uri
        self.client_key = client_key
        self.information_level = information_level
        self.request_id = request_id
        self.status = status
