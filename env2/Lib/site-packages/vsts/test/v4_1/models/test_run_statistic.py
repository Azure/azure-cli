# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestRunStatistic(Model):
    """TestRunStatistic.

    :param run:
    :type run: :class:`ShallowReference <test.v4_1.models.ShallowReference>`
    :param run_statistics:
    :type run_statistics: list of :class:`RunStatistic <test.v4_1.models.RunStatistic>`
    """

    _attribute_map = {
        'run': {'key': 'run', 'type': 'ShallowReference'},
        'run_statistics': {'key': 'runStatistics', 'type': '[RunStatistic]'}
    }

    def __init__(self, run=None, run_statistics=None):
        super(TestRunStatistic, self).__init__()
        self.run = run
        self.run_statistics = run_statistics
