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
    :type _links: :class:`ReferenceLinks <npm.v4_1.models.ReferenceLinks>`
    :param deprecate_message: Deprecated message, if any, for the package
    :type deprecate_message: str
    :param id:
    :type id: str
    :param name: The display name of the package
    :type name: str
    :param permanently_deleted_date: If and when the package was permanently deleted.
    :type permanently_deleted_date: datetime
    :param source_chain: The history of upstream sources for this package. The first source in the list is the immediate source from which this package was saved.
    :type source_chain: list of :class:`UpstreamSourceInfo <npm.v4_1.models.UpstreamSourceInfo>`
    :param unpublished_date: If and when the package was deleted
    :type unpublished_date: datetime
    :param version: The version of the package
    :type version: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'deprecate_message': {'key': 'deprecateMessage', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'permanently_deleted_date': {'key': 'permanentlyDeletedDate', 'type': 'iso-8601'},
        'source_chain': {'key': 'sourceChain', 'type': '[UpstreamSourceInfo]'},
        'unpublished_date': {'key': 'unpublishedDate', 'type': 'iso-8601'},
        'version': {'key': 'version', 'type': 'str'}
    }

    def __init__(self, _links=None, deprecate_message=None, id=None, name=None, permanently_deleted_date=None, source_chain=None, unpublished_date=None, version=None):
        super(Package, self).__init__()
        self._links = _links
        self.deprecate_message = deprecate_message
        self.id = id
        self.name = name
        self.permanently_deleted_date = permanently_deleted_date
        self.source_chain = source_chain
        self.unpublished_date = unpublished_date
        self.version = version
