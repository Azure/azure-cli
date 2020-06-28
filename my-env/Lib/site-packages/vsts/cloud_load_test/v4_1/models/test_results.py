# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestResults(Model):
    """TestResults.

    :param cloud_load_test_solution_url:
    :type cloud_load_test_solution_url: str
    :param counter_groups:
    :type counter_groups: list of :class:`CounterGroup <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.CounterGroup>`
    :param diagnostics:
    :type diagnostics: :class:`Diagnostics <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.Diagnostics>`
    :param results_url:
    :type results_url: str
    """

    _attribute_map = {
        'cloud_load_test_solution_url': {'key': 'cloudLoadTestSolutionUrl', 'type': 'str'},
        'counter_groups': {'key': 'counterGroups', 'type': '[CounterGroup]'},
        'diagnostics': {'key': 'diagnostics', 'type': 'Diagnostics'},
        'results_url': {'key': 'resultsUrl', 'type': 'str'}
    }

    def __init__(self, cloud_load_test_solution_url=None, counter_groups=None, diagnostics=None, results_url=None):
        super(TestResults, self).__init__()
        self.cloud_load_test_solution_url = cloud_load_test_solution_url
        self.counter_groups = counter_groups
        self.diagnostics = diagnostics
        self.results_url = results_url
