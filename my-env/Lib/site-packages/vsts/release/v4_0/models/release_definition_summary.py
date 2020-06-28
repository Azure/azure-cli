# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReleaseDefinitionSummary(Model):
    """ReleaseDefinitionSummary.

    :param environments:
    :type environments: list of :class:`ReleaseDefinitionEnvironmentSummary <release.v4_0.models.ReleaseDefinitionEnvironmentSummary>`
    :param release_definition:
    :type release_definition: :class:`ReleaseDefinitionShallowReference <release.v4_0.models.ReleaseDefinitionShallowReference>`
    :param releases:
    :type releases: list of :class:`Release <release.v4_0.models.Release>`
    """

    _attribute_map = {
        'environments': {'key': 'environments', 'type': '[ReleaseDefinitionEnvironmentSummary]'},
        'release_definition': {'key': 'releaseDefinition', 'type': 'ReleaseDefinitionShallowReference'},
        'releases': {'key': 'releases', 'type': '[Release]'}
    }

    def __init__(self, environments=None, release_definition=None, releases=None):
        super(ReleaseDefinitionSummary, self).__init__()
        self.environments = environments
        self.release_definition = release_definition
        self.releases = releases
