# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestResultsGroupsForBuild(Model):
    """TestResultsGroupsForBuild.

    :param build_id: BuildId for which groupby result is fetched.
    :type build_id: int
    :param fields: The group by results
    :type fields: list of :class:`FieldDetailsForTestResults <test.v4_1.models.FieldDetailsForTestResults>`
    """

    _attribute_map = {
        'build_id': {'key': 'buildId', 'type': 'int'},
        'fields': {'key': 'fields', 'type': '[FieldDetailsForTestResults]'}
    }

    def __init__(self, build_id=None, fields=None):
        super(TestResultsGroupsForBuild, self).__init__()
        self.build_id = build_id
        self.fields = fields
