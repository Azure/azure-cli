# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestResultsGroupsForRelease(Model):
    """TestResultsGroupsForRelease.

    :param fields: The group by results
    :type fields: list of :class:`FieldDetailsForTestResults <test.v4_1.models.FieldDetailsForTestResults>`
    :param release_env_id: Release Environment Id for which groupby result is fetched.
    :type release_env_id: int
    :param release_id: ReleaseId for which groupby result is fetched.
    :type release_id: int
    """

    _attribute_map = {
        'fields': {'key': 'fields', 'type': '[FieldDetailsForTestResults]'},
        'release_env_id': {'key': 'releaseEnvId', 'type': 'int'},
        'release_id': {'key': 'releaseId', 'type': 'int'}
    }

    def __init__(self, fields=None, release_env_id=None, release_id=None):
        super(TestResultsGroupsForRelease, self).__init__()
        self.fields = fields
        self.release_env_id = release_env_id
        self.release_id = release_id
