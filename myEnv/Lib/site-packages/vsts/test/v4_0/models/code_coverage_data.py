# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class CodeCoverageData(Model):
    """CodeCoverageData.

    :param build_flavor: Flavor of build for which data is retrieved/published
    :type build_flavor: str
    :param build_platform: Platform of build for which data is retrieved/published
    :type build_platform: str
    :param coverage_stats: List of coverage data for the build
    :type coverage_stats: list of :class:`CodeCoverageStatistics <test.v4_0.models.CodeCoverageStatistics>`
    """

    _attribute_map = {
        'build_flavor': {'key': 'buildFlavor', 'type': 'str'},
        'build_platform': {'key': 'buildPlatform', 'type': 'str'},
        'coverage_stats': {'key': 'coverageStats', 'type': '[CodeCoverageStatistics]'}
    }

    def __init__(self, build_flavor=None, build_platform=None, coverage_stats=None):
        super(CodeCoverageData, self).__init__()
        self.build_flavor = build_flavor
        self.build_platform = build_platform
        self.coverage_stats = coverage_stats
