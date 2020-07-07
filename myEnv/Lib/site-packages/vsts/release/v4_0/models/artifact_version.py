# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ArtifactVersion(Model):
    """ArtifactVersion.

    :param alias:
    :type alias: str
    :param default_version:
    :type default_version: :class:`BuildVersion <release.v4_0.models.BuildVersion>`
    :param error_message:
    :type error_message: str
    :param source_id:
    :type source_id: str
    :param versions:
    :type versions: list of :class:`BuildVersion <release.v4_0.models.BuildVersion>`
    """

    _attribute_map = {
        'alias': {'key': 'alias', 'type': 'str'},
        'default_version': {'key': 'defaultVersion', 'type': 'BuildVersion'},
        'error_message': {'key': 'errorMessage', 'type': 'str'},
        'source_id': {'key': 'sourceId', 'type': 'str'},
        'versions': {'key': 'versions', 'type': '[BuildVersion]'}
    }

    def __init__(self, alias=None, default_version=None, error_message=None, source_id=None, versions=None):
        super(ArtifactVersion, self).__init__()
        self.alias = alias
        self.default_version = default_version
        self.error_message = error_message
        self.source_id = source_id
        self.versions = versions
