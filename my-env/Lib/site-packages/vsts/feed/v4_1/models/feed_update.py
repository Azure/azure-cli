# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class FeedUpdate(Model):
    """FeedUpdate.

    :param allow_upstream_name_conflict: If set, the feed will allow upload of packages that exist on the upstream
    :type allow_upstream_name_conflict: bool
    :param badges_enabled:
    :type badges_enabled: bool
    :param default_view_id:
    :type default_view_id: str
    :param description:
    :type description: str
    :param hide_deleted_package_versions: If set, feed will hide all deleted/unpublished versions
    :type hide_deleted_package_versions: bool
    :param id:
    :type id: str
    :param name:
    :type name: str
    :param upstream_enabled:
    :type upstream_enabled: bool
    :param upstream_sources:
    :type upstream_sources: list of :class:`UpstreamSource <packaging.v4_1.models.UpstreamSource>`
    """

    _attribute_map = {
        'allow_upstream_name_conflict': {'key': 'allowUpstreamNameConflict', 'type': 'bool'},
        'badges_enabled': {'key': 'badgesEnabled', 'type': 'bool'},
        'default_view_id': {'key': 'defaultViewId', 'type': 'str'},
        'description': {'key': 'description', 'type': 'str'},
        'hide_deleted_package_versions': {'key': 'hideDeletedPackageVersions', 'type': 'bool'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'upstream_enabled': {'key': 'upstreamEnabled', 'type': 'bool'},
        'upstream_sources': {'key': 'upstreamSources', 'type': '[UpstreamSource]'}
    }

    def __init__(self, allow_upstream_name_conflict=None, badges_enabled=None, default_view_id=None, description=None, hide_deleted_package_versions=None, id=None, name=None, upstream_enabled=None, upstream_sources=None):
        super(FeedUpdate, self).__init__()
        self.allow_upstream_name_conflict = allow_upstream_name_conflict
        self.badges_enabled = badges_enabled
        self.default_view_id = default_view_id
        self.description = description
        self.hide_deleted_package_versions = hide_deleted_package_versions
        self.id = id
        self.name = name
        self.upstream_enabled = upstream_enabled
        self.upstream_sources = upstream_sources
