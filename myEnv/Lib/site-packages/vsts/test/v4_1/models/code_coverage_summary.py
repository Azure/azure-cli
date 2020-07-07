# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CodeCoverageSummary(Model):
    """CodeCoverageSummary.

    :param build: Uri of build for which data is retrieved/published
    :type build: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param coverage_data: List of coverage data and details for the build
    :type coverage_data: list of :class:`CodeCoverageData <test.v4_1.models.CodeCoverageData>`
    :param delta_build: Uri of build against which difference in coverage is computed
    :type delta_build: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    """

    _attribute_map = {
        'build': {'key': 'build', 'type': 'ShallowReference'},
        'coverage_data': {'key': 'coverageData', 'type': '[CodeCoverageData]'},
        'delta_build': {'key': 'deltaBuild', 'type': 'ShallowReference'}
    }

    def __init__(self, build=None, coverage_data=None, delta_build=None):
        super(CodeCoverageSummary, self).__init__()
        self.build = build
        self.coverage_data = coverage_data
        self.delta_build = delta_build
