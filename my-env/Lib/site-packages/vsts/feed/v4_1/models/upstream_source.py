# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class UpstreamSource(Model):
    """UpstreamSource.

    :param deleted_date:
    :type deleted_date: datetime
    :param id:
    :type id: str
    :param internal_upstream_collection_id:
    :type internal_upstream_collection_id: str
    :param internal_upstream_feed_id:
    :type internal_upstream_feed_id: str
    :param internal_upstream_view_id:
    :type internal_upstream_view_id: str
    :param location:
    :type location: str
    :param name:
    :type name: str
    :param protocol:
    :type protocol: str
    :param upstream_source_type:
    :type upstream_source_type: object
    """

    _attribute_map = {
        'deleted_date': {'key': 'deletedDate', 'type': 'iso-8601'},
        'id': {'key': 'id', 'type': 'str'},
        'internal_upstream_collection_id': {'key': 'internalUpstreamCollectionId', 'type': 'str'},
        'internal_upstream_feed_id': {'key': 'internalUpstreamFeedId', 'type': 'str'},
        'internal_upstream_view_id': {'key': 'internalUpstreamViewId', 'type': 'str'},
        'location': {'key': 'location', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'protocol': {'key': 'protocol', 'type': 'str'},
        'upstream_source_type': {'key': 'upstreamSourceType', 'type': 'object'}
    }

    def __init__(self, deleted_date=None, id=None, internal_upstream_collection_id=None, internal_upstream_feed_id=None, internal_upstream_view_id=None, location=None, name=None, protocol=None, upstream_source_type=None):
        super(UpstreamSource, self).__init__()
        self.deleted_date = deleted_date
        self.id = id
        self.internal_upstream_collection_id = internal_upstream_collection_id
        self.internal_upstream_feed_id = internal_upstream_feed_id
        self.internal_upstream_view_id = internal_upstream_view_id
        self.location = location
        self.name = name
        self.protocol = protocol
        self.upstream_source_type = upstream_source_type
