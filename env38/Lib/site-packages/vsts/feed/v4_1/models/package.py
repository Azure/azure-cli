# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Package(Model):
    """Package.

    :param _links:
    :type _links: :class:`ReferenceLinks <packaging.v4_1.models.ReferenceLinks>`
    :param id:
    :type id: str
    :param is_cached:
    :type is_cached: bool
    :param name: The display name of the package
    :type name: str
    :param normalized_name: The normalized name representing the identity of this package for this protocol type
    :type normalized_name: str
    :param protocol_type:
    :type protocol_type: str
    :param star_count:
    :type star_count: int
    :param url:
    :type url: str
    :param versions:
    :type versions: list of :class:`MinimalPackageVersion <packaging.v4_1.models.MinimalPackageVersion>`
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'id': {'key': 'id', 'type': 'str'},
        'is_cached': {'key': 'isCached', 'type': 'bool'},
        'name': {'key': 'name', 'type': 'str'},
        'normalized_name': {'key': 'normalizedName', 'type': 'str'},
        'protocol_type': {'key': 'protocolType', 'type': 'str'},
        'star_count': {'key': 'starCount', 'type': 'int'},
        'url': {'key': 'url', 'type': 'str'},
        'versions': {'key': 'versions', 'type': '[MinimalPackageVersion]'}
    }

    def __init__(self, _links=None, id=None, is_cached=None, name=None, normalized_name=None, protocol_type=None, star_count=None, url=None, versions=None):
        super(Package, self).__init__()
        self._links = _links
        self.id = id
        self.is_cached = is_cached
        self.name = name
        self.normalized_name = normalized_name
        self.protocol_type = protocol_type
        self.star_count = star_count
        self.url = url
        self.versions = versions
