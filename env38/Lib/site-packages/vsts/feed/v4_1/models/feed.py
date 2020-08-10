# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .feed_core import FeedCore


class Feed(FeedCore):
    """Feed.

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
    :param _links:
    :type _links: :class:`ReferenceLinks <packaging.v4_1.models.ReferenceLinks>`
    :param badges_enabled:
    :type badges_enabled: bool
    :param default_view_id:
    :type default_view_id: str
    :param deleted_date:
    :type deleted_date: datetime
    :param description:
    :type description: str
    :param hide_deleted_package_versions: If set, feed will hide all deleted/unpublished versions
    :type hide_deleted_package_versions: bool
    :param permissions:
    :type permissions: list of :class:`FeedPermission <packaging.v4_1.models.FeedPermission>`
    :param upstream_enabled_changed_date: If set, time that the UpstreamEnabled property was changed. Will be null if UpstreamEnabled was never changed after Feed creation.
    :type upstream_enabled_changed_date: datetime
    :param url:
    :type url: str
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
        'view_name': {'key': 'viewName', 'type': 'str'},
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'badges_enabled': {'key': 'badgesEnabled', 'type': 'bool'},
        'default_view_id': {'key': 'defaultViewId', 'type': 'str'},
        'deleted_date': {'key': 'deletedDate', 'type': 'iso-8601'},
        'description': {'key': 'description', 'type': 'str'},
        'hide_deleted_package_versions': {'key': 'hideDeletedPackageVersions', 'type': 'bool'},
        'permissions': {'key': 'permissions', 'type': '[FeedPermission]'},
        'upstream_enabled_changed_date': {'key': 'upstreamEnabledChangedDate', 'type': 'iso-8601'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, allow_upstream_name_conflict=None, capabilities=None, fully_qualified_id=None, fully_qualified_name=None, id=None, is_read_only=None, name=None, upstream_enabled=None, upstream_sources=None, view=None, view_id=None, view_name=None, _links=None, badges_enabled=None, default_view_id=None, deleted_date=None, description=None, hide_deleted_package_versions=None, permissions=None, upstream_enabled_changed_date=None, url=None):
        super(Feed, self).__init__(allow_upstream_name_conflict=allow_upstream_name_conflict, capabilities=capabilities, fully_qualified_id=fully_qualified_id, fully_qualified_name=fully_qualified_name, id=id, is_read_only=is_read_only, name=name, upstream_enabled=upstream_enabled, upstream_sources=upstream_sources, view=view, view_id=view_id, view_name=view_name)
        self._links = _links
        self.badges_enabled = badges_enabled
        self.default_view_id = default_view_id
        self.deleted_date = deleted_date
        self.description = description
        self.hide_deleted_package_versions = hide_deleted_package_versions
        self.permissions = permissions
        self.upstream_enabled_changed_date = upstream_enabled_changed_date
        self.url = url
