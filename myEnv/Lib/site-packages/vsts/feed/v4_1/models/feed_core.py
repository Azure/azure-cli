# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class FeedCore(Model):
    """FeedCore.

    :param allow_upstream_name_conflict: If set, the feed will allow upload of packages that exist on the upstream
    :type allow_upstream_name_conflict: bool
    :param capabilities:
    :type capabilities: object
    :param fully_qualified_id:
    :type fully_qualified_id: str
    :param fully_qualified_name:
    :type fully_qualified_name: str
    :param id:
    :type id: str
    :param is_read_only:
    :type is_read_only: bool
    :param name:
    :type name: str
    :param upstream_enabled: If set, the feed can proxy packages from an upstream feed
    :type upstream_enabled: bool
    :param upstream_sources: External assemblies should use the extension methods to get the sources for a specific protocol.
    :type upstream_sources: list of :class:`UpstreamSource <packaging.v4_1.models.UpstreamSource>`
    :param view:
    :type view: :class:`FeedView <packaging.v4_1.models.FeedView>`
    :param view_id:
    :type view_id: str
    :param view_name:
    :type view_name: str
    """

    _attribute_map = {
        'allow_upstream_name_conflict': {'key': 'allowUpstreamNameConflict', 'type': 'bool'},
        'capabilities': {'key': 'capabilities', 'type': 'object'},
        'fully_qualified_id': {'key': 'fullyQualifiedId', 'type': 'str'},
        'fully_qualified_name': {'key': 'fullyQualifiedName', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'is_read_only': {'key': 'isReadOnly', 'type': 'bool'},
        'name': {'key': 'name', 'type': 'str'},
        'upstream_enabled': {'key': 'upstreamEnabled', 'type': 'bool'},
        'upstream_sources': {'key': 'upstreamSources', 'type': '[UpstreamSource]'},
        'view': {'key': 'view', 'type': 'FeedView'},
        'view_id': {'key': 'viewId', 'type': 'str'},
        'view_name': {'key': 'viewName', 'type': 'str'}
    }

    def __init__(self, allow_upstream_name_conflict=None, capabilities=None, fully_qualified_id=None, fully_qualified_name=None, id=None, is_read_only=None, name=None, upstream_enabled=None, upstream_sources=None, view=None, view_id=None, view_name=None):
        super(FeedCore, self).__init__()
        self.allow_upstream_name_conflict = allow_upstream_name_conflict
        self.capabilities = capabilities
        self.fully_qualified_id = fully_qualified_id
        self.fully_qualified_name = fully_qualified_name
        self.id = id
        self.is_read_only = is_read_only
        self.name = name
        self.upstream_enabled = upstream_enabled
        self.upstream_sources = upstream_sources
        self.view = view
        self.view_id = view_id
        self.view_name = view_name
