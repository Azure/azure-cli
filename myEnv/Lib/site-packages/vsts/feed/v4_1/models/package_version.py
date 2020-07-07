# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .minimal_package_version import MinimalPackageVersion


class PackageVersion(MinimalPackageVersion):
    """PackageVersion.

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
    :param _links:
    :type _links: :class:`ReferenceLinks <packaging.v4_1.models.ReferenceLinks>`
    :param author:
    :type author: str
    :param deleted_date:
    :type deleted_date: datetime
    :param dependencies:
    :type dependencies: list of :class:`PackageDependency <packaging.v4_1.models.PackageDependency>`
    :param description:
    :type description: str
    :param files:
    :type files: list of :class:`PackageFile <packaging.v4_1.models.PackageFile>`
    :param other_versions:
    :type other_versions: list of :class:`MinimalPackageVersion <packaging.v4_1.models.MinimalPackageVersion>`
    :param protocol_metadata:
    :type protocol_metadata: :class:`ProtocolMetadata <packaging.v4_1.models.ProtocolMetadata>`
    :param source_chain:
    :type source_chain: list of :class:`UpstreamSource <packaging.v4_1.models.UpstreamSource>`
    :param summary:
    :type summary: str
    :param tags:
    :type tags: list of str
    :param url:
    :type url: str
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
        'views': {'key': 'views', 'type': '[FeedView]'},
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'author': {'key': 'author', 'type': 'str'},
        'deleted_date': {'key': 'deletedDate', 'type': 'iso-8601'},
        'dependencies': {'key': 'dependencies', 'type': '[PackageDependency]'},
        'description': {'key': 'description', 'type': 'str'},
        'files': {'key': 'files', 'type': '[PackageFile]'},
        'other_versions': {'key': 'otherVersions', 'type': '[MinimalPackageVersion]'},
        'protocol_metadata': {'key': 'protocolMetadata', 'type': 'ProtocolMetadata'},
        'source_chain': {'key': 'sourceChain', 'type': '[UpstreamSource]'},
        'summary': {'key': 'summary', 'type': 'str'},
        'tags': {'key': 'tags', 'type': '[str]'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, direct_upstream_source_id=None, id=None, is_cached_version=None, is_deleted=None, is_latest=None, is_listed=None, normalized_version=None, package_description=None, publish_date=None, storage_id=None, version=None, views=None, _links=None, author=None, deleted_date=None, dependencies=None, description=None, files=None, other_versions=None, protocol_metadata=None, source_chain=None, summary=None, tags=None, url=None):
        super(PackageVersion, self).__init__(direct_upstream_source_id=direct_upstream_source_id, id=id, is_cached_version=is_cached_version, is_deleted=is_deleted, is_latest=is_latest, is_listed=is_listed, normalized_version=normalized_version, package_description=package_description, publish_date=publish_date, storage_id=storage_id, version=version, views=views)
        self._links = _links
        self.author = author
        self.deleted_date = deleted_date
        self.dependencies = dependencies
        self.description = description
        self.files = files
        self.other_versions = other_versions
        self.protocol_metadata = protocol_metadata
        self.source_chain = source_chain
        self.summary = summary
        self.tags = tags
        self.url = url
