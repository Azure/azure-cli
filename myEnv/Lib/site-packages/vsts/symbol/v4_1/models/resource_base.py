# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ResourceBase(Model):
    """ResourceBase.

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
    """

    _attribute_map = {
        'created_by': {'key': 'createdBy', 'type': 'str'},
        'created_date': {'key': 'createdDate', 'type': 'iso-8601'},
        'id': {'key': 'id', 'type': 'str'},
        'storage_eTag': {'key': 'storageETag', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, created_by=None, created_date=None, id=None, storage_eTag=None, url=None):
        super(ResourceBase, self).__init__()
        self.created_by = created_by
        self.created_date = created_date
        self.id = id
        self.storage_eTag = storage_eTag
        self.url = url
