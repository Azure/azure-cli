# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestResultsSummary(Model):
    """TestResultsSummary.

    :param overall_page_summary:
    :type overall_page_summary: :class:`PageSummary <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.PageSummary>`
    :param overall_request_summary:
    :type overall_request_summary: :class:`RequestSummary <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.RequestSummary>`
    :param overall_scenario_summary:
    :type overall_scenario_summary: :class:`ScenarioSummary <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.ScenarioSummary>`
    :param overall_test_summary:
    :type overall_test_summary: :class:`TestSummary <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.TestSummary>`
    :param overall_transaction_summary:
    :type overall_transaction_summary: :class:`TransactionSummary <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.TransactionSummary>`
    :param top_slow_pages:
    :type top_slow_pages: list of :class:`PageSummary <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.PageSummary>`
    :param top_slow_requests:
    :type top_slow_requests: list of :class:`RequestSummary <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.RequestSummary>`
    :param top_slow_tests:
    :type top_slow_tests: list of :class:`TestSummary <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.TestSummary>`
    :param top_slow_transactions:
    :type top_slow_transactions: list of :class:`TransactionSummary <microsoft.-visual-studio.-test-service.-web-api-model.v4_1.models.TransactionSummary>`
    """

    _attribute_map = {
        'overall_page_summary': {'key': 'overallPageSummary', 'type': 'PageSummary'},
        'overall_request_summary': {'key': 'overallRequestSummary', 'type': 'RequestSummary'},
        'overall_scenario_summary': {'key': 'overallScenarioSummary', 'type': 'ScenarioSummary'},
        'overall_test_summary': {'key': 'overallTestSummary', 'type': 'TestSummary'},
        'overall_transaction_summary': {'key': 'overallTransactionSummary', 'type': 'TransactionSummary'},
        'top_slow_pages': {'key': 'topSlowPages', 'type': '[PageSummary]'},
        'top_slow_requests': {'key': 'topSlowRequests', 'type': '[RequestSummary]'},
        'top_slow_tests': {'key': 'topSlowTests', 'type': '[TestSummary]'},
        'top_slow_transactions': {'key': 'topSlowTransactions', 'type': '[TransactionSummary]'}
    }

    def __init__(self, overall_page_summary=None, overall_request_summary=None, overall_scenario_summary=None, overall_test_summary=None, overall_transaction_summary=None, top_slow_pages=None, top_slow_requests=None, top_slow_tests=None, top_slow_transactions=None):
        super(TestResultsSummary, self).__init__()
        self.overall_page_summary = overall_page_summary
        self.overall_request_summary = overall_request_summary
        self.overall_scenario_summary = overall_scenario_summary
        self.overall_test_summary = overall_test_summary
        self.overall_transaction_summary = overall_transaction_summary
        self.top_slow_pages = top_slow_pages
        self.top_slow_requests = top_slow_requests
        self.top_slow_tests = top_slow_tests
        self.top_slow_transactions = top_slow_transactions
