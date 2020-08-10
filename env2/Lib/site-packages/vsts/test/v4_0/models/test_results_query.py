# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestResultsQuery(Model):
    """TestResultsQuery.

    :param fields:
    :type fields: list of str
    :param results:
    :type results: list of :class:`TestCaseResult <test.v4_0.models.TestCaseResult>`
    :param results_filter:
    :type results_filter: :class:`ResultsFilter <test.v4_0.models.ResultsFilter>`
    """

    _attribute_map = {
        'fields': {'key': 'fields', 'type': '[str]'},
        'results': {'key': 'results', 'type': '[TestCaseResult]'},
        'results_filter': {'key': 'resultsFilter', 'type': 'ResultsFilter'}
    }

    def __init__(self, fields=None, results=None, results_filter=None):
        super(TestResultsQuery, self).__init__()
        self.fields = fields
        self.results = results
        self.results_filter = results_filter
