# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class MinimalPackageVersion(Model):
    """MinimalPackageVersion.

    :param direct_upstream_source_id:
    :type direct_upstream_source_id: str
    :param id:
    :type id: str
    :param is_cached_version:
    :type is_cached_version: bool
    :param is_deleted:
    :type is_deleted: bool
    :param is_latest:
    :type is_latest: bool
    :param is_listed:
    :type is_listed: bool
    :param normalized_version: The normalized version representing the identity of a package version
    :type normalized_version: str
    :param package_description:
    :type package_description: str
    :param publish_date:
    :type publish_date: datetime
    :param storage_id:
    :type storage_id: str
    :param version: The display version of the package version
    :type version: str
    :param views:
    :type views: list of :class:`FeedView <packaging.v4_1.models.FeedView>`
    """

    _attribute_map = {
        'direct_upstream_source_id': {'key': 'directUpstreamSourceId', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'is_cached_version': {'key': 'isCachedVersion', 'type': 'bool'},
        'is_deleted': {'key': 'isDeleted', 'type': 'bool'},
        'is_latest': {'key': 'isLatest', 'type': 'bool'},
        'is_listed': {'key': 'isListed', 'type': 'bool'},
        'normalized_version': {'key': 'normalizedVersion', 'type': 'str'},
        'package_description': {'key': 'packageDescription', 'type': 'str'},
        'publish_date': {'key': 'publishDate', 'type': 'iso-8601'},
        'storage_id': {'key': 'storageId', 'type': 'str'},
        'version': {'key': 'version', 'type': 'str'},
        'views': {'key': 'views', 'type': '[FeedView]'}
    }

    def __init__(self, direct_upstream_source_id=None, id=None, is_cached_version=None, is_deleted=None, is_latest=None, is_listed=None, normalized_version=None, package_description=None, publish_date=None, storage_id=None, version=None, views=None):
        super(MinimalPackageVersion, self).__init__()
        self.direct_upstream_source_id = direct_upstream_source_id
        self.id = id
        self.is_cached_version = is_cached_version
        self.is_deleted = is_deleted
        self.is_latest = is_latest
        self.is_listed = is_listed
        self.normalized_version = normalized_version
        self.package_description = package_description
        self.publish_date = publish_date
        self.storage_id = storage_id
        self.version = version
        self.views = views
