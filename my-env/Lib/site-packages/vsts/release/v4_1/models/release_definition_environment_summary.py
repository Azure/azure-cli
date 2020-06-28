# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReleaseDefinitionEnvironmentSummary(Model):
    """ReleaseDefinitionEnvironmentSummary.

    :param id:
    :type id: int
    :param last_releases:
    :type last_releases: list of :class:`ReleaseShallowReference <release.v4_1.models.ReleaseShallowReference>`
    :param name:
    :type name: str
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'int'},
        'last_releases': {'key': 'lastReleases', 'type': '[ReleaseShallowReference]'},
        'name': {'key': 'name', 'type': 'str'}
    }

    def __init__(self, id=None, last_releases=None, name=None):
        super(ReleaseDefinitionEnvironmentSummary, self).__init__()
        self.id = id
        self.last_releases = last_releases
        self.name = name
